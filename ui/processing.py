"""
ReviveAI 應用程式的業務邏輯處理模組
包含所有 API 調用、數據處理和輔助函數
"""

import requests
import json
import os
import re
from charts import create_environmental_gauges

# 設定 API 基礎 URL
API_BASE_URL = "http://localhost:8000"  # 請根據您的實際設置修改

# ================================= 中文轉英文映射 =================================
def convert_chinese_to_english(value, mapping_type):
    """
    將中文選項轉換為對應的英文代碼
    
    Args:
        value: 中文選項值
        mapping_type: 映射類型 ('online_style', 'selling_style', 'seeking_style', 'seeking_type')
    
    Returns:
        對應的英文代碼
    """
    mappings = {
        'online_style': {
            '標準專業': 'normal',
            '輕鬆活潑': 'casual', 
            '正式商務': 'formal',
            '故事體驗': 'story'
        },
        'selling_style': {
            '標準實用': 'normal',
            '故事體驗': 'storytelling',
            '簡約精要': 'minimalist',
            '超值優惠': 'bargain'
        },
        'seeking_style': {
            '標準親切': 'normal',
            '急需緊急': 'urgent',
            '預算有限': 'budget',
            '收藏愛好': 'collector'
        },
        'seeking_type': {
            '購買': 'buy',
            '租借': 'rent'
        }
    }
    
    mapping = mappings.get(mapping_type, {})
    return mapping.get(value, value)  # 如果找不到映射，返回原值

