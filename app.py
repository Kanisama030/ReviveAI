import gradio as gr
import requests
import json
import time
import os

# 設定 API 基礎 URL
API_BASE_URL = "http://localhost:8000"  # 請根據您的實際設置修改

# 自定義 CSS 樣式
css = """
:root {
    --primary-color: #6de29c;  /* 淺綠色 */
    --button-color: #185947;   /* 深綠色 */
}

.gradio-container {
    background-color: #1a1a1a;  /* 深色背景 */
    color: #ffffff;
}

/* 自定義標籤頁選擇顏色 */
.tabs > .tab-nav > button.selected {
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
    background-color: rgba(109, 226, 156, 0.1) !important;
}

.tab-nav button.selected {
    color: var(--primary-color) !important; /* 被選中 Tab 的文字顏色 */
}

.tabs > .tab-nav > button:hover {
    color: var(--primary-color) !important;
}

.tabs {
    margin-bottom: 20px;
}

.reset-btn {
    background-color: #c62828 !important;
    color: white !important;
    border: none !important;
    padding: 8px 15px !important;  /* 增加上下內邊距 */
    font-size: 0.9em !important;
    margin-left: auto !important;
    float: right !important;
    width: 120px !important;  /* 固定寬度 */
    position: fixed !important;  /* 固定位置 */
    top: 15px !important;  /* 距離頂部距離 */
    right: 15px !important;  /* 距離右側距離 */
    z-index: 1000 !important;  /* 確保按鈕在其他元素之上 */
}

.submit-btn {
    background-color: var(--button-color) !important;
    color: white !important;
    border: none !important;
    font-size: 1.1em !important;
    padding: 10px 20px !important;
}

/* 自定義表單樣式 */
label {
    color: var(--primary-color) !important;
}

button:hover {
    box-shadow: 0 0 10px var(--primary-color) !important;
}

.footer-info {
    margin-top: 30px;
    padding: 20px;
    border-top: 1px solid var(--primary-color);
    text-align: left;
}
"""

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
    text += f"**選定商品**: {selected_product.get('product_name', '未知')}\n"
    text += f"**公司**: {selected_product.get('company', '未知')}\n"
    text += f"**原始碳足跡**: {selected_product.get('carbon_footprint', 0):.2f} kg CO2e\n"
    text += f"**節省的碳排放**: {saved_carbon:.2f} kg CO2e\n\n"
    
    text += "## 環境效益\n\n"
    text += f"- 相當於 {benefits.get('trees', '0')} 棵樹一年的吸碳量\n"
    text += f"- 相當於減少開車 {benefits.get('car_km', '0')} 公里的碳排放\n"
    text += f"- 相當於減少吹冷氣 {benefits.get('ac_hours', '0')} 小時的碳排放\n"
    text += f"- 相當於減少手機充電 {benefits.get('phone_charges', '0')} 次的碳排放\n"
    
    return text

def copy_to_clipboard(text):
    """
    複製文本到剪貼板的處理函數
    """
    return text

def reset_all():
    """
    重置所有輸入和輸出
    """
    return [None, "", "normal", None, None, None, None, None, None,
            None, "", "", "請私訊詳詢", "面交/郵寄皆可", "normal", None, None, None,
            "", "", "", "請私訊詳詢", "面交/郵寄皆可", "buy", "越快越好", None, "normal", None, None]
    
