#!/usr/bin/env python3
"""
市场反应分析模块
分析财报发布后的市场反应
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta


class MarketReactionAnalyzer:
    """市场反应分析器"""
    
    def __init__(self):
        self.name = "市场反应分析"
        self.weights = {
            'price_reaction': 0.40,
            'volume_reaction': 0.30,
            'market_comparison': 0.30
        }
    
    def analyze(self, stock_code: str, earnings_date: str, price_data: pd.DataFrame = None) -> Dict:
        """
        分析市场对财报的反应
        
        Args:
            stock_code: 股票代码
            earnings_date: 财报发布日期
            price_data: 价格数据
            
        Returns:
            分析结果
        """
        result = {
            'reaction_score': 50,
            'reaction_level': 'neutral',
            'details': {}
        }
        
        # 如果没有价格数据，返回中性评分
        if price_data is None or price_data.empty:
            return result
        
        try:
            # 找到财报发布日期后的数据
            earnings_date = pd.to_datetime(earnings_date)
            
            # 计算公告日涨跌幅
            mask = price_data.index >= earnings_date
            if not mask.any():
                return result
            
            post_earnings = price_data[mask]
            if len(post_earnings) < 2:
                return result
            
            # 公告日涨跌幅
            announcement_return = post_earnings.iloc[0]['pct_change'] if 'pct_change' in post_earnings.columns else 0
            
            # 公告后3日累计涨跌幅
            three_day_return = 0
            if len(post_earnings) >= 3:
                start_price = post_earnings.iloc[0]['close']
                end_price = post_earnings.iloc[2]['close']
                three_day_return = (end_price - start_price) / start_price * 100
            
            # 成交量变化
            volume_change = 0
            if 'volume' in post_earnings.columns and len(post_earnings) > 0:
                avg_volume_pre = price_data[~mask]['volume'].mean() if len(price_data[~mask]) > 0 else 1
                volume_post = post_earnings.iloc[0]['volume']
                volume_change = (volume_post - avg_volume_pre) / avg_volume_pre * 100
            
            # 计算市场反应得分
            price_score = min(100, max(0, 50 + announcement_return * 3 + three_day_return * 2))
            volume_score = min(100, max(0, 50 + volume_change * 0.5))
            
            # 综合得分
            total_score = (
                price_score * self.weights['price_reaction'] +
                volume_score * self.weights['volume_reaction'] +
                50 * self.weights['market_comparison']
            )
            
            # 判断反应等级
            if total_score >= 80:
                level = 'strong_positive'
            elif total_score >= 65:
                level = 'positive'
            elif total_score >= 45:
                level = 'neutral'
            elif total_score >= 30:
                level = 'negative'
            else:
                level = 'strong_negative'
            
            result['reaction_score'] = round(total_score, 2)
            result['reaction_level'] = level
            result['details'] = {
                'announcement_return': round(announcement_return, 2),
                'three_day_return': round(three_day_return, 2),
                'volume_change': round(volume_change, 2),
                'price_score': round(price_score, 2),
                'volume_score': round(volume_score, 2)
            }
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_reaction_level_name(self, level: str) -> str:
        """获取反应等级名称"""
        level_names = {
            'strong_positive': '强烈积极',
            'positive': '积极',
            'neutral': '中性',
            'negative': '消极',
            'strong_negative': '强烈消极'
        }
        return level_names.get(level, '未知')
