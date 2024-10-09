import re
from datetime import datetime
from functools import reduce
from typing import Any, Optional, cast

from models import (
    AccountModel,
    PostFromListModel,
    PostModel,
    PostTagModel,
    PostVideosModel,
    UserModel,
)

template_pattern = re.compile(
    r"<(?P<key>[^:|<>]+)(?::(?P<pattern>[^:|<>]+))?(?:\|(?P<default>[^:|<>]+))?>"
)


def generate_location_from_template(
    template: str,
    account: Optional[AccountModel],
    user: Optional[UserModel],
    post_from_list: Optional[PostFromListModel],
    post: Optional[PostModel],
    post_tags: Optional[list[PostTagModel]],
    post_videos: Optional[PostVideosModel],
) -> str:
    data_dict: dict[str, Any] = {}
    if account is not None:
        data_dict["account"] = account.model_dump()
    if user is not None:
        data_dict["user"] = user.model_dump()
    if post_from_list is not None:
        data_dict["post_from_list"] = post_from_list.model_dump()
    if post is not None:
        data_dict["post"] = post.model_dump()
    if post_tags is not None:
        data_dict["post_tags"] = [post_tag.model_dump() for post_tag in post_tags]
    if post_videos is not None:
        data_dict["post_videos"] = post_videos.model_dump()

    replacement_dict: dict[str, str] = {}

    for match in template_pattern.finditer(template):
        key: Optional[str] = match.group("key")
        pattern: Optional[str] = match.group("pattern")
        default: Optional[str] = match.group("default")
        if key is None:
            continue
        if pattern is None:
            pattern = ""
        if default is None:
            default = ""
        value: Any = reduce(
            lambda d, k: (cast(list[Any], d)[int(k)] if isinstance(d, list) else d[k]),
            key.split("."),
            data_dict,
        )
        if value is None or value == "":
            replacement_dict[match.group(0)] = default
        if type(value) is str:
            result_value = value
            if pattern != "":
                try:
                    datetime_value = datetime.fromisoformat(value)
                    result_value = datetime_value.strftime(pattern)
                except ValueError:
                    pass
            replacement_dict[match.group(0)] = result_value
        if type(value) is int or type(value) is float:
            if pattern != "":
                replacement_dict[match.group(0)] = f"{{:{pattern}}}".format(value)
            else:
                replacement_dict[match.group(0)] = str(value)
        if type(value) is bool:
            pattern = pattern or f"{key}=true,{key}=false"
            true_value, false_value = pattern.split(",")
            replacement_dict[match.group(0)] = true_value if value else false_value

    result = template
    for key, value in replacement_dict.items():
        result = result.replace(key, value.strip())
    return result
