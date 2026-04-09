#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股策略融合投资顾问 - 主模块
融合10个港股策略的推荐结果，输出最优投资组合
"""

import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_ROOT = os.path.dirname(SKILLS_DIR)

sys.path.insert(0, SCRIPT_DIR)

from strategy_collector import HKStrategyCollector
from score_calculator import HKScoreCalculator
from portfolio_optimizer import HKPortfolioOptimizer
from report_generator import HKReportGenerator


class HKStrategyFusionAdvisor:
    """港股策略融合投资顾问"""

    def __init__(self):
        self.name = "港股策略融合投资顾问"
        self.config = self._load_config()
        self.strategy_weights = self._load_strategy_weights()
        self.risk_config = self._load_risk_config()

        self.collector = HKStrategyCollector(self.config)
        self.calculator = HKScoreCalculator(self.config, self.strategy_weights)
        self.optimizer = HKPortfolioOptimizer(self.config, self.risk_config)
        self.reporter = HKReportGenerator(self.config)

        self.strategies = self.config['fusion']['strategies']

    def _load_config(self) -> Dict:
        config_path = os.path.join(SKILL_ROOT, 'config', 'fusion_config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_strategy_weights(self) -> Dict:
        weights_path = os.path.join(SKILL_ROOT, 'config', 'strategy_weights.yaml')
        with open(weights_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_risk_config(self) -> Dict:
        risk_path = os.path.join(SKILL_ROOT, 'config', 'risk_config.yaml')
        with open(risk_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_daily_recommendation(self) -> Dict:
        print(f"\n{'='*60}")
        print(f"港股策略融合投资顾问 - 每日推荐")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        # 1. 收集所有策略推荐
        print("\n[步骤1] 收集策略推荐...")
        recommendations = self.collector.collect_all_recommendations()

        if not recommendations:
            return {'error': '未获取到任何策略推荐'}

        print(f"  共收集到 {len(recommendations)} 条推荐记录")

        # 2. 计算综合得分
        print("\n[步骤2] 计算综合得分...")
        scored_stocks = self.calculator.calculate_scores(recommendations)
        print(f"  共 {len(scored_stocks)} 只股票获得推荐")

        # 3. 优化仓位
        print("\n[步骤3] 优化仓位分配...")
        portfolio = self.optimizer.optimize_portfolio(scored_stocks)
        print(f"  最终入选 {len(portfolio)} 只股票")

        # 4. 生成报告
        print("\n[步骤4] 生成投资报告...")
        report = self.reporter.generate_report(scored_stocks, portfolio, recommendations)

        # 5. 保存结果
        self._save_results(scored_stocks, portfolio, recommendations)

        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'scored_stocks': scored_stocks,
            'portfolio': portfolio,
            'report': report
        }

    def _save_results(self, scored_stocks: List, portfolio: List, recommendations: List):
        date_str = datetime.now().strftime('%Y%m%d')
        save_dir = self.config['data_storage']['recommendations']
        os.makedirs(save_dir, exist_ok=True)

        json_path = os.path.join(save_dir, f"{date_str}_recommendation.json")
        json_data = {
            'date': date_str,
            'portfolio': portfolio,
            'scored_stocks': scored_stocks[:20],
            'total_recommendations': len(recommendations)
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"  已保存: {json_path}")

        md_path = os.path.join(save_dir, f"{date_str}_report.md")
        report = self.reporter.generate_report(scored_stocks, portfolio, recommendations)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"  已保存: {md_path}")

    def print_summary(self, result: Dict):
        if 'error' in result:
            print(f"\n[ERROR] {result['error']}")
            return

        portfolio = result.get('portfolio', [])
        print(f"\n{'='*60}")
        print(f"[HK] 港股策略融合 - 每日推荐结果")
        print(f"{'='*60}")
        print(f"\nTop 5 推荐组合:")
        print(f"{'-'*60}")

        for i, stock in enumerate(portfolio, 1):
            action = stock.get('investment_advice', {}).get('action', '关注')
            print(f"  {i}. {stock['stock_name']} ({stock['stock_code']})")
            print(f"     综合得分: {stock['combined_score']:.1f} | "
                  f"仓位: {stock['position_pct']*100:.1f}% | "
                  f"策略数: {stock['strategy_count']}")
            print(f"     操作: {action}")
            print()

        total_pos = sum(s['position_pct'] for s in portfolio)
        print(f"{'='*60}")
        print(f"组合仓位: {total_pos*100:.1f}% | 现金预留: {(1-total_pos)*100:.1f}%")
        print(f"{'='*60}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股策略融合投资顾问')
    parser.add_argument('--daily', action='store_true', help='生成每日推荐')
    args = parser.parse_args()

    advisor = HKStrategyFusionAdvisor()
    result = advisor.generate_daily_recommendation()
    advisor.print_summary(result)


if __name__ == '__main__':
    main()
