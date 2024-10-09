import sys

from config import get_config
from requester import Requester


def main():
    config = get_config()
    if config.auth.token == "":
        print("Please fill in the token in config.yaml")
        return

    requester = Requester(config)

    username = sys.argv[1]

    print(requester.get_account())
    user = requester.get_user_by_username(username)
    print(requester.get_user(user.id))

    # subscriptions = requester.get_account_subscriptions()
    # posts = requester.get_plan_posts(subscriptions[0].plan.id, 200, 1).data
    # for post in posts:
    #     print(requester.get_post(post.id))
    #     print(requester.get_post_tags(post.id))
    #     print(requester.get_post_videos(post.id))
    posts = requester.get_user_posts(user.id, 200, 1).data
    for post in posts:
        print(requester.get_post(post.id))
        print(requester.get_post_tags(post.id))
        print(requester.get_post_videos(post.id))


if __name__ == "__main__":
    main()
