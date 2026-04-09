#!/usr/bin/env python3
"""
港股沽空比率反转策略 - 核心分析器
HK Short Interest Reversal Analyzer
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    requests = None


class HKShortReversalAnalyzer:
    """沽空比率反转分析器"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "strategy_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _to_yahoo_code(self, symbol):
        """转换代码为 Yahoo Finance 格式"""
        raw = symbol.replace('.HK', '').lstrip('0') or '0'
        orig = symbol.replace('.HK', '')
        leading_zeros = len(orig) - len(orig.lstrip('0'))
        if leading_zeros >= 1:
            code = raw.zfill(len(raw) + 1)
        else:
            code = raw
        return code + '.HK'

    def get_stock_data(self, symbol):
        """获取港股行情数据"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '90d'}
        try:
            r = requests.get(url, params=params, proxies=self.proxies,
                             timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json().get('chart', {}).get('result')
            if not data:
                return None
            d = data[0]
            timestamps = d['timestamp']
            quotes = d['indicators']['quote'][0]
            df = pd.DataFrame({
                'date': pd.to_datetime(timestamps, unit='s'),
                'open': quotes.get('open'),
                'high': quotes.get('high'),
                'low': quotes.get('low'),
                'close': quotes.get('close'),
                'volume': quotes.get('volume'),
            })
            df = df.dropna()
            print(f"  数据来源: Yahoo Finance ({len(df)} 条)")
            return df.tail(90)
        except Exception as e:
            print(f"  数据获取失败: {e}，使用模拟数据")
            return self._get_mock_data(symbol)

    def _get_mock_data(self, symbol):
        """返回模拟数据"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=90, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        # 模拟：先持续下跌（高沽空），然后开始反弹
        trend = np.concatenate([
            np.linspace(0, -20, 50),   # 持续下跌
            np.linspace(-20, 5, 40),  # 开始反弹
        ])
        data = {
            'date': dates,
            'open': base + trend + np.random.randn(90) * 2,
            'high': base + trend + 3 + np.random.randn(90) * 2,
            'low': base + trend - 3 + np.random.randn(90) * 2,
            'close': base + trend + np.random.randn(90) * 2,
            'volume': np.random.randint(5000000, 50000000, 90),
        }
        return pd.DataFrame(data)

    def _get_short_ratio_history(self, symbol):
        """
        获取沽空比率历史数据（模拟数据）
        实际应从港交所披露易获取：
        https://www.hkexnews.hk/sha_recent_so/sha_recent_so_dataflow.aspx
        """
        np.random.seed(hash(symbol) % 1000 + 1)
        n = 30
        # 模拟沽空比率：前段较高（>25%），近期开始下降
        base = np.concatenate([
            np.random.uniform(0.22, 0.38, 15),   # 高沽空期
            np.array([0.30, 0.28, 0.26, 0.24, 0.22, 0.20]),  # 连续下降
            np.random.uniform(0.18, 0.22, 9),   # 下降后区间
        ])
        return base[-30:]

    def _get_market_cap(self, symbol):
        """
        获取市值（模拟数据）
        实际从 Yahoo Finance 获取：summaryDetail.marketCap
        """
        np.random.seed(hash(symbol) % 1000)
        caps = {
            '0700': 45000,   # 腾讯 ~4.5万亿
            '9988': 22000,   # 阿里 ~2.2万亿
            '3690': 5500,    # 美团 ~5500亿
            '0941': 12000,   # 移动 ~1.2万亿
            '0939': 15000,   # 建行 ~1.5万亿
        }
        raw = symbol.replace('.HK', '').lstrip('0')
        return caps.get(raw, np.random.uniform(100, 5000))  # 亿港元

    def check_high_short_interest(self, short_ratios):
        """检查沽空比率 > 25% 连续3日"""
        if len(short_ratios) < 3:
            return 0, 0.0
        cfg = self.config['short_interest']
        threshold = cfg['high_threshold']
        consecutive_days = cfg['consecutive_high_days']

        # 检查近N日内是否有连续3日 > 25%
        count = 0
        max_consecutive = 0
        current_streak = 0
        for ratio in short_ratios[-consecutive_days - 5:]:
            if ratio > threshold:
                current_streak += 1
                max_consecutive = max(max_consecutive, current_streak)
            else:
                current_streak = 0
        return max_consecutive, short_ratios[-1]

    def check_reversal_signal(self, short_ratios):
        """检查沽空比率连续2日下降"""
        if len(short_ratios) < 3:
            return 0
        cfg = self.config['short_interest']
        down_days = cfg['reversal_down_days']

        consecutive_down = 0
        for i in range(len(short_ratios) - 1, 0, -1):
            if short_ratios[i] < short_ratios[i - 1]:
                consecutive_down += 1
            else:
                break
        return consecutive_down

    def check_volume_surge(self, df):
        """检查成交量 > 20日均量 × 1.5"""
        vol_ma20 = df['volume'].rolling(window=20).mean()
        current_vol = df['volume'].iloc[-1]
        ma20_vol = vol_ma20.iloc[-1]
        if pd.isna(ma20_vol) or ma20_vol == 0:
            return False, 0
        ratio = current_vol / ma20_vol
        threshold = self.config['volume']['surge_multiplier']
        return ratio > threshold, ratio

    def score_stock(self, high_days, short_ratio, reversal_days, volume_ok, vol_ratio, market_cap_ok, market_cap_b):
        """综合评分"""
        score = 0
        cfg = self.config['short_interest']

        # 沽空高度
        if high_days >= 3:
            score += 30
        elif high_days >= 2:
            score += 20

        # 反转确认
        if reversal_days >= 2:
            score += 30
        elif reversal_days >= 1:
            score += 15

        # 量能
        if volume_ok:
            score += 20
        elif vol_ratio > 1.2:
            score += 10

        # 市值
        if market_cap_ok:
            score += 20

        return min(score, 100)

    def get_signal(self, score):
        if score >= 85:
            return "强烈买入", "极强"
        elif score >= 75:
            return "买入", "强"
        elif score >= 70:
            return "观望", "中等"
        else:
            return "不建议", "弱"

    def analyze_stock(self, symbol, name=""):
        """分析单只股票"""
        print(f"\n分析 {symbol} {name}...")

        # 获取行情数据
        df = self.get_stock_data(symbol)
        if df is None or df.empty:
            print(f"  无法获取数据")
            return None

        # 获取沽空比率历史
        short_ratios = self._get_short_ratio_history(symbol)

        # 获取市值
        market_cap_b = self._get_market_cap(symbol)
        market_cap_ok = market_cap_b >= self.config['market_cap']['min_billion_hkd']

        # 各条件检查
        high_days, current_short_ratio = self.check_high_short_interest(short_ratios)
        reversal_days = self.check_reversal_signal(short_ratios)
        volume_ok, vol_ratio = self.check_volume_surge(df)

        # 综合评分
        score = self.score_stock(high_days, current_short_ratio, reversal_days,
                                  volume_ok, vol_ratio, market_cap_ok, market_cap_b)
        signal, rating = self.get_signal(score)

        entry_price = df['close'].iloc[-1]
        stop_loss = entry_price * (1 - self.config['risk']['stop_loss_pct'])
        take_profit = entry_price * (1 + self.config['risk']['take_profit_pct'])

        result = {
            'symbol': symbol,
            'name': name,
            'close': entry_price,
            'short_ratio': current_short_ratio * 100,
            'high_short_days': high_days,
            'consecutive_down_days': reversal_days,
            'volume_ratio': vol_ratio,
            'volume_ok': volume_ok,
            'market_cap_b': market_cap_b,
            'market_cap_ok': market_cap_ok,
            'score': score,
            'rating': rating,
            'signal': signal,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'suggestion': f"评分{score}分({rating})，{signal}",
        }
        return result

    def print_result(self, result):
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']}")
        print(f"{'=' * 50}")
        print(f"  当前价: {result['close']:.2f}")
        print(f"  当前沽空比率: {result['short_ratio']:.2f}%")
        print(f"  高沽空(>25%)天数: {result['high_short_days']}日")
        print(f"  连续下降天数: {result['consecutive_down_days']}日")
        print(f"  量能倍数: {result['volume_ratio']:.2f}x MA20 {'✅' if result['volume_ok'] else '❌'}")
        print(f"  市值: {result['market_cap_b']:.0f}亿港元 {'✅' if result['market_cap_ok'] else '❌'}")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} | 止盈: {result['take_profit']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股沽空比率反转分析')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKShortReversalAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
