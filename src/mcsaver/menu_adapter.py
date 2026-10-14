"""麦门省钱助手 — 真实 MCP 数据适配层（纯解析，不发网络请求）。

把麦当劳 MCP Server 返回的原始 JSON（query-meals / query-meal-detail /
优惠券 / 门店）转换成 optimizer 可用的结构。

字段映射依据 2026-10-14 实测的真实返回，详见
MCP_INTEGRATION.md「实测字段说明」。本模块不读 Token、不做网络调用。
"""
from __future__ import annotations

import json
import logging
import os
import re

log = logging.getLogger(__name__)

# 1+1 随心配的分类名（query-meals 原样返回，含换行符）
SUIXINPEI_CATEGORY = "随心配\n1+1"

# tradeDateTime 形如 "2026-10-12 10:30:00-2026-10-16 23:59:59"
_RANGE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})-(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$"
)


def parse_price(s: str | float | int | None) -> float:
    """价格字符串转 float：'34' -> 34.0，'47.5' -> 47.5。"""
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(str(s).strip())
    except (ValueError, TypeError):
        return 0.0


def parse_diff_price(s: str | None) -> float:
    """套餐替换差价转 float：'+ ¥1.5' -> 1.5，'- ¥0.5' -> -0.5，缺失 -> 0.0。"""
    if not s:
        return 0.0
    cleaned = str(s).replace("¥", "").replace("￥", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_menu(categories_data: list, meals_data: dict) -> list[dict]:
    """合并 data.categories 与 data.meals，产出统一的菜品列表。

    每项：{code, name, category, tags, current_price, original_price,
           is_combo, is_suixinpei, image}。
    同一编码可能出现在多个分类中，取首次出现的分类；meals 字典里
    找不到的编码会被跳过并记数（如可乐中杯 3050 这类仅出现在套餐
    详情里的编码）。
    """
    code_to_cat: dict[str, dict] = {}
    for cat in categories_data or []:
        cname = cat.get("name", "")
        for ref in cat.get("meals", []) or []:
            code = str(ref.get("code", ""))
            if code and code not in code_to_cat:
                code_to_cat[code] = {
                    "category": cname,
                    "tags": list(ref.get("tags") or []),
                }

    menu: list[dict] = []
    skipped = 0
    for code, ref in code_to_cat.items():
        info = (meals_data or {}).get(code)
        if not info:
            skipped += 1
            continue
        tags: list = ref["tags"]
        category: str = ref["category"]
        menu.append({
            "code": code,
            "name": info.get("name", ""),
            "category": category,
            "tags": tags,
            "current_price": parse_price(info.get("currentPrice")),
            "original_price": parse_price(info.get("originalPrice")),
            "is_combo": ("套餐" in tags) or ("套餐" in category),
            "is_suixinpei": category == SUIXINPEI_CATEGORY,
            "discount_type": info.get("discountType"),
            "can_with_order": bool(info.get("canWithOrder", False)),
            "image": info.get("image", ""),
        })
    if skipped:
        log.warning("load_menu：%d 个编码在 meals 字典中缺失，已跳过", skipped)
    return menu


def find_suixinpei(menu: list[dict]) -> list[dict]:
    """筛出 1+1 随心配餐品。"""
    return [m for m in menu if m["is_suixinpei"]]


def find_combos(menu: list[dict]) -> list[dict]:
    """筛出套餐（tags 或分类名含“套餐”）。"""
    return [m for m in menu if m["is_combo"]]


def find_singles(menu: list[dict]) -> list[dict]:
    """筛出单品（非套餐、非随心配）。"""
    return [m for m in menu if not m["is_combo"] and not m["is_suixinpei"]]


def _split_valid_range(rng: str | None) -> tuple[str, str]:
    m = _RANGE_RE.match((rng or "").strip())
    if m:
        return m.group(1), m.group(2)
    return (rng or ""), ""


def load_coupons(coupons_data: list) -> list[dict]:
    """解析优惠券列表。

    每项：{title, coupon_id, coupon_code, valid_from, valid_to,
           product_codes}。注意券绑定具体产品，无显式优惠金额，
    实际优惠以 calculate-price 验算为准。
    """
    out: list[dict] = []
    for c in coupons_data or []:
        valid_from, valid_to = _split_valid_range(c.get("tradeDateTime"))
        out.append({
            "title": c.get("title", ""),
            "coupon_id": c.get("couponId", ""),
            "coupon_code": c.get("couponCode", ""),
            "valid_from": valid_from,
            "valid_to": valid_to,
            "product_codes": [p.get("productCode", "")
                              for p in c.get("products", []) or []],
        })
    return out


def parse_meal_detail(detail_data: dict) -> dict:
    """解析 query-meal-detail 返回。

    得到：{code, name, rounds: [{name, quantity,
             choices: [{code, name, is_default, diff_price}]}]}。
    注意详情里没有套餐基准价，基准价取自 query-meals。
    """
    rounds: list[dict] = []
    for r in detail_data.get("rounds", []) or []:
        rounds.append({
            "name": r.get("name", ""),
            "quantity": r.get("quantity", 1),
            "choices": [{
                "code": str(ch.get("code", "")),
                "name": ch.get("name", ""),
                "is_default": ch.get("isDefault") == 1,
                "diff_price": parse_diff_price(ch.get("diffPrice")),
            } for ch in r.get("choices", []) or []],
        })
    return {
        "code": str(detail_data.get("code", "")),
        "name": detail_data.get("name", ""),
        "rounds": rounds,
    }


def to_optimizer_items(menu: list[dict]) -> list[dict]:
    """转成 optimizer 风格的扁平条目。

    每项：{code, name, price（= current_price）, original_price,
           category, tags}。
    """
    return [{
        "code": m["code"],
        "name": m["name"],
        "price": m["current_price"],
        "original_price": m["original_price"],
        "category": m["category"],
        "tags": m["tags"],
    } for m in menu]


def load_samples_dir(samples_dir: str) -> tuple[list[dict], list[dict], dict]:
    """从本地采样目录读 query-meals 两部分 + 优惠券，返回 (menu, coupons, meals_data)。"""
    with open(os.path.join(samples_dir, "query_meals_part1.json"),
              encoding="utf-8") as f:
        part1 = json.load(f)
    with open(os.path.join(samples_dir, "query_meals_part2.json"),
              encoding="utf-8") as f:
        part2 = json.load(f)
    with open(os.path.join(samples_dir, "coupons_sample.json"),
              encoding="utf-8") as f:
        coupons_raw = json.load(f)

    categories = part1["data"]["categories"]
    meals_data = part2.get("meals") or part2.get("data", {}).get("meals", {})
    menu = load_menu(categories, meals_data)
    coupons = load_coupons(coupons_raw.get("data", []))
    return menu, coupons, meals_data


def parse_calculate_price(price_data: dict) -> dict:
    """解析 calculate-price 返回。

    注意：金额全部是“分”为单位的整数，这里统一转成元。
    得到：{product_original_price, product_price, original_price,
           discount, price（应付总价）,
           items: [{code, name, quantity, original_subtotal, subtotal}],
           takeways: [{code, title, subtitle}]}。
    """
    def _yuan(cents) -> float:
        try:
            return round(float(cents) / 100, 2)
        except (TypeError, ValueError):
            return 0.0

    return {
        "product_original_price": _yuan(price_data.get("productOriginalPrice")),
        "product_price": _yuan(price_data.get("productPrice")),
        "original_price": _yuan(price_data.get("originalPrice")),
        "discount": _yuan(price_data.get("discount")),
        "price": _yuan(price_data.get("price")),
        "items": [{
            "code": str(it.get("productCode", "")),
            "name": it.get("productName", ""),
            "quantity": it.get("quantity", 1),
            "original_subtotal": _yuan(it.get("originalSubtotal")),
            "subtotal": _yuan(it.get("subtotal")),
        } for it in price_data.get("productList", []) or []],
        "takeways": [{
            "code": tw.get("code", ""),
            "title": tw.get("title", ""),
            "subtitle": tw.get("subtitle", ""),
        } for tw in price_data.get("takeWayList", []) or []],
    }
