#!/usr/bin/env python3
"""
港股流动性过滤策略 - 核心分析器
HK Liquidity Filter Analyzer
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


class HKLiquidityAnalyzer:
    """流动性分析器"""

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
        """H股代码转 Yahoo Finance 格式"""
        raw = symbol.replace('.HK', '').lstrip('0') or '0'
        orig = symbol.replace('.HK', '')
        leading_zeros = len(orig) - len(orig.lstrip('0'))
        if leading_zeros >= 1:
            code = raw.zfill(len(raw) + 1)
        else:
            code = raw
        return code + '.HK'

    def get_price_data(self, symbol):
        """获取近期行情数据"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '30d'}
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
            return df.tail(30)
        except Exception as e:
            print(f"  数据获取失败: {e}，使用模拟数据")
            return self._get_mock_data(symbol)

    def _get_mock_data(self, symbol):
        """模拟行情数据"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=30, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        data = {
            'date': dates,
            'open': base + np.random.randn(30).cumsum() * 2,
            'high': base + 3 + np.random.randn(30).cumsum() * 2,
            'low': base - 3 + np.random.randn(30).cumsum() * 2,
            'close': base + np.random.randn(30).cumsum() * 2,
            'volume': np.random.randint(5000000, 50000000, 30),
        }
        return pd.DataFrame(data)

    def _get_market_cap(self, symbol):
        """获取市值（模拟）"""
        np.random.seed(hash(symbol) % 1000 + 3)
        caps = {
            '0700': 45000,   # 腾讯 ~4.5万亿
            '0981': 2800,    # 中芯 ~2800亿
            '0999': 800,     # 泡泡玛特 ~800亿
            '0003': 1200,    # 煤气 ~1200亿
            '0823': 1500,    # 领展 ~1500亿
        }
        raw = symbol.replace('.HK', '').lstrip('0')
        return caps.get(raw, np.random.uniform(50, 5000))  # 亿港元

    def check_volume(self, df):
        """检查日均成交额 > 2000万港元"""
        cfg = self.config['liquidity']
        ma_days = cfg['min_volume_ma_days']
        avg_volume = df['volume'].tail(ma_days).mean()
        threshold = cfg['min_avg_volume_m_hkd'] * 1000000
        return avg_volume >= threshold, avg_volume / 1000000

    def check_turnover(self, df, raw_symbol):
        """检查换手率 > 0.5%"""
        cfg = self.config['liquidity']
        latest_close = df['close'].iloc[-1]
        latest_volume = df['volume'].iloc[-1]
        market_cap = self._get_market_cap(raw_symbol) * 100000000
        if latest_close <= 0 or market_cap <= 0:
            return False, 0.0
        daily_turnover = (latest_volume * latest_close) / market_cap
        threshold = cfg['min_turnover_rate']
        return daily_turnover >= threshold, daily_turnover * 100

    def _symbol_to_raw(self, df):
        """从df反推symbol（简化处理）"""
        return "0700"

    def check_bid_ask_spread(self, df):
        """
        检查买卖价差 < 0.2%
        注：Yahoo Finance 不提供实时 bid/ask，使用日内价差估算（仅作参考）
        实际 bid/ask 价差通常远小于日内高低差，此处用 /5 作为保守估算
        """
        cfg = self.config['liquidity']
        latest = df.iloc[-1]
        if latest['close'] <= 0:
            return False, 99.0
        # 日内高低差作为 bid-ask 估算的上限，实际价差约为日内波幅的 10-30%
        daily_range = (latest['high'] - latest['low']) / latest['close']
        bid_ask_est = daily_range * 0.2  # 保守估算为日内波幅的 20%
        threshold = cfg['max_bid_ask_spread'] * 100  # 0.005 -> 0.5（百分比比较）
        return bid_ask_est * 100 <= threshold, bid_ask_est * 100

    def check_market_cap(self, market_cap_b):
        """检查市值 > 50亿港元"""
        cfg = self.config['liquidity']
        threshold = cfg['min_market_cap_b_hkd']
        return market_cap_b >= threshold

    def score_liquidity(self, avg_volume_m, turnover_rate, spread_pct, market_cap_b):
        """综合流动性评分"""
        score = 0

        # 成交额评分
        if avg_volume_m > 100:
            score += 30
        elif avg_volume_m > 50:
            score += 25
        elif avg_volume_m > 20:
            score += 20
        elif avg_volume_m > 10:
            score += 10

        # 换手率评分
        if turnover_rate > 1.0:
            score += 25
        elif turnover_rate > 0.5:
            score += 20
        elif turnover_rate > 0.3:
            score += 10

        # 价差评分
        if spread_pct < 0.05:
            score += 20
        elif spread_pct < 0.1:
            score += 15
        elif spread_pct < 0.2:
            score += 10

        # 市值评分
        if market_cap_b > 500:
            score += 25
        elif market_cap_b > 100:
            score += 20
        elif market_cap_b > 50:
            score += 15
        elif market_cap_b > 10:
            score += 5

        return min(score, 100)

    def check_stock(self, symbol, name=""):
        """检查单只股票是否满足流动性条件"""
        print(f"\n检查 {symbol} {name}...")

        df = self.get_price_data(symbol)
        if df is None or df.empty:
            return {'allowed': False, 'symbol': symbol, 'name': name,
                    'reject_reasons': ['无法获取数据'],
                    'score': 0, 'avg_volume_m': 0, 'vol_ok': False,
                    'turnover_rate': 0, 'turnover_ok': False,
                    'bid_ask_spread': 0, 'spread_ok': False,
                    'market_cap_b': 0, 'cap_ok': False,
                    'price': 0, 'penny_rejected': False}

        # 获取市值
        raw_symbol = symbol.replace('.HK', '').lstrip('0')
        market_cap_b = self._get_market_cap(raw_symbol)

        # 各条件检查
        vol_ok, avg_vol_m = self.check_volume(df)
        turnover_ok, turnover_rate = self.check_turnover(df, raw_symbol)
        spread_ok, spread_pct = self.check_bid_ask_spread(df)
        cap_ok = self.check_market_cap(market_cap_b)

        # 仙股检查
        current_price = df['close'].iloc[-1]
        penny_rejected = current_price < 1.0

        # 汇总
        all_ok = vol_ok and turnover_ok and spread_ok and cap_ok and not penny_rejected
        reject_reasons = []
        if not vol_ok:
            reject_reasons.append(f"日均成交额 {avg_vol_m:.1f}M < 20M")
        if not turnover_ok:
            reject_reasons.append(f"换手率 {turnover_rate:.3f}% < 0.5%")
        if not spread_ok:
            reject_reasons.append(f"买卖价差 {spread_pct:.3f}% (阈值: {self.config["liquidity"]["max_bid_ask_spread"]*100:.1f}%)")
        if not cap_ok:
            reject_reasons.append(f"市值 {market_cap_b:.0f}B < 50B")
        if penny_rejected:
            reject_reasons.append(f"股价 {current_price:.2f}港元 < 1港元（仙股）")

        score = self.score_liquidity(avg_vol_m, turnover_rate, spread_pct, market_cap_b)

        result = {
            'symbol': symbol,
            'name': name,
            'allowed': all_ok,
            'avg_volume_m': avg_vol_m,
            'vol_ok': vol_ok,
            'turnover_rate': turnover_rate,
            'turnover_ok': turnover_ok,
            'bid_ask_spread': spread_pct,
            'spread_ok': spread_ok,
            'market_cap_b': market_cap_b,
            'cap_ok': cap_ok,
            'price': current_price,
            'penny_rejected': penny_rejected,
            'reject_reasons': reject_reasons,
            'score': score,
        }
        return result

    def print_result(self, result):
        if result['allowed']:
            print(f"\n✅ 允许交易: {result['symbol']} {result['name']}")
            print(f"   日均成交额: {result['avg_volume_m']:.1f}M 港元")
            print(f"   换手率: {result['turnover_rate']:.3f}%")
            print(f"   买卖价差: {result['bid_ask_spread']:.3f}%")
            print(f"   市值: {result['market_cap_b']:.1f}B 港元")
            print(f"   综合评分: {result['score']}")
        else:
            print(f"\n❌ 拒绝交易: {result['symbol']} {result['name']}")
            for reason in result['reject_reasons']:
                print(f"   - {reason}")
            print(f"   综合评分: {result['score']}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股流动性检查')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKLiquidityAnalyzer()
    result = analyzer.check_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