# ================================= 拍賣網站功能 =================================
def process_online_sale(description, image, style, generate_image=False):
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
    8. online_beautified_image: AI 美化圖片路徑
    """
    if image is None:
        yield {"error": "請上傳商品圖片"}, None, None, None, None, None, None, None
        return
    
    try:
        # 轉換中文風格選項為英文代碼
        english_style = convert_chinese_to_english(style, 'online_style')
        
        # 準備檔案和表單資料
        files = {'image': (os.path.basename(image), open(image, 'rb'), 'image/jpeg')}
        data = {
            'description': description or "",
            'style': english_style,
            'generate_image': generate_image
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
        beautified_image_path = None
        
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
                    beautified_image_path = chunk_data.get("beautified_image", None)
                    # 將相對路徑轉換為絕對路徑，並統一路徑分隔符
                    if beautified_image_path:
                        beautified_image_path = os.path.abspath(beautified_image_path).replace('\\', '/')
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    metadata_received = True
                    
                    # 傳遞初始元數據，不包含文案內容
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis, "", "", carbon_text, search_results, carbon_chart, beautified_image_path
                
                # 處理內容部分
                elif chunk_data.get("type") == "content":
                    content = chunk_data.get("chunk", "")
                    content_chunks += content
                    
                    # 第一次接收內容時標記串流開始
                    if not streaming_started:
                        streaming_started = True
                    
                    # 處理目前已有的內容，使用純文字格式
                    current_sections = split_content_sections(content_chunks)
                    current_title = current_sections["title_plain"]  # 使用純文字標題
                    current_content = current_sections["basic_info_plain"]  # 使用純文字內容
                    
                    # 即時返回更新的內容
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": streaming_started
                    }, image_analysis, current_title, current_content, carbon_text, search_results, carbon_chart, beautified_image_path
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    # 處理碳足跡文本表示和圖表
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    
                    # 將文案內容分拆為不同部分，使用純文字格式
                    content_sections = split_content_sections(content_chunks)
                    
                    # 最終更新，使用純文字格式
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": True,
                        "completed": True
                    }, image_analysis, content_sections["title_plain"], content_sections["basic_info_plain"], carbon_text, search_results, carbon_chart, beautified_image_path
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None, None, None, None, None, None, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None, None, None, None, None, None, None

# ================================= 社群賣文功能 =================================
def process_selling_post(description, image, price, contact_info, trade_method, style, generate_image=False):
    """
    處理社群賣文功能，調用 API 並處理串流回應
    
    返回組件:
    1. selling_result_json: 完整結果的 JSON
    2. selling_image_analysis: 圖片分析結果
    3. selling_carbon: 碳足跡分析
    4. selling_carbon_chart: 碳足跡圖表
    5. selling_search: 網路搜尋結果
    6. selling_beautified_image: AI 美化圖片路徑
    """
    if image is None:
        yield {"error": "請上傳商品圖片"}, None, None, None, None, None
        return
    
    try:
        # 轉換中文風格選項為英文代碼
        english_style = convert_chinese_to_english(style, 'selling_style')
        
        # 準備檔案和表單資料
        files = {'image': (os.path.basename(image), open(image, 'rb'), 'image/jpeg')}
        data = {
            'description': description or "",
            'price': price,
            'contact_info': contact_info,
            'trade_method': trade_method,
            'style': english_style,
            'stream': True,  # 使用串流模式
            'generate_image': generate_image
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
        beautified_image_path = None
        
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
                    beautified_image_path = chunk_data.get("beautified_image", None)
                    # 將相對路徑轉換為絕對路徑，並統一路徑分隔符
                    if beautified_image_path:
                        beautified_image_path = os.path.abspath(beautified_image_path).replace('\\', '/')
                    carbon_text = format_carbon_footprint(carbon_footprint) if carbon_footprint else ""
                    carbon_chart = create_carbon_chart(carbon_footprint) if carbon_footprint else None
                    metadata_received = True
                    
                    # 傳遞初始元數據，不包含文案內容
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis, carbon_text, carbon_chart, search_results, beautified_image_path
                
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
                    }, image_analysis, carbon_text, carbon_chart, search_results, beautified_image_path
                
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
                    }, image_analysis, carbon_text, carbon_chart, search_results, beautified_image_path
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None, None, None, None, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None, None, None, None, None

# ================================= 社群徵文功能 =================================
def process_seeking_post(product_description, purpose, expected_price, contact_info, trade_method, 
                        seeking_type, deadline, image, style, generate_image=False):
    """
    處理社群徵文功能，調用 API 並處理串流回應
    
    返回組件:
    1. seeking_result_json: 完整結果的 JSON
    2. seeking_image_analysis: 圖片分析結果
    3. seeking_generated_image: 生成的圖片路徑（如果有）
    """
    try:
        # 轉換中文選項為英文代碼
        english_seeking_type = convert_chinese_to_english(seeking_type, 'seeking_type')
        english_style = convert_chinese_to_english(style, 'seeking_style')
        
        # 準備表單資料
        data = {
            'product_description': product_description,
            'purpose': purpose,
            'expected_price': expected_price,
            'contact_info': contact_info,
            'trade_method': trade_method,
            'seeking_type': english_seeking_type,
            'deadline': deadline,
            'style': english_style,
            'stream': True,  # 使用串流模式
            'generate_image': generate_image  # 新增生成圖片選項
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
        generated_image_path = None
        
        # 處理串流回應
        for line in response.iter_lines():
            if line:
                # 解析 JSON 回應
                chunk_data = json.loads(line.decode('utf-8'))
                
                # 處理元數據部分
                if chunk_data.get("type") == "metadata":
                    image_analysis = chunk_data.get("image_analysis", "")
                    generated_image_path = chunk_data.get("generated_image", None)
                    # 將相對路徑轉換為絕對路徑，並統一路徑分隔符
                    if generated_image_path:
                        generated_image_path = os.path.abspath(generated_image_path).replace('\\', '/')
                    metadata_received = True
                    
                    # 傳遞初始元數據
                    yield {
                        "success": True,
                        "full_content": "",
                        "streaming_started": False
                    }, image_analysis, generated_image_path
                
                # 處理圖片更新
                elif chunk_data.get("type") == "image_update":
                    updated_image_path = chunk_data.get("generated_image", None)
                    if updated_image_path:
                        # 將相對路徑轉換為絕對路徑，並統一路徑分隔符
                        updated_image_path = os.path.abspath(updated_image_path).replace('\\', '/')
                        generated_image_path = updated_image_path
                        # 發送圖片更新，但保持文案內容不變
                        yield {
                            "success": True,
                            "full_content": content_chunks,
                            "streaming_started": streaming_started,
                            "image_updated": True
                        }, image_analysis, generated_image_path
                
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
                    }, image_analysis, generated_image_path
                
                # 處理結束標記
                elif chunk_data.get("type") == "end":
                    # 最終更新
                    yield {
                        "success": True,
                        "full_content": content_chunks,
                        "streaming_started": True,
                        "completed": True
                    }, image_analysis, generated_image_path
                    break
                
                # 處理錯誤
                elif chunk_data.get("type") == "error":
                    error_msg = chunk_data.get("error", "未知錯誤")
                    yield {"error": error_msg}, None, None
                    return
    
    except Exception as e:
        yield {"error": f"發生錯誤: {str(e)}"}, None, None

# ================================= 輔助函數 =================================
def convert_markdown_to_plain_text(content):
    """
    將 markdown 格式轉換為適合拍賣平台的純文字格式
    
    Args:
        content (str): 包含 markdown 格式的文案內容
        
    Returns:
        str: 轉換後的純文字格式
    """
    if not content:
        return ""
    
    # 先處理粗體格式 **文字** -> 移除星號
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    
    lines = content.split('\n')
    converted_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳過空行
        if not line:
            i += 1
            continue
            
        # 處理一級標題 (# 標題)
        if line.startswith('# '):
            title = line[2:].strip()
            # 跳過 "優化商品標題" 這個標題，因為會單獨顯示
            if title == "優化商品標題":
                i += 1
                continue
            
            # 如果前面有內容，加空行分隔
            if converted_lines and converted_lines[-1] != "":
                converted_lines.append("")
            
            converted_lines.append(f"◆ {title}")
            
            # 檢查下一行是否有內容，如果有則添加空行
            if i + 1 < len(lines) and lines[i + 1].strip():
                converted_lines.append("")
            
        # 處理二級標題 (## 標題)
        elif line.startswith('## '):
            title = line[3:].strip()
            
            # 如果前面有內容，加空行分隔
            if converted_lines and converted_lines[-1] != "":
                converted_lines.append("")
            
            converted_lines.append(f"▶ {title}")
            
            # 檢查下一行是否有內容，如果有則添加空行
            if i + 1 < len(lines) and lines[i + 1].strip():
                converted_lines.append("")
            
        # 處理三級標題 (### 標題)
        elif line.startswith('### '):
            title = line[4:].strip()
            
            # 如果前面有內容，加空行分隔
            if converted_lines and converted_lines[-1] != "":
                converted_lines.append("")
            
            converted_lines.append(f"• {title}")
            
            # 檢查下一行是否有內容，如果有則添加空行
            if i + 1 < len(lines) and lines[i + 1].strip():
                converted_lines.append("")
            
        # 處理列表項目 (- 或 • 開頭)
        elif line.startswith('- ') or line.startswith('• '):
            item = line[2:].strip()
            converted_lines.append(f"• {item}")
            
            # 檢查後面是否有標題或其他非列表內容，如果有則加空行
            next_line_index = i + 1
            while next_line_index < len(lines) and not lines[next_line_index].strip():
                next_line_index += 1
            
            if (next_line_index < len(lines) and 
                lines[next_line_index].strip() and
                not lines[next_line_index].strip().startswith(('- ', '• ')) and
                not lines[next_line_index].strip()[0].isdigit()):
                # 如果下個非空行不是列表項目且不是數字列表，則加空行
                converted_lines.append("")
            
        # 處理數字列表 (1. 2. 等)
        elif line and line[0].isdigit() and '. ' in line:
            converted_lines.append(line)
            
            # 檢查後面是否有標題或其他非列表內容，如果有則加空行
            next_line_index = i + 1
            while next_line_index < len(lines) and not lines[next_line_index].strip():
                next_line_index += 1
            
            if (next_line_index < len(lines) and 
                lines[next_line_index].strip() and
                not lines[next_line_index].strip()[0].isdigit() and
                not lines[next_line_index].strip().startswith(('- ', '• '))):
                # 如果下個非空行不是數字列表且不是項目列表，則加空行
                converted_lines.append("")
            
        # 處理 hashtag (以 # 結尾的行)
        elif line.startswith('#') and not line.startswith('# '):
            converted_lines.append(line)
            
        # 處理普通文字行
        else:
            converted_lines.append(line)
        
        i += 1
    
    # 清理多餘的連續空行，最多保留一個空行
    final_lines = []
    prev_was_empty = False
    
    for line in converted_lines:
        if line == "":
            if not prev_was_empty:
                final_lines.append(line)
                prev_was_empty = True
        else:
            final_lines.append(line)
            prev_was_empty = False
    
    # 移除開頭和結尾的空行
    while final_lines and final_lines[0] == "":
        final_lines.pop(0)
    while final_lines and final_lines[-1] == "":
        final_lines.pop()
    
    return '\n'.join(final_lines)

def split_content_sections(content):
    """
    將文案內容分拆為不同部分，返回 markdown 和純文字兩種格式
    """
    sections = {
        "title": "",
        "basic_info": "",
        "title_plain": "",
        "basic_info_plain": ""
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
                sections["title_plain"] = lines[j].strip()  # 標題本身不需要特殊轉換
                title_section_end = j + 1
                break
            break
    
    # 組合排除了標題部分的商品詳細內容
    basic_info_markdown = ""
    if title_section_end > 0:
        basic_info_markdown = '\n'.join(lines[title_section_end:])
    else:
        basic_info_markdown = content
    
    sections["basic_info"] = basic_info_markdown
    sections["basic_info_plain"] = convert_markdown_to_plain_text(basic_info_markdown)
    
    return sections

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
        ac_hours = benefits.get('ac_hours', '0')
        phone_charges = benefits.get('phone_charges', '0')
        
        # 創建環保效益儀表板（傳遞所有五個參數）
        return create_environmental_gauges(saved_carbon, trees, car_km, ac_hours, phone_charges)
    
    except Exception as e:
        print(f"創建碳足跡圖表時發生錯誤: {e}")
        return None

def format_carbon_footprint(carbon_data):
    """
    格式化碳足跡數據為易讀文本，包含搜尋參數和候選產品列表
    """
    if not carbon_data:
        return "無法計算碳足跡"
    
    selected_product = carbon_data.get("selected_product", {})
    saved_carbon = carbon_data.get("saved_carbon", 0)
    benefits = carbon_data.get("environmental_benefits", {})
    search_params = carbon_data.get("search_params", {})
    candidates = carbon_data.get("candidates", [])
    
    text = f"## 碳足跡分析\n\n"
    text += f"- **gpt rerank 選定商品**: {selected_product.get('product_name', '未知')}\n"
    text += f"- **公司**: {selected_product.get('company', '未知')}\n"
    text += f"- **原始碳足跡**: {selected_product.get('carbon_footprint', 0):.2f} kg CO2e\n"
    text += f"- **節省的碳排放**: {saved_carbon:.2f} kg CO2e\n\n"
    
    text += "## 環境效益\n\n"
    text += f"- 相當於 {benefits.get('trees', '0')} 棵樹一年的吸碳量\n"
    text += f"- 相當於減少開車 {benefits.get('car_km', '0')} 公里的碳排放\n"
    text += f"- 相當於減少吹冷氣 {benefits.get('ac_hours', '0')} 小時的碳排放\n"
    text += f"- 相當於減少手機充電 {benefits.get('phone_charges', '0')} 次的碳排放\n\n"
    
    # 新增搜尋參數部分
    if search_params:
        text += "## 智慧 Function calling 搜尋參數\n\n"
        text += f"- **搜尋關鍵字**: {search_params.get('query_text', '未知')}\n"
        if search_params.get('min_carbon_footprint') is not None:
            text += f"- **最小碳足跡**: {search_params.get('min_carbon_footprint')} kg CO2e\n"
        if search_params.get('max_carbon_footprint') is not None:
            text += f"- **最大碳足跡**: {search_params.get('max_carbon_footprint')} kg CO2e\n"
        if search_params.get('sector'):
            text += f"- **產業分類**: {search_params.get('sector')}\n"
        text += "\n"
    
    # 新增候選產品列表部分
    if candidates:
        text += f"## 候選產品列表 ({len(candidates)} 個)\n\n"
        for i, candidate in enumerate(candidates, 1):
            text += f"**{i}. {candidate.get('product_name', '未知')}**\n"
            text += f"   - 公司: {candidate.get('company', '未知')}\n"
            text += f"   - 碳足跡: {candidate.get('carbon_footprint', 0)} kg CO2e\n"
            text += f"   - 產業類別: {candidate.get('sector', '未知')}\n"
            text += f"   - 相似度分數: {candidate.get('similarity_score', 0):.4f}\n\n"
    
    return text

def reset_all():
    """
    重置所有輸入和輸出
    """
    # 按照 app.py 中 reset_btn.click 的 outputs 順序返回重置值
    return [
        # online 區塊: online_image, online_product_name, online_desc, online_style, online_result_json, online_image_analysis, 
        # online_title, online_basic_info, online_carbon, online_search, online_usage_time, 
        # online_condition, online_brand, online_carbon_chart, online_generate_image, online_beautified_image
        None, "", "", "標準專業", None, None,  # online_image, online_product_name, online_desc, online_style, online_result_json, online_image_analysis
        None, None, None, None, 2,  # online_title, online_basic_info, online_carbon, online_search, online_usage_time
        "八成新", "", None, False, None,  # online_condition, online_brand, online_carbon_chart, online_generate_image, online_beautified_image
        
        # selling 區塊: selling_image, selling_product_name, selling_desc, selling_price, selling_contact, selling_trade, 
        # selling_usage_time, selling_condition, selling_brand,
        # selling_style, selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search, selling_content, selling_generate_image, selling_beautified_image
        None, "", "", "", "請私訊詳詢", "面交/郵寄皆可",  # selling_image, selling_product_name, selling_desc, selling_price, selling_contact, selling_trade
        2, "八成新", "",  # selling_usage_time, selling_condition, selling_brand
        "標準實用", None, None, None, None, None, "", False, None,  # selling_style, selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search, selling_content, selling_generate_image, selling_beautified_image
        
        # seeking 區塊: seeking_product_name, seeking_desc, seeking_purpose, seeking_price, seeking_contact, seeking_trade,
        # seeking_type, seeking_deadline, seeking_image, seeking_style, seeking_generate_image, seeking_result_json,
        # seeking_image_analysis, seeking_content, seeking_generated_image
        "", "", "", "", "請私訊詳詢", "面交/郵寄皆可",  # seeking_product_name, seeking_desc, seeking_purpose, seeking_price, seeking_contact, seeking_trade
        "購買", "越快越好", None, "標準親切", False, None,  # seeking_type, seeking_deadline, seeking_image, seeking_style, seeking_generate_image, seeking_result_json
        None, "", None  # seeking_image_analysis, seeking_content, seeking_generated_image
    ]
