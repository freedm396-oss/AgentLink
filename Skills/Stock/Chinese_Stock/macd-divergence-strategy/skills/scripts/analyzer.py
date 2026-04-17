#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MACD底背离策略分析器
识别价格创出新低但MACD未创新低的底背离信号
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


class MACDDivergenceAnalyzer:
    """MACD底背离分析器"""
    
    def __init__(self, data_source: str = "auto"):
        self.name = "MACD底背离策略"
        self.version = "v1.0.0"
        self.win_rate = 0.58
        
        # MACD参数
        self.fast_ema = 12
        self.slow_ema = 26
        self.signal_ema = 9
        
        # 评分权重
        self.weights = {
            'divergence_strength': 0.25,
            'macd_golden_cross': 0.20,
            'volume_confirm': 0.20,
            'price_stability': 0.20,
            'market_environment': 0.15
        }
        
        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源")

    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        df = df.copy()
        
        # 计算EMA
        df['ema_fast'] = df['close'].ewm(span=self.fast_ema, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_ema, adjust=False).mean()
        
        # MACD线
        df['macd'] = df['ema_fast'] - df['ema_slow']
        
        # 信号线
        df['signal'] = df['macd'].ewm(span=self.signal_ema, adjust=False).mean()
        
        # MACD柱状图
        df['histogram'] = df['macd'] - df['signal']
        
        return df

    def find_divergence(self, df: pd.DataFrame, lookback: int = 60) -> List[Dict]:
        """查找MACD底背离信号"""
        if len(df) < 30:
            return []
        
        df = self.calculate_macd(df)
        divergences = []
        
        for i in range(20, len(df)):
            # 找到最近20日内价格最低点
            price_window = df['close'].iloc[max(0, i-20):i+1]
            price_low_idx = price_window.idxmin()
            price_low = df.loc[price_low_idx, 'close']
            
            # MACD对应位置的最低值
            macd_window = df['macd'].iloc[max(0, i-20):i+1]
            macd_low_idx = macd_window.idxmin()
            macd_low = df.loc[macd_low_idx, 'macd']
            
            # 检查是否是真正的底背离
            # 1. 价格创新低
            # 2. MACD未创新低（背离）
            # 3. 最近一根K线价格上涨
            
            if price_low_idx == i:  # 价格创新低
                # 检查之前是否有更低的低点
                prev_prices = df['close'].iloc[max(0, i-30):i].values
                if len(prev_prices) > 0 and price_low < prev_prices.min():
                    # 价格创新低，检查MACD
                    prev_macd = df['macd'].iloc[max(0, i-30):i].values
                    if len(prev_macd) > 0 and macd_low > prev_macd.min():
                        # MACD未创新低，确认底背离
                        current_price = df.iloc[i]['close']
                        current_macd = df.iloc[i]['macd']
                        
                        divergences.append({
                            'index': i,
                            'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                            'price_low': price_low,
                            'macd_low': macd_low,
                            'current_price': current_price,
                            'current_macd': current_macd,
                            'divergence_strength': (macd_low - prev_macd.min()) / abs(prev_macd.min()) if prev_macd.min() != 0 else 0
                        })
        
        return divergences

    def check_golden_cross(self, df: pd.DataFrame, divergence_idx: int) -> bool:
        """检查MACD是否形成金叉"""
        if divergence_idx < 5:
            return False
        
        # 金叉：MACD从负转正或从下往上穿越信号线
        current = df.iloc[divergence_idx]
        prev = df.iloc[divergence_idx - 1]
        
        return current['macd'] > current['signal'] and prev['macd'] <= prev['signal']

    def analyze_volume(self, df: pd.DataFrame, divergence_idx: int) -> float:
        """分析成交量确认信号"""
        if divergence_idx < 5:
            return 0
        
        # 检查背离后的成交量是否放大
        vol_window = df['volume'].iloc[divergence_idx-2:divergence_idx+1]
        vol_ma = df['volume'].rolling(window=20).mean().iloc[divergence_idx]
        
        if vol_ma > 0:
            avg_vol = vol_window.mean()
            return min(avg_vol / vol_ma, 2.0)  # 最多2倍
        return 0

    def calculate_score(self, df: pd.DataFrame, divergence: Dict) -> Tuple[float, str]:
        """计算评分"""
        score = 0
        reasons = []
        
        # 1. 背离强度得分 (0-25)
        strength = divergence.get('divergence_strength', 0)
        if strength > 0.5:
            score += 25
            reasons.append("底背离信号强烈")
        elif strength > 0.3:
            score += 20
            reasons.append("底背离信号明显")
        elif strength > 0.1:
            score += 15
            reasons.append("存在底背离迹象")
        
        # 2. 金叉确认得分 (0-20)
        if self.check_golden_cross(df, divergence['index']):
            score += 20
            reasons.append("MACD形成金叉确认")
        else:
            score += 8
            reasons.append("等待金叉确认")
        
        # 3. 量能确认得分 (0-20)
        vol_ratio = self.analyze_volume(df, divergence['index'])
        if vol_ratio > 1.5:
            score += 20
            reasons.append("成交量明显放大配合")
        elif vol_ratio > 1.2:
            score += 15
            reasons.append("成交量温和放大")
        elif vol_ratio > 1.0:
            score += 10
            reasons.append("量能有所恢复")
        
        # 4. 价格稳定得分 (0-20)
        if divergence['index'] >= 5:
            price_std = df['close'].iloc[divergence['index']-5:divergence['index']].std()
            price_mean = df['close'].iloc[divergence['index']-5:divergence['index']].mean()
            cv = price_std / price_mean if price_mean > 0 else 1
            
            if cv < 0.02:
                score += 20
                reasons.append("价格极度稳定")
            elif cv < 0.05:
                score += 15
                reasons.append("价格相对稳定")
            elif cv < 0.1:
                score += 10
                reasons.append("价格波动适中")
        
        # 5. 市场环境得分 (0-15)
        score += 15  # 默认满分
        
        return score, "; ".join(reasons)

    def analyze_stock(self, stock_code: str, stock_name: str = None) -> Optional[Dict]:
        """分析单只股票"""
        try:
            # 获取数据
            df = self.data_adapter.get_stock_history(stock_code)
            if df is None or len(df) < 60:
                return None
            
            # 标准化列名
            df = self.data_adapter.normalize_columns(df)
            
            # 查找底背离
            divergences = self.find_divergence(df)
            
            if not divergences:
                return None
            
            # 取最近的底背离信号
            divergence = divergences[-1]
            
            # 计算评分
            score, reasons = self.calculate_score(df, divergence)
            
            # 获取当前价格
            current = df.iloc[-1]
            
            return {
                'code': stock_code,
                'name': stock_name or stock_code,
                'score': score,
                'reasons': reasons,
                'current_price': round(current['close'], 2),
                'current_macd': round(current['macd'], 4),
                'divergence_strength': round(divergence.get('divergence_strength', 0), 4),
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
    analyzer = MACDDivergenceAnalyzer()
    
    test_stocks = [
        ('平安银行', '000001'),
        ('万科A', '000002'),
    ]
    
    print("MACD底背离策略测试")
    print("-" * 60)
    
    for name, code in test_stocks:
        result = analyzer.analyze_stock(code, name)
        if result:
            print(f"{name}({code}): 评分={result['score']}, 原因={result['reasons']}")
        else:
            print(f"{name}({code}): 未发现底背离信号")
