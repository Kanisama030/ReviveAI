"""
ReviveAI 圖表視覺化模組
包含所有圖表生成和視覺化相關函數
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_environmental_gauges(saved_carbon, tree_equivalent, car_km_equivalent, ac_hours=0, phone_charges=0):
    """創建環保效益儀表板"""
    def parse_value(value):
        if isinstance(value, str):
            try:
                if value.startswith("少於"):
                    return float(value.split("少於")[1].strip())
                return float(''.join(filter(lambda x: x.isdigit() or x == '.', value)))
            except (ValueError, AttributeError):
                return 0.0
        return float(value)

    # 解析值
    saved_carbon = parse_value(saved_carbon)
    tree_equivalent = parse_value(tree_equivalent)
    car_km_equivalent = parse_value(car_km_equivalent)
    ac_hours = parse_value(ac_hours)
    phone_charges = parse_value(phone_charges)

    # 計算每個儀表的最大範圍
    carbon_max = saved_carbon * 1.4
    tree_max = tree_equivalent * 1.5
    car_max = car_km_equivalent * 1.45
    ac_max = ac_hours * 1.4
    phone_max = phone_charges * 1.05  # 手機充電使用更誇張的範圍

    # 創建兩行三列的子圖布局，按照 123/045 排列
    fig = make_subplots(
        rows=2, cols=3,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}],
               [None, {'type': 'indicator'}, {'type': 'indicator'}]],  # 第二行第一個位置空白
        horizontal_spacing=0.05,  # 調整水平間距
        vertical_spacing=0.1,     # 調整垂直間距
        subplot_titles=('', '', '', '', '', '')  # 空標題
    )

    # 定義共用的字體樣式
    title_font = {'family': 'Arial', 'size': 20, 'color': '#2E4053'}
    number_font = {'family': 'Arial', 'size': 24, 'color': '#2E4053'}

    # 定義共用的儀表設計
    gauge_config = {
        'bgcolor': 'white',
        'borderwidth': 2,
        'bordercolor': '#34495E',
        'steps': [],
        'threshold': {
            'line': {'color': '#E74C3C', 'width': 4},
            'thickness': 0.8,
        }
    }

    # 通用的轴配置
    axis_config = {
        'tickfont': {'size': 12},  # 刻度字體
        'nticks': 6  # 刻度数量
    }

    # 減碳量儀表 - 位置1（第1行第2列）
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",  # 顯示儀表盤和數字
            value=saved_carbon,
            number={'font': number_font, 'suffix': ' kg', 'valueformat': '.2f'},  # 中間數字
            title={'text': '🌏減碳量', 'font': title_font},  # 上方標題
            gauge={
                **gauge_config,
                'axis': {**axis_config, 'range': [0, carbon_max]},  # 刻度軸設置
                'bar': {'color': '#27AE60'},  # 指針/弧形
                'steps': [{'range': [0, saved_carbon], 'color': '#A9DFBF'}],  # 填充顏色區域
                'threshold': {**gauge_config['threshold'], 'value': saved_carbon}  # 當前值的標記線
            }
        ),
        row=1, col=1
    )

    # 樹木數量儀表 - 位置2（第1行第3列）
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=tree_equivalent,
            number={'font': number_font, 'suffix': ' 棵', 'valueformat': '.1f'},
            title={'text': '🌳等於幾顆樹一年吸碳量', 'font': title_font},
            gauge={
                **gauge_config,
                'axis': {**axis_config, 'range': [0, tree_max]},
                'bar': {'color': '#218F76'},
                'steps': [{'range': [0, tree_equivalent], 'color': '#A3E4D7'}],
                'threshold': {**gauge_config['threshold'], 'value': tree_equivalent}
            }
        ),
        row=1, col=2
    )

    # 車程儀表
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=car_km_equivalent,
            number={'font': number_font, 'suffix': ' km', 'valueformat': '.1f'},
            title={'text': '🚗減少開車幾公里的碳排', 'font': title_font},
            gauge={
                **gauge_config,
                'axis': {**axis_config, 'range': [0, car_max]},
                'bar': {'color': '#2874A6'},
                'steps': [{'range': [0, car_km_equivalent], 'color': '#AED6F1'}],
                'threshold': {**gauge_config['threshold'], 'value': car_km_equivalent}
            }
        ),
        row=1, col=3
    )

    # 冷氣儀表（第二行第二列 - 位於第一行第1和第3列之間）
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=ac_hours,
            number={'font': number_font, 'suffix': ' 小時', 'valueformat': '.1f'},
            title={'text': '❄️減少吹冷氣小時數', 'font': title_font},
            gauge={
                **gauge_config,
                'axis': {**axis_config, 'range': [0, ac_max]},
                'bar': {'color': '#5DADE2'},
                'steps': [{'range': [0, ac_hours], 'color': '#D4EDDA'}],
                'threshold': {**gauge_config['threshold'], 'value': ac_hours}
            }
        ),
        row=2, col=2
    )

    # 手機充電儀表（第二行第四列 - 位於第一行第3和第5列之間）
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=phone_charges,
            number={'font': number_font, 'suffix': ' 次', 'valueformat': '.0f'},
            title={'text': '📱減少手機充電次數', 'font': title_font},
            gauge={
                **gauge_config,
                'axis': {**axis_config, 'range': [0, phone_max]},
                'bar': {'color': '#F39C12'},
                'steps': [{'range': [0, phone_charges], 'color': '#FCF3CF'}],
                'threshold': {**gauge_config['threshold'], 'value': phone_charges}
            }
        ),
        row=2, col=3
    )

    # 更新布局
    fig.update_layout(
        height=500,  # 大幅增加高度
        showlegend=False,
        title={
            'text': "<b>環保效益視覺化</b>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 32, 'color': '#2E4053'}
        },
        margin=dict(l=40, r=40, t=100, b=20),  # 增加邊距給更多空間
        paper_bgcolor='rgba(255,255,255,0.8)',
        plot_bgcolor='rgba(255,255,255,0.8)',
        font={'family': 'Arial', 'size': 14, 'color': '#2E4053'}
    )

    return fig
