import os
import subprocess
import sys
from datetime import datetime
from os import path
from pathlib import Path
from posixpath import join as urljoin
from typing import Literal

from pydantic import TypeAdapter
from tqdm import tqdm

from config import get_config
from location import LocationGetter
from models import (
    AccountModel,
    PlanModel,
    PostFromListModel,
    PostModel,
    PostTagModel,
    PostVideoModel,
    PostVideosModel,
    SubscriptionModel,
    UserModel,
)
from requester import Requester

LAST_MODIFIED_PATTERN = "%a, %d %b %Y %H:%M:%S %Z"

# TODO
supported_video_resolutions = [240, 360, 480, 720, 1080, 1440, 2160]


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


def download_video(
    requester: Requester,
    video_type: Literal["trial"] | Literal["main"],
    video_index: int,
    video: PostVideoModel,
    dir_path: str,
) -> None:
    video_url_dirname = path.dirname(video.url)
    video_url_stem = Path(video.url).stem
    video_resolution = min(
        r for r in [video.width, video.height] if r in supported_video_resolutions
    )
    video_url = urljoin(video_url_dirname, video_url_stem, f"{video_resolution}p.m3u8")
    video_filename = f"[{video_type}.{video_index:02d}] [{video_url_stem[:8]}] ({video.resolution},{video.width}×{video.height}).mp4"
    video_file_path = path.join(dir_path, video_filename)
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_url,
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-loglevel",
                "error",
                video_file_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode())


def download_account(
    requester: Requester, location_getter: LocationGetter
) -> tuple[AccountModel, list[SubscriptionModel]]:
    account = requester.get_account()
    account_subscriptions = requester.get_account_subscriptions()
    location_getter.update_data_dict("account", account)
    location_getter.update_data_dict("account_subscriptions", account_subscriptions)

    dir_path = location_getter.get_account_dir_path()
    if not path.exists(dir_path):
        os.makedirs(dir_path)

    conf = requester.config.download.account
    if (n := conf.account_data_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
            f.write(account.model_dump_json())
    if (n := conf.account_subscriptions_data_filename) is not None:
        with open(path.join(dir_path, n), "wb") as f:
            f.write(
                TypeAdapter(list[SubscriptionModel]).dump_json(account_subscriptions)
            )
    if (n := conf.account_about_text_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
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
    location_getter: LocationGetter,
) -> tuple[UserModel, list[PlanModel]]:
    user = requester.get_user(id_or_username, by)
    user_plans = requester.get_user_plans(user.id)
    location_getter.update_data_dict("user", user)
    location_getter.update_data_dict("user_plans", user_plans)

    dir_path = location_getter.get_user_dir_path()
    if not path.exists(dir_path):
        os.makedirs(dir_path)

    conf = requester.config.download.user
    if (n := conf.user_data_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
            f.write(user.model_dump_json())
    if (n := conf.user_plans_data_filename) is not None:
        with open(path.join(dir_path, n), "wb") as f:
            f.write(TypeAdapter(list[PlanModel]).dump_json(user_plans))

    if (n := conf.user_about_text_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
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
    post_from_list: PostFromListModel,
    location_getter: LocationGetter,
) -> tuple[PostModel, list[PostTagModel], PostVideosModel]:
    post = requester.get_post(post_from_list.id)
    post_tags = requester.get_post_tags(post_from_list.id)
    post_videos = requester.get_post_videos(post_from_list.id)
    location_getter.update_data_dict("post_from_list", post_from_list)
    location_getter.update_data_dict("post", post)
    location_getter.update_data_dict("post_tags", post_tags)
    location_getter.update_data_dict("post_videos", post_videos)

    dir_path = location_getter.get_post_dir_path()
    if not path.exists(dir_path):
        os.makedirs(dir_path)

    conf = requester.config.download.post
    if (n := conf.post_data_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
            f.write(post.model_dump_json())
    if (n := conf.post_from_list_data_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
            f.write(post_from_list.model_dump_json())
    if (n := conf.post_tags_data_filename) is not None:
        with open(path.join(dir_path, n), "wb") as f:
            f.write(TypeAdapter(list[PostTagModel]).dump_json(post_tags))
    if (n := conf.post_videos_data_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
            f.write(post_videos.model_dump_json())
    if (n := conf.post_body_text_filename) is not None:
        with open(path.join(dir_path, n), "w") as f:
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

    if post_videos.trial is not None:
        for i, video in enumerate(post_videos.trial):
            download_video(requester, "trial", i, video, dir_path)
    if post_videos.main is not None:
        for i, video in enumerate(post_videos.main):
            download_video(requester, "main", i, video, dir_path)

    return post, post_tags, post_videos


def main():
    config = get_config()
    if config.auth.token == "":
        print("Please fill in the token in config.toml")
        return

    requester = Requester(config)

    username = sys.argv[1]

    location_getter = LocationGetter(config)

    if config.download.need_scrape_account:
        download_account(requester, location_getter)
    user, _ = download_user(requester, username, "username", location_getter)
    posts = requester.get_user_posts(user.id, 200, 1).data
    progress_bar = tqdm(total=len(posts), desc="Downloading posts", unit="posts")
    for post_from_list in posts:
        download_post(requester, post_from_list, location_getter)
        progress_bar.update(1)
    progress_bar.close()


if __name__ == "__main__":
    main()
