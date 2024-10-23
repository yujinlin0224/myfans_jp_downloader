import re
import string
from collections.abc import Callable
from datetime import datetime
from functools import reduce
from os import path
from typing import Any, Optional, Sequence, Union, cast, get_args, get_origin

from pathvalidate import sanitize_filename
from pydantic import BaseModel

import models
from config import Config

PydanticModel = BaseModel | Sequence[BaseModel] | dict[str, BaseModel]

model_type_dict: dict[str, type[PydanticModel]] = {
    "account": models.AccountModel,
    "user": models.UserModel,
    "post_from_list": models.PostFromListModel,
    "post": models.PostModel,
    "post_tags": list[models.PostTagModel],
    "post_videos": models.PostVideosModel,
}

SupportedType = bool | int | float | str | datetime
DataDictType = dict[str, Any]


template_pattern = re.compile(
    r"<(?P<key_path>[\w.]+)(?::(?P<pattern>[^|<>]+))?(?:\|(?P<default>[^|<>]+))?>"
)
str_method_pattern = re.compile(r"\.\s*(\w+)\s*\(([^()]*)\)")


def is_type_or_its_optional(
    test: type[PydanticModel] | SupportedType | None, targets: Sequence[type]
) -> bool:
    if test in targets:
        return True
    if not (get_origin(test) is Union):
        return False
    type_args = get_args(test)
    return (type_args[0] is type(None) and type_args[1] in targets) or (
        type_args[1] is type(None) and type_args[0] in targets
    )


def get_key_path_type_in_models(key_path: str) -> SupportedType | None:
    keys = key_path.split(".")
    type_ = model_type_dict[keys[0]]
    for key in keys[1:]:
        if get_origin(type_) is list:
            if set(key).issubset(string.digits):
                type_ = cast(
                    type[PydanticModel] | SupportedType | None,
                    get_args(type_)[0],
                )
            else:
                raise ValueError(f"Invalid path: '{key_path}' at '{key}'")
        else:
            try:
                type_ = cast(
                    type[PydanticModel] | SupportedType | None,
                    cast(type[BaseModel], type_).model_fields[key].annotation,
                )
            except (KeyError, AttributeError):
                raise ValueError(f"Invalid path: '{key_path}' at '{key}'")

    if not is_type_or_its_optional(type_, get_args(SupportedType)):
        raise ValueError(f"The path '{key_path}' does not point to supported type")
    return cast(SupportedType | None, type_)


supported_str_method_args_dict: dict[str, list[list[type]]] = {
    # str to str methods
    "capitalize": [[]],
    "casefold": [[]],
    "center": [[int], [int, str]],
    "expandtabs": [[], [int]],
    "ljust": [[int], [int, str]],
    "lower": [[]],
    "lstrip": [[], [str]],
    "removeprefix": [[str]],
    "removesuffix": [[str]],
    "replace": [[str, str], [str, str, int]],
    "rjust": [[int], [int, str]],
    "rstrip": [[], [str]],
    "strip": [[], [str]],
    "swapcase": [[]],
    "title": [[]],
    "upper": [[]],
    "zfill": [[int]],
    # special methods
    "slice": [[int], [int, int], [int, int, int]],
}


def parse_str_method(method_name: str, method_args_str: str) -> Callable[[str], str]:
    method_name = method_name.strip()
    if not (method_name in supported_str_method_args_dict):
        raise ValueError(f"Unsupported method: {method_name}")
    supported_method_args_list = supported_str_method_args_dict[method_name]
    method_arg_strs = [arg.strip() for arg in method_args_str.split(",")]
    method_args_indexes: list[int] = [
        i
        for i, args in enumerate(supported_method_args_list)
        if len(args) == len(method_arg_strs)
    ]
    if len(method_args_indexes) == 0:
        raise ValueError(
            f"Unsupported arguments for method: {method_name}: {method_arg_strs}"
        )
    method_args: Optional[list[object]] = None
    for i in method_args_indexes:
        supported_method_args = supported_method_args_list[i]
        try:
            method_args = [t(a) for t, a in zip(supported_method_args, method_arg_strs)]
            break
        except Exception:
            pass
    if method_args is None:
        raise ValueError(
            f"Unsupported arguments for method: {method_name}: {method_arg_strs}"
        )
    match method_name:
        case "slice":
            return lambda s: s[slice(*method_args)]
        case _:
            return lambda s: getattr(s, method_name)(*method_args)


