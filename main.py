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
    dir_path = path.join(
        requester.config.download.downloads_dir_path,
        dir_path,
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

    image_urls = {
        *account.appeal_image_urls,
        account.avatar_url,
        account.banner_url,
    }
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
    dir_path = path.join(
        requester.config.download.downloads_dir_path,
        dir_path,
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

    image_urls = {
        user.avatar_url,
        user.banner_url,
    }
    for image_url in image_urls:
        if image_url == "":
            continue
        download_image(requester, image_url, dir_path)
    return user, user_plans


def download_post(
    requester: Requester,
    account: models.AccountModel,
    user: models.UserModel,
    post_from_list: models.PostFromListModel,
) -> tuple[models.PostModel, list[models.PostTagModel], models.PostVideosModel]:
    post = requester.get_post(post_from_list.id)
    post_tags = requester.get_post_tags(post_from_list.id)
    post_videos = requester.get_post_videos(post_from_list.id)

    dir_path = generate_location_from_template(
        requester.config.download.post_dir_path,
        account,
        user,
        post_from_list,
        post,
        post_tags,
        post_videos,
    )
    dir_path = path.join(
        requester.config.download.downloads_dir_path,
        dir_path,
    )
    if not path.exists(dir_path):
        os.makedirs(dir_path)

    if requester.config.download.post_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.post_data_filename), "w"
        ) as f:
            f.write(post.model_dump_json())
    if requester.config.download.post_from_list_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.post_from_list_data_filename),
            "w",
        ) as f:
            f.write(post_from_list.model_dump_json())
    if requester.config.download.post_tags_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.post_tags_data_filename),
            "wb",
        ) as f:
            f.write(TypeAdapter(list[models.PostTagModel]).dump_json(post_tags))
    if requester.config.download.post_videos_data_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.post_videos_data_filename),
            "w",
        ) as f:
            f.write(post_videos.model_dump_json())
    if requester.config.download.post_body_text_filename is not None:
        with open(
            path.join(dir_path, requester.config.download.post_body_text_filename),
            "w",
        ) as f:
            f.write(post.body)

    image_urls = {
        post.thumbnail_url,
        post.post_image.file_url,
        *(
            [post.post_image.square_thumbnail_url]
            if post.post_image.square_thumbnail_url is not None
            else []
        ),
        *(
            [video.image_url for video in post.videos.trial]
            if post.videos.trial is not None
            else []
        ),
        *(
            [video.image_url for video in post.videos.main]
            if post.videos.main is not None
            else []
        ),
        *[image.url for image in post.images],
        post_from_list.thumbnail_url,
        *[image.file_url for image in post_from_list.post_images],
        *[
            image.square_thumbnail_url
            for image in post_from_list.post_images
            if image.square_thumbnail_url is not None
        ],
        *(
            [video.image_url for video in post_videos.trial]
            if post_videos.trial
            else []
        ),
        *([video.image_url for video in post_videos.main] if post_videos.main else []),
    }
    for image_url in image_urls:
        if image_url == "":
            continue
        download_image(requester, image_url, dir_path)

    return post, post_tags, post_videos


def main():
    config = get_config()
    if config.auth.token == "":
        print("Please fill in the token in config.toml")
        return

    requester = Requester(config)

    username = sys.argv[1]

    account, account_subscriptions = download_account(requester)
    user, user_plans = download_user(requester, username, "username", account)

    posts = requester.get_user_posts(user.id, 200, 1).data
    for post_from_list in posts:
        download_post(requester, account, user, post_from_list)


if __name__ == "__main__":
    main()
