# A股量化策略工具箱

目录路径：`Chinese_Stock/`

---

## 目录结构

```
Chinese_Stock/
├── my_holdings/              ← 个人持仓录入与管理
│   ├── holdings.json          ← 当前持仓（sell-monitor 自动读取）
│   ├── 20260412_holdings.json ← 日期归档
│   └── scripts/
│       └── holdings_editor.py ← 交互式持仓录入工具
│
├── my_stock_pool/            ← 自选股池
│   └── watchlist.yaml        ← 所有策略的分析范围
│
├── recommendations/           ← 融合策略推荐输出
│   ├── YYYYMMDD_EVENING_BUY_recommendation.json      ← 尾盘买推荐
│   └── YYYYMMDD_MORNING_BUY_recommendation.json       ← 早盘买推荐
│
├── sell-monitor/              ← 持仓实时监控（止盈/止损）
│   └── scripts/
│       ├── monitor.py        ← 核心监控脚本
│       └── rebalance.py      ← 调仓分析脚本
│
├── strategy-fusion-advisor/   ← 融合策略（定时生成推荐）
│   └── skills/scripts/
│       └── fusion_runner.py  ← 融合运行器
│
├── breakout-high-strategy/    ← 突破新高策略
├── gap-fill-strategy/         ← 缺口填充策略
├── ma-bullish-strategy/       ← 均线多头策略
├── macd-divergence-strategy/  ← MACD底背离策略
├── morning-star-strategy/      ← 早晨之星策略
├── rsi-oversold-strategy/    ← RSI超卖策略
├── volume-extreme-strategy/   ← 地量见底策略
├── volume-retrace-ma-strategy/← 缩量回踩均线策略
├── earnings-surprise-strategy/← 业绩超预期策略
├── limit-up-retrace-strategy/← 涨停回踩策略
├── limit-up-analysis/        ← 涨停分析（打板）
└── strategy-optimizer/         ← 策略参数优化
```

---

## 快速开始

### 1. 录入持仓

```bash
python3 my_holdings/scripts/holdings_editor.py
```

### 2. 查看推荐（自动生成）

- **14:30 尾盘买**：`strategy-fusion-advisor/skills/scripts/fusion_runner.py --session EVENING`
- **16:00 早盘买**： `--session MORNING`

结果写入 `recommendations/` 目录。

### 3. 监控持仓

```bash
python3 sell-monitor/scripts/monitor.py              # 监控持仓
python3 sell-monitor/scripts/rebalance.py            # 调仓分析
```

---

## 工作流程

```
每日 14:30                    每日 16:00
     │                            │
     ▼                            ▼
融合策略(尾盘组)          融合策略(早盘组)
     │                            │
     ▼                            ▼
recommendations/           recommendations/
EVENING_BUY.json          MORNING_BUY.json
     │                            │
     │◄─────── sell-monitor ──────►│
     │                            │
     ▼                            ▼
持仓监控 + 调仓分析      持仓监控 + 调仓分析
```

---

## buy_reason 策略类型

| buy_reason | 含义 | 止损 |
|-----------|------|-----|
| `limit_up` | 涨停连板 | -7% |
| `breakout_high` | 突破新高 | -7% |
| `gap_fill` | 缺口填充 | -5% |
| `ma_bullish` | 均线多头 | -5% |
| `macd_divergence` | MACD底背离 | -3% |
| `rsi_oversold` | RSI超卖 | -3% |
| `morning_star` | 早晨之星 | -3% |
| `volume_extreme` | 地量见底 | -3% |
| `a_stock_1430` | 尾盘超短 | -2% |

---

## 自选股池板块

由 `my_stock_pool/watchlist.yaml` 定义，共 23 个板块，覆盖：
AI算力、光通信、半导体设备、机器人、新能源、医药、贵金属、航天等热门赛道。

---

## 数据文件说明

| 文件位置 | 用途 |
|---------|------|
| `my_holdings/holdings.json` | 当前持仓 |
| `my_holdings/YYYYMMDD_holdings.json` | 持仓归档 |
| `recommendations/YYYYMMDD_*_recommendation.json` | 融合策略推荐 |
| `my_stock_pool/watchlist.yaml` | 自选股池 |

---

## 免责声明

本工具箱仅供参考学习，不构成投资建议。股市有风险，投资需谨慎。
