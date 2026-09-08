# LiveCore Service Models Package
from .live_core import LiveRoom
from .live_core import LiveSession
from .live_core import SessionStatistics

# 专题聚合功能模型（新增）
from .topic import Topic, TopicCategory, TopicCategoryRoom

# 直播间 Tab 和留言功能模型（新增）
from .live_features import LiveRoomMessage, LiveRoomTab

# 专家模块模型（新增）
from .experts import Expert, UserExpertSubscription, LiveSessionExpert

# 内容管理模块模型（新增）
from .content_management import Tag, Category, SessionTag, LiveRoomCategory

# 用户偏好与通知模块模型（新增）
from .user_preference_notification import UserPreferences, Notification

# 品牌模块模型（新增）
from .brand import Brand, BrandTopic, BrandRoom

# 首页与搜索模块模型（新增）
from .homepage_search import FeaturedContent

# 直播间与公众号关联模块模型（新增）
from .liveroom_official_accounts import OfficialAccount, LiveRoomOfficialAccount

# 用户行为模块模型（新增）
from .user_behavior import UserSubscription, UserFavorite, WatchHistory

# 搜索历史与热词统计模块模型（新增）
from .search import UserSearchHistory, SearchKeywordStats