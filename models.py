from datetime import datetime
from typing import Optional

from pydantic import BaseModel as BaseBasicModel
from pydantic import ConfigDict


class BaseModel(BaseBasicModel):
    model_config = ConfigDict(extra="forbid")


class PaginationModel(BaseModel):
    current: int
    next: Optional[int]
    previous: Optional[int]


class PagedDataModel[T](BaseModel):
    data: list[T]
    pagination: PaginationModel


class UserBasicModel(BaseModel):
    about: str
    active: bool
    avatar_url: str
    banner_url: str
    id: str
    is_following: bool
    likes_count: int
    name: str
    username: str


class UserInPostFromListModel(UserBasicModel):
    is_official_creator: bool
    is_official: bool
    label: Optional[str]
    current_back_number_plan: Optional[str]


class UserInPostModel(UserBasicModel):
    cant_receive_message: Optional[bool] = None  # FIXME


class UserModel(UserInPostFromListModel, UserInPostModel):
    back_number_post_images_count: int
    back_number_post_videos_count: int
    followers_count: int
    followings_count: int
    has_approved_user_identification: bool
    is_bought_back_number: bool
    is_followed: bool
    is_subscribed: bool
    limited_posts_count: int
    link_instagram_id: str
    link_instagram_url: Optional[str]
    link_tiktok_id: str
    link_tiktok_url: Optional[str]
    link_twitter_id: str
    link_twitter_url: Optional[str]
    link_youtube_url: str
    post_images_count: int
    post_videos_count: int
    posts_count: int
    sns_link1: str
    sns_link2: str


class AccountModel(UserModel):
    appeal_image_urls: list[str]
    birthday: Optional[str]
    comment_permission: str
    disallow_receive_message: bool
    email: str
    full_name: Optional[str]
    has_hd_access: bool
    has_spending_cap: bool
    is_confirmed: bool
    is_creater: bool
    personal_info_status: str
    phone_number: Optional[str]
    phone_number_verified: bool
    postable_status: str


class PlanBasicModel(BaseModel):
    id: str
    product_name: str
    monthly_price: int
    status: str
    is_limited_access: bool
    disallow_new_subscriber: bool


class PlanInPostFromListModel(PlanBasicModel):
    active_discount: Optional[str]


class PlanInPostModel(PlanBasicModel):
    description: str
    flag: Optional[str]
    posts_count: int
    user: UserInPostModel


class PlanModel(PlanInPostFromListModel, PlanInPostModel):
    is_back_number: bool
    welcome_message: str
    plan_discounts: Optional[str]


class PlanInSubscriptionModel(PlanModel):
    active_user_subscriptions_count: int
    message_room_id: Optional[str]


class SubscriptionModel(BaseModel):
    id: str
    status: str
    active_until: str
    active_until_i18n: str
    active_until_for_user_i18n: str
    created_at: datetime
    humanized_created_at: Optional[str]
    user: UserModel
    kind_i18n: str
    amount: Optional[int]
    creator_fee: Optional[int]
    web_path: str
    sort: Optional[str]
    contracted_price: int
    plan: PlanInSubscriptionModel


class PostSinglePlanModel(BaseModel):
    id: str
    amount: int


class PostCurrentSinglePlanModel(PostSinglePlanModel):
    auto_message_body: str


class PostMetadataImageModel(BaseModel):
    count: int


class PostMetadataVideoModel(BaseModel):
    duration: int
    resolutions: list[str]


class PostMetadataModel(BaseModel):
    image: Optional[PostMetadataImageModel] = None  # FIXME
    video: Optional[PostMetadataVideoModel] = None  # FIXME


class PostPostImageModel(BaseModel):
    file_url: str
    square_thumbnail_url: Optional[str]
    raw_image_height: int
    raw_image_width: int


class PostVideoDurationModel(BaseModel):
    hours: Optional[int]
    minutes: Optional[int]
    seconds: int


class PostVideoModel(BaseModel):
    url: str
    image_url: str
    resolution: str
    duration_ms: int
    width: int
    height: int


class PostVideosModel(BaseModel):
    trial: Optional[list[PostVideoModel]]
    main: Optional[list[PostVideoModel]]


class PostImageModel(BaseModel):
    height: int
    width: int
    url: str


class PostMainVideoInfoModel(BaseModel):
    duration_ms: int
    resolutions: list[str]


class PostTagModel(BaseModel):
    id: str
    name: str
    posts_count: int


class PostBasicModel(BaseModel):
    id: str
    kind: str
    status: str
    status_label: Optional[str]
    body: str
    likes_count: int
    published_at: datetime
    publish_end_at: Optional[datetime]
    pinned_at: Optional[datetime]
    deleted_at_i18n: Optional[str]
    visible: bool
    available: bool
    bookmarked: bool
    liked: bool
    attachment: Optional[str]
    metadata: PostMetadataModel
    thumbnail_url: str


class PostFromListModel(PostBasicModel):
    humanized_publish_start_at: str
    user: UserInPostFromListModel
    post_images: list[PostPostImageModel]
    publish_start_at: Optional[datetime]
    plan: Optional[PlanModel]
    current_single_plan: Optional[PostCurrentSinglePlanModel]
    plans: list[PlanInPostFromListModel]
    video_processing: Optional[bool]
    video_duration: Optional[PostVideoDurationModel]
    free: bool
    limited: bool


class PostModel(PostBasicModel):
    comments_count: int
    bookmarks_count: int
    deleted_at: Optional[datetime]
    user: UserInPostModel
    post_image: PostPostImageModel
    videos: PostVideosModel
    images: list[PostImageModel]
    plans: list[PlanInPostModel]
    commentable: bool
    main_video_info: Optional[PostMainVideoInfoModel]
    single_plan: Optional[PostSinglePlanModel]
