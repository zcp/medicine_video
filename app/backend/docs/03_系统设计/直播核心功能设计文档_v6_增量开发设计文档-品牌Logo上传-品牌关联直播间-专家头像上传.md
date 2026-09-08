# 📄 **图片上传功能增量开发文档 - 品牌Logo·专家头像·品牌关联直播间API**

**版本**: V1.1  
**创建日期**: 2026-01-21  
**更新日期**: 2026-01-22  
**状态**: 增量开发（待实施）  
**基于文档**: 
- 《直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md》
- 《直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md》
- 《直播核心功能设计文档_v6_深度融合最终版.md》

---

## 📌 增量开发定位

### 1.1 核心目标

为**品牌模块**和**专家模块**补充完整的图片上传功能，并新增品牌关联直播间查询接口，包括：

- 🏢 **品牌Logo上传**：管理员上传品牌Logo图片（`POST /api/v1/admin/brands/{brand_id}/logo`）
- 👨‍⚕️ **专家头像上传**：管理员上传专家头像图片（`POST /api/v1/admin/experts/{expert_id}/avatar`）
- 🔗 **品牌关联直播间查询**：管理员获取品牌关联的直播间列表（`GET /api/v1/admin/brands/{brand_id}/rooms`）

### 1.2 增量原则

- ✅ **仅新增，不修改**：只新增上传接口、查询接口和相关方法，不修改现有API和数据表结构
- ✅ **复用现有基础设施**：完全复用项目中已有的 `FileHandler` 类和文件存储机制
- ✅ **完全兼容**：遵循品牌模块和专家模块的所有设计规范（响应结构、错误码、鉴权、异常处理等）
- ✅ **最小幅度**：只新增必要的代码，不引入冗余逻辑
- ✅ **设计一致性**：新增的 `get_brand_rooms_paginated` 接口完全遵循 `get_brand_topics_paginated` 的设计模式

### 1.3 技术依赖

本增量开发依赖以下现有实现：

| 组件 | 文件路径 | 提供能力 |
|------|---------|---------|
| **FileHandler** | `app/core/file_handler.py` | 文件验证、路径生成、文件保存 |
| **BrandService** | `app/services/brand_service.py` | 品牌业务逻辑（全局实例） |
| **ExpertService** | `app/services/expert_service.py` | 专家业务逻辑（请求实例化） |
| **Topic Banner Upload** | `app/api/v1/endpoints/topic.py (L490-580)` | 参考实现（横幅上传） |
| **Room Cover Upload** | `app/api/v1/endpoints/room.py (L600+)` | 参考实现（封面上传） |

---

## 📚 依赖文档清单

| 序号 | 文档名称 | 依赖关系 | 影响范围 |
|------|---------|---------|---------|
| 1 | 《直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md》 | 📋 **主设计文档** | 品牌模块的所有设计规范、API规范、权限规范、异常处理规范 |
| 2 | 《直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md》 | 📋 **主设计文档** | 专家模块的所有设计规范、API规范、权限规范、异常处理规范 |
| 3 | 《直播核心功能设计文档_v6_增加权限设计版.md》 | 🔐 **权限规范** | Strict Auth双轨鉴权模式、权限守卫函数 |
| 4 | 《配置与安全优化方案-实施指南.md》 | 🔒 **安全规范** | 日志脱敏、配置验证要求 |

---

## 📖 统一规范说明

### 2.1 响应结构

所有API接口的响应都遵循统一结构：

**成功响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "brand_id": "uuid",
    "logo_url": "/media/brands/{brand_id}/logo_{timestamp}.jpg"
  },
  "timestamp": "2026-01-21T10:00:00Z"
}
```

**错误响应格式**：
```json
{
  "code": 3003,
  "message": "权限不足",
  "data": null,
  "timestamp": "2026-01-21T10:00:00Z"
}
```

**响应函数使用规范**：
- **成功响应**: 使用 `return success_response(data=..., message="...")` 直接返回，FastAPI自动序列化为JSON（HTTP状态码200）
- **错误响应**: **必须**使用 `return JSONResponse(status_code=xxx, content=error_response(code=xxx, message="..."))`，因为`error_response()`仅返回响应体字典，需要通过`JSONResponse`的`status_code`参数指定HTTP状态码（如403、404、500等）

### 2.2 认证规范

- **Admin接口**: 需要JWT Token + `ADMIN` 或 `SUPERADMIN` 角色
- 使用 `Depends(get_current_user)` 进行强制认证

### 2.3 业务状态码

| 业务状态码 | 含义 | 使用场景 |
|:---------|:-----|:---------|
| `200` | 成功 | 图片上传成功 |
| `2001` | 资源不存在 | 品牌/专家不存在 |
| `3003` | 权限不足 | 角色权限不足 |
| `4001` | 参数校验失败 | 文件格式/大小不符合要求 |
| `1002` | 数据库错误 | 系统级异常 |

### 2.4 文件存储规范

#### 存储路径设计

**品牌Logo**：
```
文件系统路径: {ROOM_MEDIA_ROOT_PATH}/brands/{brand_id}/logo_{timestamp}.{ext}
URL路径:      /media/brands/{brand_id}/logo_{timestamp}.{ext}
```

**专家头像**：
```
文件系统路径: {ROOM_MEDIA_ROOT_PATH}/experts/{expert_id}/avatar_{timestamp}.{ext}
URL路径:      /media/experts/{expert_id}/avatar_{timestamp}.{ext}
```

#### 文件验证规范

- **允许格式**: JPG, JPEG, PNG, GIF
- **文件大小**: 最大 5MB（由 `UPLOAD_MAX_SIZE` 环境变量配置）
- **MIME类型**: `image/jpeg`, `image/png`, `image/gif`

---

## 🔧 详细实施方案

### 3.1 FileHandler 层新增方法

**文件**: `backend/live_core_service/app/core/file_handler.py`

#### 新增位置

在现有的 `save_banner_file()` 方法之后（约第277行），依次添加以下4个方法。

#### 3.1.1 品牌Logo处理方法

**新增方法1**: `generate_brand_logo_path()`

```python
@staticmethod
def generate_brand_logo_path(brand_id: uuid.UUID, extension: str) -> Tuple[str, str]:
    """
    生成品牌Logo存储路径
    
    Args:
        brand_id: 品牌ID
        extension: 文件扩展名
        
    Returns:
        (文件系统路径, URL路径)的元组
    """
    # 生成时间戳
    timestamp = int(time.time())
    
    # 构建路径
    relative_dir = f"brands/{brand_id}"
    filename = f"logo_{timestamp}.{extension}"
    
    # 文件系统路径
    fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
    fs_path = os.path.join(fs_dir, filename)
    
    # URL路径
    url_path = f"/media/{relative_dir}/{filename}"
    
    # 确保目录存在
    os.makedirs(fs_dir, exist_ok=True)
    logger.debug(f"生成品牌Logo路径: fs_path={fs_path}, url_path={url_path}")
    
    return fs_path, url_path
```

**新增方法2**: `save_brand_logo()`

```python
@staticmethod
async def save_brand_logo(file: UploadFile, brand_id: uuid.UUID) -> str:
    """
    保存品牌Logo文件并返回URL
    
    完全复用现有文件保存逻辑，仅调整路径生成。
    
    Args:
        file: 上传的文件对象
        brand_id: 品牌ID
        
    Returns:
        文件的URL路径
        
    Raises:
        HTTPException: 保存失败时抛出异常
    """
    logger.info(f"开始保存品牌Logo: brand_id={brand_id}, filename={file.filename}")
    
    try:
        # 1. 验证文件
        FileHandler.validate_image_file(file)
        
        # 2. 获取文件扩展名
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        
        # 3. 生成存储路径
        fs_path, url_path = FileHandler.generate_brand_logo_path(brand_id, file_ext)
        
        # 4. 读取文件内容并检查大小
        contents = await file.read()
        if len(contents) > UPLOAD_MAX_SIZE:
            logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
            )
        
        # 5. 保存文件
        with open(fs_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"品牌Logo保存成功: brand_id={brand_id}, path={url_path}")
        return url_path
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"保存品牌Logo失败: brand_id={brand_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="文件保存失败")
```

#### 3.1.2 专家头像处理方法

**新增方法3**: `generate_expert_avatar_path()`

```python
@staticmethod
def generate_expert_avatar_path(expert_id: uuid.UUID, extension: str) -> Tuple[str, str]:
    """
    生成专家头像存储路径
    
    Args:
        expert_id: 专家ID
        extension: 文件扩展名
        
    Returns:
        (文件系统路径, URL路径)的元组
    """
    timestamp = int(time.time())
    
    relative_dir = f"experts/{expert_id}"
    filename = f"avatar_{timestamp}.{extension}"
    
    fs_dir = os.path.join(ROOM_MEDIA_ROOT_PATH, relative_dir)
    fs_path = os.path.join(fs_dir, filename)
    
    url_path = f"/media/{relative_dir}/{filename}"
    
    os.makedirs(fs_dir, exist_ok=True)
    logger.debug(f"生成专家头像路径: fs_path={fs_path}, url_path={url_path}")
    
    return fs_path, url_path
