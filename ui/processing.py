"""
ReviveAI 應用程式的業務邏輯處理模組
包含所有 API 調用、數據處理和輔助函數
"""

import gradio as gr
import requests
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 設定 API 基礎 URL
API_BASE_URL = "http://localhost:8000"  # 請根據您的實際設置修改

# ================================= 拍賣網站功能 =================================
def process_online_sale(description, image, style):
    """
    處理拍賣網站文案功能，調用 API 並處理串流回應
    
    返回組件:
    1. online_result_json: 完整結果的 JSON
    2. online_image_analysis: 圖片分析結果
    3. online_title: 優化的商品標題
    4. online_basic_info: 即時更新的商品詳細文案
    5. online_carbon: 碳足跡分析
    6. online_search: 網路搜尋結果
    7. online_carbon_chart: 碳足跡圖表
    """
    if image is None:
        yield {"error": "請上傳商品圖片"}, None, None, None, None, None, None
        return
    
    try:
        # 準備檔案和表單資料
        files = {'image': (os.path.basename(image), open(image, 'rb'), 'image/jpeg')}
        data = {
            'description': description or "",
            'style': style
        }
        
        # 創建串流請求
        response = requests.post(
            f"{API_BASE_URL}/combined_service/online_sale_stream",
            files=files,
            data=data,
            stream=True
        )
        
        # 初始化結果變數
        image_analysis = ""
        carbon_footprint = None
        search_results = ""
        content_chunks = ""
        current_title = ""
        metadata_received = False
        streaming_started = False
        
        # 處理串流回應
        for line in response.iter_lines():
            if line:
                # 解析 JSON 回應
                chunk_data = json.loads(line.decode('utf-8'))
                
                # 處理元數據部分
                if chunk_data.get("type") == "metadata":
                    image_analysis = chunk_data.get("image_analysis", "")
                    search_results = chunk_data.get("search_results", "")
                    carbon_footprint = chunk_data.get("carbon_footprint", {})
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    metadata_received = True
                    
                    # 傳遞初始元數據，不包含文案內容
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis, "", "", carbon_text, search_results, carbon_chart
                
                # 處理內容部分
                elif chunk_data.get("type") == "content":
                    content = chunk_data.get("chunk", "")
                    content_chunks += content
                    
                    # 第一次接收內容時標記串流開始
                    if not streaming_started:
                        streaming_started = True
                    
                    # 處理目前已有的內容
                    current_sections = split_content_sections(content_chunks)
                    current_title = current_sections["title"]
                    current_content = current_sections["basic_info"]
                    
                    # 即時返回更新的內容
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": streaming_started
                    }, image_analysis, current_title, current_content, carbon_text, search_results, carbon_chart
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    # 處理碳足跡文本表示和圖表
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    
                    # 將文案內容分拆為不同部分
                    content_sections = split_content_sections(content_chunks)
                    
                    # 最終更新
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": True,
                        "completed": True
                    }, image_analysis, content_sections["title"], content_sections["basic_info"], carbon_text, search_results, carbon_chart
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None, None, None, None, None, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None, None, None, None, None, None

# ================================= 社群賣文功能 =================================
def process_selling_post(description, image, price, contact_info, trade_method, style):
    """
    處理社群賣文功能，調用 API 並處理串流回應
    
    返回組件:
    1. selling_result_json: 完整結果的 JSON
    2. selling_image_analysis: 圖片分析結果
    3. selling_carbon: 碳足跡分析
    4. selling_carbon_chart: 碳足跡圖表
    5. selling_search: 網路搜尋結果
    """
    if image is None:
        yield {"error": "請上傳商品圖片"}, None, None, None, None
        return
    
    try:
        # 準備檔案和表單資料
        files = {'image': (os.path.basename(image), open(image, 'rb'), 'image/jpeg')}
        data = {
            'description': description or "",
            'price': price,
            'contact_info': contact_info,
            'trade_method': trade_method,
            'style': style,
            'stream': True  # 使用串流模式
        }
        
        # 創建串流請求
        response = requests.post(
            f"{API_BASE_URL}/combined_service/selling_post",
            files=files,
            data=data,
            stream=True
        )
        
        # 初始化結果變數
        image_analysis = ""
        carbon_footprint = None
        search_results = ""
        content_chunks = ""
        metadata_received = False
        streaming_started = False
        
        # 處理串流回應
        for line in response.iter_lines():
            if line:
                # 解析 JSON 回應
                chunk_data = json.loads(line.decode('utf-8'))
                
                # 處理元數據部分
                if chunk_data.get("type") == "metadata":
                    image_analysis = chunk_data.get("image_analysis", "")
                    carbon_footprint = chunk_data.get("carbon_footprint", {})
                    search_results = chunk_data.get("search_results", "")
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    metadata_received = True
                    
                    # 傳遞初始元數據，不包含文案內容
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis, carbon_text, carbon_chart, search_results
                
                # 處理內容部分
                elif chunk_data.get("type") == "content":
                    content = chunk_data.get("chunk", "")
                    content_chunks += content
                    
                    # 第一次接收內容時標記串流開始
                    if not streaming_started:
                        streaming_started = True
                    
                    # 即時返回更新的內容
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": streaming_started
                    }, image_analysis, carbon_text, carbon_chart, search_results
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    # 處理碳足跡文本表示和圖表
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    
                    # 最終更新
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": True,
                        "completed": True
                    }, image_analysis, carbon_text, carbon_chart, search_results
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None, None, None, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None, None, None, None

