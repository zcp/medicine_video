from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from uuid import UUID
from typing import Optional, Dict, List
from datetime import datetime
import logging
import csv
import io
import chardet
import secrets
import uuid
import pandas as pd

from app.crud import room as crud_room
from app.crud import session as crud_session
from app.exceptions import (
    InvalidParameterException,
    PermissionDeniedException,
    RoomNotFoundException,
    NotFoundException
)
from app.core.exceptions import (
    DatabaseIntegrityException,
    DatabaseOperationException,
)
from app.models.live_core import LiveRoom
from app.services.session_import import SessionImportService

logger = logging.getLogger(__name__)

class BatchImportService:
    """批量导入服务（学院派实现）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    def _check_admin_role(self, role: str) -> None:
        """
        管理员角色校验（用于批量导入等后台管理功能）
        
        Args:
            role: 当前用户的角色
            
        Raises:
            PermissionDeniedException: 非Admin用户, 非regular用户（403）
        """
        if role not in ['REGULAR', 'ADMIN', 'SUPERADMIN']:
            raise PermissionDeniedException("Admin role required")
    
    async def import_from_file(
        self,
        public_id: UUID,
        file: UploadFile,
        mode: str = 'dry_run',
        encoding_hint: Optional[str] = None,
        role: str = None  # ← 新增：权限参数
    ) -> Dict:
        """
        从 CSV/Excel 文件批量导入直播间和会话（Admin Only）
        
        职责：
        1. 验证管理员权限
        2. 读取并解析文件
        3. 验证必需列
        4. 逐行处理（行级事务隔离）
        5. 根据 mode 决定是否提交事务
        
        参数：
        - public_id: 当前用户公开标识
        - file: 上传的文件
        - mode: 'dry_run' 或 'apply'
        - encoding_hint: 编码提示（仅对CSV有效）
        - role: 当前用户的角色（从JWT的role字段提取）
        
        返回：
        - {"total_rows": int, "success_count": int, "failed_count": int, "items": []}
        
        Raises:
            PermissionDeniedException: 非Admin用户（403）
        """
        # ← 新增：权限校验（Admin Only）
        self._check_admin_role(role)
        # 1. 读取文件内容
        content = await file.read()
        
        # 2. 根据文件扩展名选择解析器
        filename = file.filename or ""
        file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if file_extension == 'xlsx':
            # 解析 Excel 文件
            rows = self._parse_excel(content)
        elif file_extension == 'csv':
            # 解析 CSV 文件
            encoding = self._detect_encoding(content, encoding_hint)
            logger.info(f"CSV 文件编码：{encoding}")
            rows = self._parse_csv(content, encoding)
        else:
            raise InvalidParameterException(
                code=4001,
                message="不支持的文件格式，仅支持 .csv 或 .xlsx 文件"
            )
        
        # 3. 标准化列名并验证必需列（支持中文表头别名映射）
        #    先对行数据应用别名映射（例如：标题 → room_title，播放url（以及历史表头“播放url1”）→ playback_url，封面图片 → cover_url）
        rows = self._apply_header_aliases(rows)

        required_columns = {'room_title', 'playback_url'}
        if not rows:
            raise InvalidParameterException(
                code=4002,
                message="文件为空或格式错误"
            )
        
        # 从第一行获取列名（此时已包含逻辑字段名）
        first_row = rows[0] if rows else {}
        columns = {col.lower().strip() for col in first_row.keys()}
        
        if not required_columns.issubset(columns):
            missing = required_columns - columns
            # 与设计文档保持一致，仍然使用逻辑字段名给出错误提示
            raise InvalidParameterException(
                code=4002,
                message=f"CSV 文件缺少必需列：{', '.join(sorted(missing))}"
            )
        
        # 4. 逐行处理
        import_results = []
        success_count = 0
        failed_count = 0
        
        for row_no, row in enumerate(rows, start=1):
            try:
                # 行数据已经在解析时标准化，直接使用
                row_data = row
                
                # 处理单行
                result = await self._process_row(
                    public_id=public_id,
                    row_no=row_no,
                    row=row_data,
                    mode=mode,
                    role=role  # ← 新增：传递权限参数
                )
                
                import_results.append(result)
                
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"处理第 {row_no} 行失败：{e}", exc_info=True)
                import_results.append({
                    "row_no": row_no,
                    "room_id": None,
                    "session_id": None,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        # 6. 统计幂等跳过数量（V6 新增，可选字段）
        skipped_count = sum(
            1 for item in import_results if item.get("skipped") is True
        )

        # 7. 返回导入报告
        report = {
            "total_rows": len(import_results),
            "success_count": success_count,
            "failed_count": failed_count,
            "items": import_results,
        }
        # 仅当存在 skipped 记录时返回该字段，保持向后兼容
        if skipped_count:
            report["skipped_count"] = skipped_count

        return report

    async def _get_or_create_room_for_row(
        self,
        public_id: UUID,
        row: Dict,
    ) -> LiveRoom:
        """
        根据行数据获取或创建房间（V6 房间幂等逻辑）

        优先级：
        1. 若提供 room_id：按 V5 行为复用，并验证权限；
        2. 否则若提供 external_room_id：按 (user_id, external_room_id) 幂等复用；
        3. 否则：创建新房间，必要时写入 external_room_id。
        """
        room_id_str = row.get("room_id")
        external_room_id = row.get("external_room_id")

        # a) 有 room_id：按 V5 行为复用 + 权限校验
        if room_id_str:
            try:
                room_id = UUID(room_id_str)
            except ValueError:
                raise InvalidParameterException(
                    code=4002,
                    message=f"无效的 room_id 格式: {room_id_str}",
                )

            room = await crud_room.get(self.db, room_id=room_id, user_id=public_id)
            if not room:
                raise InvalidParameterException(
                    code=4002,
                    message=f"房间 {room_id} 不存在或无权限",
                )
            return room

        # b) 有 external_room_id：按 (user_id, external_room_id) 幂等复用
        if external_room_id:
            existing = await crud_room.get_by_external_id(
                db=self.db,
                user_id=public_id,
                external_room_id=external_room_id,
            )
            if existing:
                return existing

        # c) 否则或 external_room_id 未命中：创建新房间
        room_title = row.get("room_title") or "未命名直播间"
        room_data = {
            "id": uuid.uuid4(),
            "user_id": public_id,
            "title": room_title,
            "description": row.get("room_description", ""),
            "stream_key": self._generate_stream_key(),
            "cover_url": row.get("cover_url"),
        }

        room = await crud_room.create(self.db, obj_in=room_data, user_id=public_id)

        # 若提供 external_room_id，则回写到新房间并提交
        if external_room_id:
            room.external_room_id = external_room_id
            await self.db.commit()
            await self.db.refresh(room)

        return room
    
    async def _process_row(
        self,
        public_id: UUID,
        row_no: int,
        row: Dict,
        mode: str,
        role: str = "REGULAR"  # ← 新增：权限参数
    ) -> Dict:
        """处理单行数据（行级事务）"""
        # 1. 验证必需字段
        room_title = row.get("room_title")
        playback_url = row.get("playback_url")

        if not room_title or not playback_url:
            return {
                "row_no": row_no,
                "room_id": None,
                "session_id": None,
                "status": "failed",
                "error": "room_title 和 playback_url 不能为空",
                "skipped": False,
                "skip_reason": None,
            }

        # 2. 创建或复用房间
        room_id: Optional[UUID] = None
        room: Optional[LiveRoom] = None

        if mode == "apply":
            try:
                room = await self._get_or_create_room_for_row(public_id, row)
                room_id = room.id
            except InvalidParameterException as e:
                return {
                    "row_no": row_no,
                    "room_id": None,
                    "session_id": None,
                    "status": "failed",
                    "error": str(e),
                    "skipped": False,
                    "skip_reason": None,
                }
            except (DatabaseIntegrityException, DatabaseOperationException) as e:
                return {
                    "row_no": row_no,
                    "room_id": None,
                    "session_id": None,
                    "status": "failed",
                    "error": f"创建或复用房间失败: {str(e)}",
                    "skipped": False,
                    "skip_reason": None,
                }
        else:
            # dry_run 模式：不写库，只做格式校验和权限检查
            room_id_str = row.get("room_id")
            if room_id_str:
                try:
                    room_id = UUID(room_id_str)
                except ValueError:
                    return {
                        "row_no": row_no,
                        "room_id": None,
                        "session_id": None,
                        "status": "failed",
                        "error": f"无效的 room_id 格式: {room_id_str}",
                        "skipped": False,
                        "skip_reason": None,
                    }

            if not room_id:
                room_id = uuid.uuid4()  # dry_run 模式，生成临时 ID

        # 3. 创建会话或模拟创建（按 mode 区分）
        session_id: Optional[UUID] = None
        session_id_str = row.get("session_id")

        if session_id_str:
            try:
                session_id = UUID(session_id_str)
            except ValueError:
                return {
                    "row_no": row_no,
                    "room_id": str(room_id) if room_id else None,
                    "session_id": None,
                    "status": "failed",
                    "error": f"无效的 session_id 格式: {session_id_str}",
                    "skipped": False,
                    "skip_reason": None,
                }
        else:
            session_id = uuid.uuid4()

        if mode == "apply":
            try:
                # 解析时间
                start_time_str = row.get("start_time")
                start_time = datetime.utcnow()
                if start_time_str:
                    try:
                        if start_time_str.endswith("Z"):
                            start_time = datetime.fromisoformat(start_time_str[:-1])
                        else:
                            start_time = datetime.fromisoformat(start_time_str)
                    except ValueError:
                        # 使用默认当前时间
                        pass

                end_time_str = row.get("end_time")
                end_time = None
                if end_time_str:
                    try:
                        if end_time_str.endswith("Z"):
                            end_time = datetime.fromisoformat(end_time_str[:-1])
                        else:
                            end_time = datetime.fromisoformat(end_time_str)
                    except ValueError:
                        pass

                session_in = {
                    "status": row.get("status", "finished"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "playback_url": playback_url,
                    # 其他字段如 title/description 可按需要扩展
                }

                session_service = SessionImportService(self.db)
                session, idempotent_hit = await session_service.import_create_session(
                    room_id=room_id,
                    public_id=public_id,
                    session_in=session_in,
                    role=role  # ← 新增：传递权限参数
                )
                session_id = session.id

                return {
                    "row_no": row_no,
                    "room_id": str(room_id),
                    "session_id": str(session_id),
                    "status": "success",
                    "error": None,
                    "skipped": idempotent_hit,
                    "skip_reason": (
                        "duplicate_session_by_playback_url" if idempotent_hit else None
                    ),
                }
            except (DatabaseIntegrityException, DatabaseOperationException) as e:
                return {
                    "row_no": row_no,
                    "room_id": str(room_id),
                    "session_id": None,
                    "status": "failed",
                    "error": f"创建会话失败: {str(e)}",
                    "skipped": False,
                    "skip_reason": None,
                }
            except (RoomNotFoundException, PermissionDeniedException) as e:
                # 保持与 Service 层异常语义一致
                return {
                    "row_no": row_no,
                    "room_id": str(room_id),
                    "session_id": None,
                    "status": "failed",
                    "error": str(e),
                    "skipped": False,
                    "skip_reason": None,
                }

        # dry_run：仅做字段与格式校验，不写库
        return {
            "row_no": row_no,
            "room_id": str(room_id),
            "session_id": str(session_id),
            "status": "success",
            "error": None,
            "skipped": False,
            "skip_reason": None,
        }
    
    def _parse_csv(self, content: bytes, encoding: str) -> List[Dict]:
        """
        解析 CSV 文件
        
        参数：
        - content: 文件内容（bytes）
        - encoding: 文件编码
        
        返回：
        - List[Dict]: 行数据列表，每行为字典格式
        """
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError as e:
            raise InvalidParameterException(
                code=4001,
                message=f"CSV 文件编码解析失败，建议指定编码格式。错误: {e}"
            )
        
        csv_reader = csv.DictReader(io.StringIO(text))
        
        if not csv_reader.fieldnames:
            raise InvalidParameterException(
                code=4002,
                message="CSV 文件为空或格式错误"
            )
        
        # 读取所有行并标准化列名（转小写，去除空格）
        rows = []
        for row in csv_reader:
            standardized_row = {
                k.lower().strip(): (v.strip() if v else '')
                for k, v in row.items()
                if k
            }
            rows.append(standardized_row)
        
        return rows
    
    def _parse_excel(self, content: bytes) -> List[Dict]:
        """
        解析 Excel 文件（.xlsx）
        
        参数：
        - content: 文件内容（bytes）
        
        返回：
        - List[Dict]: 行数据列表，每行为字典格式
        """
        try:
            # 使用 pandas 读取 Excel 文件
            excel_file = io.BytesIO(content)
            df = pd.read_excel(excel_file, engine='openpyxl')
            
            # 检查是否为空
            if df.empty:
                raise InvalidParameterException(
                    code=4002,
                    message="Excel 文件为空或格式错误"
                )
            
            # 标准化列名（转小写，去除空格）
            df.columns = df.columns.str.lower().str.strip()
            
            # 转换为字典列表，处理 NaN 值为空字符串
            rows = []
            for _, row in df.iterrows():
                row_dict = {}
                for col, val in row.items():
                    # 处理 NaN 值
                    if pd.isna(val):
                        row_dict[col] = ''
                    else:
                        row_dict[col] = str(val).strip()
                rows.append(row_dict)
            
            return rows
            
        except Exception as e:
            logger.error(f"解析 Excel 文件失败：{e}", exc_info=True)
            raise InvalidParameterException(
                code=4001,
                message=f"Excel 文件解析失败：{str(e)}"
            )
    
    def _detect_encoding(self, content: bytes, hint: Optional[str]) -> str:
        """自动探测文件编码（仅用于 CSV）"""
        if hint:
            return hint
        
        # 尝试顺序：utf-8-sig -> utf-8 -> gbk -> chardet
        for encoding in ['utf-8-sig', 'utf-8', 'gbk']:
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # 使用 chardet 自动探测
        detected = chardet.detect(content)
        return detected['encoding'] or 'utf-8'
    
    def _generate_stream_key(self) -> str:
        """生成唯一的推流密钥"""
        return f"sk_live_{secrets.token_hex(16)}"

    def _apply_header_aliases(self, rows: List[Dict]) -> List[Dict]:
        """
        对解析后的行数据应用表头别名映射，将中文表头规范化为内部逻辑字段名。

        逻辑字段与典型来源表头映射关系：
        - room_title  <-  room_title / 标题
        - playback_url <- playback_url / 播放url / 播放url1  （实际文件通常为“播放url”，部分历史模板可能为“播放url1”）
        - cover_url   <-  cover_url / 封面图片

        注意：
        - 只在逻辑字段不存在或为空时才尝试从别名列填充，避免覆盖显式提供的英文表头值。
        - 行数据的 key 在 CSV/Excel 解析阶段已经做了 lower().strip() 处理，这里按照相同规则处理别名。
        """
        if not rows:
            return rows

        alias_map = {
            "room_title": ["room_title", "标题"],
            # 优先使用实际文件中的“播放url”，同时兼容历史表头“播放url1”
            "playback_url": ["playback_url", "播放url", "播放url1"],
            "cover_url": ["cover_url", "封面图片"],
            # V6 新增：external_room_id 映射
            "external_room_id": ["external_room_id", "直播间id", "直播间ID"],
        }

        normalized_rows: List[Dict] = []
        for row in rows:
            # 复制一份，避免直接修改原始引用
            normalized = dict(row)

            for logical, aliases in alias_map.items():
                current_value = normalized.get(logical)
                # 如果逻辑字段已经有非空值，则不再尝试从别名填充
                if current_value:
                    continue

                # 从别名列表（跳过第一个canonical）中寻找第一个有值的列
                for alias in aliases[1:]:
                    alias_key = alias.lower().strip()
                    if alias_key in row and row.get(alias_key):
                        normalized[logical] = row.get(alias_key)
                        break

            normalized_rows.append(normalized)

        return normalized_rows