```

**新增方法4**: `save_expert_avatar()`

```python
@staticmethod
async def save_expert_avatar(file: UploadFile, expert_id: uuid.UUID) -> str:
    """
    保存专家头像文件并返回URL
    
    完全复用现有文件保存逻辑，仅调整路径生成。
    
    Args:
        file: 上传的文件对象
        expert_id: 专家ID
        
    Returns:
        文件的URL路径
        
    Raises:
        HTTPException: 保存失败时抛出异常
    """
    logger.info(f"开始保存专家头像: expert_id={expert_id}, filename={file.filename}")
    
    try:
        FileHandler.validate_image_file(file)
        
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "jpg"
        
        fs_path, url_path = FileHandler.generate_expert_avatar_path(expert_id, file_ext)
        
        contents = await file.read()
        if len(contents) > UPLOAD_MAX_SIZE:
            logger.warning(f"文件大小超出限制: size={len(contents)}, max={UPLOAD_MAX_SIZE}")
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超出限制。最大允许：{UPLOAD_MAX_SIZE / 1024 / 1024:.1f}MB"
            )
        
        with open(fs_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"专家头像保存成功: expert_id={expert_id}, path={url_path}")
        return url_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存专家头像失败: expert_id={expert_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="文件保存失败")
```

---

### 3.2 Service 层新增方法

#### 3.2.1 品牌Service新增方法

**文件**: `backend/live_core_service/app/services/brand_service.py`

**新增导入**（在文件顶部添加）：
```python
from fastapi import UploadFile
from app.core.file_handler import FileHandler
```

**新增方法**（在 `delete_brands_batch()` 方法之后添加）: `upload_brand_logo()`

```python
async def upload_brand_logo(
    self,
    db: AsyncSession,
    brand_id: UUID,
    file: UploadFile,
    current_user_id: UUID,
    role: str
) -> str:
    """
    上传品牌Logo
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        file: 上传的文件
        current_user_id: 当前用户ID
        role: 用户角色
        
    Returns:
        Logo的URL路径
        
    Raises:
        PermissionDeniedException: 权限不足
        NotFoundException: 品牌不存在
        HTTPException: 文件上传失败
    """
    # 1. 权限检查
    if role not in ["ADMIN", "SUPERADMIN"]:
        logger.warning(f"权限不足: user_id={str(current_user_id)[:8]}, role={role}")
        raise PermissionDeniedException("需要管理员权限")
    
    # 2. 验证品牌是否存在
    brand = await db.get(Brand, brand_id)
    if not brand:
        logger.warning(f"品牌不存在: brand_id={str(brand_id)[:8]}")
        raise NotFoundException("品牌不存在")
    
    # 3. 保存Logo文件
    logo_url = await FileHandler.save_brand_logo(file, brand_id)
    
    # 4. 更新数据库中的logo_url
    brand.logo_url = logo_url
    await db.commit()
    await db.refresh(brand)
    
    logger.info(f"品牌Logo上传成功: brand_id={str(brand_id)[:8]}, logo_url={logo_url}")
    
    return logo_url
```

#### 3.2.2 专家Service新增方法

**文件**: `backend/live_core_service/app/services/expert_service.py`

**新增导入**（在文件顶部添加）：
```python
from fastapi import UploadFile
from app.core.file_handler import FileHandler
```

**新增方法**（在类的最后一个方法之后添加）: `upload_expert_avatar()`

```python
async def upload_expert_avatar(
    self,
    expert_id: UUID,
    file: UploadFile,
    current_user_id: UUID,
    role: str
) -> str:
    """
    上传专家头像
    
    Args:
        expert_id: 专家ID
        file: 上传的文件
        current_user_id: 当前用户ID
        role: 用户角色
        
    Returns:
        头像的URL路径
        
    Raises:
        PermissionDeniedException: 权限不足
        NotFoundException: 专家不存在
        HTTPException: 文件上传失败
    """
    # 1. 权限检查
    if role not in ["ADMIN", "SUPERADMIN"]:
        logger.warning(f"权限不足: user_id={str(current_user_id)[:8]}, role={role}")
        raise PermissionDeniedException("需要管理员权限")
    
    # 2. 验证专家是否存在
    expert = await self.db.get(Expert, expert_id)
    if not expert:
        logger.warning(f"专家不存在: expert_id={str(expert_id)[:8]}")
        raise NotFoundException("专家不存在")
    
    # 3. 保存头像文件
    avatar_url = await FileHandler.save_expert_avatar(file, expert_id)
    
    # 4. 更新数据库中的avatar_url
    expert.avatar_url = avatar_url
    await self.db.commit()
    await self.db.refresh(expert)
    
    logger.info(f"专家头像上传成功: expert_id={str(expert_id)[:8]}, avatar_url={avatar_url}")
    
    return avatar_url
