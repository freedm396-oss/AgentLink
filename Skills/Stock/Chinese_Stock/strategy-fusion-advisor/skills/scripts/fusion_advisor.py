# skills/scripts/fusion_advisor.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略融合投资顾问 - 主模块
融合11个策略的推荐结果，输出最优投资组合
"""

import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy_collector import StrategyCollector
from score_calculator import ScoreCalculator
from portfolio_optimizer import PortfolioOptimizer
from report_generator import ReportGenerator


class StrategyFusionAdvisor:
    """策略融合投资顾问"""
    
    def __init__(self):
        self.name = "策略融合投资顾问"
        
        # 加载配置
        self.config = self._load_config()
        self.strategy_weights = self._load_strategy_weights()
        self.risk_config = self._load_risk_config()
        
        # 初始化子模块
        self.collector = StrategyCollector(self.config)
        self.calculator = ScoreCalculator(self.config, self.strategy_weights)
        self.optimizer = PortfolioOptimizer(self.config, self.risk_config)
        self.reporter = ReportGenerator(self.config)
        
        # 策略列表
        self.strategies = self.config['fusion']['strategies']
        
    def _load_config(self) -> Dict:
        """加载融合配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'fusion_config.yaml'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_strategy_weights(self) -> Dict:
        """加载策略权重配置"""
        weights_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'strategy_weights.yaml'
        )
        with open(weights_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_risk_config(self) -> Dict:
        """加载风险配置"""
        risk_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'risk_config.yaml'
        )
        with open(risk_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def generate_daily_recommendation(self) -> Dict:
        """生成每日投资推荐"""
        print(f"\n{'='*60}")
        print(f"策略融合投资顾问 - 每日推荐")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # 1. 收集所有策略推荐
        print("\n【步骤1】收集策略推荐...")
        recommendations = self.collector.collect_all_recommendations()
        
        if not recommendations:
            return {'error': '未获取到任何策略推荐'}
        
        print(f"  共收集到 {len(recommendations)} 条推荐记录")
        
        # 2. 计算综合得分
        print("\n【步骤2】计算综合得分...")
        scored_stocks = self.calculator.calculate_scores(recommendations)
        
        print(f"  共 {len(scored_stocks)} 只股票获得推荐")
        
        # 3. 优化投资组合
        print("\n【步骤3】优化投资组合...")
        portfolio = self.optimizer.optimize_portfolio(scored_stocks)
        
        print(f"  选出 {len(portfolio)} 只股票")
        
        # 4. 生成报告
        print("\n【步骤4】生成投资报告...")
        report = self.reporter.generate_report(
            scored_stocks, 
            portfolio,
            recommendations
        )
        
        # 5. 保存结果
        self._save_recommendation(portfolio, report)
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_recommendations': len(recommendations),
            'unique_stocks': len(scored_stocks),
            'portfolio': portfolio,
            'report': report,
            'summary': self._generate_summary(portfolio)
        }
    
    def _generate_summary(self, portfolio: List[Dict]) -> Dict:
        """生成摘要信息"""
        if not portfolio:
            return {}
        
        total_weight = sum(s['position_pct'] for s in portfolio)
        
        # 计算组合预期收益
        expected_return = sum(
            s['position_pct'] * s.get('expected_return', 0.10) 
            for s in portfolio
        ) / total_weight if total_weight > 0 else 0
        
        # 计算组合风险评分
        avg_risk_score = sum(s.get('risk_score', 50) for s in portfolio) / len(portfolio)
        
        return {
            'stock_count': len(portfolio),
            'total_position': round(total_weight * 100, 1),
            'expected_return': round(expected_return * 100, 1),
            'avg_risk_score': round(avg_risk_score, 1),
            'top_stock': portfolio[0].get('stock_name', portfolio[0].get('name', 'Unknown')) if portfolio else None,
            'top_stock_weight': portfolio[0].get('position_pct', 0) * 100 if portfolio else 0
        }
    
    def _save_recommendation(self, portfolio: List[Dict], report: str):
        """保存推荐结果"""
        save_dir = self.config['data_storage']['recommendations']
        os.makedirs(save_dir, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 保存JSON格式
        json_path = os.path.join(save_dir, f"{date_str}_recommendation.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'date': date_str,
                'portfolio': portfolio,
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # 保存Markdown报告
        md_path = os.path.join(save_dir, f"{date_str}_report.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n推荐结果已保存:")
        print(f"  JSON: {json_path}")
        print(f"  报告: {md_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='策略融合投资顾问')
    parser.add_argument('--daily', action='store_true', help='生成每日推荐')
    parser.add_argument('--save', action='store_true', help='保存结果')
    
    args = parser.parse_args()
    
    advisor = StrategyFusionAdvisor()
    
    if args.daily:
        result = advisor.generate_daily_recommendation()
        
        if 'report' in result:
            print("\n" + result['report'])
        else:
            print(f"\n生成失败: {result.get('error', '未知错误')}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()