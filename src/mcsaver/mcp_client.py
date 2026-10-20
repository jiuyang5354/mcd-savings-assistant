"""麦当劳中国 MCP Server 调用封装。

认证：Authorization: Bearer <TOKEN>，Token 从环境变量 MCD_MCP_TOKEN 读取，
绝不在代码或配置文件里写明文 Token（参赛声明要求）。
协议：Streamable HTTP JSON-RPC，endpoint https://mcp.mcd.cn。
工具清单以官方仓库 M-China/mcd-mcp-server 为准。
"""
from __future__ import annotations

import json
import os
import urllib.request

ENDPOINT = "https://mcp.mcd.cn"

# 场景常量（来自官方 inputSchema 字段说明）
ORDER_TYPE_IN_STORE = 1      # 到店（含到店自取 + 得来速）
BE_TYPE_PICKUP = 1           # 到店取餐
BE_TYPE_DRIVE_THRU = 5       # 得来速车道取餐


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

    def query_meal_detail(self, store_code: str, code: str,
                          order_type: int = ORDER_TYPE_IN_STORE,
                          be_type: int = BE_TYPE_PICKUP,
                          be_code: str | None = None) -> dict:
        """按餐品编码查详情、套餐组成与可替换项。

        inputSchema：code + 门店场景参数 storeCode / orderType / beType；
        到店自取（beType=1）时 beCode 是无效参数，传了会报错；得来速（beType=5）必传 beCode。
        """
        args = {"code": str(code), "storeCode": str(store_code),
                "orderType": int(order_type), "beType": int(be_type)}
        if be_code and be_type != BE_TYPE_PICKUP:
            args["beCode"] = be_code
        return self.call("query-meal-detail", args)

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
    def query_nearby_stores(self, city: str, keyword: str,
                            be_type: int = BE_TYPE_PICKUP) -> dict:
        """按「城市 + 关键词」查门店（拿 storeCode）。

        inputSchema：searchType=2（按位置搜）时 city 与 keyword 必须同传，
        只传其一会报 600058；不接受整段地址字符串。
        关键词可以是商圈、地标、车站，例如 city="杭州市", keyword="西湖文化广场"。
        """
        return self.call("query-nearby-stores", {
            "searchType": 2, "beType": int(be_type),
            "city": city, "keyword": keyword})

    def list_nutrition_foods(self) -> dict:
        """餐品营养成分（能量、蛋白质、脂肪等），可做低热量搭配。"""
        return self.call("list-nutrition-foods")

    def now_time_info(self) -> dict:
        """服务器当前时间（判断早餐/午市时段）。"""
        return self.call("now-time-info")
