# MCP_INTEGRATION.md

本项目实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值说明。

## 1. 使用的 MCP Server

- **地址**：`https://mcp.mcd.cn`（Streamable HTTP，JSON-RPC）
- **认证**：`Authorization: Bearer <TOKEN>`
- **Token 获取**：https://open.mcd.cn 手机号验证登录后申请
- **Token 传递**：环境变量 `MCD_MCP_TOKEN`（代码中仅为占位符，符合参赛声明的信息安全要求）
- 工具清单来源：麦当劳官方仓库 `M-China/mcd-mcp-server`

## 2. 实际使用的 Tool

| Tool | 用途 | 在本项目中的调用点 |
|---|---|---|
| `query-nearby-stores` | 按地址查附近门店，拿 `storeCode` | 流程起点：定位用户门店 |
| `query-meals` | 查门店可售餐品列表（分类、编码、标签） | 拉菜单 → 喂给 optimizer |
| `query-meal-detail` | 按编码查餐品详情、套餐组成、可替换项 | 套餐 vs 单点比价时确认套餐内容 |
| `query-store-coupons` | 查当前门店可用券 | 优惠券叠加计算的输入 |
| `available-coupons` | 查可领取的麦麦省券 | 提醒用户先领券再点单 |
| `my-coupons` | 查卡包已领券 | 用“用户已有券”做最优叠加 |
| `campaign-calendar` | 当月营销活动日历 | 活动期（如 9.9 元吃堡）改写推荐策略 |
| `calculate-price` | 官方价格验算（含券、配送费） | 方案输出前的官方复核，以其结果为准 |
| `list-nutrition-foods` | 餐品营养成分 | 可选：低热量搭配模式 |
| `now-time-info` | 服务器当前时间 | 判断早餐/午市时段券是否可用 |

## 3. 调用流程（按功能）

**整单省钱方案**：
`query-nearby-stores` → `query-meals` → `query-store-coupons`/`my-coupons`
→ `optimizer.plan_order()` 本地算最优 → `calculate-price` 官方验算 → 输出结论卡

**1+1 随心配最优解**：
`query-meals`（筛红白区）→ `optimizer.one_plus_one_best()` → 输出省得最多的一对

**凑满减**：
当前小计 → `optimizer.addon_to_threshold()` → 只推荐净省为正的加购
→ `calculate-price` 验证 → 输出

**活动感知**：
`campaign-calendar` → 若有大促活动（如指定产品 9.9 元），优先用活动价重算方案

## 4. 业务价值

- MCP 提供**真实菜单、真实价格、真实券**：省钱计算不靠编造，所有结论可被 `calculate-price` 官方验算；
- 本地 optimizer 做**组合优化**（券叠加穷举、凑单净省判断），这是 MCP 原生能力之外的增量价值；
- 输出形态面向普通用户：一句话需求 → 一张结论卡，吃什么、怎么点、省多少一目了然。

## 5. 实测字段说明（2026-10-14）

以下结构来自真实接口返回的采样（已剔除个人信息与门店定位细节），
`src/mcsaver/menu_adapter.py` 的解析逻辑以此为准：

**query-meals**：`data.categories[] = {name, meals: [{code, tags?}]}`；
`data.meals = {code: {name, image, currentPrice（字符串，如 "34"）, originalPrice（字符串）, canWithOrder, discountType?, withOrder?}}`。
注意：价格是字符串；`tags` 含"套餐"/"单品"等标签；实测 15 个分类、114 件餐品。

**query-meal-detail**：`data = {code, name, rounds: [{id, name, quantity, maxQuantity, minQuantity, choices: [{code, name, quantity, maxQuantity, isDefault（0/1）, diffPrice, supportModify}]}], image, supportModify}`。
`diffPrice` 形如 `"+ ¥1.5"` / `"- ¥0.5"` / `"+ ¥0"`；详情里没有套餐基准价，基准价取自 query-meals。

**优惠券（available-coupons / query-store-coupons）**：`data[] = {title, couponId, couponCode, tradeDateTime（"开始-结束"，如 "2026-10-12 10:30:00-2026-10-16 23:59:59"）, products: [{productCode, productName}], promotionId}`。
券绑定具体产品，无显式优惠金额，实际优惠以 `calculate-price` 为准。

**query-nearby-stores**：`data[] = {storeCode, storeName, address, distance, businessStatus, businessStartTime, businessEndTime, reservation, ...}`。

**calculate-price**：`data = {productOriginalPrice, productPrice, originalPrice, discount, price, productList: [{productCode, productName, quantity, originalSubtotal, subtotal}], takeWayList: [{code, title, subtitle}]}`。
注意：金额全部是**分**为单位的整数（如 4050 = ¥40.50），`menu_adapter.parse_calculate_price` 统一转成元；`takeWayList` 如堂食（eat-in）/外带（take-in-store）。
