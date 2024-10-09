import os
from os import path
from typing import Any, Optional

import requests
import yaml
from pydantic import BaseModel

LATEST_USER_AGENTS_API_URL = "https://jnrbsn.github.io/user-agents/user-agents.json"


def get_latest_windows_chrome_user_agent() -> str:
    user_agents: list[str] = requests.get(LATEST_USER_AGENTS_API_URL).json()
    for user_agent in user_agents:
        if (
            "Windows NT" in user_agent
            and "Chrome/" in user_agent
            and not "Edg/" in user_agent
        ):
            return user_agent
    raise ValueError("No user agent found")


class RequestConfig(BaseModel):
    user_agent: str = get_latest_windows_chrome_user_agent()


class AuthConfig(BaseModel):
    token: str = ""


class DownloadConfig(BaseModel):
    download_account_files: bool = False
    account_dir_path: str = "."
    account_data_filename: Optional[str] = "account.json"
    account_subscriptions_data_filename: Optional[str] = "account_subscriptions.json"
    account_about_text_filename: Optional[str] = "account_about.txt"
    download_user_files: bool = True
    user_dir_path: str = "[<user.username>] <user.name>"
    user_data_filename: Optional[str] = "user.json"
    user_plans_data_filename: Optional[str] = "user_plans.json"
    user_about_text_filename: Optional[str] = "user_about.txt"
    post_dir_path: str = (
        "[<post.user.username>] <post.user.name>/[<post.published_at:%Y.%m.%d>] <post.id> (<post_from_list.free:free,paid>,<post_from_list.limited:limited,unlocked>)"
    )
    post_data_filename: Optional[str] = "post.json"
    post_from_list_data_filename: Optional[str] = "post_from_list.json"
    post_tags_data_filename: Optional[str] = "post_tags.json"
    post_videos_data_filename: Optional[str] = "post_videos.json"
    post_body_text_filename: Optional[str] = "post_body.txt"


class Config(BaseModel):
    request: RequestConfig
    auth: AuthConfig
    download: DownloadConfig


def init_config(raw_config: Optional[dict[str, Any]]) -> Config:
    if raw_config is None:
        if path.exists("config.yaml"):
            os.replace("config.yaml", "config.yaml.bak")
        config = Config(
            request=RequestConfig(),
            auth=AuthConfig(),
            download=DownloadConfig(),
        )
    else:
        config = Config(**raw_config)
    config_dict = config.model_dump()
    with open("config.yaml", "w") as f:
        yaml.dump(config_dict, f)
    return config


def get_config() -> Config:
    try:
        with open("config.yaml", "r") as f:
            config_dict = yaml.safe_load(f)
        return init_config(config_dict)
    except Exception as e:
        print(e)
        return init_config(None)
