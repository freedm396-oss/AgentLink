# SKILL.md

---
name: hk-short-stop-loss-strategy
description: 港股做空止损策略 - 所有多头仓位的前置风控核心，-7%无条件离场，多重保险机制
version: 1.0.0
author: QuantTeam
tags: [港股, 止损, 风险管理, 风控核心, 仓位管理]
dependencies:
  - requests>=2.28.0
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
---

# 港股做空止损策略

## 策略概述

做空止损策略是**所有多头持仓的风控核心**，在任何持仓期间严格执行止损纪律，避免亏损无限扩大。

### 核心逻辑

```
止损规则（三层防线）：

第1层 - 硬止损（无条件执行）：
  亏损超过 7% → 立即市价卖出，不犹豫

第2层 - 单日止损（减仓保护）：
  单日亏损超过 3% → 减仓50%，降低风险敞口

第3层 - 周度止损（强制冷却）：
  周亏损超过 10% → 清仓所有持仓

冷却期规则：
  止损触发后，禁止开新仓 3个交易日（冷静期）

持仓期限：
  最大持仓 20个交易日，到期强制平仓
```

### 风控分级

| 亏损区间 | 触发条件 | 动作 |
|---------|---------|------|
| **硬止损** | 亏损 ≥ 7% | 立即市价卖出 |
| **减仓** | 单日亏损 ≥ 3% | 减仓 50% |
| **周止损** | 周亏损 ≥ 10% | 清仓所有持仓 |
| **到期强制** | 持仓 ≥ 20日 | 强制平仓 |

## 为什么需要止损策略？

- **港股波动大**：恒指单日涨跌 2-3% 常见
- **防止套牢**：下跌50%需要上涨100%才能回本
- **保护本金**：亏损20%需要25%盈利才能弥补
- **执行纪律**：情绪化交易是亏损的主要原因

## 快速开始

### 安装依赖

```bash
pip install requests pandas numpy pyyaml
```

### 命令行使用

```bash
# 进入脚本目录
cd skills/Stock/HongKong_Stock/short-stop-loss-strategy/skills/scripts

# 检查持仓止损状态
python3 hk_stop_loss_checker.py --stock 0700.HK --entry 480.0 --current 450.0

# 批量扫描所有持仓
python3 hk_stop_loss_scanner.py

# 一致性检查
python3 check_consistency.py
```

### Python API

```python
import sys
sys.path.insert(0, 'skills/scripts')
from hk_stop_loss_analyzer import HKStopLossAnalyzer

analyzer = HKStopLossAnalyzer()
result = analyzer.check_position('0700.HK', entry_price=480.0, current_price=450.0,
                                holding_days=5, daily_pnl=-0.04, weekly_pnl=-0.06)

if result['action'] == 'SELL':
    print(f"⚠️ 止损信号: {result['action']} | {result['reason']}")
else:
    print(f"✅ 持仓安全: {result['remaining_pct']}%")
```

## 目录结构

```
short-stop-loss-strategy/
├── SKILL.md                        # 本文件
├── README.md                        # 策略说明文档
├── requirements.txt                 # Python依赖
├── demo.py                          # 演示脚本
├── check_consistency.py             # 一致性检查
├── config/                          # 配置文件
│   ├── strategy_config.yaml        # 策略参数
│   ├── scoring_weights.yaml         # 评分权重
│   └── risk_rules.yaml              # 风险规则
├── agents/                          # Agent配置
│   └── hk-stop-loss-agent.yaml
├── crons/                           # 定时任务
│   └── hk-stop-loss-crons.yaml
└── skills/scripts/                 # 策略脚本
    ├── hk_stop_loss_analyzer.py        # 核心分析器
    ├── hk_stop_loss_checker.py         # 单持仓检查
    ├── hk_stop_loss_scanner.py          # 批量扫描
    └── check_consistency.py             # 一致性检查
```

## 风险提示

- 止损执行必须坚决，不存在"等反弹再卖"的侥幸心理
- 冷却期（3日）是强制性的，即使看好市场也禁止开新仓
- 周度止损以周五收盘价为基准
- 本策略为风控工具，不构成交易建议

## 更新日志

### v1.0.0 (2026-04-08)
- ✨ 初始版本发布
- ✨ 三层止损体系（7%硬止损/3%减仓/10%周止损）
- ✨ 20日最大持仓期限
- ✨ 止损后3日冷却期机制
- ✨ 适用所有港股多头仓位的前置风控
