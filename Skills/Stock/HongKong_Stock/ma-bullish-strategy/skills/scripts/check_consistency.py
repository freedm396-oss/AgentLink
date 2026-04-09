#!/usr/bin/env python3
"""
一致性检查脚本
"""

import os
import sys

# 切换到脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))


def check_consistency():
    """检查 skill 文件结构一致性"""
    errors = []
    warnings = []

    # 1. 检查 SKILL.md
    skill_md = os.path.join(skill_root, 'SKILL.md')
    if not os.path.exists(skill_md):
        errors.append("SKILL.md 不存在")

    # 2. 检查配置文件
    config_dir = os.path.join(skill_root, 'config')
    required_configs = ['strategy_config.yaml', 'scoring_weights.yaml', 'risk_rules.yaml']
    for cfg in required_configs:
        cfg_path = os.path.join(config_dir, cfg)
        if not os.path.exists(cfg_path):
            errors.append(f"配置文件缺失: {cfg}")

    # 3. 检查脚本
    scripts_dir = os.path.join(skill_root, 'skills', 'scripts')
    required_scripts = ['hk_ma_bullish_analyzer.py', 'hk_ma_bullish_scanner.py']
    for script in required_scripts:
        script_path = os.path.join(scripts_dir, script)
        if not os.path.exists(script_path):
            errors.append(f"脚本缺失: {script}")

    # 4. 检查 agents 和 crons
    if not os.path.exists(os.path.join(skill_root, 'agents')):
        warnings.append("agents/ 目录不存在")
    if not os.path.exists(os.path.join(skill_root, 'crons')):
        warnings.append("crons/ 目录不存在")

    # 5. 关键参数一致性
    if os.path.exists(skill_md):
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ("MA5 > MA10 > MA20 > MA60", "均线排列条件"),
            ("5%", "发散度阈值"),
            ("6%", "止损阈值"),
            ("20%", "止盈阈值"),
        ]
        for check, name in checks:
            if check not in content:
                warnings.append(f"SKILL.md 中未找到 {name} ({check})")

    return errors, warnings


def main():
    print("=" * 50)
    print("港股均线多头排列策略 - 一致性检查")
    print("=" * 50)

    errors, warnings = check_consistency()

    if errors:
        print("\n❌ 错误:")
        for e in errors:
            print(f"  - {e}")

    if warnings:
        print("\n⚠️ 警告:")
        for w in warnings:
            print(f"  - {w}")

    if not errors and not warnings:
        print("\n✅ 所有检查通过")

    print()


if __name__ == "__main__":
    main()
