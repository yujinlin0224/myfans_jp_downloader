import os
import sys
from datetime import datetime
from os import path
from typing import Literal

from pydantic import TypeAdapter

import models
from config import get_config
from location import generate_location_from_template
from requester import Requester

LAST_MODIFIED_PATTERN = "%a, %d %b %Y %H:%M:%S %Z"


def download_image(requester: Requester, url: str, dir_path: str) -> None:
    image_filename = path.basename(url)
    image_file_path = path.join(dir_path, image_filename)
    with open(image_file_path, "wb") as f:
        resp = requester.session.get(url)
        f.write(resp.content)
    access_time = modification_time = datetime.strptime(
        resp.headers["Last-Modified"], LAST_MODIFIED_PATTERN
    ).timestamp()
    os.utime(image_file_path, (access_time, modification_time))


def download_account(
    requester: Requester,
) -> tuple[models.AccountModel, list[models.SubscriptionModel]]:
    account = requester.get_account()
    account_subscriptions = requester.get_account_subscriptions()
    if not requester.config.download.download_account_files:
        return account, account_subscriptions

    dir_path = generate_location_from_template(
        requester.config.download.account_dir_path,
        account,
        None,
        None,
        None,
        None,
        None,
    )
    if not path.exists(dir_path):
        os.makedirs(dir_path)

    if requester.config.download.account_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.account_data_filename), "w"
        ) as f:
            f.write(account.model_dump_json())
    if requester.config.download.account_subscriptions_data_filename is not None:
        with open(
            path.join(
                dir_path, requester.config.download.account_subscriptions_data_filename
            ),
            "wb",
        ) as f:
            f.write(
                TypeAdapter(list[models.SubscriptionModel]).dump_json(
                    account_subscriptions
                )
            )
    if requester.config.download.account_about_text_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.account_about_text_filename),
            "w",
        ) as f:
            f.write(account.about)

    image_urls = [
        *account.appeal_image_urls,
        account.avatar_url,
        account.banner_url,
    ]
    for image_url in image_urls:
        if image_url == "":
            continue
        download_image(requester, image_url, dir_path)
    return account, account_subscriptions


def download_user(
    requester: Requester,
    id_or_username: str,
    by: Literal["id"] | Literal["username"],
    account: models.AccountModel,
) -> tuple[models.UserModel, list[models.PlanModel]]:
    user = requester.get_user(id_or_username, by)
    user_plans = requester.get_user_plans(user.id)

    dir_path = generate_location_from_template(
        requester.config.download.user_dir_path,
        account,
        user,
        None,
        None,
        None,
        None,
    )
    if not path.exists(dir_path):
        os.makedirs(dir_path)

    if requester.config.download.user_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.user_data_filename), "w"
        ) as f:
            f.write(user.model_dump_json())
    if requester.config.download.user_plans_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.user_plans_data_filename),
            "wb",
        ) as f:
            f.write(TypeAdapter(list[models.PlanModel]).dump_json(user_plans))

    if requester.config.download.user_about_text_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.user_about_text_filename),
            "w",
        ) as f:
            f.write(user.about)

    image_urls = [
        user.avatar_url,
        user.banner_url,
    ]
    for image_url in image_urls:
        if image_url == "":
            continue
        download_image(requester, image_url, dir_path)

    return user, user_plans


def main():
    config = get_config()
    if config.auth.token == "":
        print("Please fill in the token in config.yaml")
        return

    requester = Requester(config)

    username = sys.argv[1]

    account, account_subscriptions = download_account(requester)
    user, user_plans = download_user(requester, username, "username", account)

    posts = requester.get_user_posts(user.id, 200, 1).data
    for post_from_list in posts:
        post = requester.get_post(post_from_list.id)
        post_tags = requester.get_post_tags(post_from_list.id)
        post_videos = requester.get_post_videos(post_from_list.id)
        post_dir_path = generate_location_from_template(
            config.download.post_dir_path,
            account,
            user,
            post_from_list,
            post,
            post_tags,
            post_videos,
        )
        print(post_dir_path)


if __name__ == "__main__":
    main()
