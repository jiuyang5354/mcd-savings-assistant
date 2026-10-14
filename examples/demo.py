"""演示：用示例菜单跑一遍省钱方案（无需 MCP Token）。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcsaver import (addon_to_threshold, best_coupon, compare_combo_vs_alacarte,
load_menu, one_plus_one_best, plan_order)

menu = load_menu("data/sample_menu.json")

print("")
p = one_plus_one_best(menu)
print(f" {p['red']} + {p['white']} = {p['pay']} 元（原价 {p['orig_total']}，省 {p['saving']}）")

print("\n想吃：巨无霸、中薯条、中可乐")
c = compare_combo_vs_alacarte(["巨无霸", "中薯条", "中可乐"], menu)
print(f" 选{ c['choice']}：{c['plan']}，实付 {c['pay']} 元（比单点省 {c['saving']}）")

print("\n")
plan = plan_order(budget=60, people=3, menu=menu)
print(f" {plan['pairs']} 份 1+1（{p['red']}+{p['white']}），小计 {plan['subtotal']} 元")
print(f" 用券：{plan['coupon']['coupons'] or '无可用券'}，券后 {plan['coupon']['pay']} 元")
if plan["addon_tip"]:
    a = plan["addon_tip"]
    print(f" 凑单提示：加一份{a['add']}（{a['add_price']} 元）凑满 {a['threshold']['spend']}，"
          f"净多省 {a['net_saving']} 元")
print(f" 人均 {plan['per_person']} 元，{'在预算内 ✅' if plan['within_budget'] else '超预算 ❌'}")

print("\n小计 55 元")
b = best_coupon(55, menu["coupons"])
print(f" 用券 {b['coupons']}，立减 {b['discount']}，实付 {b['pay']} 元")
