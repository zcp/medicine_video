# LiveCore Service Schemas Package

# 专家模块 Schema（新增）
from .experts import (
    SessionExpertRole,
    ExpertBase,
    ExpertCreate,
    ExpertUpdate,
    ExpertItem,
    FeaturedExpertItem,
    ExpertFollowRequest,
    ExpertFollowResponse,
    FollowedExpertItem,
    FollowedExpertsResponse,
    SessionExpertItem

)

# 直播间 Tab 和留言功能 Schema（新增）
from .live_features import (
    LiveRoomMessageUserRole,
    LiveRoomTabContentType,
    LiveRoomTabBase,
    LiveRoomTabCreate,
    LiveRoomTabUpdate,
    LiveRoomTabInDB,
    LiveRoomTabResponse,
    LiveRoomMessageBase,
    LiveRoomMessageCreate,
    LiveRoomMessageCreateInternal,
    LiveRoomMessageUpdate,
    LiveRoomMessageInDB,
    LiveRoomMessagePostResponse,
    LiveRoomMessageListResponseItem,
    PaginatedLiveRoomMessageResponse
)

# 内容管理模块 Schema（新增）
from .content_management import (
    TagBase,
    TagCreate,
    TagUpdate,
    TagItem,
    TagListResponse,
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryItem,
    CategoryListResponse,
    PaginatedData,
    CategoryAdminListResponse,
    SessionTagsSetRequest,
    TagBriefItem,
    SessionTagsSetResponse,
    SessionTagsListResponse
)

# 用户行为模块 Schema（新增）
from .user_behavior import (
    SubscriptionTargetType,
    FavoriteCreate,
    FavoriteItem,
    FavoriteListResponse,
    WatchEventRequest,
    WatchHistoryItem,
    WatchHistoryListResponse,
    SubscriptionCreate,
    SubscriptionItem,
    SubscriptionListResponse,
)

# 用户偏好与通知模块 Schema（新增）
from .user_preference_notification import (
    UserPreferencesBase,
    UserPreferencesUpdate,
    UserPreferencesItem,
    NotificationBase,
    NotificationItem,
    NotificationCreateRequest,
    NotificationBatchCreateResponse,
    NotificationUpdateRequest,
    NotificationBatchDeleteRequest,
    NotificationListResponse,
)

# 品牌模块 Schema（新增）
from .brand import (
    BrandBase,
    BrandCreate,
    BrandUpdate,
    BrandItem,
    TopicBriefItem,
    BrandContentData,
    BrandContentResponse,
    BrandTopicBindIn,
    BrandTopicBindOut,
    TopicBrandItem,
    BrandRoomBindIn,
    BrandRoomBindOut,
    RoomBrandItem
)

# 首页与搜索模块 Schema（新增）
from .homepage_search import (
    FeaturedContentBase,
    FeaturedContentCreate,
    FeaturedContentUpdate,
    FeaturedContentItem,
    LiveStatusEnum,
    HomepageHostInfo,
    HomepageStatusData,
    HomepageRoomItem,
    HomepageRoomsResponse,
    SearchResultType,
    SearchResultItem,
    SearchResponse
)

# 直播间与公众号关联模块 Schema（新增）
from .liveroom_official_accounts import (
    OfficialAccountBase,
    OfficialAccountCreate,
    OfficialAccountUpdate,
    OfficialAccountItem,
    OfficialAccountAdminListResponse,
    LiveRoomOfficialAccountsSetRequest,
    LiveRoomOfficialAccountsSetResponse,
    LiveRoomOfficialAccountsListResponse,
    RoomBriefItem,
    OfficialAccountRoomsListResponse,
)