"""
ReviveAI 應用程式的業務邏輯處理模組
包含所有 API 調用、數據處理和輔助函數
"""

import gradio as gr
import requests
import json
import os

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
    """
    if image is None:
        yield {"error": "請上傳商品圖片"}, None, None, None, None, None
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
                    metadata_received = True
                    
                    # 傳遞初始元數據，不包含文案內容
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis, "", "", carbon_text, search_results
                
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
                    }, image_analysis, current_title, current_content, carbon_text, search_results
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    # 處理碳足跡文本表示
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    
                    # 將文案內容分拆為不同部分
                    content_sections = split_content_sections(content_chunks)
                    
                    # 最終更新
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": True,
                        "completed": True
                    }, image_analysis, content_sections["title"], content_sections["basic_info"], carbon_text, search_results
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None, None, None, None, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None, None, None, None, None

# ================================= 社群賣文功能 =================================
def process_selling_post(description, image, price, contact_info, trade_method, style, progress=gr.Progress()):
    """
    處理社群賣文功能，調用 API 並處理串流回應
    """
    progress(0, desc="準備請求...")
    
    if image is None:
        return {"error": "請上傳商品圖片"}, None, None
    
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
        progress(0.1, desc="正在連接 API...")
        response = requests.post(
            f"{API_BASE_URL}/combined_service/selling_post",
            files=files,
            data=data,
            stream=True
        )
        
        # 初始化結果變數
        image_analysis = ""
        carbon_footprint = None
        content_chunks = ""
        is_first_chunk = True
        progress_value = 0.2
        
        progress(progress_value, desc="正在處理回應...")
        
        # 處理串流回應
        for line in response.iter_lines():
            if line:
                # 解析 JSON 回應
                chunk_data = json.loads(line.decode('utf-8'))
                
                # 處理元數據部分
                if chunk_data.get("type") == "metadata":
                    image_analysis = chunk_data.get("image_analysis", "")
                    carbon_footprint = chunk_data.get("carbon_footprint", {})
                    progress_value = 0.4
                    progress(progress_value, desc="接收圖片分析和碳足跡資料...")
                
                # 處理內容部分
                elif chunk_data.get("type") == "content":
                    content = chunk_data.get("chunk", "")
                    content_chunks += content
                    progress_value = min(progress_value + 0.02, 0.9)
                    progress(progress_value, desc="接收文案內容...")
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    progress(1.0, desc="完成！")
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    return {"error": error_msg}, None, None
        
        # 處理碳足跡文本表示
        carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
        
        progress(1.0, desc="處理完成！")
        return {
            "success": True,
            "full_content": content_chunks  # 完整文案，用於複製
        }, image_analysis, carbon_text
    
    except Exception as e:
        return {"error": f"發生錯誤: {str(e)}"}, None, None

# ================================= 社群徵文功能 =================================
def process_seeking_post(product_description, purpose, expected_price, contact_info, trade_method, 
                        seeking_type, deadline, image, style, progress=gr.Progress()):
    """
    處理社群徵文功能，調用 API 並處理串流回應
    """
    progress(0, desc="準備請求...")
    
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
        progress(0.1, desc="正在連接 API...")
        response = requests.post(
            f"{API_BASE_URL}/combined_service/seeking_post",
            files=files,
            data=data,
            stream=True
        )
        
        # 初始化結果變數
        image_analysis = ""
        content_chunks = ""
        is_first_chunk = True
        progress_value = 0.2
        
        progress(progress_value, desc="正在處理回應...")
        
        # 處理串流回應
        for line in response.iter_lines():
            if line:
                # 解析 JSON 回應
                chunk_data = json.loads(line.decode('utf-8'))
                
                # 處理元數據部分
                if chunk_data.get("type") == "metadata":
                    image_analysis = chunk_data.get("image_analysis", "")
                    progress_value = 0.4
                    progress(progress_value, desc="接收圖片分析資料...")
                
                # 處理內容部分
                elif chunk_data.get("type") == "content":
                    content = chunk_data.get("chunk", "")
                    content_chunks += content
                    progress_value = min(progress_value + 0.02, 0.9)
                    progress(progress_value, desc="接收文案內容...")
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    progress(1.0, desc="完成！")
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    return {"error": error_msg}, None
        
        progress(1.0, desc="處理完成！")
        return {
            "success": True,
            "full_content": content_chunks  # 完整文案，用於複製
        }, image_analysis
    
    except Exception as e:
        return {"error": f"發生錯誤: {str(e)}"}, None

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
    return [None, "", "normal", None, None, None, None, None, None,
            None, "", "", "請私訊詳詢", "面交/郵寄皆可", "normal", None, None, None,
            "", "", "", "請私訊詳詢", "面交/郵寄皆可", "buy", "越快越好", None, "normal", None, None]
