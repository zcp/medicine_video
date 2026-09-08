-- 分类优化 V16：standard 标记回填（阶段 1A K1 的 DB 侧配套）
-- 背景：K1 已把常量中 4 条扩展科目 standard 改为 false，
--      本迁移同步 DB 中已存在的 4 条分类的 standard 标记（33 true → 29 true / 6 false）
-- 前置条件：K1（category_constants.py 4 条改 false）已随代码部署/热更新
-- 幂等性：WHERE standard = true 守卫，可重复执行
-- 重要：本迁移必须与 K1 同批执行（中间窗口期编辑这 4 条分类将触发 standard 校验 400）

-- 1) 4 条扩展科目 standard 改 false
UPDATE categories
SET standard = false
WHERE name IN ('心胸外科', '血管外科', '器官移植科', '烧伤与创面修复科')
  AND standard = true;

-- 2) 验证：预期 29 true / 6 false
-- SELECT count(*) FILTER (WHERE standard) AS std_true,
--        count(*) FILTER (WHERE NOT standard) AS std_false
-- FROM categories;
-- 预期：std_true=29, std_false=6（生殖医学科/其他/心胸外科/血管外科/器官移植科/烧伤与创面修复科）
