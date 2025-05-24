#!/usr/bin/env python3
"""
測試碳足跡圖表的獨立腳本
"""

import sys
import os

# 添加 ui 目錄到路徑中
sys.path.append('ui')

from charts import create_environmental_gauges

def test_chart():
    """測試圖表生成"""
    
    # 模擬數據（來自您提供的實際數據）
    saved_carbon = 71.18
    tree_equivalent = 3.4
    car_km_equivalent = 284.7
    ac_hours = 142.4
    phone_charges = 7118
    
    print("正在生成測試圖表...")
    
    # 生成圖表
    fig = create_environmental_gauges(
        saved_carbon=saved_carbon,
        tree_equivalent=tree_equivalent,
        car_km_equivalent=car_km_equivalent,
        ac_hours=ac_hours,
        phone_charges=phone_charges
    )
    
    if fig:
        # 保存為 HTML 文件
        output_file = "test_chart.html"
        fig.write_html(output_file)
        print(f"圖表已保存為: {output_file}")
        
        # 自動打開瀏覽器（MacOS）
        import subprocess
        try:
            subprocess.run(['open', output_file], check=True)
            print("已在瀏覽器中打開圖表")
        except:
            print(f"請手動打開 {output_file} 查看圖表")
            
        return True
    else:
        print("圖表生成失敗")
        return False

if __name__ == "__main__":
    test_chart()
