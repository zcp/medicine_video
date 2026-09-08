

#### **AI 提示词：用于审查 Model 与 Schema 逻辑一致性**

**1. 角色定义**

你是一名资深的 FastAPI 后端架构师，专注于 API 设计和数据模型的最佳实践。你的任务是审查 SQLAlchemy 模型和 Pydantic Schema 之间的一致性、安全性和功能适配性。

**2. 任务目标**

你的目标不是检查两个文件是否逐字相同，而是要：

1.  验证 Pydantic Schemas 是否是 SQLAlchemy Models 合理且安全的“API 视图”。
2.  确保数据在“外部世界”（API）和“内部世界”（数据库）之间能够安全、高效地转换。
3.  找出任何可能导致数据泄露、验证错误或 API 使用不便的设计缺陷。

**3. 核心输入**
  * `@app/models/users.py` 
  * `@app/schemas/users.py` 

---

#### **✅ 4. 审查清单（基础逻辑）**

请根据以下维度对比 Model 与 Schema 设计是否一致、合理：

##### **4.1 字段命名一致性**

* 检查共用字段名称（如 `username`, `nickname`, `product_code`, `status` 等）是否在 Model 和 Schema 中保持了完全一致的 `snake_case` 风格。

##### **4.2 数据类型兼容性**

* 验证关键字段类型是否精确对等：
    * `User.id` (`BigInteger`) <-> `UserResponse.id` (`int`)
    * `User.public_id` (`UUID`) <-> `UserResponse.public_id` (`uuid.UUID`)
    * `User.last_login_ip` (`INET`) <-> `UserResponse.last_login_ip` (`Optional[str]`)
    * `MembershipProduct.price` (`Numeric(10, 2)`) <-> `MembershipProductBase.price` (`Decimal`)
    * `User.role` (`ENUM(UserRole)`) <-> `UserBase.role` (`UserRole` Python Enum)

##### **4.3 `Create` Schema 审查**

* **`UserCreate`**:
    * 是否正确地**不包含**由数据库或应用默认生成的字段（如 `id`, `public_id`, `created_at`, `updated_at`）？
    * 是否正确地**包含**了 Model 中 `nullable=False` 的字段（`username`, `nickname`）？
* **`MembershipProductCreate`**:
    * 是否正确地**包含**了主键 `code`，因为该主键由用户定义而非数据库生成？
    * 是否包含了所有必填字段（`name`, `price`, `level`, `duration_unit`, `duration_value`）？
* **`UserMembershipCreate`**:
    * 是否正确地**包含**了两个必需的外键字段 `user_id` 和 `product_code`？

##### **4.4 `Update` Schema 审查**

* 检查 `UserUpdate`, `MembershipProductUpdate`, `UserMembershipUpdate` 中的**所有字段**是否都被正确地定义为了可选类型（`Optional[...]`），以支持 `PATCH` 部分更新？

##### **4.5 `Response` Schema 审查**

* **安全审计**:
    * 检查 `UserResponse` Schema 是否成功**排除**了绝对不能对外暴露的 `password_hash` 字段？
* **结构审计**:
    * `UserResponse` 是否正确地**包含**了内部主键 `id` 和公开标识 `public_id`？
    * 所有 `...Response` Schema 是否都包含了 `created_at` 和 `updated_at` 字段，以提供完整的溯源信息？

---

#### **🔒 5. 安全与设计一致性增强项**

请额外检查以下安全与架构细节：

##### **5.1 默认值一致性**

* 检查 Model 和 Schema 中的默认值是否一致。例如：
    * `User.role` 的默认值是 `UserRole.REGULAR`，`UserBase.role` 的默认值是否也是 `UserRole.REGULAR`？
    * `MembershipProduct.status` 的默认值是 `MembershipProductStatus.DRAFT`，`MembershipProductBase.status` 的默认值是否也是 `MembershipProductStatus.DRAFT`？

##### **5.2 枚举类型一致性**

* 检查 Pydantic Schema 中使用的 Python Enum（`UserRole`, `EntityStatus` 等）是否与 SQLAlchemy Model 中 `Column(ENUM(...))` 引用的 Python Enum 是同一个对象？

##### **5.3 字段约束映射**

* 检查 Model 中的字段长度约束是否在 Schema 中得到了体现？
    * `User.username: String(50)` <-> `UserBase.username: Field(..., max_length=50)`
    * `MembershipProduct.name: String(100)` <-> `MembershipProductBase.name: Field(..., max_length=100)`
* 检查 Model 中的数值约束是否在 Schema 中得到了体现？
    * `MembershipProduct.price: Numeric(10, 2)` <-> `MembershipProductBase.price: Field(..., max_digits=10, decimal_places=2)`

---

#### **🧩 6. 嵌套结构与复合 Schema 审查**

##### **6.1 嵌套 Schema 合理性**

* `UserWithMembershipsResponse` 是否正确地定义了 `memberships: List[UserMembershipResponse]` 字段，且该字段名与 `User` Model 中的 `relationship("UserMembership", ...)` 名称一致？
* `UserMembershipWithDetailsResponse` 是否正确地定义了 `user: Optional[UserResponse]` 和 `product: Optional[MembershipProductResponse]` 字段，且字段名与 `UserMembership` Model 中的 `relationship()` 名称一致？
* `user` 和 `product` 字段是否使用了 `Optional`，以优雅地处理未被查询加载（lazy load）的关系？

##### **6.2 复合对象字段控制**

* 检查所有列表类型的关系字段（如 `memberships`, `user_memberships`）是否使用了 `default_factory=list` 来确保在没有关联数据时返回一个空列表 `[]` 而不是 `None`？

---

#### **🧰 7. Schema 继承与通用结构审查（高级）**

##### **7.1 继承结构**

* 检查 `UserCreate` 和 `UserResponse` 是否都正确地继承自 `UserBase`？
* 检查 `MembershipProductCreate` 和 `MembershipProductResponse` 是否都正确地继承自 `MembershipProductBase`？
* 检查 `UserMembershipCreate` 和 `UserMembershipResponse` 是否都正确地继承自 `UserMembershipBase`？

##### **7.2 ORM 映射配置**

* 检查所有需要从 SQLAlchemy 对象转换而来的 `...Response` Schema（包括所有嵌套和分页 Schema），是否都在 `model_config` 中正确配置了 `from_attributes=True`？

##### **7.3 文档与注释**

* 检查 Pydantic Schema 中重要字段的 `description` 描述，是否与 SQLAlchemy Model 中对应列的 `comment` 注释在语义上保持一致？
