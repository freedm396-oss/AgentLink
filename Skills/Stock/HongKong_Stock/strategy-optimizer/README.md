# 港股策略优化器

基于 OpenClaw 开发的港股策略自动化优化工具，支持 10 种港股交易策略的参数网格搜索和评分权重调优。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 优化单个策略

```bash
python3 skills/scripts/strategy_optimizer.py --strategy ma-bullish-strategy
```

### 优化所有策略

```bash
python3 skills/scripts/strategy_optimizer.py --all
```

### 优化评分权重

```bash
python3 skills/scripts/strategy_optimizer.py --weights ma-bullish-strategy
```

## 支持的策略

| # | 策略代码 | 策略名称 | 胜率 |
|---|---------|---------|------|
| 1 | `ma-bullish-strategy` | 均线多头排列策略 | 65% |
| 2 | `breakout-strategy` | 突破高点策略 | 58% |
| 3 | `short-interest-reversal-strategy` | 沽空比率反转策略 | 70% |
| 4 | `ah-premium-arbitrage-strategy` | AH溢价套利策略 | 74% |
| 5 | `buyback-follow-strategy` | 回购公告跟进策略 | 62% |
| 6 | `placement-dip-strategy` | 配股砸盘抄底策略 | 60% |
| 7 | `dividend-exright-strategy` | 分红除权博弈策略 | 67% |
| 8 | `liquidity-filter-strategy` | 流动性过滤策略 | 风控 |
| 9 | `short-stop-loss-strategy` | 做空止损策略 | 风控 |
| 10 | `earnings-surprise-strategy` | 财报超预期策略 | 70% |
| 11 | `ma-pullback-strategy` | 均线回踩策略 | 待测 |

## 目录结构

```
strategy-optimizer/
├── SKILL.md
├── README.md
├── requirements.txt
├── demo.py
├── check_consistency.py
├── config/
│   ├── optimizer_config.yaml
│   ├── optimization_params.yaml
│   └── evaluation_config.yaml
├── agents/
│   └── hk-strategy-optimizer-agent.yaml
├── crons/
│   └── hk-strategy-optimizer-crons.yaml
├── data/
│   ├── backtest_results/
│   ├── optimized_params/
│   ├── predictions/
│   └── logs/
└── skills/scripts/
    ├── strategy_optimizer.py
    ├── param_optimizer.py
    ├── performance_analyzer.py
    ├── model_updater.py
    └── check_consistency.py
```

## 版本历史

### v1.0.0 (2026-04-08)
- 初始版本发布
- 支持 10 种港股策略
- 集成网格搜索优化
- 支持权重优化

## 许可证

MIT License
