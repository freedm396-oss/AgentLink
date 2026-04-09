#!/usr/bin/env python3
"""
港股策略优化器 - 一致性检查
"""

import os

skill_root = os.path.dirname(os.path.abspath(__file__))


def check_consistency():
    errors = []
    warnings = []

    # 1. SKILL.md
    skill_md = os.path.join(skill_root, 'SKILL.md')
    if not os.path.exists(skill_md):
        errors.append("SKILL.md 不存在")
    else:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
        checks = [
            ("ma-bullish-strategy", "均线多头排列策略"),
            ("breakout-strategy", "突破高点策略"),
            ("short-interest-reversal-strategy", "沽空比率反转"),
            ("ah-premium-arbitrage-strategy", "AH溢价套利"),
            ("buyback-follow-strategy", "回购公告跟进"),
            ("placement-dip-strategy", "配股砸盘抄底"),
            ("dividend-exright-strategy", "分红除权博弈"),
            ("liquidity-filter-strategy", "流动性过滤"),
            ("short-stop-loss-strategy", "做空止损"),
            ("ma-pullback-strategy", "均线回踩"),
        ]
        for check, name in checks:
            if check not in content:
                warnings.append(f"SKILL.md 中未找到策略: {name}")

    # 2. 配置文件
    config_dir = os.path.join(skill_root, 'config')
    for cfg in ['optimizer_config.yaml', 'optimization_params.yaml', 'evaluation_config.yaml']:
        if not os.path.exists(os.path.join(config_dir, cfg)):
            errors.append(f"配置文件缺失: {cfg}")

    # 3. 脚本
    scripts_dir = os.path.join(skill_root, 'skills', 'scripts')
    for script in ['strategy_optimizer.py', 'param_optimizer.py',
                   'performance_analyzer.py', 'model_updater.py']:
        if not os.path.exists(os.path.join(scripts_dir, script)):
            errors.append(f"脚本缺失: {script}")

    return errors, warnings


def main():
    print("=" * 50)
    print("港股策略优化器 - 一致性检查")
    print("=" * 50)
    print(f"检查目录: {skill_root}\n")

    errors, warnings = check_consistency()

    if errors:
        print("❌ 错误:")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\n⚠️ 警告:")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("✅ 所有检查通过")

    print()


if __name__ == "__main__":
    main()
