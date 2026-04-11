#!/usr/bin/env python3
"""
板块分析模块 - 支持按板块分析股票
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime


class SectorAnalyzer:
    """板块分析器"""

    # 预定义板块和代表性成分股
    SECTORS = {
        '科技': ['000938', '000977', '002230', '002236', '002415', '300033', '300059', '600570', '600584', '603019'],
        '医药': ['000538', '000623', '000999', '002001', '002007', '300003', '300015', '600276', '600436', '603259'],
        '金融': ['000001', '000002', '600000', '600016', '600030', '600036', '600837', '601318', '601398', '601628'],
        '消费': ['000568', '000596', '000858', '002304', '600519', '600887', '601012', '601888', '603288', '603899'],
        '新能源': ['002074', '002129', '002202', '002594', '300014', '300124', '600438', '601012', '601727', '603806'],
        '军工': ['000768', '002013', '002179', '300034', '300114', '600038', '600150', '600372', '600893', '600967'],
        '半导体': ['002049', '002156', '300046', '300223', '300661', '600360', '600584', '603005', '603501', '688008'],
        '能源': ['000552', '000723', '002128', '600028', '600348', '600508', '600971', '601088', '601857', '601899'],
        '电网': ['000400', '002028', '300001', '300274', '600406', '600452', '600487', '600885', '601179', '601669'],
        '算力': ['000938', '000977', '002236', '300017', '300212', '300383', '600570', '600756', '603019', '688561'],
        '存储': ['002049', '300223', '300661', '600667', '603501', '688008', '688018', '688123', '688256', '688525'],
        '创新药': ['002422', '002653', '300003', '300142', '300558', '600196', '600276', '688180', '688266', '688331'],
    }

    def __init__(self, analyzer):
        self.analyzer = analyzer
        print(f"⚠️ 注意：当前板块分析使用预定义的代表性股票（共{sum(len(s) for s in self.SECTORS.values())}只）")
        print(f"   如需分析全市场，请使用 scan_all_stocks() 功能")

    def analyze_sector(self, sector: str, analysis_date: Optional[str] = None) -> List[Dict]:
        if sector not in self.SECTORS:
            print(f"❌ 未知板块: {sector}")
            print(f"   可用板块: {', '.join(self.SECTORS.keys())}")
            return []

        stocks = self.SECTORS[sector]
        print(f"\n开始分析 {sector} 板块 ({len(stocks)} 只股票)...")

        if analysis_date:
            old_date = self.analyzer.analysis_date
            self.analyzer.analysis_date = datetime.strptime(analysis_date, '%Y-%m-%d')
            results = [self.analyzer.analyze_stock(code, code) for code in stocks]
            self.analyzer.analysis_date = old_date
        else:
            results = [self.analyzer.analyze_stock(code, code) for code in stocks]

        bullish = [r for r in results if r['is_bullish']]
        print(f"   {sector}板块: 发现 {len(bullish)} 只均线多头排列股票")

        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def analyze_all_sectors(self, analysis_date: Optional[str] = None) -> Dict[str, List[Dict]]:
        all_results = {}
        for sector in self.SECTORS:
            results = self.analyze_sector(sector, analysis_date)
            all_results[sector] = [r for r in results if r['is_bullish']]
        return all_results

    def generate_sector_report(self, results: List[Dict]) -> str:
        if not results:
            return "该板块暂无符合均线多头排列的股票"
        lines = []
        lines.append(f"发现 {len(results)} 只符合条件的股票：")
        for r in results[:10]:
            lines.append(f"  {r['name']} ({r['code']}) - 评分: {r['score']}")
        return "\n".join(lines)
