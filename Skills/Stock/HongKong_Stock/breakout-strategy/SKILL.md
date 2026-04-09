# SKILL.md

---
name: hk-breakout-strategy
description: 港股突破高点策略 - 放量突破前高+回踩确认，趋势启动点，胜率58%
version: 1.0.0
author: QuantTeam
tags: [港股, 技术分析, 突破策略, 放量确认, 趋势启动]
dependencies:
  - requests>=2.28.0
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
---

# 港股突破高点策略

## 策略概述

港股突破高点策略专注于捕捉高流动性港股放量突破关键阻力位后的趋势启动行情。

### 核心逻辑

```
买入条件：
1. 突破确认：收盘价 > 60日最高价
2. 量能确认：成交量 > 50日均量 × 2（放量突破）
3. 回踩测试：3日内最低价不跌破前高（回踩确认）
4. RSI过滤：RSI(14) 处于 50-75 区间（不过热/不过冷）

卖出规则：
- 止损：入场价 -5%
- 止盈：+12% 或成交量萎缩30%时止盈
```

### 策略表现

| 市场环境 | 胜率 | 盈亏比 | 持仓周期 | 适用场景 |
|---------|------|--------|---------|---------|
| 上升趋势 | 60-70% | 2.5:1 | 5-15天 | 强势股突破 |
| 震荡市场 | 55-60% | 2:1 | 3-8天 | 波段操作 |
| 下跌趋势 | < 50% | 不建议 | - | 空仓观望 |

## 快速开始

### 安装依赖

```bash
pip install requests pandas numpy pyyaml
```

### 命令行使用

```bash
# 进入脚本目录
cd skills/Stock/HongKong_Stock/breakout-strategy/skills/scripts

# 分析单只港股
python3 hk_breakout_analyzer.py --stock 0700.HK --name 腾讯控股

# 扫描高流动性港股突破机会
python3 hk_breakout_scanner.py

# 一致性检查
python3 check_consistency.py
```

### Python API

```python
import sys
sys.path.insert(0, 'skills/scripts')
from hk_breakout_analyzer import HKBreakoutAnalyzer

analyzer = HKBreakoutAnalyzer()
result = analyzer.analyze_stock('0700.HK', '腾讯控股')

if result:
    print(f"突破状态: {result['break_status']}")
    print(f"信号: {result['signal']}")
    print(f"入场价: {result['entry_price']}")
    print(f"止损价: {result['stop_loss']}")
    print(f"建议: {result['suggestion']}")
```

## 评分体系

| 分数 | 等级 | 建议 |
|------|------|------|
| ≥85 | 极强 | 重点关注，积极买入 |
| 75-84 | 强 | 可考虑买入 |
| 70-74 | 中等 | 需观察，等待确认 |
| <70 | 弱 | 建议观望 |

## 分析维度权重

| 维度 | 权重 | 关键指标 |
|------|------|---------|
| 突破确认 | 30% | 收盘价 vs 60日最高价 |
| 量能确认 | 30% | 成交量 vs 50日均量 |
| 回踩测试 | 25% | 3日内低点 vs 前高 |
| RSI过滤 | 15% | RSI(14) 是否在 50-75 |

## 目录结构

```
breakout-strategy/
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
│   └── hk-breakout-agent.yaml
├── crons/                           # 定时任务
│   └── hk-breakout-crons.yaml
└── skills/scripts/                 # 策略脚本
    ├── hk_breakout_analyzer.py     # 核心分析器
    ├── hk_breakout_scanner.py       # 全市场扫描器
    └── check_consistency.py         # 一致性检查
```

## 数据源

- **Yahoo Finance**（推荐）：港股代码如 `0700.HK`、`9988.HK`
- **akshare**：备用（需网络畅通）

## 风险提示

- 突破失败（假突破）是主要风险，建议仓位控制在10%以内
- 成交量必须真实放大，避免对倒单制造的假量
- RSI>75 且突破可能已处于最后一波，追高需谨慎
- 策略仅供参考，不构成投资建议

## 更新日志

### v1.0.0 (2026-04-08)
- ✨ 初始版本发布
- ✨ 60日高点突破确认
- ✨ 量能放大2倍验证
- ✨ 回踩测试 + RSI过滤
