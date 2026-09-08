分类：api调用显示404
      

Tab:没有管理员权限，普通用户无法查看，我的app端是做了降级处理才可以显示相关tab，但是会缺少真实的内容显示，如果新增的tab则无法获取，可能需要后端增添一个公开的tab接口或者其他的方案解决

收藏，观看历史，订阅，删除直播间的api显示500的报错，提示内部服务器错误：
订阅的报错信息：订阅页面显示,  (首次) at pages/app/tabbar/my/subscriptions/index.vue:154
14:52:44.405 📱 订阅页面加载 at pages/app/tabbar/my/subscriptions/index.vue:143
14:52:44.405 ✅ 已登录，继续执行 at utils/auth.ts:61
14:52:44.405 🌐 请求开始:,  [Object] {"url":"/users/me/subscriptions","method":"GET","retry":3,"timeout":5000,"timestamp":"2026-...} at utils/request.ts:68
14:52:44.406 🔍 网络诊断信息:,  [Object] {"url":"/users/me/subscriptions","baseUrl":"https://mp.dayilive.com/api/core","fullUrl":"ht...} at utils/request.ts:81
14:52:44.406 🔍 getAuthToken调用:,  [Object] {"hasToken":true,"tokenLength":297,"tokenPreview":"eyJhbGciOiJIUzI1NiIs..."}  at utils/request.ts:16
14:52:44.406 🔑 请求认证Token:,  [Object] {"hasToken":true,"tokenLength":297,"tokenPreview":"eyJhbGciOiJIUzI1NiIs..."}  at utils/request.ts:123
14:52:44.406 🔍 JWT格式验证:,  [Object] {"isValid":true,"parts":3}  at utils/request.ts:166
14:52:44.406 ✅ 已添加认证头:,  Bearer eyJhbGciOiJIUzI1NiIs... at utils/request.ts:178
14:52:44.406 📋 完整请求头:,  [Object] {"Content-Type":"application/json","Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...} at utils/request.ts:190
14:52:44.487 🌐 [DEBUG] 请求成功响应:,  [Object] {"statusCode":500,"url":"https://mp.dayilive.com/api/core/users/me/subscriptions","data":{"...} at utils/request.ts:209
14:52:44.487 HTTP Error: 500,  [Object] {"url":"https://mp.dayilive.com/api/core/users/me/subscriptions","method":"GET","requestDat...} at utils/request.ts:315
14:52:44.487 🔍 [诊断] 构造错误对象:,  [Object] {"statusCode":500,"code":1002,"message":"内部服务器错误","data":null}  at utils/request.ts:332
14:52:44.499 [API Error],  [Object] {"code":1002,"message":"内部服务器错误","details":{"statusCode":500,"code":1002,"data":null,"fullR...} at utils/errorHandler.ts:105观看历史记录的报错信息 ：
[DEBUG] 请求成功响应:,  [Object] {"statusCode":500,"url":"https://mp.dayilive.com/api/core/users/me/watch-history","data":{"...} at utils/request.ts:209
14:39:43.065 HTTP Error: 500,  [Object] {"url":"https://mp.dayilive.com/api/core/users/me/watch-history","method":"POST","requestDa...} at utils/request.ts:315
14:39:43.065 🔍 [诊断] 构造错误对象:,  [Object] {"statusCode":500,"code":1002,"message":"内部服务器错误","data":null}  at utils/request.ts:332
14:39:43.065 [LiveView] 记录观看历史失败:,  Error: 内部服务器错误 at pages/app/live/LiveView.vue:1210
14:39:43.095 🌐 [DEBUG] 请求成功响应:,  [Object] {"statusCode":500,"url":"https://mp.dayilive.com/api/core/users/me/watch-history","data":{"...} at utils/request.ts:209
14:39:43.095 HTTP Error: 500,  [Object] {"url":"https://mp.dayilive.com/api/core/users/me/watch-history","method":"POST","requestDa...} at utils/request.ts:315
14:39:43.095 🔍 [诊断] 构造错误对象:,  [Object] {"statusCode":500,"code":1002,"message":"内部服务器错误","data":null}  at utils/request.ts:332
14:39:43.108 [LiveView] 记录观看历史失败:,  Error: 内部服务器错误 at pages/app/live/LiveView.vue:1210
收藏页面报错信息：
收藏页面显示,  (首次) at pages/app/tabbar/my/favorites/index.vue:145
14:52:39.156 📱 收藏页面加载 at pages/app/tabbar/my/favorites/index.vue:135
14:52:39.156 ✅ 已登录，继续执行 at utils/auth.ts:61
14:52:39.156 [FavoriteStore] 开始加载收藏列表 at store/favorite.ts:62
14:52:39.156 🌐 请求开始:,  [Object] {"url":"/users/me/favorites","method":"GET","retry":3,"timeout":5000,"timestamp":"2026-03-16T06:52:37.231Z"}  at utils/request.ts:68
14:52:39.156 🔍 网络诊断信息:,  [Object] {"url":"/users/me/favorites","baseUrl":"https://mp.dayilive.com/api/core","fullUrl":"https:...} at utils/request.ts:81
14:52:39.156 🔍 getAuthToken调用:,  [Object] {"hasToken":true,"tokenLength":297,"tokenPreview":"eyJhbGciOiJIUzI1NiIs..."}  at utils/request.ts:16
14:52:39.157 🔑 请求认证Token:,  [Object] {"hasToken":true,"tokenLength":297,"tokenPreview":"eyJhbGciOiJIUzI1NiIs..."}  at utils/request.ts:123
14:52:39.157 🔍 JWT格式验证:,  [Object] {"isValid":true,"parts":3}  at utils/request.ts:166
14:52:39.157 ✅ 已添加认证头:,  Bearer eyJhbGciOiJIUzI1NiIs... at utils/request.ts:178
14:52:39.157 📋 完整请求头:,  [Object] {"Content-Type":"application/json","Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...} at utils/request.ts:190
14:52:39.235 🌐 [DEBUG] 请求成功响应:,  [Object] {"statusCode":500,"url":"https://mp.dayilive.com/api/core/users/me/favorites","data":{"code...} at utils/request.ts:209
14:52:39.235 HTTP Error: 500,  [Object] {"url":"https://mp.dayilive.com/api/core/users/me/favorites","method":"GET","requestData":{...} at utils/request.ts:315
14:52:39.235 🔍 [诊断] 构造错误对象:,  [Object] {"statusCode":500,"code":1002,"message":"内部服务器错误","data":null}  at utils/request.ts:332
14:52:39.235 [FavoriteStore] 加载收藏列表失败:,  Error: 内部服务器错误 at store/favorite.ts:104
14:52:39.248 ❌ 加载收藏列表失败:,  Error: 内部服务器错误 at pages/app/tabbar/my/favorites/index.vue:176
删除直播间的报错信息：
请求开始:,  [Object] {"url":"/rooms/04fc2084-8d04-4ccd-bf79-d711387a5bf9","method":"DELETE","retry":0,"timeout":...} at utils/request.ts:68
15:06:07.125 🔍 网络诊断信息:,  [Object] {"url":"/rooms/04fc2084-8d04-4ccd-bf79-d711387a5bf9","baseUrl":"https://mp.dayilive.com/api...} at utils/request.ts:81
15:06:07.136 🔍 getAuthToken调用:,  [Object] {"hasToken":true,"tokenLength":343,"tokenPreview":"eyJhbGciOiJIUzI1NiIs..."}  at utils/request.ts:16
15:06:07.136 🔑 请求认证Token:,  [Object] {"hasToken":true,"tokenLength":343,"tokenPreview":"eyJhbGciOiJIUzI1NiIs..."}  at utils/request.ts:123
15:06:07.136 🔍 JWT格式验证:,  [Object] {"isValid":true,"parts":3}  at utils/request.ts:166
15:06:07.136 ✅ 已添加认证头:,  Bearer eyJhbGciOiJIUzI1NiIs... at utils/request.ts:178
15:06:07.136 📋 完整请求头:,  [Object] {"Content-Type":"application/json","Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...} at utils/request.ts:190
15:06:07.229 🌐 [DEBUG] 请求成功响应:,  [Object] {"statusCode":500,"url":"https://mp.dayilive.com/api/core/rooms/04fc2084-8d04-4ccd-bf79-d71...} at utils/request.ts:209
15:06:07.229 HTTP Error: 500,  [Object] {"url":"https://mp.dayilive.com/api/core/rooms/04fc2084-8d04-4ccd-bf79-d711387a5bf9","metho...} at utils/request.ts:315
15:06:07.229 🔍 [诊断] 构造错误对象:,  [Object] {"statusCode":500,"message":"HTTP Error: 500"}  at utils/request.ts:332
15:06:07.229 Failed to delete room 04fc2084-8d04-4ccd-bf79-d711387a5bf9:,  Error: HTTP Error: 500 at store/room.ts:202
15:06:07.229 ❌ 删除房间失败:,  Error: HTTP Error: 500 at pages/app/live-manage/list.vue:192
个人信息页：头像需要支持本地上传
我的直播页面：目前只有针对管理员设计的返回所有直播间list的api，没有筛选，不能实现针对不同账号返回不同账号创建的直播间list的功能