#!/usr/bin/env python3
"""
港股回购公告跟进策略 - 核心分析器
HK Buyback Follow Strategy Analyzer
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    requests = None


class HKBuybackAnalyzer:
    """回购公告跟进分析器"""

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

    def get_current_price(self, symbol):
        """获取当前股价"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '5d'}
        try:
            r = requests.get(url, params=params, proxies=self.proxies,
                             timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json().get('chart', {}).get('result')
            if not data:
                return None
            quotes = data[0]['indicators']['quote'][0]
            closes = [c for c in quotes.get('close', []) if c is not None]
            if not closes:
                return None
            print(f"  股价来源: Yahoo Finance (最新价: {closes[-1]:.2f})")
            return closes[-1]
        except Exception as e:
            print(f"  股价获取失败: {e}")
            return None

    def _get_buyback_info(self, symbol):
        """
        获取回购信息（模拟数据）
        实际应从港交所披露易获取：
        https://www.hkexnewshk.com/sha_recent_buyback/sha_recent_buyback_dataflow.aspx
        """
        np.random.seed(hash(symbol) % 1000)
        cfg = self.config['buyback']

        # 常见持续回购公司
        known_buybacks = {
            '0700': {  # 腾讯
                'avg_price': 380.0,
                'total_shares': 500000,
                'shares_bought': 1200,
                'last_announce_days': 3,
                'historical_count': 8,
            },
            '9988': {  # 阿里
                'avg_price': 110.0,
                'total_shares': 1000000,
                'shares_bought': 800,
                'last_announce_days': 5,
                'historical_count': 5,
            },
            '3690': {  # 美团
                'avg_price': 95.0,
                'total_shares': 600000,
                'shares_bought': 450,
                'last_announce_days': 2,
                'historical_count': 4,
            },
        }

        raw = symbol.replace('.HK', '').lstrip('0')
        if raw in known_buybacks:
            info = known_buybacks[raw].copy()
        else:
            # 模拟随机数据
            avg_price = np.random.uniform(20, 200)
            total_shares = np.random.randint(100000, 5000000)
            shares_bought = int(total_shares * np.random.uniform(0.0005, 0.003))
            info = {
                'avg_price': avg_price,
                'total_shares': total_shares,
                'shares_bought': shares_bought,
                'last_announce_days': np.random.randint(1, 10),
                'historical_count': np.random.randint(1, 8),
            }

        info['buyback_ratio'] = info['shares_bought'] / info['total_shares']
        return info

    def _get_market_cap(self, symbol):
        """获取市值（模拟）"""
        np.random.seed(hash(symbol) % 1000 + 2)
        caps = {
            '0700': 45000,
            '9988': 22000,
            '3690': 5500,
        }
        raw = symbol.replace('.HK', '').lstrip('0')
        return caps.get(raw, np.random.uniform(500, 8000))  # 亿港元

    def check_price_discount(self, current_price, buyback_avg_price):
        """检查当前价是否低于回购均价5%"""
        cfg = self.config['buyback']
        threshold = cfg['price_discount_threshold']
        if buyback_avg_price <= 0:
            return False, 0.0
        discount = (buyback_avg_price - current_price) / buyback_avg_price
        return discount >= threshold, discount * 100

    def check_buyback_scale(self, buyback_ratio):
        """检查回购规模是否达标"""
        cfg = self.config['buyback']
        threshold = cfg['min_ratio_threshold']
        return buyback_ratio >= threshold

    def check_historical_compliance(self, historical_count):
        """检查2年内历史回购次数"""
        cfg = self.config['buyback']
        min_programs = cfg['historical_min_programs']
        return historical_count >= min_programs

    def check_timing(self, days_since_announce):
        """检查公告时效"""
        cfg = self.config['buyback']
        window = cfg['announcement_window_days']
        return days_since_announce <= window

    def score_stock(self, discount_pct, buyback_ratio, historical_count,
                   days_since, market_cap_ok, scale_ok, history_ok, timing_ok, discount_ok):
        """综合评分"""
        score = 0
        cfg = self.config['buyback']

        # 价格偏离度
        if discount_pct >= 15:
            score += 30
        elif discount_pct >= 10:
            score += 25
        elif discount_pct >= 5:
            score += 20
        elif discount_ok:
            score += 10

        # 回购规模
        if buyback_ratio >= 0.005:
            score += 25
        elif buyback_ratio >= 0.002:
            score += 20
        elif scale_ok:
            score += 15

        # 历史合规
        if historical_count >= 5:
            score += 25
        elif history_ok:
            score += 20
        elif historical_count >= 2:
            score += 15

        # 时效性
        if days_since <= 3:
            score += 20
        elif timing_ok:
            score += 15

        # 市值加成
        if market_cap_ok:
            score += 5

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

        # 获取当前股价
        current_price = self.get_current_price(symbol)
        if current_price is None:
            current_price = 100.0  # 模拟

        # 获取回购信息
        bb = self._get_buyback_info(symbol)

        # 获取市值
        market_cap_b = self._get_market_cap(symbol)
        market_cap_ok = market_cap_b >= self.config['filters']['min_market_cap']

        # 各条件检查
        discount_ok, discount_pct = self.check_price_discount(current_price, bb['avg_price'])
        scale_ok = self.check_buyback_scale(bb['buyback_ratio'])
        history_ok = self.check_historical_compliance(bb['historical_count'])
        timing_ok = self.check_timing(bb['last_announce_days'])

        # 综合评分
        score = self.score_stock(discount_pct, bb['buyback_ratio'],
                                bb['historical_count'], bb['last_announce_days'],
                                market_cap_ok, scale_ok, history_ok, timing_ok, discount_ok)
        signal, rating = self.get_signal(score)

        # 入场和止损
        entry_price = current_price  # 明日开盘买入
        stop_loss = entry_price * (1 - self.config['risk']['stop_loss_pct'])
        take_profit = entry_price * (1 + self.config['risk']['take_profit_pct'])

        result = {
            'symbol': symbol,
            'name': name,
            'current_price': current_price,
            'buyback_avg_price': bb['avg_price'],
            'price_discount': discount_pct,
            'discount_ok': discount_ok,
            'buyback_ratio': bb['buyback_ratio'] * 100,
            'scale_ok': scale_ok,
            'historical_count': bb['historical_count'],
            'history_ok': history_ok,
            'days_since_announce': bb['last_announce_days'],
            'timing_ok': timing_ok,
            'market_cap_b': market_cap_b,
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
        print(f"  当前价: {result['current_price']:.2f}")
        print(f"  回购均价: {result['buyback_avg_price']:.2f}")
        print(f"  偏离度: {result['price_discount']:.2f}% {'✅' if result['discount_ok'] else '❌'}")
        print(f"  回购规模: {result['buyback_ratio']:.3f}% {'✅' if result['scale_ok'] else '❌'}")
        print(f"  历史合规: {result['historical_count']}次/2年 {'✅' if result['history_ok'] else '❌'}")
        print(f"  公告时效: {result['days_since_announce']}日内 {'✅' if result['timing_ok'] else '❌'}")
        print(f"  市值: {result['market_cap_b']:.0f}亿港元")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} | 止盈: {result['take_profit']}")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股回购公告跟进分析')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKBuybackAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
