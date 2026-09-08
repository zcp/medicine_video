请帮我验证 schemas/download.py 和 models/download.py 的完全一致性，需要检查以下几个方面：

### 1. 枚举类型一致性：
   - 检查所有枚举类（TaskStatus, VideoType, SegmentType, FailureType, ResourceType, FailureStatus）是否完全一致
   - 检查每个枚举类的所有值是否相同
   - 检查枚举值的字符串表示是否相同

### 2. 字段定义一致性：
   - 检查每个模型的所有字段名是否完全一致
   - 检查每个字段的类型是否一致（包括 Optional 类型）
   - 检查每个字段的默认值是否一致
   - 检查每个字段的约束条件是否一致（如 max_length, min_length 等）
   - 检查每个字段的描述（description）是否一致

### 3. 关系定义一致性：
   - 检查所有外键字段的定义是否一致
   - 检查外键字段的类型是否一致（如 UUID 类型）
   - 检查外键字段的约束条件是否一致

### 4. 验证规则一致性：
   - 检查所有字段的验证器（validator）是否一致
   - 检查自定义验证规则是否一致
   - 检查字段验证的错误消息是否一致

### 5. 模型结构一致性：
   - 检查所有模型的继承关系是否一致
   - 检查所有模型的配置（Config）是否一致
   - 检查所有模型的 from_attributes 设置是否一致

### 6. 特殊字段处理一致性：
   - 检查日期时间字段的处理方式是否一致
   - 检查 UUID 字段的处理方式是否一致
   - 检查枚举字段的处理方式是否一致

### 7. 文档注释一致性：
   - 检查所有模型的文档字符串是否一致
   - 检查所有字段的描述是否一致
   - 检查所有枚举类型的描述是否一致

### 8. 一致性参考（DownloadTask 示例）：

**models/download.py**
```python
class DownloadTask(Base):
    __tablename__ = "download_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, comment="任务名称")
```
**schemas/download.py**
```python
class DownloadTaskOut(BaseModel):
    id: UUID = Field(..., description="任务 ID")
    name: str = Field(..., max_length=255, description="任务名称")
```

## 输出格式要求

请详细列出所有不一致的地方，包括：
1. 具体是哪个模型/枚举
2. 具体是哪个字段/值
3. 两个文件中的差异
4. 建议的修改方案

## 特别注意：
- 确保所有字段名完全一致，包括大小写
- 确保所有类型定义完全一致，包括 Optional 类型
- 确保所有约束条件完全一致
- 确保所有验证规则完全一致
- 确保所有关系定义完全一致