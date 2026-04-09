# SKILL.md

---
name: hk-liquidity-filter-strategy
description: 港股流动性过滤策略 - 所有交易的前置风控层，仅交易高流动性标的，防御流动性陷阱
version: 1.0.0
author: QuantTeam
tags: [港股, 流动性, 风险管理, 风控层, 仙股过滤]
dependencies:
  - requests>=2.28.0
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
---

# 港股流动性过滤策略

## 策略概述

流动性过滤策略是**所有交易的前置风控层**，在任何策略开仓前必须通过流动性验证，避免陷入仙股/老千股的流动性陷阱。

### 核心逻辑

```
过滤条件（全部满足才允许交易）：
1. 日均成交额：20日均值 > 2000万港元
2. 换手率：> 0.5%（市场认可度）
3. 买卖价差：< 0.2%（价差成本低）
4. 市值：> 50亿港元（避免仙股）

动作：
- 全部满足 → 允许交易（ALLOW）
- 任一不满足 → 自动拒绝（REJECT），打印仙股警告
```

### 适用场景

| 场景 | 说明 |
|------|------|
| 单独使用 | 作为选股前置过滤器 |
| 组合使用 | 叠加在任何交易策略前，作为风控门神 |
| 批量扫描 | 每日盘前扫描全市场流动性 |

## 为什么要做流动性过滤？

港股市场特点：
- **仙股陷阱**：大量股价 < 1港元的仙股，日成交极低
- **老千股**：庄家操控股价，流动性极差
- **壳股**：市值虽大但实际流通量极低
- **买卖价差大**：低流动性股买卖价差可达 1-5%，交易成本极高

流动性过滤是**防御性策略**，不追求进攻，而是**避免踩雷**。

## 快速开始

### 安装依赖

```bash
pip install requests pandas numpy pyyaml
```

### 命令行使用

```bash
# 进入脚本目录
cd skills/Stock/HongKong_Stock/liquidity-filter-strategy/skills/scripts

# 检查单只港股流动性
python3 hk_liquidity_analyzer.py --stock 0700.HK --name 腾讯控股

# 批量扫描多只港股流动性
python3 hk_liquidity_scanner.py

# 一致性检查
python3 check_consistency.py
```

### Python API

```python
import sys
sys.path.insert(0, 'skills/scripts')
from hk_liquidity_analyzer import HKLiquidityAnalyzer

analyzer = HKLiquidityAnalyzer()
result = analyzer.check_stock('0700.HK', '腾讯控股')

if result['allowed']:
    print(f"允许交易: {result['symbol']}")
else:
    print(f"拒绝交易: {result['symbol']} | 原因: {result['reject_reasons']}")
```

## 目录结构

```
liquidity-filter-strategy/
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
│   └── hk-liquidity-agent.yaml
├── crons/                           # 定时任务
│   └── hk-liquidity-crons.yaml
└── skills/scripts/                 # 策略脚本
    ├── hk_liquidity_analyzer.py     # 核心分析器
    ├── hk_liquidity_scanner.py      # 批量扫描器
    └── check_consistency.py           # 一致性检查
```

## 数据源

- **Yahoo Finance**：实时行情、成交量
- **港交所披露易**：市值数据
- **AKShare / Choice**：备用

## 风险提示

- 流动性指标是动态的，盘前满足条件不代表盘中也满足
- 极端市场环境下（如股灾），即使高流动性股也可能丧失流动性
- 建议结合市值、股价等基本面指标综合判断
- 本策略为风控工具，不构成交易建议

## 更新日志

### v1.0.0 (2026-04-08)
- ✨ 初始版本发布
- ✨ 4维流动性验证（成交额/换手率/价差/市值）
- ✨ 仙股自动拒绝机制
- ✨ 可作为所有策略的前置风控层
