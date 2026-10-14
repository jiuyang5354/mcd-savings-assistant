# 麦门省钱助手 🍔

麦当劳程序员节创意开发大赛参赛作品。输入预算、人数、忌口，输出最优点单方案——怎么点最省，一算便知。

## 功能

- **整单方案**：预算 + 人数 → 1+1 凑人均 + 最优券 + 凑单提示，一张结论卡讲清
- **1+1 随心配最优解**：红白区各选一件，算出省得最多的组合
- **套餐 vs 单点**：想吃的东西清单，直接比出哪种买法便宜
- **优惠券叠加**：可叠加券穷举 + 不可叠加券取最大，算出立减最多的用券方案
- **拼单凑满减**：只推荐“多花的钱 < 多省的钱”的加购，不为了凑单而凑单

## 安装

```bash
git clone https://github.com/jiuyang5354/mcd-savings-assistant.git
cd mcd-savings-assistant
python3 -c "import sys; assert sys.version_info >= (3,9)"
```

零第三方依赖（只用 Python 标准库）。

## 使用

```bash
# 无 Token 演示（示例菜单数据）
python3 examples/demo.py

# 接入真实数据（需先去 https://open.mcd.cn 手机号登录申请 MCP Token）
export MCD_MCP_TOKEN=你的Token
python3 - <<'EOF'
import sys; sys.path.insert(0, "src")
from mcsaver import McdMcp
mcp = McdMcp()  # 从环境变量读 Token
print(mcp.query_nearby_stores("杭州市西湖区"))
EOF
```

## 目标用户

- 每次点麦当劳都要纠结“怎么点最划算”的普通用户
- 宿舍 / 办公室拼单的凑单发起人
- 麦门信徒：优惠券叠满、1+1 吃到爽

## 参赛说明

本项目参加麦当劳程序员节创意开发大赛（报名及排名：2026-10-09 10:30 至 2026-10-25 23:59）。
`CONTEST_DECLARATION.md` 为官方文件原文，未做任何修改。
价格、券与活动以麦当劳 MCP 实时接口为准；`data/sample_menu.json` 为演示用示例数据。
