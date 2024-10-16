API_BASE = "https://api.myfans.jp/api"

get_account = f"{API_BASE}/v1/account"
get_account_subscriptions = f"{API_BASE}/v1/account/subscriptions"
get_plan_posts = f"{API_BASE}/v2/plans/{{id}}/posts?sort_key=publish_start_at&per_page={{per_page}}&page={{page}}"
get_post = f"{API_BASE}/v2/posts/{{id}}"
get_post_tags = f"{API_BASE}/v1/posts/{{id}}/tags"
get_post_videos = f"{API_BASE}/v2/posts/{{id}}/videos"
get_user = f"{API_BASE}/v1/users/{{id}}"
get_user_by_username = f"{API_BASE}/v2/users/show_by_username?username={{username}}"
get_user_plans = f"{API_BASE}/v1/users/{{id}}/plans"
get_user_posts = f"{API_BASE}/v2/users/{{id}}/posts?sort_key=publish_start_at&per_page={{per_page}}&page={{page}}"
