# skills/scripts/hk_ma_pullback_scanner.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股缩量回踩均线全市场扫描器
"""

from hk_ma_pullback_analyzer import HKMaPullbackAnalyzer
from datetime import datetime
from typing import List, Tuple
import sys


class HKMaPullbackScanner:
    """港股缩量回踩均线扫描器"""
    
    def __init__(self):
        self.analyzer = HKMaPullbackAnalyzer()
        
    def scan_all(self, top_n: int = 20):
        """扫描全市场港股"""
        print(f"开始扫描港股缩量回踩均线股票...")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # 获取港股成分股列表（恒生指数成分股）
        stock_list = self._get_hk_constituents()
        
        candidates = []
        total = len(stock_list)
        
        for idx, (code, name) in enumerate(stock_list, 1):
            print(f"进度: {idx}/{total} ({idx/total*100:.1f}%)", end='\r')
            
            result = self.analyzer.analyze_stock(code, name)
            if result and result['score'] >= 70:
                candidates.append(result)
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        self._print_results(candidates[:top_n])
        
        return candidates[:top_n]
    
    def _get_hk_constituents(self) -> List[Tuple[str, str]]:
        """获取恒生指数成分股列表"""
        # 恒生指数主要成分股
        return [
            ('00700', '腾讯控股'),
            ('09988', '阿里巴巴-SW'),
            ('03690', '美团-W'),
            ('09999', '网易-S'),
            ('01810', '小米集团-W'),
            ('00941', '中国移动'),
            ('00883', '中国海洋石油'),
            ('03988', '中国银行'),
            ('01398', '工商银行'),
            ('00939', '建设银行'),
            ('02318', '中国平安'),
            ('02628', '中国人寿'),
            ('00005', '汇丰控股'),
            ('00011', '恒生银行'),
            ('00016', '新鸿基地产'),
            ('00001', '长和'),
            ('00002', '中电控股'),
            ('00003', '香港中华煤气'),
            ('00006', '电能实业'),
            ('00012', '恒基地产'),
            ('00017', '新世界发展'),
            ('00019', '太古股份'),
            ('00023', '东亚银行'),
            ('00027', '银河娱乐'),
            ('00066', '港铁公司'),
            ('00101', '恒隆地产'),
            ('00151', '中国旺旺'),
            ('00175', '吉利汽车'),
            ('00267', '中信股份'),
            ('00288', '万洲国际'),
        ]
    
    def _print_results(self, results):
        """打印结果"""
        if not results:
            print("\n未发现港股回踩机会")
            return
        
        print("\n" + "=" * 80)
        print(f"发现 {len(results)} 只港股回踩机会")
        print("=" * 80)
        
        for i, stock in enumerate(results, 1):
            print(f"\n{i}. {stock['stock_name']}({stock['stock_code']})")
            print(f"   评分: {stock['score']}分 | 信号: {stock['signal']}")
            print(f"   当前价: {stock['current_price']} | 20日线: {stock['ma20']}")
            print(f"   偏离度: {stock['deviation']}% | 缩量: {stock['volume_ratio']}")
            print(f"   成交额: {stock['avg_volume_hkd']}万港元")
            print(f"   入场: {stock['entry_price']} | 止损: {stock['stop_loss']} (-7%)")
            print(f"   建议: {stock['suggestion']}")


def main():
    scanner = HKMaPullbackScanner()
    scanner.scan_all(top_n=10)


if __name__ == '__main__':
    main()