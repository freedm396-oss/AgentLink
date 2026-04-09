# skills/scripts/score_calculator.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
评分计算器 - 计算股票综合得分
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class ScoreCalculator:
    """股票综合得分计算器"""
    
    def __init__(self, config: Dict, strategy_weights: Dict):
        self.config = config
        self.strategy_weights = strategy_weights
        
        self.strategy_score_weight = config['fusion']['scoring']['strategy_score_weight']
        self.win_rate_weight = config['fusion']['scoring']['win_rate_weight']
        self.min_score = config['fusion']['scoring']['min_combined_score']
        
    def calculate_scores(self, recommendations: List[Dict]) -> List[Dict]:
        """计算所有股票的综合得分"""
        # 按股票聚合
        stock_scores = defaultdict(lambda: {
            'total_score': 0,
            'total_weight': 0,
            'strategies': [],
            'strategy_scores': [],
            'win_rates': [],
            'prices': [],
            'expected_returns': []
        })
        
        for rec in recommendations:
            stock_code = rec['stock_code']
            stock_name = rec['stock_name']
            
            # 获取策略权重
            strategy_name = rec['strategy_name']
            strategy_weight = self._get_strategy_weight(strategy_name)
            win_rate = rec.get('strategy_win_rate', 0.5)
            strategy_score = rec.get('strategy_score', 70)
            
            # 计算贡献得分
            contribution = self._calculate_contribution(
                strategy_score, win_rate, strategy_weight
            )
            
            stock_scores[stock_code]['total_score'] += contribution
            stock_scores[stock_code]['total_weight'] += strategy_weight
            stock_scores[stock_code]['strategies'].append(rec['strategy_display'])
            stock_scores[stock_code]['strategy_scores'].append(strategy_score)
            stock_scores[stock_code]['win_rates'].append(win_rate)
            stock_scores[stock_code]['prices'].append(rec.get('current_price', 0))
            stock_scores[stock_code]['expected_returns'].append(rec.get('expected_return', 10))
            stock_scores[stock_code]['stock_name'] = stock_name
            
            # 存储原始推荐信息
            if 'recommendations' not in stock_scores[stock_code]:
                stock_scores[stock_code]['recommendations'] = []
            stock_scores[stock_code]['recommendations'].append(rec)
        
        # 计算最终得分和排名
        scored_stocks = []
        
        for stock_code, data in stock_scores.items():
            # 综合得分
            combined_score = data['total_score']
            
            # 平均策略内评分
            avg_strategy_score = np.mean(data['strategy_scores'])
            
            # 平均胜率
            avg_win_rate = np.mean(data['win_rates'])
            
            # 推荐策略数量
            strategy_count = len(data['strategies'])
            
            # 平均价格
            avg_price = np.mean(data['prices']) if data['prices'] else 0
            
            # 预期收益
            expected_return = np.mean(data['expected_returns']) / 100
            
            # 风险评分（推荐策略越多，风险越低）
            risk_score = min(100, 100 - strategy_count * 5 + 30)
            
            # 一致性评分（多个策略推荐同一股票）
            consistency_score = min(100, strategy_count * 20)
            
            if combined_score >= self.min_score:
                scored_stocks.append({
                    'stock_code': stock_code,
                    'stock_name': data['stock_name'],
                    'combined_score': round(combined_score, 2),
                    'avg_strategy_score': round(avg_strategy_score, 2),
                    'avg_win_rate': round(avg_win_rate * 100, 1),
                    'strategy_count': strategy_count,
                    'strategies': data['strategies'],
                    'current_price': round(avg_price, 2),
                    'expected_return': expected_return,
                    'risk_score': risk_score,
                    'consistency_score': consistency_score,
                    'recommendations': data['recommendations']
                })
        
        # 按综合得分排序
        scored_stocks.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return scored_stocks
    
    def _get_strategy_weight(self, strategy_name: str) -> float:
        """获取策略权重"""
        fixed_weights = self.strategy_weights.get('fixed_weights', {})
        return fixed_weights.get(strategy_name, 1.0)
    
    def _calculate_contribution(self, strategy_score: float, 
                                win_rate: float, 
                                strategy_weight: float) -> float:
        """计算单次推荐的贡献得分"""
        # 归一化策略内评分（0-100 -> 0-1）
        normalized_score = strategy_score / 100
        
        # 计算贡献
        contribution = (
            normalized_score * self.strategy_score_weight +
            win_rate * self.win_rate_weight
        ) * strategy_weight * 100
        
        return contribution
    
    def get_top_stocks(self, scored_stocks: List[Dict], top_n: int = 20) -> List[Dict]:
        """获取Top N股票"""
        return scored_stocks[:top_n]