# ================================= 主應用程式 =================================
def create_app():
    # 初始化應用程式
    with gr.Blocks(css=css, theme=gr.themes.Base()) as app:
        # 添加頁面標題
        gr.Markdown("# ReviveAI - 二手商品優化系統", elem_classes=["page-title"])
        
        with gr.Row():
            # 右上角的重置按鈕
            reset_btn = gr.Button("重置所有輸入", variant="stop", elem_classes=["reset-btn"])
        
        # 主要標籤頁
        with gr.Tabs() as tabs:
            # =============== 拍賣網站 TAB ===============
            with gr.Tab("拍賣網站"):
                with gr.Row():
                    # 左側輸入區域
                    with gr.Column(scale=1):
                        online_image = gr.Image(label="上傳商品圖片", type="filepath")
                        online_desc = gr.Textbox(label="商品描述", placeholder="請輸入商品描述...", lines=5)
                        online_style = gr.Radio(
                            ["normal", "casual", "formal", "story"], 
                            label="文案風格", 
                            value="normal", 
                            info="normal=標準專業, casual=輕鬆活潑, formal=正式商務, story=故事體驗"
                        )
                        online_submit = gr.Button("生成拍賣文案", variant="primary", elem_classes=["submit-btn"])
                    
                    # 右側輸出區域
                    with gr.Column(scale=2):
                        with gr.Tabs() as online_output_tabs:
                            with gr.Tab("文案輸出"):
                                online_result_json = gr.JSON(visible=False)  # 儲存完整結果
                                online_title = gr.Textbox(label="優化商品標題", lines=2, interactive=False, show_copy_button=True)
                                online_basic_info = gr.Textbox(label="商品詳細內容", lines=15, interactive=False, show_copy_button=True)
                                
                            with gr.Tab("碳足跡"):
                                online_carbon = gr.Markdown()
                                
                            with gr.Tab("圖片分析"):
                                online_image_analysis = gr.Markdown(label="圖片分析結果")
                                
                            with gr.Tab("網路搜尋結果"):
                                online_search = gr.Markdown(label="網路搜尋結果")
                
                # 連接按鈕事件
                online_submit.click(
                    lambda: gr.update(interactive=False, value="生成中..."),
                    inputs=[],
                    outputs=[online_submit]
                ).then(
                    process_online_sale, 
                    inputs=[online_desc, online_image, online_style],
                    outputs=[online_result_json, online_image_analysis, online_title, online_basic_info, online_carbon, online_search]
                ).then(
                    lambda result: gr.update(interactive=True, value="生成拍賣文案") if result and ("success" in result or "error" in result) else gr.update(),
                    inputs=[online_result_json],
                    outputs=[online_submit]
                )
                
                # 複製按鈕事件
                
            # =============== 社群賣文 TAB ===============
            with gr.Tab("社群賣文"):
                with gr.Row():
                    # 左側輸入區域
                    with gr.Column(scale=1):
                        selling_image = gr.Image(label="上傳商品圖片", type="filepath")
                        selling_desc = gr.Textbox(label="商品描述", placeholder="請輸入商品描述...", lines=4)
                        selling_price = gr.Textbox(label="商品售價", placeholder="例如：$18,000")
                        selling_contact = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                        selling_trade = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                        selling_style = gr.Radio(
                            ["normal", "storytelling", "minimalist", "bargain"], 
                            label="文案風格", 
                            value="normal", 
                            info="normal=標準實用, storytelling=故事體驗, minimalist=簡約精要, bargain=超值優惠"
                        )
                        selling_submit = gr.Button("生成社群賣文", variant="primary", elem_classes=["submit-btn"])
                    
                    # 右側輸出區域
                    with gr.Column(scale=2):
                        with gr.Tabs() as selling_output_tabs:
                            with gr.Tab("文案輸出"):
                                selling_result_json = gr.JSON(visible=False)  # 儲存完整結果
                                selling_content = gr.Textbox(label="社群銷售文案", lines=15, interactive=False, show_copy_button=True)
                                selling_copy_btn = gr.Button("複製文案", variant="secondary", elem_classes=["copy-btn"])
                                
                            with gr.Tab("碳足跡"):
                                selling_carbon = gr.Markdown()
                                
                            with gr.Tab("圖片分析"):
                                selling_image_analysis = gr.Markdown(label="圖片分析結果")
                
                # 連接按鈕事件
                selling_submit.click(
                    process_selling_post, 
                    inputs=[selling_desc, selling_image, selling_price, selling_contact, selling_trade, selling_style],
                    outputs=[selling_result_json, selling_image_analysis, selling_carbon]
                ).then(
                    lambda x: x["full_content"] if x and "success" in x and x["success"] else "處理失敗，請檢查輸入",
                    inputs=[selling_result_json],
                    outputs=[selling_content]
                )
                
                # 複製按鈕事件
                selling_copy_btn.click(
                    lambda x: x, 
                    inputs=[selling_content], 
                    outputs=[]
                ).then(
                    None,
                    None,
                    None,
                    js="""
                    (content) => {
                        navigator.clipboard.writeText(content);
                        return [];
                    }
                    """
                )
            
            # =============== 社群徵文 TAB ===============
            with gr.Tab("社群徵文"):
                with gr.Row():
                    # 左側輸入區域
                    with gr.Column(scale=1):
                        seeking_desc = gr.Textbox(label="徵求商品描述", placeholder="請輸入想徵求的商品描述...", lines=3)
                        seeking_purpose = gr.Textbox(label="徵求目的", placeholder="請說明徵求目的...", lines=2)
                        seeking_price = gr.Textbox(label="期望價格", placeholder="例如：希望不超過 $5,000")
                        seeking_contact = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                        seeking_trade = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                        seeking_type = gr.Radio(
                            ["buy", "rent"], 
                            label="徵求類型", 
                            value="buy", 
                            info="buy=購買, rent=租借"
                        )
                        seeking_deadline = gr.Textbox(label="徵求時效", value="越快越好")
                        seeking_image = gr.Image(label="上傳參考圖片 (選填)", type="filepath")
                        seeking_style = gr.Radio(
                            ["normal", "urgent", "budget", "collector"], 
                            label="文案風格", 
                            value="normal", 
                            info="normal=標準親切, urgent=急需緊急, budget=預算有限, collector=收藏愛好"
                        )
                        seeking_submit = gr.Button("生成徵求文案", variant="primary", elem_classes=["submit-btn"])
                    
                    # 右側輸出區域
                    with gr.Column(scale=2):
                        with gr.Tabs() as seeking_output_tabs:
                            with gr.Tab("文案輸出"):
                                seeking_result_json = gr.JSON(visible=False)  # 儲存完整結果
                                seeking_content = gr.Textbox(label="社群徵求文案", lines=15, interactive=False, show_copy_button=True)
                                seeking_copy_btn = gr.Button("複製文案", variant="secondary", elem_classes=["copy-btn"])
                                
                            with gr.Tab("圖片分析"):
                                seeking_image_analysis = gr.Markdown(label="參考圖片分析結果")
                
                # 連接按鈕事件
                seeking_submit.click(
                    process_seeking_post, 
                    inputs=[
                        seeking_desc, seeking_purpose, seeking_price, seeking_contact, 
                        seeking_trade, seeking_type, seeking_deadline, seeking_image, seeking_style
                    ],
                    outputs=[seeking_result_json, seeking_image_analysis]
                ).then(
                    lambda x: x["full_content"] if x and "success" in x and x["success"] else "處理失敗，請檢查輸入",
                    inputs=[seeking_result_json],
                    outputs=[seeking_content]
                )
                
                # 複製按鈕事件
                seeking_copy_btn.click(
                    lambda x: x, 
                    inputs=[seeking_content], 
                    outputs=[]
                ).then(
                    None,
                    None,
                    None,
                    js="""
                    (content) => {
                        navigator.clipboard.writeText(content);
                        return [];
                    }
                    """
                )
        
        # 重置按鈕事件
        reset_btn.click(
            reset_all,
            inputs=[],
            outputs=[
                online_image, online_desc, online_style, online_result_json, online_image_analysis, 
                online_title, online_basic_info, online_carbon, online_search,
                selling_image, selling_desc, selling_price, selling_contact, selling_trade, 
                selling_style, selling_result_json, selling_image_analysis, selling_carbon,
                seeking_desc, seeking_purpose, seeking_price, seeking_contact, seeking_trade,
                seeking_type, seeking_deadline, seeking_image, seeking_style, seeking_result_json,
                seeking_image_analysis
            ]
        )
        
        # 底部介紹與使用教學
        gr.Markdown("""
        ## 使用教學與系統介紹
        
        ReviveAI 是一個專為二手商品優化設計的系統，幫助您創建專業的商品描述，增加曝光和銷售機會。
        
        ### 使用方法：
        
        1. 選擇您想使用的服務類型：拍賣網站、社群賣文或社群徵文
        2. 上傳商品圖片（徵文功能為選填）和填寫相關資訊
        3. 選擇適合的文案風格
        4. 點擊「生成文案」按鈕
        5. 在右側查看生成的文案內容，並可使用複製按鈕複製文案
        
        ### 系統特色：
        
        - **智能圖片分析**：自動分析商品圖片，提取關鍵特徵
        - **優化內容生成**：根據不同平台特性生成最適合的文案
        - **碳足跡計算**：計算選購二手商品的環境效益，幫助您了解對環境的貢獻
        - **串流生成**：實時生成和顯示文案內容，讓您能夠即時看到結果
        
        ### 永續價值
        
        使用 ReviveAI 系統不只是為了創建更好的二手商品描述，也是在為環境永續發展盡一份心力。
        每次選擇購買或銷售二手商品，都能減少新商品生產所帶來的碳排放和資源消耗。
        
        感謝您選擇 ReviveAI，讓我們一起為永續未來努力！
        """, elem_classes=["footer-info"])
        
    return app

# 啟動應用程式
if __name__ == "__main__":
    app = create_app()
    app.launch()