# ================================= 社群徵文功能 =================================
def process_seeking_post(product_description, purpose, expected_price, contact_info, trade_method, 
                        seeking_type, deadline, image, style):
    """
    處理社群徵文功能，調用 API 並處理串流回應
    
    返回組件:
    1. seeking_result_json: 完整結果的 JSON
    2. seeking_image_analysis: 圖片分析結果
    """
    try:
        # 準備表單資料
        data = {
            'product_description': product_description,
            'purpose': purpose,
            'expected_price': expected_price,
            'contact_info': contact_info,
            'trade_method': trade_method,
            'seeking_type': seeking_type,
            'deadline': deadline,
            'style': style,
            'stream': True  # 使用串流模式
        }
        
        # 準備文件資料（如有）
        files = {}
        if image:
            files = {'image': (os.path.basename(image), open(image, 'rb'), 'image/jpeg')}
        
        # 創建串流請求
        response = requests.post(
            f"{API_BASE_URL}/combined_service/seeking_post",
            files=files,
            data=data,
            stream=True
        )
        
        # 初始化結果變數
        image_analysis = ""
        content_chunks = ""
        metadata_received = False
        streaming_started = False
        
        # 處理串流回應
        for line in response.iter_lines():
            if line:
                # 解析 JSON 回應
                chunk_data = json.loads(line.decode('utf-8'))
                
                # 處理元數據部分
                if chunk_data.get("type") == "metadata":
                    image_analysis = chunk_data.get("image_analysis", "")
                    metadata_received = True
                    
                    # 傳遞初始元數據，不包含文案內容
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis
                
                # 處理內容部分
                elif chunk_data.get("type") == "content":
                    content = chunk_data.get("chunk", "")
                    content_chunks += content
                    
                    # 第一次接收內容時標記串流開始
                    if not streaming_started:
                        streaming_started = True
                    
                    # 即時返回更新的內容
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": streaming_started
                    }, image_analysis
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    # 最終更新
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": True,
                        "completed": True
                    }, image_analysis
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None

# ================================= 輔助函數 =================================
def split_content_sections(content):
    """
    將文案內容分拆為不同部分，去掉basic_info中重複的標題部分
    """
    sections = {
        "title": "",
        "basic_info": ""
    }
    
    # 找出標題部分（第一個#後面的內容）
    lines = content.split('\n')
    title_section_end = 0
    
    for i, line in enumerate(lines):
        if line.startswith("# 優化商品標題"):
            # 尋找標題內容
            for j in range(i+1, len(lines)):
                if not lines[j].strip():
                    continue
                if lines[j].startswith("#"):
                    title_section_end = j
                    break
                sections["title"] = lines[j].strip()
                title_section_end = j + 1
                break
            break
    
    # 組合排除了標題部分的商品詳細內容
    if title_section_end > 0:
        sections["basic_info"] = '\n'.join(lines[title_section_end:])
    else:
        sections["basic_info"] = content
    
    return sections