def parse_str_methods(raw_string: str) -> list[Callable[[str], str]]:
    raw_string = "." + raw_string.strip(".")
    methods = [
        parse_str_method(*cast(tuple[str, str], matched))
        for matched in str_method_pattern.findall(raw_string)
    ]
    if len(methods) == 0:
        return [lambda s: s]
    return methods


def make_location_generator(template: str) -> Callable[[DataDictType], str]:

    replacer_dict: dict[str, Callable[[DataDictType], str]] = {}

    for match in template_pattern.finditer(template):
        key_path: Optional[str] = match.group("key_path")
        pattern = m if (m := match.group("pattern")) and type(m) is str else ""
        default = m if (m := match.group("default")) and type(m) is str else ""
        if key_path is None:
            continue

        key_path_type = get_key_path_type_in_models(key_path)

        def create_replacer(
            key_path: str = key_path,
            pattern: str = pattern,
            default: str = default,
        ) -> Callable[[DataDictType], str]:

            def value_getter(data_dict: DataDictType, key_path: str) -> Any:
                return reduce(
                    lambda d, k: (
                        cast(list[Any], d)[int(k)] if isinstance(d, Sequence) else d[k]
                    ),
                    key_path.split("."),
                    data_dict,
                )

            if is_type_or_its_optional(key_path_type, [bool]):
                pattern = pattern or f"{key_path}=true,{key_path}=false"
                true_value, false_value = pattern.split(",")

                def replacer(data_dict: DataDictType) -> str:
                    value: Optional[bool] = value_getter(data_dict, key_path)
                    if value is None:
                        return default
                    return true_value if value else false_value

            elif is_type_or_its_optional(key_path_type, [int, float]):
                if pattern != "":
                    pattern = f"{{:{pattern}}}"
                else:
                    pattern = "{}"

                def replacer(data_dict: DataDictType) -> str:
                    value: Optional[int | float] = value_getter(data_dict, key_path)
                    if value is None:
                        return default
                    return pattern.format(value)

            elif is_type_or_its_optional(key_path_type, [str]):
                methods = parse_str_methods(pattern)

                def replacer(data_dict: DataDictType) -> str:
                    value: Optional[str] = value_getter(data_dict, key_path)
                    if value is None:
                        return default
                    for method in methods:
                        value = method(value)
                    return re.sub(r"\s+", " ", sanitize_filename(value, " ")).strip()

            elif is_type_or_its_optional(key_path_type, [datetime]):
                if pattern == "":
                    pattern = "%Y.%m.%d"

                def replacer(data_dict: DataDictType) -> str:
                    value: Optional[datetime] = value_getter(data_dict, key_path)
                    if value is None:
                        return default
                    return value.strftime(pattern)

            else:
                raise ValueError(f"Unsupported type: {key_path_type}")

            return replacer

        replacer_dict[match.group(0)] = create_replacer(key_path, pattern, default)

    def location_generator(data_dict: DataDictType) -> str:
        location = template
        for match, replacer in replacer_dict.items():
            location = location.replace(
                match, sanitize_filename(replacer(data_dict), "_")
            )
        return location

    return location_generator


# TODO
class LocationGetter:
    def __init__(self, config: Config) -> None:
        self.__downloads_dir_path_generator = make_location_generator(
            config.download.dir_path
        )
        self.__account_dir_path_generator = make_location_generator(
            config.download.account.dir_path
        )
        self.__user_dir_path_generator = make_location_generator(
            config.download.user.dir_path
        )
        self.__post_dir_path_generator = make_location_generator(
            config.download.post.dir_path
        )
        self.__data_dict: DataDictType = {}

    def update_data_dict(self, key: str, model: PydanticModel) -> None:
        if isinstance(model, dict):
            dumped = {k: v.model_dump() for k, v in model.items()}
        elif isinstance(model, Sequence):
            dumped = [v.model_dump() for v in model]
        else:
            dumped = model.model_dump()
        self.__data_dict[key] = dumped

    def get_account_dir_path(self) -> str:
        download_dir_path = self.__downloads_dir_path_generator(self.__data_dict)
        account_dir_path = self.__account_dir_path_generator(self.__data_dict)
        return path.join(download_dir_path, account_dir_path)

    def get_user_dir_path(self) -> str:
        download_dir_path = self.__downloads_dir_path_generator(self.__data_dict)
        user_dir_path = self.__user_dir_path_generator(self.__data_dict)
        return path.join(download_dir_path, user_dir_path)

    def get_post_dir_path(self) -> str:
        download_dir_path = self.__downloads_dir_path_generator(self.__data_dict)
        post_dir_path = self.__post_dir_path_generator(self.__data_dict)
        return path.join(download_dir_path, post_dir_path)
