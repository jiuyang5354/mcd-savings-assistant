[中文](README.md) | **English**

# McDonald's Savings Assistant

A project entered in the McDonald's Programmer's Day creative development competition. Enter a budget, party size, and dietary exclusions to compare ordering plans, meal combinations, and coupons.

## Features

- Whole-order planning: combine 1+1 deals, coupons, and additional-item suggestions within a budget.
- Compare one item from each 1+1 selection group to find the largest saving.
- Compare meals against ordering the same items individually.
- Enumerate stackable coupon combinations and compare non-stackable discounts.
- Suggest threshold-discount add-ons only when the extra spending is smaller than the extra saving.

## Install

```sh
git clone https://github.com/jiuyang5354/mcd-savings-assistant.git
cd mcd-savings-assistant
python3 -c "import sys; assert sys.version_info >= (3,9)"
```

Uses only the Python standard library; no third-party dependencies.

## Usage

Run a demo with sample menu data and no token:

```sh
python3 examples/demo.py
```

For live data, sign in at https://open.mcd.cn and apply for an MCP token:

```sh
export MCD_MCP_TOKEN=your_token
python3 - <<'PY'
import sys
sys.path.insert(0, "src")
from mcsaver import McdMcp
mcp = McdMcp()
print(mcp.query_nearby_stores("杭州市", "西湖文化广场"))
PY
```

The token is read from the environment.

## Intended users

People comparing affordable McDonald's orders, organizing shared orders in dorms or offices, or combining available coupons and 1+1 offers.

## Competition and data

The competition registration and ranking period documented by this project was October 9, 2026, 10:30 through October 25, 2026, 23:59. `CONTEST_DECLARATION.md` preserves the official declaration verbatim.

Prices, coupons, and promotions are determined by the live McDonald's MCP API. `data/sample_menu.json` contains demonstration data.