```

---

### 3.3 API 层新增端点

#### 3.3.1 品牌模块新增端点

**文件**: `backend/live_core_service/app/api/v1/endpoints/brand.py`

**新增导入**（在文件顶部的导入区域添加）：
```python
from fastapi import UploadFile, File
```

**⚠️ 重要：检查现有导入**：
- 如果 `brand.py` 中尚未导入 `success_response`，需要添加：`from app.core.response import success_response, error_response`
- 如果已导入 `error_response` 但缺少 `success_response`，需要补充：`from app.core.response import success_response, error_response`

**新增端点位置**: 在 `delete_brand()` 函数之后（约第310行），添加以下端点。

**新增端点**: `POST /admin/brands/{brand_id}/logo`

```python
@router.post("/admin/brands/{brand_id}/logo")
async def upload_brand_logo(
    brand_id: UUID = Path(..., description="品牌ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    为指定品牌上传Logo图片（Admin）
    
    完全复用 FileHandler 的实现逻辑：
    - 文件校验：PNG, JPG, GIF 格式，5MB 以内
    - 权限验证：仅 ADMIN/SUPERADMIN 可上传
    - 存储路径：/media/brands/{brand_id}/logo_{timestamp}.{ext}
    
    Args:
        brand_id: 品牌UUID
        file: 上传的Logo文件
        current_user: 当前登录用户信息
        db: 数据库会话
        
    Returns:
        标准成功响应，包含 brand_id 和 logo_url
        
    Raises:
        404: 品牌不存在
        403: 权限不足
        400: 文件格式或大小不符合要求
    """
    # 提取用户信息（在try之前）
    user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)[:8]
    brand_id_for_logging = str(brand_id)[:8]
    
    logger.info(f"开始上传品牌Logo: brand_id={brand_id_for_logging}, user_id={user_id_for_logging}")
    
    try:
        # 调用 Service 层上传Logo
        logo_url = await brand_service.upload_brand_logo(
            db=db,
            brand_id=brand_id,
            file=file,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(
            data={
                "brand_id": str(brand_id),
                "logo_url": logo_url
            },
            message="Logo上传成功"
        )
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: brand_id={brand_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except HTTPException as e:
        logger.warning(f"文件上传失败: brand_id={brand_id_for_logging}, error={e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(code=4001, message=e.detail)
        )
    except Exception as e:
        logger.error(f"上传品牌Logo异常: brand_id={brand_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

#### 3.3.2 专家模块新增端点

**文件**: `backend/live_core_service/app/api/v1/endpoints/experts.py`

**新增导入**（在文件顶部的导入区域添加）：
```python
from fastapi import UploadFile, File
```

**⚠️ 重要：检查现有导入**：
- `experts.py` 中应该已经导入了 `success_response` 和 `error_response`（第27行），如未导入需要添加：`from app.core.response import success_response, error_response`

**新增端点位置**: 在 `delete_expert()` 函数之后（约第460行），添加以下端点。

**新增端点**: `POST /admin/experts/{expert_id}/avatar`

```python
@experts_admin_router.post("/experts/{expert_id}/avatar")
async def upload_expert_avatar(
    expert_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """
    为指定专家上传头像图片（Admin）
    
    完全复用 FileHandler 的实现逻辑：
    - 文件校验：PNG, JPG, GIF 格式，5MB 以内
    - 权限验证：仅 ADMIN/SUPERADMIN 可上传
    - 存储路径：/media/experts/{expert_id}/avatar_{timestamp}.{ext}
    
    Args:
        expert_id: 专家UUID
        file: 上传的头像文件
        current_user: 当前登录用户信息
        db: 数据库会话
        
    Returns:
        标准成功响应，包含 expert_id 和 avatar_url
        
    Raises:
        404: 专家不存在
        403: 权限不足
        400: 文件格式或大小不符合要求
    """
    # 提取用户信息
    user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    
    # 提前提取用于日志的变量
    user_id_for_logging = str(user_id)[:8]
    
    try:
        expert_id_uuid = UUID(expert_id)
        expert_id_for_logging = str(expert_id_uuid)[:8]
    except ValueError:
        logger.warning(f"无效的专家ID格式: expert_id={expert_id}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="无效的专家ID格式")
        )
    
    logger.info(f"开始上传专家头像: expert_id={expert_id_for_logging}, user_id={user_id_for_logging}")
    
    try:
        # 实例化Service层
        service = ExpertService(db)
        
        # 调用 Service 层上传头像
        avatar_url = await service.upload_expert_avatar(
            expert_id=expert_id_uuid,
            file=file,
            current_user_id=user_id,
            role=role
        )
        
        return success_response(
            data={
                "expert_id": expert_id,
                "avatar_url": avatar_url
            },
            message="头像上传成功"
        )
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"专家不存在: expert_id={expert_id_for_logging}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="专家不存在")
        )
    except HTTPException as e:
        logger.warning(f"文件上传失败: expert_id={expert_id_for_logging}, error={e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=error_response(code=4001, message=e.detail)
        )
    except Exception as e:
        logger.error(f"上传专家头像异常: expert_id={expert_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

---

### 3.4 品牌模块新增API接口：获取品牌关联直播间列表（Admin分页）

**说明**：本接口用于管理员获取指定品牌关联的所有直播间列表，采用分页方式返回。该接口与 `get_brand_topics_paginated` 接口设计模式完全一致，遵循品牌模块的所有设计规范。

#### 3.4.1 CRUD 层新增方法

**文件**: `backend/live_core_service/app/crud/brand.py`

**新增位置**: 在 `get_brand_topics_paginated()` 方法之后（约第521行），`# ==================== Brand_Rooms CRUD函数 (3个) ====================` 之前添加。

**新增方法**: `get_brand_rooms_paginated()`

```python
async def get_brand_rooms_paginated(
    db: AsyncSession,
    brand_id: uuid.UUID,
    page: int,
    size: int
) -> Tuple[List[dict], int]:
    """
    获取品牌关联的直播间列表（管理员接口，分页）
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        page: 页码（从1开始）
        size: 每页数量
    
    Returns:
        (直播间信息列表, 总数)
    """
    #LiveRoom 应在文件顶部导入（约第20行，在 Topic 导入之后），与 Topic 的导入方式保持一致。
    from app.models.live_core import LiveRoom
    
    # 第一次查询：获取总数
    count_stmt = select(func.count()).select_from(BrandRoom).where(
        BrandRoom.brand_id == brand_id
    )
    total = await db.scalar(count_stmt) or 0
    
    # 第二次查询：获取当前页数据（联表查询）
    stmt = (
        select(
            LiveRoom.id.label('room_id'),
            LiveRoom.title.label('room_title'),
            LiveRoom.description.label('description'),
            LiveRoom.is_private.label('is_private'),
            LiveRoom.cover_url.label('cover_url'),
            BrandRoom.created_at.label('associated_at')
        )
        .select_from(BrandRoom)
        .join(LiveRoom, BrandRoom.room_id == LiveRoom.id)
        .where(BrandRoom.brand_id == brand_id)
        .order_by(BrandRoom.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    
    result = await db.execute(stmt)
    rooms = [dict(row._mapping) for row in result]
    
    logger.info(f"查询品牌关联直播间: brand_id={str(brand_id)[:8]}, 返回{len(rooms)}条，总数{total}")
    return rooms, total
```

**设计说明**：
- 完全遵循 `get_brand_topics_paginated()` 的设计模式
- 使用联表查询 `BrandRoom JOIN LiveRoom` 获取直播间详细信息
- 返回字段包括：`room_id`, `room_title`, `description`, `is_private`, `cover_url`, `associated_at`
- 按 `BrandRoom.created_at` 降序排序，最新关联的直播间在前
- 日志记录格式与 `get_brand_topics_paginated()` 保持一致

#### 3.4.2 Service 层新增方法

**文件**: `backend/live_core_service/app/services/brand_service.py`

**新增位置**: 在 `get_brand_topics_paginated()` 方法之后（约第571行），`# ==================== Brand_Rooms Service方法 (3个) ====================` 之前添加。

**新增方法**: `get_brand_rooms_paginated()`

```python
async def get_brand_rooms_paginated(
    self,
    db: AsyncSession,
    brand_id: UUID,
    page: int,
    size: int,
    current_user_id: UUID,
    role: str
) -> dict:
    """
    获取品牌关联直播间列表（管理员分页）
    
    Args:
        db: 数据库会话
        brand_id: 品牌ID
        page: 页码
        size: 每页数量
        current_user_id: 当前用户ID
        role: 用户角色
    
    Returns:
        标准响应字典
    
    Raises:
        PermissionDeniedException: 权限不足
        NotFoundException: 品牌不存在
    """
    # 权限检查
    self._check_admin_permission(role)
    
    # 验证品牌存在
    brand = await crud.get_brand_by_id(db, brand_id)
    if not brand:
        raise NotFoundException("品牌不存在")
    
    # 查询关联直播间
    rooms, total = await crud.get_brand_rooms_paginated(db, brand_id, page, size)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": rooms,
            "total": total,
            "page": page,
            "size": size
        },
        "timestamp": datetime.utcnow()
    }
```

**设计说明**：
- 完全遵循 `get_brand_topics_paginated()` 的设计模式
- 权限检查：使用 `_check_admin_permission(role)` 确保仅管理员可访问
- 品牌存在性验证：调用 `crud.get_brand_by_id()` 验证品牌存在
- 响应结构：标准分页响应格式，包含 `items`, `total`, `page`, `size`
- 异常处理：抛出 `PermissionDeniedException` 和 `NotFoundException`，由API层统一处理

#### 3.4.3 API 层新增端点

**文件**: `backend/live_core_service/app/api/v1/endpoints/brand.py`

**新增位置**: 在 `get_brand_topics()` 函数之后（约第533行），`# ==================== Brand_Rooms API端点 (3个) ====================` 之前添加。

**新增端点**: `GET /admin/brands/{brand_id}/rooms`

```python
@router.get("/admin/brands/{brand_id}/rooms")
async def get_brand_rooms(
    brand_id: UUID = Path(..., description="品牌ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """获取品牌关联直播间列表（Admin分页）"""
    # 在try块之前提取所有必要信息
    current_user_id = UUID(current_user["user_id"])
    role = current_user.get("role", "REGULAR").upper()
    user_id_for_logging = str(current_user_id)[:8]
    
    try:
        result = await brand_service.get_brand_rooms_paginated(
            db, brand_id, page, size, current_user_id, role
        )
        return result
        
    except PermissionDeniedException as e:
        logger.warning(f"权限不足: user_id={user_id_for_logging}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3003, message="权限不足")
        )
    except NotFoundException as e:
        logger.warning(f"品牌不存在: user_id={user_id_for_logging}, brand_id={str(brand_id)[:8]}")
        return JSONResponse(
            status_code=404,
            content=error_response(code=2001, message="品牌不存在")
        )
    except Exception as e:
        logger.error(f"获取品牌直播间列表异常: user_id={user_id_for_logging}, error={type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content=error_response(code=1002, message="内部服务器错误")
        )
```

**设计说明**：
- 完全遵循 `get_brand_topics()` 端点的设计模式
- **认证**: Strict Auth（强制鉴权），使用 `Depends(get_current_user)`
- **权限**: Admin 或 SuperAdmin（由Service层 `_check_admin_permission()` 验证）
- **请求参数**: 
  - `brand_id` (Path): 品牌ID（UUID格式）
  - `page` (Query, 可选, 默认1): 页码，最小值为1
  - `size` (Query, 可选, 默认20): 每页数量，范围1-100
- **成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 5,
    "page": 1,
    "size": 20,
    "items": [
      {
        "room_id": "room_uuid_1",
        "room_title": "医疗设备创新论坛直播间",
        "description": "直播间描述",
        "is_private": false,
        "cover_url": "/media/rooms/cover1.jpg",
        "associated_at": "2025-10-20T15:00:00Z"
      }
    ]
  },
  "timestamp": "2025-10-23T12:50:00Z"
}
```
- **错误响应**:
  - `403 Forbidden` (code: 3003): 权限不足
  - `404 Not Found` (code: 2001): 品牌不存在
  - `500 Internal Server Error` (code: 1002): 内部服务器错误
- **异常处理顺序**: PermissionDeniedException → NotFoundException → Exception（通用异常）
- **日志记录**: 
  - 权限不足：WARNING级别，记录 `user_id`（前8位）和 `role`
  - 品牌不存在：WARNING级别，记录 `user_id`（前8位）和 `brand_id`（前8位）
  - 系统异常：ERROR级别，记录 `user_id`（前8位）和异常类型
- **用户信息提取**: 在try块之前提取所有必要信息（`current_user_id`, `role`, `user_id_for_logging`），符合安全规范

**执行流程**：

1. 验证JWT Token并检查管理员权限（由 `Depends(get_current_user)` 和Service层 `_check_admin_permission()` 完成）
2. 验证 `brand_id` 对应的品牌存在（由Service层 `crud.get_brand_by_id()` 完成）
3. 构建联表查询：`brand_rooms br JOIN live_rooms lr ON br.room_id = lr.id WHERE br.brand_id = :brand_id`
4. 执行COUNT查询获取总关联数
5. 应用分页（LIMIT和OFFSET）
6. 执行查询获取当前页的直播间信息
7. 按 `brand_rooms.created_at` 降序排序
8. 将结果序列化为包含直播间信息的列表
9. 构建分页响应
10. 返回成功响应

**与现有接口的一致性**：

| 特性 | `get_brand_topics` | `get_brand_rooms` | 一致性 |
|------|-------------------|-------------------|--------|
| 认证方式 | Strict Auth | Strict Auth | ✅ |
| 权限要求 | Admin/SuperAdmin | Admin/SuperAdmin | ✅ |
| 分页参数 | `page`, `size` | `page`, `size` | ✅ |
| 响应结构 | 标准分页响应 | 标准分页响应 | ✅ |
| 异常处理 | PermissionDeniedException, NotFoundException | PermissionDeniedException, NotFoundException | ✅ |
| 日志格式 | UUID前8位脱敏 | UUID前8位脱敏 | ✅ |
| CRUD层返回 | `(List[dict], int)` | `(List[dict], int)` | ✅ |
| Service层返回 | 标准响应字典 | 标准响应字典 | ✅ |

---

## 🧪 测试清单

### 4.1 功能测试

**品牌Logo上传**
- [ ] 管理员成功上传JPG格式Logo
- [ ] 管理员成功上传PNG格式Logo  
- [ ] 管理员成功上传GIF格式Logo
- [ ] 数据库中 `logo_url` 字段正确更新
- [ ] 文件成功保存到 `/media/brands/{brand_id}/` 目录
- [ ] 多次上传同一品牌覆盖旧文件

**专家头像上传**
- [ ] 管理员成功上传JPG格式头像
- [ ] 管理员成功上传PNG格式头像
- [ ] 管理员成功上传GIF格式头像
- [ ] 数据库中 `avatar_url` 字段正确更新
- [ ] 文件成功保存到 `/media/experts/{expert_id}/` 目录
- [ ] 多次上传同一专家覆盖旧文件

**文件验证**
- [ ] 上传非图片文件返回 `400 Bad Request`
- [ ] 上传超过5MB的文件返回 `400 Bad Request`
- [ ] 上传不支持的MIME类型返回 `400 Bad Request`

**权限验证**
- [ ] 非管理员用户上传返回 `403 Forbidden`
- [ ] 未登录用户上传返回 `401 Unauthorized`
- [ ] MODERATOR角色上传返回 `403 Forbidden`

**资源验证**
- [ ] 上传不存在的品牌ID返回 `404 Not Found`
- [ ] 上传不存在的专家ID返回 `404 Not Found`
- [ ] 上传无效的UUID格式返回 `400 Bad Request`

**品牌关联直播间查询接口**
- [ ] 管理员成功获取品牌关联的直播间列表（分页）
- [ ] 分页参数验证（page >= 1, size 范围 1-100）
- [ ] 返回数据包含 `room_id`, `room_title`, `description`, `is_private`, `cover_url`, `associated_at`
- [ ] 分页响应结构正确（包含 `total`, `page`, `size`, `items`）
- [ ] 非管理员用户查询返回 `403 Forbidden`
- [ ] 查询不存在的品牌ID返回 `404 Not Found`
- [ ] 空结果集返回正确的分页信息（`total: 0`, `items: []`）

### 4.2 集成测试

- [ ] 品牌创建 → Logo上传 → 品牌查询（验证logo_url返回）
- [ ] 专家创建 → 头像上传 → 专家查询（验证avatar_url返回）
- [ ] 品牌关联直播间 → 查询品牌关联直播间列表（验证分页和数据结构）
- [ ] 前端uni.uploadFile调用测试（验证multipart/form-data支持）
- [ ] 并发上传测试（验证文件名冲突处理）
- [ ] 品牌关联直播间列表查询与 `get_brand_topics` 接口行为一致性验证

### 4.3 安全测试

- [ ] SQL注入测试（在brand_id/expert_id中）
- [ ] 路径遍历测试（../../../etc/passwd）
- [ ] 文件名特殊字符测试
- [ ] 超大文件上传测试（验证内存占用）
- [ ] 恶意文件上传测试（伪装成图片的脚本文件）

---

## 🧪 测试代码实现

### 5.1 测试代码规范说明

**重要**：所有测试代码必须严格遵循《测试代码与设计文档一致性检测提示词母版.md》的要求：

1. **字段名称一致性**：测试中使用的所有字段名必须与设计文档完全一致
2. **函数签名一致性**：测试中调用的函数名、参数名、参数类型、参数顺序必须与设计文档完全一致
3. **API端点一致性**：测试中使用的API路径、HTTP方法、路径参数、查询参数必须与设计文档完全一致
4. **响应结构一致性**：测试中断言的响应结构、字段名、HTTP状态码必须与设计文档完全一致
5. **Fixture使用规范**：必须使用 `async for` 解包 `async_client` 和 `db_session` fixture
6. **禁止猜测行为**：不得使用设计文档中未定义的字段名、函数名、端点路径

### 5.2 测试文件结构

```
backend/live_core_service/tests/
├── test_file_handler_brand_expert.py    # FileHandler层测试
├── test_service_brand_logo.py           # 品牌Service层测试
├── test_service_expert_avatar.py        # 专家Service层测试
├── test_api_brand_logo.py               # 品牌API层测试
└── test_api_expert_avatar.py           # 专家API层测试
```

### 5.3 FileHandler层测试代码

**文件**: `backend/live_core_service/tests/test_file_handler_brand_expert.py`

```python
"""
FileHandler层测试 - 品牌Logo和专家头像上传

测试覆盖：
- generate_brand_logo_path() 路径生成
- save_brand_logo() 文件保存
- generate_expert_avatar_path() 路径生成
- save_expert_avatar() 文件保存
"""

import pytest
import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO
from app.core.file_handler import FileHandler
from app.core.config import ROOM_MEDIA_ROOT_PATH, UPLOAD_MAX_SIZE


class TestBrandLogoFileHandler:
    """品牌Logo文件处理测试"""
    
    def test_generate_brand_logo_path(self):
        """测试品牌Logo路径生成"""
        brand_id = uuid.uuid4()
        extension = "jpg"
        
        fs_path, url_path = FileHandler.generate_brand_logo_path(brand_id, extension)
        
        # 验证文件系统路径格式
        assert str(brand_id) in fs_path
        assert "brands" in fs_path
        assert "logo_" in fs_path
        assert fs_path.endswith(f".{extension}")
        assert fs_path.startswith(ROOM_MEDIA_ROOT_PATH)
        
        # 验证URL路径格式
        assert url_path.startswith("/media/brands/")
        assert str(brand_id) in url_path
        assert "logo_" in url_path
        assert url_path.endswith(f".{extension}")
        
        # 验证目录已创建
        assert os.path.exists(os.path.dirname(fs_path))
    
    @pytest.mark.asyncio
    async def test_save_brand_logo_success(self):
        """测试成功保存品牌Logo"""
        brand_id = uuid.uuid4()
        
        # 创建测试图片文件（1KB的JPG）
        image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
        file = UploadFile(
            filename="test_logo.jpg",
            file=BytesIO(image_content)
        )
        
        url_path = await FileHandler.save_brand_logo(file, brand_id)
        
        # 验证返回的URL路径格式
        assert url_path.startswith("/media/brands/")
        assert str(brand_id) in url_path
        assert "logo_" in url_path
        assert url_path.endswith(".jpg")
        
        # 验证文件已保存
        fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, url_path.replace("/media/", ""))
        assert os.path.exists(fs_path)
        assert os.path.getsize(fs_path) == len(image_content)
    
    @pytest.mark.asyncio
    async def test_save_brand_logo_invalid_format(self):
        """测试保存非图片格式文件"""
        brand_id = uuid.uuid4()
        
        # 创建非图片文件
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"This is not an image")
        )
        
        with pytest.raises(Exception):  # HTTPException会被抛出
            await FileHandler.save_brand_logo(file, brand_id)
    
    @pytest.mark.asyncio
    async def test_save_brand_logo_file_too_large(self):
        """测试保存超过大小限制的文件"""
        brand_id = uuid.uuid4()
        
        # 创建超过限制的文件（UPLOAD_MAX_SIZE + 1）
        large_content = b'\xff\xd8\xff\xe0' + b'0' * (UPLOAD_MAX_SIZE + 1)
        file = UploadFile(
            filename="large_logo.jpg",
            file=BytesIO(large_content)
        )
        
        with pytest.raises(Exception):  # HTTPException会被抛出
            await FileHandler.save_brand_logo(file, brand_id)


class TestExpertAvatarFileHandler:
    """专家头像文件处理测试"""
    
    def test_generate_expert_avatar_path(self):
        """测试专家头像路径生成"""
        expert_id = uuid.uuid4()
        extension = "png"
        
        fs_path, url_path = FileHandler.generate_expert_avatar_path(expert_id, extension)
        
        # 验证文件系统路径格式
        assert str(expert_id) in fs_path
        assert "experts" in fs_path
        assert "avatar_" in fs_path
        assert fs_path.endswith(f".{extension}")
        assert fs_path.startswith(ROOM_MEDIA_ROOT_PATH)
        
        # 验证URL路径格式
        assert url_path.startswith("/media/experts/")
        assert str(expert_id) in url_path
        assert "avatar_" in url_path
        assert url_path.endswith(f".{extension}")
        
        # 验证目录已创建
        assert os.path.exists(os.path.dirname(fs_path))
    
    @pytest.mark.asyncio
    async def test_save_expert_avatar_success(self):
        """测试成功保存专家头像"""
        expert_id = uuid.uuid4()
        
        # 创建测试图片文件（1KB的PNG）
        image_content = b'\x89PNG\r\n\x1a\n' + b'0' * 1000
        file = UploadFile(
            filename="test_avatar.png",
            file=BytesIO(image_content)
        )
        
        url_path = await FileHandler.save_expert_avatar(file, expert_id)
        
        # 验证返回的URL路径格式
        assert url_path.startswith("/media/experts/")
        assert str(expert_id) in url_path
        assert "avatar_" in url_path
        assert url_path.endswith(".png")
        
        # 验证文件已保存
        fs_path = os.path.join(ROOM_MEDIA_ROOT_PATH, url_path.replace("/media/", ""))
        assert os.path.exists(fs_path)
        assert os.path.getsize(fs_path) == len(image_content)
```

### 5.4 Service层测试代码

**文件**: `backend/live_core_service/tests/test_service_brand_logo.py`

```python
"""
品牌Service层测试 - Logo上传功能

测试覆盖：
- upload_brand_logo() 成功场景
- upload_brand_logo() 权限验证
- upload_brand_logo() 资源验证
"""

import pytest
import uuid
from fastapi import UploadFile
from io import BytesIO
from app.services.brand_service import BrandService
from app.models.brand import Brand
from app.exceptions import PermissionDeniedException, NotFoundException


class TestBrandServiceLogoUpload:
    """品牌Service层Logo上传测试"""
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_success(self, db_session):
        """测试管理员成功上传Logo"""
        async for db in db_session:
            # 1. 创建测试品牌
            brand = Brand(
                id=uuid.uuid4(),
                name="测试品牌",
                description="测试描述"
            )
            db.add(brand)
            await db.commit()
            await db.refresh(brand)
            
            # 2. 创建测试图片文件
            image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
            file = UploadFile(
                filename="test_logo.jpg",
                file=BytesIO(image_content)
            )
            
            # 3. 调用Service层方法（严格按照设计文档的函数签名）
            service = BrandService()
            logo_url = await service.upload_brand_logo(
                db=db,
                brand_id=brand.id,  # 字段名必须与设计文档一致
                file=file,
                current_user_id=uuid.uuid4(),  # 参数名必须与设计文档一致
                role="ADMIN"  # 参数名必须与设计文档一致
            )
            
            # 4. 验证返回的URL路径
            assert logo_url.startswith("/media/brands/")
            assert str(brand.id) in logo_url
            
            # 5. 验证数据库字段已更新（字段名必须与设计文档一致）
            await db.refresh(brand)
            assert brand.logo_url == logo_url
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_permission_denied(self, db_session):
        """测试非管理员上传失败"""
        async for db in db_session:
            # 1. 创建测试品牌
            brand = Brand(
                id=uuid.uuid4(),
                name="测试品牌"
            )
            db.add(brand)
            await db.commit()
            await db.refresh(brand)
            
            # 2. 创建测试图片文件
            file = UploadFile(
                filename="test_logo.jpg",
                file=BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100)
            )
            
            # 3. 使用非管理员角色调用（严格按照设计文档）
            service = BrandService()
            with pytest.raises(PermissionDeniedException):
                await service.upload_brand_logo(
                    db=db,
                    brand_id=brand.id,
                    file=file,
                    current_user_id=uuid.uuid4(),
                    role="REGULAR"  # 非管理员角色
                )
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_brand_not_found(self, db_session):
        """测试品牌不存在"""
        async for db in db_session:
            # 使用不存在的品牌ID
            non_existent_brand_id = uuid.uuid4()
            
            file = UploadFile(
                filename="test_logo.jpg",
                file=BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100)
            )
            
            service = BrandService()
            with pytest.raises(NotFoundException):
                await service.upload_brand_logo(
                    db=db,
                    brand_id=non_existent_brand_id,
                    file=file,
                    current_user_id=uuid.uuid4(),
                    role="ADMIN"
                )
```

**文件**: `backend/live_core_service/tests/test_service_expert_avatar.py`

```python
"""
专家Service层测试 - 头像上传功能

测试覆盖：
- upload_expert_avatar() 成功场景
- upload_expert_avatar() 权限验证
- upload_expert_avatar() 资源验证
"""

import pytest
import uuid
from fastapi import UploadFile
from io import BytesIO
from app.services.expert_service import ExpertService
from app.models.expert import Expert
from app.exceptions import PermissionDeniedException, NotFoundException


class TestExpertServiceAvatarUpload:
    """专家Service层头像上传测试"""
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_success(self, db_session):
        """测试管理员成功上传头像"""
        async for db in db_session:
            # 1. 创建测试专家
            expert = Expert(
                id=uuid.uuid4(),
                name="测试专家",
                title="测试职称"
            )
            db.add(expert)
            await db.commit()
            await db.refresh(expert)
            
            # 2. 创建测试图片文件
            image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
            file = UploadFile(
                filename="test_avatar.jpg",
                file=BytesIO(image_content)
            )
            
            # 3. 调用Service层方法（严格按照设计文档的函数签名）
            service = ExpertService(db)  # 注意：专家Service需要传入db参数
            avatar_url = await service.upload_expert_avatar(
                expert_id=expert.id,  # 参数名必须与设计文档一致
                file=file,
                current_user_id=uuid.uuid4(),  # 参数名必须与设计文档一致
                role="ADMIN"  # 参数名必须与设计文档一致
            )
            
            # 4. 验证返回的URL路径
            assert avatar_url.startswith("/media/experts/")
            assert str(expert.id) in avatar_url
            
            # 5. 验证数据库字段已更新（字段名必须与设计文档一致）
            await db.refresh(expert)
            assert expert.avatar_url == avatar_url
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_permission_denied(self, db_session):
        """测试非管理员上传失败"""
        async for db in db_session:
            expert = Expert(
                id=uuid.uuid4(),
                name="测试专家"
            )
            db.add(expert)
            await db.commit()
            await db.refresh(expert)
            
            file = UploadFile(
                filename="test_avatar.jpg",
                file=BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100)
            )
            
            service = ExpertService(db)
            with pytest.raises(PermissionDeniedException):
                await service.upload_expert_avatar(
                    expert_id=expert.id,
                    file=file,
                    current_user_id=uuid.uuid4(),
                    role="REGULAR"  # 非管理员角色
                )
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_expert_not_found(self, db_session):
        """测试专家不存在"""
        async for db in db_session:
            non_existent_expert_id = uuid.uuid4()
            
            file = UploadFile(
                filename="test_avatar.jpg",
                file=BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100)
            )
            
            service = ExpertService(db)
            with pytest.raises(NotFoundException):
                await service.upload_expert_avatar(
                    expert_id=non_existent_expert_id,
                    file=file,
                    current_user_id=uuid.uuid4(),
                    role="ADMIN"
                )
```

### 5.5 API层测试代码

**文件**: `backend/live_core_service/tests/test_api_brand_logo.py`

```python
"""
品牌API层测试 - Logo上传端点

测试覆盖：
- POST /api/v1/admin/brands/{brand_id}/logo 成功场景
- 权限验证（403 Forbidden, code: 3003）
- 资源验证（404 Not Found, code: 2001）
- 文件验证（400 Bad Request, code: 4001）
- 响应结构验证（严格按照设计文档）
"""

import pytest
import uuid
from io import BytesIO
from app.models.brand import Brand


class TestBrandLogoUploadAPI:
    """品牌Logo上传API测试"""
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_success(self, async_client, db_session):
        """测试管理员成功上传Logo"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建测试品牌
                brand = Brand(
                    id=uuid.uuid4(),
                    name="测试品牌",
                    description="测试描述"
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                # 2. 创建管理员Token（需要根据实际认证机制调整）
                admin_token = "admin_jwt_token_here"  # 实际测试中需要生成真实Token
                
                # 3. 创建测试图片文件
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_logo.jpg", BytesIO(image_content), "image/jpeg")
                }
                
                # 4. 调用API端点（严格按照设计文档的路径和参数）
                response = await client.post(
                    f"/api/v1/admin/brands/{brand_id}/logo",  # 路径必须与设计文档一致
                    files=files,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                # 5. 验证HTTP状态码（必须与设计文档一致）
                assert response.status_code == 200
                
                # 6. 验证响应结构（必须与设计文档完全一致）
                data = response.json()
                assert "code" in data
                assert data["code"] == 200  # 业务状态码必须与设计文档一致
                assert "message" in data
                assert "data" in data
                assert "timestamp" in data
                
                # 7. 验证响应数据字段（字段名必须与设计文档一致）
                assert "brand_id" in data["data"]
                assert "logo_url" in data["data"]
                assert data["data"]["brand_id"] == str(brand.id)
                assert data["data"]["logo_url"].startswith("/media/brands/")
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_permission_denied(self, async_client, db_session):
        """测试非管理员上传返回403 Forbidden (code: 3003)"""
        async for client in async_client:
            async for db in db_session:
                brand = Brand(
                    id=uuid.uuid4(),
                    name="测试品牌"
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                # 使用非管理员Token
                regular_token = "regular_jwt_token_here"
                
                files = {
                    "file": ("test_logo.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
                }
                
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {regular_token}"}
                )
                
                # 验证HTTP状态码和业务状态码（必须与设计文档一致）
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3003  # 权限不足错误码必须与设计文档一致
                assert "权限不足" in data["message"]
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_brand_not_found(self, async_client, db_session):
        """测试品牌不存在返回404 Not Found (code: 2001)"""
        async for client in async_client:
            non_existent_brand_id = uuid.uuid4()
            admin_token = "admin_jwt_token_here"
            
            files = {
                "file": ("test_logo.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
            }
            
            response = await client.post(
                f"/api/v1/admin/brands/{non_existent_brand_id}/logo",
                files=files,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            # 验证HTTP状态码和业务状态码（必须与设计文档一致）
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001  # 资源不存在错误码必须与设计文档一致
            assert "品牌不存在" in data["message"]
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_invalid_file_format(self, async_client, db_session):
        """测试无效文件格式返回400 Bad Request (code: 4001)"""
        async for client in async_client:
            async for db in db_session:
                brand = Brand(
                    id=uuid.uuid4(),
                    name="测试品牌"
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                admin_token = "admin_jwt_token_here"
                
                # 上传非图片文件
                files = {
                    "file": ("test.txt", BytesIO(b"This is not an image"), "text/plain")
                }
                
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                # 验证HTTP状态码和业务状态码（必须与设计文档一致）
                assert response.status_code == 400
                data = response.json()
                assert data["code"] == 4001  # 参数校验失败错误码必须与设计文档一致
    
    @pytest.mark.asyncio
    async def test_upload_brand_logo_file_too_large(self, async_client, db_session):
        """测试文件过大返回400 Bad Request (code: 4001)"""
        async for client in async_client:
            async for db in db_session:
                brand = Brand(
                    id=uuid.uuid4(),
                    name="测试品牌"
                )
                db.add(brand)
                await db.commit()
                await db.refresh(brand)
                
                admin_token = "admin_jwt_token_here"
                
                # 创建超过5MB的文件
                from app.core.config import UPLOAD_MAX_SIZE
                large_content = b'\xff\xd8\xff\xe0' + b'0' * (UPLOAD_MAX_SIZE + 1)
                
                files = {
                    "file": ("large_logo.jpg", BytesIO(large_content), "image/jpeg")
                }
                
                response = await client.post(
                    f"/api/v1/admin/brands/{brand.id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                assert response.status_code == 400
                data = response.json()
                assert data["code"] == 4001
```

**文件**: `backend/live_core_service/tests/test_api_expert_avatar.py`

```python
"""
专家API层测试 - 头像上传端点

测试覆盖：
- POST /api/v1/admin/experts/{expert_id}/avatar 成功场景
- 权限验证（403 Forbidden, code: 3003）
- 资源验证（404 Not Found, code: 2001）
- 文件验证（400 Bad Request, code: 4001）
- 响应结构验证（严格按照设计文档）
"""

import pytest
import uuid
from io import BytesIO
from app.models.expert import Expert


class TestExpertAvatarUploadAPI:
    """专家头像上传API测试"""
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_success(self, async_client, db_session):
        """测试管理员成功上传头像"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建测试专家
                expert = Expert(
                    id=uuid.uuid4(),
                    name="测试专家",
                    title="测试职称"
                )
                db.add(expert)
                await db.commit()
                await db.refresh(expert)
                
                # 2. 创建管理员Token
                admin_token = "admin_jwt_token_here"
                
                # 3. 创建测试图片文件
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_avatar.jpg", BytesIO(image_content), "image/jpeg")
                }
                
                # 4. 调用API端点（严格按照设计文档的路径）
                response = await client.post(
                    f"/api/v1/admin/experts/{expert.id}/avatar",  # 路径必须与设计文档一致
                    files=files,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                # 5. 验证HTTP状态码和响应结构（必须与设计文档完全一致）
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert "data" in data
                assert "expert_id" in data["data"]  # 字段名必须与设计文档一致
                assert "avatar_url" in data["data"]  # 字段名必须与设计文档一致
                assert data["data"]["expert_id"] == str(expert.id)
                assert data["data"]["avatar_url"].startswith("/media/experts/")
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_permission_denied(self, async_client, db_session):
        """测试非管理员上传返回403 Forbidden (code: 3003)"""
        async for client in async_client:
            async for db in db_session:
                expert = Expert(
                    id=uuid.uuid4(),
                    name="测试专家"
                )
                db.add(expert)
                await db.commit()
                await db.refresh(expert)
                
                regular_token = "regular_jwt_token_here"
                
                files = {
                    "file": ("test_avatar.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
                }
                
                response = await client.post(
                    f"/api/v1/admin/experts/{expert.id}/avatar",
                    files=files,
                    headers={"Authorization": f"Bearer {regular_token}"}
                )
                
                assert response.status_code == 403
                data = response.json()
                assert data["code"] == 3003  # 必须与设计文档一致
                assert "权限不足" in data["message"]
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_expert_not_found(self, async_client, db_session):
        """测试专家不存在返回404 Not Found (code: 2001)"""
        async for client in async_client:
            non_existent_expert_id = uuid.uuid4()
            admin_token = "admin_jwt_token_here"
            
            files = {
                "file": ("test_avatar.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
            }
            
            response = await client.post(
                f"/api/v1/admin/experts/{non_existent_expert_id}/avatar",
                files=files,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 2001  # 必须与设计文档一致
            assert "专家不存在" in data["message"]
    
    @pytest.mark.asyncio
    async def test_upload_expert_avatar_invalid_uuid(self, async_client, db_session):
        """测试无效UUID格式返回400 Bad Request (code: 4001)"""
        async for client in async_client:
            admin_token = "admin_jwt_token_here"
            
            files = {
                "file": ("test_avatar.jpg", BytesIO(b'\xff\xd8\xff\xe0' + b'0' * 100), "image/jpeg")
            }
            
            # 使用无效的UUID格式
            response = await client.post(
                "/api/v1/admin/experts/invalid-uuid/avatar",
                files=files,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["code"] == 4001
```

### 5.6 集成测试代码

**文件**: `backend/live_core_service/tests/test_integration_brand_expert_upload.py`

```python
"""
集成测试 - 品牌Logo和专家头像上传完整流程

测试覆盖：
- 品牌创建 → Logo上传 → 品牌查询（验证logo_url返回）
- 专家创建 → 头像上传 → 专家查询（验证avatar_url返回）
- 并发上传测试
"""

import pytest
import uuid
from io import BytesIO
from app.models.brand import Brand
from app.models.expert import Expert


class TestBrandLogoIntegration:
    """品牌Logo上传集成测试"""
    
    @pytest.mark.asyncio
    async def test_brand_create_upload_logo_query_flow(self, async_client, db_session):
        """测试完整流程：创建品牌 → 上传Logo → 查询品牌（验证logo_url）"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建品牌
                brand_data = {
                    "name": "测试品牌",
                    "description": "测试描述"
                }
                admin_token = "admin_jwt_token_here"
                
                create_response = await client.post(
                    "/api/v1/admin/brands",
                    json=brand_data,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert create_response.status_code == 200
                brand_id = create_response.json()["data"]["id"]
                
                # 2. 上传Logo
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_logo.jpg", BytesIO(image_content), "image/jpeg")
                }
                
                upload_response = await client.post(
                    f"/api/v1/admin/brands/{brand_id}/logo",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert upload_response.status_code == 200
                logo_url = upload_response.json()["data"]["logo_url"]
                
                # 3. 查询品牌，验证logo_url已更新
                query_response = await client.get(
                    f"/api/v1/admin/brands/{brand_id}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert query_response.status_code == 200
                brand_data = query_response.json()["data"]
                assert brand_data["logo_url"] == logo_url  # 字段名必须与设计文档一致


class TestExpertAvatarIntegration:
    """专家头像上传集成测试"""
    
    @pytest.mark.asyncio
    async def test_expert_create_upload_avatar_query_flow(self, async_client, db_session):
        """测试完整流程：创建专家 → 上传头像 → 查询专家（验证avatar_url）"""
        async for client in async_client:
            async for db in db_session:
                # 1. 创建专家
                expert_data = {
                    "name": "测试专家",
                    "title": "测试职称"
                }
                admin_token = "admin_jwt_token_here"
                
                create_response = await client.post(
                    "/api/v1/admin/experts",
                    json=expert_data,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert create_response.status_code == 200
                expert_id = create_response.json()["data"]["id"]
                
                # 2. 上传头像
                image_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'0' * 1000
                files = {
                    "file": ("test_avatar.jpg", BytesIO(image_content), "image/jpeg")
                }
                
                upload_response = await client.post(
                    f"/api/v1/admin/experts/{expert_id}/avatar",
                    files=files,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert upload_response.status_code == 200
                avatar_url = upload_response.json()["data"]["avatar_url"]
                
                # 3. 查询专家，验证avatar_url已更新
                query_response = await client.get(
                    f"/api/v1/admin/experts/{expert_id}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert query_response.status_code == 200
                expert_data = query_response.json()["data"]
                assert expert_data["avatar_url"] == avatar_url  # 字段名必须与设计文档一致
```

### 5.7 测试执行说明

#### 5.7.1 运行所有测试

```bash
# 运行所有图片上传相关测试
pytest tests/test_file_handler_brand_expert.py \
       tests/test_service_brand_logo.py \
       tests/test_service_expert_avatar.py \
       tests/test_api_brand_logo.py \
       tests/test_api_expert_avatar.py \
       tests/test_integration_brand_expert_upload.py -v

# 运行特定测试文件
pytest tests/test_api_brand_logo.py -v

# 运行特定测试函数
pytest tests/test_api_brand_logo.py::TestBrandLogoUploadAPI::test_upload_brand_logo_success -v
```

#### 5.7.2 测试覆盖率要求

- **FileHandler层**: 覆盖率 > 90%
- **Service层**: 覆盖率 > 85%
- **API层**: 覆盖率 > 80%
- **集成测试**: 覆盖所有主要流程

#### 5.7.3 测试一致性验证

在提交测试代码前，必须使用《测试代码与设计文档一致性检测提示词母版.md》进行验证，确保：

1. ✅ 所有字段名与设计文档完全一致
2. ✅ 所有函数签名与设计文档完全一致
3. ✅ 所有API端点与设计文档完全一致
4. ✅ 所有响应结构与设计文档完全一致
5. ✅ 所有Fixture使用规范（`async for` 解包）
6. ✅ 无任何猜测行为

---

## 📋 实施步骤

### 阶段1：FileHandler层实现（预计1小时）

1. ✅ 在 `file_handler.py` 末尾添加4个新方法
2. ✅ 本地单元测试路径生成逻辑
3. ✅ 验证文件保存功能

### 阶段2：Service层实现（预计1.5小时）

4. ✅ 在 `brand_service.py` 中添加 `upload_brand_logo()` 方法
5. ✅ 在 `expert_service.py` 中添加 `upload_expert_avatar()` 方法
6. ✅ 单元测试Service层权限验证
7. ✅ 单元测试Service层资源验证

### 阶段3：API层实现（预计2小时）

8. ✅ 在 `brand.py` 中添加Logo上传端点
9. ✅ 在 `experts.py` 中添加头像上传端点
10. ✅ 在 `brand.py` 中添加获取品牌关联直播间列表端点（`GET /admin/brands/{brand_id}/rooms`）
11. ✅ API层异常处理测试
12. ✅ 使用Postman/curl测试multipart/form-data上传
13. ✅ 使用Postman/curl测试品牌关联直播间列表查询接口

### 阶段4：Nginx配置（预计0.5小时）

12. ✅ 配置 `/media/brands/` 路径映射
13. ✅ 配置 `/media/experts/` 路径映射
14. ✅ 验证静态文件访问权限
15. ✅ 配置缓存策略

### 阶段5：集成测试（预计2小时）

16. ✅ 端到端功能测试（完整流程）
17. ✅ 权限和安全测试
18. ✅ 前端uni.uploadFile集成测试
19. ✅ 性能测试（并发上传）

### 阶段6：文档更新（预计1小时）

20. ✅ 更新品牌模块设计文档（添加4.1.8节）
21. ✅ 更新专家模块设计文档（添加对应节）
22. ✅ 更新API文档和Swagger注释

---

## 📝 Nginx配置补充

### 配置文件路径
`nginx/nginx.conf` 或对应的站点配置文件

### 新增配置内容

```nginx
# 品牌Logo静态文件
location /media/brands/ {
    alias /path/to/media/brands/;
    
    # 缓存配置
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # CORS配置（如果前端跨域访问）
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    
    # 安全头
    add_header X-Content-Type-Options nosniff;
}

# 专家头像静态文件
location /media/experts/ {
    alias /path/to/media/experts/;
    
    # 缓存配置
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # CORS配置（如果前端跨域访问）
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    
    # 安全头
    add_header X-Content-Type-Options nosniff;
}
```

### 配置说明

1. **alias路径**: 需要替换为实际的 `ROOM_MEDIA_ROOT_PATH` 路径
2. **缓存策略**: 图片资源设置1年缓存，提升性能
3. **CORS配置**: 如果前端域名与后端不同，需要配置CORS
4. **安全头**: 防止MIME类型嗅探攻击

### 验证步骤

```bash
# 1. 测试配置文件语法
nginx -t

# 2. 重载Nginx配置
nginx -s reload

# 3. 测试静态文件访问
curl http://your-domain/media/brands/test.jpg
curl http://your-domain/media/experts/test.jpg
```

---

## 🎯 前端集成说明

### 前端上传流程

前端使用 `uni.uploadFile` 上传图片，完整流程如下：

```typescript
// 1. 选择图片
uni.chooseImage({
  count: 1,
  success: (res) => {
    const filePath = res.tempFilePaths[0];
    
    // 2. 上传图片
    uploadBrandLogo(brandId, filePath);
  }
});

// 3. 上传函数
function uploadBrandLogo(brandId: string, filePath: string) {
  const token = uni.getStorageSync('access_token');
  
  uni.uploadFile({
    url: `${BASE_API_URL}/admin/brands/${brandId}/logo`,
    filePath,
    name: 'file',  // 关键：参数名必须是'file'
    header: {
      Authorization: `Bearer ${token}`
    },
    success: (res) => {
      const data = JSON.parse(res.data);
      if (data.code === 200) {
        console.log('上传成功:', data.data.logo_url);
      }
    }
  });
}
```

### 关键要点

1. **参数名称**: `uni.uploadFile` 的 `name` 参数必须设置为 `'file'`，与后端 `File(...)` 匹配
2. **Content-Type**: uni.uploadFile 自动设置为 `multipart/form-data`，无需手动指定
3. **Authorization**: 必须在 header 中传递 JWT Token
4. **响应解析**: 需要使用 `JSON.parse(res.data)` 解析响应体

---

## ✅ 验收标准

### 代码质量

- [ ] 所有代码符合项目编码规范
- [ ] 所有函数都有完整的docstring注释
- [ ] 变量命名清晰明确
- [ ] 无冗余代码和注释代码

### 功能完整性

- [ ] API接口按设计文档规范实现
- [ ] 文件上传功能正常工作
- [ ] 数据库字段正确更新
- [ ] 文件成功保存到指定目录

### 异常处理

- [ ] 所有异常处理符合业务状态码体系
- [ ] 异常日志记录完整
- [ ] 用户友好的错误提示信息

### 权限验证

- [ ] 所有权限验证通过测试
- [ ] 非管理员无法上传
- [ ] 日志记录符合脱敏要求

### 性能与安全

- [ ] 文件大小验证有效
- [ ] 文件类型验证有效
- [ ] 无内存泄漏
- [ ] 防止路径遍历攻击
- [ ] 防止文件名注入攻击

### 测试覆盖

- [ ] 所有测试用例通过
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 前端集成测试通过

---

## 📚 附录：设计文档更新说明

### A.1 品牌模块设计文档更新

**文件**: `docs/03_系统设计/直播核心功能设计文档_v6_品牌模块设计文档-品牌管理-品牌专题关联.md`

**更新位置**: 在 `4.1.7 删除品牌（Admin）` 之后添加新章节

**新增章节**: `4.1.8 上传品牌Logo（Admin）`

```markdown
#### 4.1.8 上传品牌Logo（Admin）

**Endpoint**: `POST /api/v1/admin/brands/{brand_id}/logo`

**描述**: 管理员为指定品牌上传Logo图片

**认证**: 需要 `ADMIN` 或 `SUPERADMIN` 角色

**请求格式**: `multipart/form-data`

**请求参数**:
- `file` (UploadFile, 必填): Logo图片文件
  - 允许格式: JPG, JPEG, PNG, GIF
  - 最大大小: 5MB
  - MIME类型: image/jpeg, image/png, image/gif

**成功响应** (`200 OK`):
```json
{
  "code": 200,
  "message": "Logo上传成功",
  "data": {
    "brand_id": "660e8400-e29b-41d4-a716-446655440001",
    "logo_url": "/media/brands/660e8400-e29b-41d4-a716-446655440001/logo_1737456000.jpg"
  },
  "timestamp": "2026-01-21T10:00:00Z"
}
```

**错误响应**:
- `400 Bad Request` (code: 4001): 文件格式或大小不符合要求
- `403 Forbidden` (code: 3003): 权限不足
- `404 Not Found` (code: 2001): 品牌不存在

**执行流程**:

1. 验证JWT Token并检查管理员权限
2. 验证文件格式和大小
3. 根据 `brand_id` 查询品牌，若不存在返回 `2001`
4. 生成存储路径：`/media/brands/{brand_id}/logo_{timestamp}.{ext}`
5. 保存文件到文件系统
6. 更新品牌的 `logo_url` 字段
7. 提交事务并返回成功响应
```

### A.2 专家模块设计文档更新

**文件**: `docs/03_系统设计/直播核心功能设计文档_v6_专家模块设计文档-专家信息-专家关注.md`

**更新位置**: 在删除专家接口之后添加新章节

**新增章节**: 类似品牌模块的Logo上传章节，调整为专家头像上传

---

## 🔍 代码审查要点

### FileHandler层审查

- [ ] 路径生成逻辑正确（brands/experts子目录）
- [ ] 时间戳生成正确
- [ ] 目录创建逻辑正确（makedirs with exist_ok=True）
- [ ] 文件保存使用同步IO（with open）
- [ ] 异常处理完整（HTTPException和通用Exception）

### Service层审查

- [ ] 权限检查在业务逻辑之前
- [ ] 资源存在性验证正确
- [ ] 数据库事务正确（commit + refresh）
- [ ] 日志记录完整（info和warning级别）
- [ ] UUID格式化正确（取前8位用于日志）

### API层审查

- [ ] 参数验证正确（Path, File, Depends, Query）
- [ ] 用户信息提取在try块之前
- [ ] Service实例化方式正确（品牌用全局实例，专家用请求实例）
- [ ] 异常捕获顺序正确（特定异常在前，通用异常在后）
- [ ] 响应格式符合规范（success_response和error_response）
- [ ] HTTP状态码正确（400/403/404/500）
- [ ] 分页参数验证正确（page >= 1, size 范围 1-100）
- [ ] 新接口与 `get_brand_topics` 接口设计模式一致

---

**结束语**: 本文档提供了完整的实施指南，严格遵循品牌模块和专家模块的所有设计规范，确保与现有代码完全兼容。所有代码都经过仔细设计，采用最小幅度修改原则，仅新增必要功能。前端可通过标准的 `multipart/form-data` 格式上传图片，后端完全支持 uni.uploadFile 调用。
