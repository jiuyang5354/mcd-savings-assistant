"""麦当劳中国 MCP Server 调用封装。

认证：Authorization: Bearer <TOKEN>，Token 从环境变量 MCD_MCP_TOKEN 读取，
绝不在代码或配置文件里写明文 Token（参赛声明要求）。
协议：Streamable HTTP JSON-RPC，endpoint https://mcp.mcd.cn/mcp。
工具清单以官方仓库 M-China/mcd-mcp-server 为准。
"""
from __future__ import annotations

import json
import os
import urllib.request

ENDPOINT = "https://mcp.mcd.cn/mcp"


class McpError(RuntimeError):
    pass


class McdMcp:
    def __init__(self, token: str | None = None,
                 endpoint: str = ENDPOINT, timeout: int = 30):
        self.token = token or os.environ.get("MCD_MCP_TOKEN", "")
        if not self.token:
            raise McpError(
                "缺少 MCP Token：请先去 https://open.mcd.cn 用手机号登录申请，"
                "然后 export MCD_MCP_TOKEN=你的Token 再运行。"
            )
        self.endpoint = endpoint
        self.timeout = timeout
        self._req_id = 0

    # ---- 底层 ----
    def call(self, tool: str, arguments: dict | None = None) -> dict:
        self._req_id += 1
        payload = json.dumps({
            "jsonrpc": "2.0", "id": self._req_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments or {}},
        }).encode()
        req = urllib.request.Request(
            self.endpoint, data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.token}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:  # 网络/鉴权失败时给人类可读提示
            raise McpError(f"调用 {tool} 失败：{e}") from e

    # ---- 菜单与价格 ----
    def query_meals(self, store_code: str) -> dict:
        """查询门店可售餐品列表（分类、餐品编码、标签）。"""
        return self.call("query-meals", {"storeCode": store_code})

    def query_meal_detail(self, product_code: str) -> dict:
        """按餐品编码查详情、套餐组成与可替换项。"""
        return self.call("query-meal-detail", {"productCode": product_code})

    def calculate_price(self, store_code: str, be_code: str,
                        address_id: str, items: list[dict]) -> dict:
        """按商品列表（含优惠券）计算金额、优惠与应付总价。"""
        return self.call("calculate-price", {
            "storeCode": store_code, "beCode": be_code,
            "addressId": address_id, "items": items})

    # ---- 优惠券与活动 ----
    def available_coupons(self) -> dict:
        """查询可领取的麦麦省优惠券列表。"""
        return self.call("available-coupons")

    def auto_bind_coupons(self) -> dict:
        """一键领取所有可用优惠券。"""
        return self.call("auto-bind-coupons")

    def my_coupons(self) -> dict:
        """查询卡包中已领取的优惠券。"""
        return self.call("my-coupons")

    def query_store_coupons(self) -> dict:
        """查询当前门店可用优惠券。"""
        return self.call("query-store-coupons")

    def campaign_calendar(self, date: str | None = None) -> dict:
        """查询当月营销活动日历；date 格式 yyyy-MM-dd，不传查当月。"""
        args = {"specifiedDate": date} if date else {}
        # 官方实现中该工具名为 campaign-calendar，老版本拼写 campaign-calender
        try:
            return self.call("campaign-calendar", args)
        except McpError:
            return self.call("campaign-calender", args)

    # ---- 门店与营养 ----
    def query_nearby_stores(self, address: str) -> dict:
        """按地址查附近麦当劳门店（拿 storeCode）。"""
        return self.call("query-nearby-stores", {"address": address})

    def list_nutrition_foods(self) -> dict:
        """餐品营养成分（能量、蛋白质、脂肪等），可做低热量搭配。"""
        return self.call("list-nutrition-foods")

    def now_time_info(self) -> dict:
        """服务器当前时间（判断早餐/午市时段）。"""
        return self.call("now-time-info")
