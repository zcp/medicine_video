# Nginx expires 指令说明

## ❌ 误解澄清

**重要**：`expires` 指令**不是**控制文件在服务器上的保存时间，而是控制**浏览器缓存时间**。

### 两个不同的概念

1. **浏览器缓存时间**（`expires` 控制）
   - 告诉浏览器这个文件可以缓存多久
   - 影响的是客户端（浏览器）的行为
   - 文件仍然在服务器上

2. **服务器文件保存时间**（代码逻辑控制）
   - 文件实际在服务器磁盘上的存在时间
   - 由你的代码逻辑决定（比如文件删除策略）
   - 与 `expires` 无关

---

## 📋 当前配置分析

### 你的当前配置

```nginx
location /media/ {
    alias /var/www/html/live-core-media/;
    #expires 7d;  # 缓存7天（已注释）
    add_header Cache-Control "public";
    # ...
}
```

### 注释掉 `expires 7d;` 后的效果

**实际效果**：
- ❌ **不是**图片永久保存在服务器上
- ✅ **是**浏览器不会收到明确的缓存过期时间
- ✅ 浏览器会使用默认的缓存策略（通常是短时间缓存）

### 当前配置的实际行为

由于你还有 `add_header Cache-Control "public";`：

```nginx
add_header Cache-Control "public";
```

**实际效果**：
- 浏览器知道这是公共资源，可以缓存
- 但没有明确的过期时间（因为 `expires` 被注释了）
- 浏览器会使用**启发式缓存**（heuristic caching）：
  - 通常根据文件的 `Last-Modified` 时间
  - 一般缓存 10% 的 `(当前时间 - Last-Modified)` 时间
  - 或者使用浏览器默认策略（通常是几分钟到几小时）

---

## 🔍 详细说明

### 1. `expires` 指令的作用

```nginx
expires 7d;  # 设置缓存7天
```

**HTTP 响应头**：
```
Expires: Wed, 15 Jan 2025 10:00:00 GMT
Cache-Control: max-age=604800
```

**浏览器行为**：
- 浏览器会缓存这个文件 7 天
- 7 天内，浏览器直接从缓存读取，不请求服务器
- 7 天后，浏览器会重新请求服务器

### 2. 注释掉 `expires` 后的行为

```nginx
#expires 7d;  # 已注释
add_header Cache-Control "public";
```

**HTTP 响应头**：
```
Cache-Control: public
（没有 Expires 头）
（没有 max-age）
```

**浏览器行为**：
- 浏览器知道这是公共资源（`public`）
- 但没有明确的过期时间
- 使用启发式缓存或默认策略
- **通常缓存时间较短**（几分钟到几小时）

### 3. 完全移除缓存控制

如果连 `add_header Cache-Control "public";` 也注释掉：

```nginx
#expires 7d;
#add_header Cache-Control "public";
```

**HTTP 响应头**：
```
（没有缓存相关的响应头）
```

**浏览器行为**：
- 每次访问都可能请求服务器
- 或者使用非常短的默认缓存时间
- **性能较差**，因为无法利用浏览器缓存

---

## 💡 推荐配置

### 方案一：短期缓存（适合频繁更新的图片）

```nginx
location /media/ {
    alias /var/www/html/live-core-media/;
    expires 1h;  # 缓存1小时
    add_header Cache-Control "public";
    # ...
}
```

**适用场景**：
- 图片可能会更新
- 需要用户能较快看到最新版本

### 方案二：中期缓存（推荐，平衡性能和更新）

```nginx
location /media/ {
    alias /var/www/html/live-core-media/;
    expires 7d;  # 缓存7天
    add_header Cache-Control "public";
    # ...
}
```

**适用场景**：
- 图片更新不频繁
- 封面图片、横幅等相对稳定的资源

### 方案三：长期缓存（适合带版本号的资源）

```nginx
location /media/ {
    alias /var/www/html/live-core-media/;
    expires 1y;  # 缓存1年
    add_header Cache-Control "public, immutable";
    # ...
}
```

**适用场景**：
- 文件名包含版本号或时间戳（如 `cover_1234567890.jpg`）
- 文件一旦创建就不会改变
- 你的代码中文件名已经包含时间戳，所以这个方案很合适！

### 方案四：不设置过期时间（不推荐）

```nginx
location /media/ {
    alias /var/www/html/live-core-media/;
    #expires 7d;  # 已注释
    add_header Cache-Control "public";
    # ...
}
```

**问题**：
- 浏览器缓存时间不确定
- 可能导致频繁请求服务器
- 性能较差

---

## 🎯 针对你的项目的建议

### 分析你的文件命名

根据你的代码，图片文件名格式是：
```
cover_{timestamp}.{ext}
例如：cover_1765244798.jpg
```

**特点**：
- ✅ 文件名包含时间戳，每次更新都是新文件
- ✅ 旧文件不会被覆盖
- ✅ 文件名唯一，不会冲突

### 推荐配置

```nginx
location /media/ {
    alias /var/www/html/live-core-media/;
    expires 1y;  # 缓存1年（因为文件名包含时间戳，不会更新）
    add_header Cache-Control "public, immutable";
    access_log off;
    
    types {
        image/jpeg jpg jpeg;
        image/png png;
        image/gif gif;
    }
    
    try_files $uri =404;
}
```

**理由**：
1. **文件名包含时间戳**：每次更新都是新文件，旧文件不会改变
2. **`immutable` 标记**：告诉浏览器这个文件永远不会改变
3. **长期缓存**：减少服务器请求，提升性能
4. **不影响更新**：因为新图片是新文件名，浏览器会请求新文件

---

## 📊 配置对比

| 配置 | 浏览器缓存时间 | 性能 | 更新及时性 | 推荐度 |
|------|--------------|------|-----------|--------|
| `expires 1h;` | 1小时 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| `expires 7d;` | 7天 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| `expires 1y;` + `immutable` | 1年 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 注释掉 `expires` | 不确定 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## ⚠️ 重要提醒

### 关于"永久保存"

**`expires` 指令与文件保存时间无关**：

- ❌ `expires` **不会**让文件永久保存在服务器上
- ❌ 注释掉 `expires` **不会**让文件永久保存
- ✅ 文件保存时间由你的代码逻辑决定
- ✅ `expires` 只影响浏览器缓存行为

### 文件实际保存时间

文件在服务器上的保存时间由以下因素决定：

1. **代码逻辑**：
   ```python
   # 例如：删除旧封面
   FileHandler.delete_old_cover(old_cover_url)
   ```

2. **磁盘空间管理**：
   - 定期清理旧文件
   - 磁盘满了需要删除

3. **备份策略**：
   - 是否定期备份
   - 备份保留时间

---

## ✅ 总结

### 当前配置的问题

```nginx
#expires 7d;  # 已注释
add_header Cache-Control "public";
```

**问题**：
- 浏览器缓存时间不确定
- 可能导致频繁请求服务器
- 性能不是最优

### 推荐配置

```nginx
expires 1y;  # 因为文件名包含时间戳
add_header Cache-Control "public, immutable";
```

**优势**：
- ✅ 长期缓存，性能最佳
- ✅ 不影响更新（新文件新名字）
- ✅ 符合你的文件命名策略

### 关键理解

- `expires` = 浏览器缓存时间（不是文件保存时间）
- 文件保存时间 = 由代码逻辑决定
- 你的文件名包含时间戳，适合长期缓存

