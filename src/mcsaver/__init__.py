"""麦门省钱助手 skill 包。"""
from .optimizer import (addon_to_threshold, best_coupon, compare_combo_vs_alacarte,
                        load_menu, one_plus_one_best, plan_order)
from .mcp_client import McdMcp, McpError
from .menu_adapter import (find_combos, find_singles, find_suixinpei,
                           load_coupons, load_menu as load_real_menu,
                           load_samples_dir, parse_diff_price, parse_meal_detail,
                           parse_price, to_optimizer_items)

__all__ = ["addon_to_threshold", "best_coupon", "compare_combo_vs_alacarte",
           "load_menu", "one_plus_one_best", "plan_order", "McdMcp", "McpError",
           "find_combos", "find_singles", "find_suixinpei", "load_coupons",
           "load_real_menu", "load_samples_dir", "parse_diff_price",
           "parse_meal_detail", "parse_price", "to_optimizer_items"]