def create_environmental_gauges(saved_carbon, tree_equivalent, car_km_equivalent):
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

    # 計算每個儀表的最大範圍（統一使用 1.5 倍）
    carbon_max = saved_carbon * 1.4
    tree_max = tree_equivalent * 1.5
    car_max = car_km_equivalent * 1.45

    # 創建三個子圖
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
        horizontal_spacing=0.1  # 增加水平间距
    )

    # 定義共用的字體樣式
    title_font = {'family': 'Arial', 'size': 18, 'color': '#2E4053'}
    number_font = {'family': 'Arial', 'size': 22, 'color': '#2E4053'}

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

    # 減碳量儀表
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

    # 樹木數量儀表
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

    # 更新布局
    fig.update_layout(
        height=250,
        width=750,  # 設定固定寬度
        showlegend=False,
        title={
            'text': "<b>環保效益視覺化</b>",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Arial', 'size': 28, 'color': '#2E4053'}
        },
        margin=dict(l=40, r=40, t=70, b=70),  # 左右邊距
        paper_bgcolor='rgba(255,255,255,0.8)',
        plot_bgcolor='rgba(255,255,255,0.8)',
        font={'family': 'Arial', 'size': 14, 'color': '#2E4053'}
    )

    return fig

def create_carbon_chart(carbon_data):
    """
    根據碳足跡數據創建 plotly 圖表
    """
    if not carbon_data:
        return None
    
    try:
        # 從碳足跡數據中提取環境效益
        benefits = carbon_data.get("environmental_benefits", {})
        saved_carbon = carbon_data.get("saved_carbon", 0)
        
        # 提取各項效益值
        trees = benefits.get('trees', '0')
        car_km = benefits.get('car_km', '0')
        
        # 創建環保效益儀表板
        return create_environmental_gauges(saved_carbon, trees, car_km)
    
    except Exception as e:
        print(f"創建碳足跡圖表時發生錯誤: {e}")
        return None

def format_carbon_footprint(carbon_data):
    """
    格式化碳足跡數據為易讀文本
    """
    if not carbon_data:
        return "無法計算碳足跡"
    
    selected_product = carbon_data.get("selected_product", {})
    saved_carbon = carbon_data.get("saved_carbon", 0)
    benefits = carbon_data.get("environmental_benefits", {})
    
    text = f"## 碳足跡分析\n\n"
    text += f"- **選定商品**: {selected_product.get('product_name', '未知')}\n"
    text += f"- **公司**: {selected_product.get('company', '未知')}\n"
    text += f"- **原始碳足跡**: {selected_product.get('carbon_footprint', 0):.2f} kg CO2e\n"
    text += f"- **節省的碳排放**: {saved_carbon:.2f} kg CO2e\n\n"
    
    text += "## 環境效益\n\n"
    text += f"- 相當於 {benefits.get('trees', '0')} 棵樹一年的吸碳量\n"
    text += f"- 相當於減少開車 {benefits.get('car_km', '0')} 公里的碳排放\n"
    text += f"- 相當於減少吹冷氣 {benefits.get('ac_hours', '0')} 小時的碳排放\n"
    text += f"- 相當於減少手機充電 {benefits.get('phone_charges', '0')} 次的碳排放\n"
    
    return text

def reset_all():
    """
    重置所有輸入和輸出
    """
    # 按照 app.py 中 reset_btn.click 的 outputs 順序返回重置值
    return [
        # online_image, online_desc, online_style, online_result_json, online_image_analysis, 
        # online_title, online_basic_info, online_carbon, online_search, online_usage_time, 
        # online_condition, online_brand, online_original_price, online_carbon_chart,
        None, "", "normal", None, None,  # online 前5個
        None, None, None, None, 2,  # online 後5個 (usage_time 預設為 2)
        "八成新", "", "", None,  # online 表單元件 (condition, brand, original_price, carbon_chart)
        
        # selling_image, selling_desc, selling_price, selling_contact, selling_trade, 
        # selling_style, selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search, selling_content
        None, "", "", "請私訊詳詢", "面交/郵寄皆可",  # selling 前5個
        "normal", None, None, None, None, None, "",  # selling 後7個 (包含 carbon_chart, selling_search, selling_content)
        
        # seeking_desc, seeking_purpose, seeking_price, seeking_contact, seeking_trade,
        # seeking_type, seeking_deadline, seeking_image, seeking_style, seeking_result_json,
        # seeking_image_analysis, seeking_content
        "", "", "", "請私訊詳詢", "面交/郵寄皆可",  # seeking 前5個
        "buy", "越快越好", None, "normal", None,  # seeking 中5個
        None, ""  # seeking_image_analysis, seeking_content
    ]
