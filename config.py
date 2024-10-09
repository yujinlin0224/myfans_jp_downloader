import os
from os import path

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
    user_agent: str


class AuthConfig(BaseModel):
    token: str


class Config(BaseModel):
    request: RequestConfig
    auth: AuthConfig


def init_config() -> Config:
    if path.exists("config.yaml"):
        os.replace("config.yaml", "config.yaml.bak")
    config = Config(
        request=RequestConfig(user_agent=get_latest_windows_chrome_user_agent()),
        auth=AuthConfig(token=""),
    )
    config_dict = config.model_dump()
    with open("config.yaml", "w") as f:
        yaml.dump(config_dict, f)
    return config


def get_config() -> Config:
    try:
        with open("config.yaml", "r") as f:
            config_dict = yaml.safe_load(f)
        return Config(**config_dict)
    except Exception as e:
        print(e)
        return init_config()
