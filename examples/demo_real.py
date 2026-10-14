"""演示：用 2026-10-14 实测的真实 MCP 采样数据跑省钱方案。

只读本地 data/real_samples/*.json，不发网络请求、不需要 Token。
采样门店：麦当劳青岛胶州利群餐厅（storeCode 3350072）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcsaver import menu_adapter as ma
from mcsaver import optimizer as opt

BASE = os.path.join(os.path.dirname(__file__), "..")
SAMPLES = os.path.join(BASE, "data", "real_samples")


def main() -> int:
    if not os.path.isdir(SAMPLES):
        print("未找到 data/real_samples/ 真实采样，改用 data/sample_menu.json 演示数据。")
        menu = opt.load_menu(os.path.join(BASE, "data", "sample_menu.json"))
        plan = opt.plan_order(budget=60, people=3, menu=menu)
        print(f"示例：{plan['pairs']} 份 1+1，人均 {plan['per_person']} 元")
        return 0

    menu, coupons, _ = ma.load_samples_dir(SAMPLES)
    by_code = {m["code"]: m for m in menu}
    print(f"真实菜单：15 个分类，{len(menu)} 件餐品（2026-10-14 实测采样）")
    print(f"其中套餐 {len(ma.find_combos(menu))} 款，券 {len(coupons)} 张\n")

    # (a) 1+1 随心配：真实价格
    sxp = ma.find_suixinpei(menu)
    print("【1+1 随心配 · 真实价格】")
    for m in sxp:
        print(f"  {m['name']}（{m['code']}）：现价 {m['current_price']} 元")
    cheap = min(sxp, key=lambda m: m["current_price"])
    pricey = max(sxp, key=lambda m: m["current_price"])
    print(f"  → {cheap['name']} {cheap['current_price']} 元，"
          f"比{pricey['name']}便宜 "
          f"{round(pricey['current_price'] - cheap['current_price'], 2)} 元")

    # (b) 巨无霸三件套：套餐 vs 单点（真实价格）
    # 套餐默认组成来自 query-meal-detail 实测：巨无霸(1100) + 中薯条(4810) + 可乐中杯
    # 4810 在菜单中名为「薯条」14.5 元；可乐中杯(3050)未在菜单字典中，
    # 用同系列的「可乐」(9900008751) 9.5 元代替
    combo = by_code["9900005466"]
    singles = [by_code["1100"], by_code["4810"], by_code["9900008751"]]
    want = [s["name"] for s in singles]
    real_menu = {
        "pair_price": cheap["current_price"],
        "red_zone": [], "white_zone": [],
        "alacarte": [{"name": s["name"], "price": s["current_price"]}
                     for s in singles],
        "combos": [{"id": combo["code"], "name": combo["name"],
                    "price": combo["current_price"], "items": want}],
        "coupons": [], "thresholds": [],
    }
    print(f"\n【套餐 vs 单点 · 真实价格】想吃：{'、'.join(want)}")
    print("  单品价："
          + " + ".join(f"{s['name']}{s['current_price']} 元" for s in singles)
          + f" = {round(sum(s['current_price'] for s in singles), 2)} 元")
    c = opt.compare_combo_vs_alacarte(want, real_menu)
    print(f"  {combo['name']}套餐价 {combo['current_price']} 元"
          f"（官方原价 {combo['original_price']} 元）")
    print(f"  → 选{c['choice']}：{c['plan']}，实付 {c['pay']} 元，"
          f"比单点省 {c['saving']} 元")

    # (c) 全场立省 TOP5（原价 - 现价，真实价格）
    ranked = sorted(menu,
                    key=lambda m: m["original_price"] - m["current_price"],
                    reverse=True)
    print("\n【全场立省 TOP5 · 真实价格】")
    for m in ranked[:5]:
        save = round(m["original_price"] - m["current_price"], 2)
        print(f"  {m['name']}：{m['original_price']} → "
              f"{m['current_price']} 元，立省 {save} 元")

    # (d) 券：真实结构
    print("\n【优惠券 · 真实结构】")
    for cp in coupons:
        print(f"  {cp['title']}：{cp['coupon_code']}，"
              f"有效期 {cp['valid_from']} 至 {cp['valid_to']}")
    print("  （券绑定具体产品、无显式金额，实际优惠以 calculate-price 为准）")

    # (e) calculate-price 官方验算：金额单位为分，已转元
    from mcsaver.menu_adapter import parse_calculate_price
    calc_path = os.path.join(SAMPLES, "calculate_price_sample.json")
    if os.path.exists(calc_path):
        with open(calc_path, encoding="utf-8") as f:
            calc = parse_calculate_price(json.load(f)["data"])
        items = " + ".join(
            f"{it['name']}{it['subtotal']} 元" for it in calc["items"])
        print("\n【calculate-price 官方验算 · 真实返回】")
        print(f"  {items} = 应付 {calc['price']} 元"
              f"（优惠 {calc['discount']} 元）")
        ways = "、".join(tw["title"] for tw in calc["takeways"])
        print(f"  取餐方式：{ways}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
