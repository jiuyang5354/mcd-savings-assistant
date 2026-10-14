# 麦门省钱助手 Skill

一个帮你把麦当劳吃到最值的 Agent Skill：输入预算、人数、忌口，输出最优点单方案。

## 触发条件

当用户提到麦当劳点单、怎么点划算、优惠券、凑单、1+1 随心配、拼单时使用。

## 工作流

1. **拿数据**：优先调用麦当劳 MCP 实时数据（见 `MCP_INTEGRATION.md`）：
   `query-nearby-stores` → 拿 storeCode → `query-meals` 拉菜单 → `query-store-coupons` /
   `available-coupons` / `my-coupons` 拉券 → `campaign-calendar` 看活动。
   无 Token 时用 `data/sample_menu.json` 演示（会明确告知用户是示例数据）。
2. **算最优**：调用 `src/mcsaver/optimizer.py`：
   - `plan_order(budget, people, menu)`：按预算人数出整单方案（1+1 凑人均 + 最优券 + 凑单提示）
   - `one_plus_one_best(menu)`：1+1 随心配红白区最优组合（省得最多的那一对）
   - `compare_combo_vs_alacarte(want, menu)`：想吃的东西，套餐和单点哪个便宜
   - `best_coupon(subtotal, coupons)`：优惠券最优叠加（含可叠加券穷举）
   - `addon_to_threshold(subtotal, menu)`：凑满减提示，只推荐“多花的钱 < 多省的钱”的加购
3. **算实价**：把方案丢给 MCP `calculate-price` 做官方验算（以官方返回为准）。
4. **呈现**：给用户一张省钱结论卡：吃什么、怎么点、用什么券、实付多少、人均多少、比原价省多少。

## 能力边界

- 只做“怎么点更省”的计算和建议，不代下单、不代领券（领券、下单类动作需用户自己确认）。
- 价格、券、活动以 MCP 实时返回为准；示例数据仅用于演示。
- Token 通过环境变量 `MCD_MCP_TOKEN` 传入，绝不写进代码或配置文件。
