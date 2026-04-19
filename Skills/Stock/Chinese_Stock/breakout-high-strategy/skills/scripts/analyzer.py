#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
突破前期高点分析器
识别和分析股价突破前期重要高点的买入机会
"""

import os
import sys

# ── 路径设置（相对路径，基于脚本所在目录）────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../skills/scripts
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)  # .../skills
_SKILL_ROOT = os.path.dirname(_SKILL_DIR)  # .../<strategy-name>
_BASE_DIR = os.path.dirname(_SKILL_ROOT)  # .../Chinese_Stock

if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 导入数据源适配器
try:
    from skills.scripts.data_source_adapter import DataSourceAdapter
except ImportError:
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)
    from skills.scripts.data_source_adapter import DataSourceAdapter


class BreakoutHighAnalyzer:
    """突破前期高点分析器"""
    
    def __init__(self, data_source: str = "auto"):
        self.name = "突破前期高点策略"
        self.version = "v1.0.0"
        self.win_rate = 0.68
        
        # 突破参数
        self.lookback_days = 60
        self.breakout_threshold = 0.02  # 突破确认阈值 2%
        self.volume_multiplier = 1.5  # 成交量放大倍数
        
        # 评分权重
        self.weights = {
            'breakout_strength': 0.30,
            'volume_confirm': 0.25,
            'price_momentum': 0.20,
            'pattern_quality': 0.15,
            'market_environment': 0.10
        }
        
        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源")

    def find_breakout(self, df: pd.DataFrame) -> List[Dict]:
        """查找突破前期高点的信号"""
        if len(df) < 30:
            return []
        
        breakouts = []
        
        for i in range(20, len(df)):
            current = df.iloc[i]
            current_price = current['close']
            
            # 计算前60日最高价（不包括当天）
            price_window = df['close'].iloc[max(0, i-60):i]
            highest_price = price_window.max()
            
            # 检查是否突破
            if current_price > highest_price * (1 + self.breakout_threshold):
                # 计算突破强度
                breakout_ratio = (current_price - highest_price) / highest_price
                
                # 检查成交量是否放大
                vol_window = df['volume'].iloc[max(0, i-20):i]
                avg_volume = vol_window.mean()
                current_volume = current['volume']
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                
                # 计算动量
                momentum_5d = (current_price - df['close'].iloc[i-5]) / df['close'].iloc[i-5] if i >= 5 else 0
                
                breakouts.append({
                    'index': i,
                    'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                    'breakout_price': current_price,
                    'highest_price': highest_price,
                    'breakout_ratio': breakout_ratio,
                    'volume_ratio': volume_ratio,
                    'momentum_5d': momentum_5d,
                    'volume': current_volume,
                    'avg_volume': avg_volume
                })
        
        return breakouts

    def calculate_score(self, breakout: Dict, market_data: Dict = None) -> Tuple[float, str]:
        """计算评分"""
        score = 0
        reasons = []
        
        # 1. 突破强度得分 (0-30)
        ratio = breakout['breakout_ratio']
        if ratio > 0.08:
            score += 30
            reasons.append("突破力度极强(>8%)")
        elif ratio > 0.05:
            score += 25
            reasons.append("突破力度较强(>5%)")
        elif ratio > 0.03:
            score += 20
            reasons.append("突破力度良好(>3%)")
        else:
            score += 15
            reasons.append("突破力度一般")
        
        # 2. 量能确认得分 (0-25)
        vol_ratio = breakout['volume_ratio']
        if vol_ratio > 2.0:
            score += 25
            reasons.append("成交量大幅放大(>2倍)")
        elif vol_ratio > 1.5:
            score += 20
            reasons.append("成交量明显放大(>1.5倍)")
        elif vol_ratio > 1.2:
            score += 15
            reasons.append("成交量温和放大")
        else:
            score += 8
            reasons.append("成交量未明显放大")
        
        # 3. 动量得分 (0-20)
        momentum = breakout['momentum_5d']
        if momentum > 0.10:
            score += 20
            reasons.append("短期动量强劲(>10%)")
        elif momentum > 0.05:
            score += 15
            reasons.append("短期动量良好(>5%)")
        elif momentum > 0:
            score += 10
            reasons.append("短期价格上涨")
        
        # 4. 形态质量得分 (0-15)
        if ratio > 0.05 and vol_ratio > 1.5:
            score += 15
            reasons.append("突破形态标准")
        elif ratio > 0.03 and vol_ratio > 1.2:
            score += 10
            reasons.append("突破形态尚可")
        else:
            score += 5
            reasons.append("突破形态较弱")
        
        # 5. 市场环境得分 (0-10) - 基于突破时的市场数据
        market_score = self._calculate_market_environment_score(breakout, market_data)
        score += market_score['score']
        if market_score['reason']:
            reasons.append(market_score['reason'])
        
        return score, "; ".join(reasons)
    
    def _calculate_market_environment_score(self, breakout: Dict, market_data: Dict = None) -> Dict:
        """
        计算市场环境得分 (0-10分)
        基于突破时的多项市场指标综合判断
        """
        score = 0
        reason_parts = []
        
        # 指标1: 突破时的市场整体趋势 (0-4分)
        # 使用5日动量作为市场趋势代理指标
        momentum = breakout.get('momentum_5d', 0)
        if momentum > 0.08:
            score += 4
            reason_parts.append("趋势极强")
        elif momentum > 0.05:
            score += 3
            reason_parts.append("趋势强劲")
        elif momentum > 0.02:
            score += 2
            reason_parts.append("趋势向上")
        elif momentum > 0:
            score += 1
            reason_parts.append("趋势偏弱")
        
        # 指标2: 成交量配合度 (0-3分)
        vol_ratio = breakout.get('volume_ratio', 1)
        if vol_ratio > 2.5:
            score += 3
            reason_parts.append("量能充沛")
        elif vol_ratio > 1.8:
            score += 2
            reason_parts.append("量能充足")
        elif vol_ratio > 1.2:
            score += 1
            reason_parts.append("量能一般")
        
        # 指标3: 突破有效性 (0-3分)
        # 突破幅度与量能的配合度
        breakout_ratio = breakout.get('breakout_ratio', 0)
        if breakout_ratio > 0.05 and vol_ratio > 1.5:
            score += 3
            reason_parts.append("突破有效")
        elif breakout_ratio > 0.03 and vol_ratio > 1.2:
            score += 2
            reason_parts.append("突破较有效")
        elif breakout_ratio > 0.02:
            score += 1
            reason_parts.append("突破较弱")
        
        # 构建原因字符串
        if reason_parts:
            reason = f"市场环境({'/'.join(reason_parts)})"
        else:
            reason = "市场环境不佳"
        
        return {'score': score, 'reason': reason}

    def analyze_stock(self, stock_code: str, stock_name: str = None) -> Optional[Dict]:
        """分析单只股票"""
        try:
            df = self.data_adapter.get_stock_history(stock_code)
            if df is None or len(df) < 30:
                return None
            
            df = self.data_adapter.normalize_columns(df)
            
            breakouts = self.find_breakout(df)
            
            if not breakouts:
                return None
            
            # 取最后一次突破信号
            breakout = breakouts[-1]
            score, reasons = self.calculate_score(breakout, None)
            
            current = df.iloc[-1]
            
            return {
                'code': stock_code,
                'name': stock_name or stock_code,
                'score': score,
                'reasons': reasons,
                'current_price': round(current['close'], 2),
                'breakout_price': round(breakout['breakout_price'], 2),
                'highest_60d': round(breakout['highest_price'], 2),
                'breakout_ratio': round(breakout['breakout_ratio'] * 100, 2),
                'volume_ratio': round(breakout['volume_ratio'], 2),
                'strategy': self.name,
                'win_rate': self.win_rate
            }
            
        except Exception as e:
            return None

    def batch_analyze(self, stock_list: List[tuple], top_n: int = 10) -> List[Dict]:
        """批量分析"""
        results = []
        
        for name, code in stock_list:
            try:
                result = self.analyze_stock(code, name)
                if result and result['score'] > 0:
                    results.append(result)
            except Exception:
                continue
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]


if __name__ == '__main__':
    analyzer = BreakoutHighAnalyzer()
    
    test_stocks = [('平安银行', '000001'), ('东山精密', '002384')]
    
    print("突破前期高点策略测试")
    print("-" * 60)
    
    for name, code in test_stocks:
        result = analyzer.analyze_stock(code, name)
        if result:
            print(f"{name}({code}): 评分={result['score']}, 突破={result['breakout_ratio']}%, 量比={result['volume_ratio']}")
        else:
            print(f"{name}({code}): 未发现突破信号")
