"""麦门省钱助手 — 省钱优化核心逻辑（纯函数，不依赖网络）。

输入统一为 data/sample_menu.json 结构；接入 MCP Token 后，
上游数据由 mcp_client 拉取并转换成同样结构后传入。
"""
from __future__ import annotations

import itertools
import json


def load_menu(path: str = "data/sample_menu.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def one_plus_one_best(menu: dict) -> dict:
    """1+1 随心配：在红白区各选一件，使“原价总和 - 配价”最大。"""
    pair_price = menu["pair_price"]
    best = None
    for red in menu["red_zone"]:
        for white in menu["white_zone"]:
            saving = round(red["price"] + white["price"] - pair_price, 2)
            if best is None or saving > best["saving"]:
                best = {
                    "red": red["name"],
                    "white": white["name"],
                    "orig_total": round(red["price"] + white["price"], 2),
                    "pay": pair_price,
                    "saving": saving,
                }
    return best


def compare_combo_vs_alacarte(want: list[str], menu: dict) -> dict:
    """想吃的东西清单：比较“直接买套餐” vs “全部单点”，返回更便宜的方案。"""
    price_of = {}
    for zone in ("red_zone", "white_zone", "alacarte"):
        for it in menu.get(zone, []):
            price_of[it["name"]] = it["price"]
    alacarte_total = round(sum(price_of.get(n, 0) for n in want), 2)

    combo_options = []
    for combo in menu.get("combos", []):
        if all(n in want for n in combo["items"]):
            combo_options.append({"name": combo["name"], "pay": combo["price"]})
    best_combo = min(combo_options, key=lambda c: c["pay"]) if combo_options else None

    if best_combo and best_combo["pay"] < alacarte_total:
        return {"choice": "combo", "plan": best_combo["name"],
                "pay": best_combo["pay"], "vs_alacarte": alacarte_total,
                "saving": round(alacarte_total - best_combo["pay"], 2)}
    return {"choice": "alacarte", "plan": "全部单点",
            "pay": alacarte_total, "vs_alacarte": alacarte_total, "saving": 0.0}


def best_coupon(subtotal: float, coupons: list[dict]) -> dict:
    """从优惠券里选最优组合：先试可叠加券全叠，再与最优单张不可叠加券比。"""
    usable = [c for c in coupons if subtotal >= c["threshold"]]
    if not usable:
        return {"coupons": [], "discount": 0.0, "pay": round(subtotal, 2)}

    stackable = [c for c in usable if c.get("stackable")]
    best = {"coupons": [], "discount": 0.0}
    # 穷举可叠加券子集（数量很少，暴力即可）
    for r in range(1, len(stackable) + 1):
        for combo in itertools.combinations(stackable, r):
            d = round(sum(c["discount"] for c in combo), 2)
            if d > best["discount"]:
                best = {"coupons": [c["name"] for c in combo], "discount": d}
    # 不可叠加券只能单用，取最大的一张
    for c in usable:
        if not c.get("stackable") and c["discount"] > best["discount"]:
            best = {"coupons": [c["name"]], "discount": round(c["discount"], 2)}
    best["pay"] = round(max(subtotal - best["discount"], 0), 2)
    return best


def addon_to_threshold(subtotal: float, menu: dict) -> dict | None:
    """拼单凑满减：找最便宜的加购，让“多花的钱 < 多省的钱”。"""
    items = []
    for zone in ("red_zone", "white_zone", "alacarte"):
        items += menu.get(zone, [])
    suggestions = []
    for th in menu.get("thresholds", []):
        if subtotal >= th["spend"]:
            continue
        need = th["spend"] - subtotal
        cheapest = min((it for it in items if it["price"] >= need),
                       key=lambda it: it["price"], default=None)
        if cheapest is None:
            continue
        net = round(th["off"] - cheapest["price"], 2)
        if net > 0:
            suggestions.append({
                "threshold": th, "add": cheapest["name"],
                "add_price": cheapest["price"], "net_saving": net,
            })
    if not suggestions:
        return None
    return max(suggestions, key=lambda s: s["net_saving"])


def plan_order(budget: float, people: int, menu: dict) -> dict:
    """一句话需求 → 省钱方案：先 1+1 凑人均，再算券。"""
    pair = one_plus_one_best(menu)
    pairs_needed = people
    subtotal = round(pair["pay"] * pairs_needed, 2)
    coupon = best_coupon(subtotal, menu["coupons"])
    addon = addon_to_threshold(coupon["pay"], menu)
    return {
        "budget": budget, "people": people,
        "pair_plan": pair, "pairs": pairs_needed,
        "subtotal": subtotal, "coupon": coupon,
        "addon_tip": addon,
        "final_pay": coupon["pay"],
        "per_person": round(coupon["pay"] / people, 2),
        "within_budget": coupon["pay"] <= budget,
    }
