from typing import Literal

import requests
from pydantic import TypeAdapter

import models
import urls
from config import Config
from headers import get_headers


class Requester:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers = get_headers(config)
        if config.request.proxy_url is not None and config.request.proxy_url != "":
            self.session.proxies.update({"https": config.request.proxy_url})

    def get_account(self) -> models.AccountModel:
        url = urls.get_account
        resp = self.session.get(url)
        resp.raise_for_status()
        return models.AccountModel(**resp.json())

    def get_account_subscriptions(self) -> list[models.SubscriptionModel]:
        url = urls.get_account_subscriptions
        resp = self.session.get(url)
        resp.raise_for_status()
        return TypeAdapter(list[models.SubscriptionModel]).validate_python(resp.json())

    def get_plan_posts(
        self, id: str, per_page: int, page: int
    ) -> models.PagedDataModel[models.PostFromListModel]:
        url = urls.get_plan_posts.format(id=id, per_page=per_page, page=page)
        resp = self.session.get(url)
        resp.raise_for_status()
        return models.PagedDataModel[models.PostFromListModel](**resp.json())

    def get_post(self, id: str) -> models.PostModel:
        url = urls.get_post.format(id=id)
        resp = self.session.get(url)
        resp.raise_for_status()
        return models.PostModel(**resp.json())

    def get_post_tags(self, id: str) -> list[models.PostTagModel]:
        url = urls.get_post_tags.format(id=id)
        resp = self.session.get(url)
        resp.raise_for_status()
        return TypeAdapter(list[models.PostTagModel]).validate_python(resp.json())

    def get_post_videos(self, id: str) -> models.PostVideosModel:
        url = urls.get_post_videos.format(id=id)
        resp = self.session.get(url)
        resp.raise_for_status()
        return models.PostVideosModel(**resp.json())

    def get_user(
        self, id_or_username: str, by: Literal["id"] | Literal["username"]
    ) -> models.UserModel:
        match by:
            case "id":
                url = urls.get_user.format(id=id_or_username)
            case "username":
                url = urls.get_user_by_username.format(username=id_or_username)
        resp = self.session.get(url)
        resp.raise_for_status()
        return models.UserModel(**resp.json())

    def get_user_plans(self, id: str) -> list[models.PlanModel]:
        url = urls.get_user_plans.format(id=id)
        resp = self.session.get(url)
        resp.raise_for_status()
        return TypeAdapter(list[models.PlanModel]).validate_python(resp.json())

    def get_user_posts(
        self, id: str, per_page: int, page: int
    ) -> models.PagedDataModel[models.PostFromListModel]:
        url = urls.get_user_posts.format(id=id, per_page=per_page, page=page)
        resp = self.session.get(url)
        resp.raise_for_status()
        return models.PagedDataModel[models.PostFromListModel](**resp.json())
