import gradio as gr
import requests
import json
from PIL import Image
import io
import numpy as np

username = "kani"
password = "12341021"

# API 端點
API_BASE_URL = "https://tough-aardvark-suddenly.ngrok-free.app"

# 定義各服務端點
ONLINE_SALE_ENDPOINT = f"{API_BASE_URL}/combined_service/online_sale"
SELLING_POST_ENDPOINT = f"{API_BASE_URL}/combined_service/selling_post"
SEEKING_POST_ENDPOINT = f"{API_BASE_URL}/combined_service/seeking_post"

# 內容風格選項
CONTENT_STYLES = {
    "標準專業": "normal",
    "輕鬆活潑": "casual",
    "正式商務": "formal",
    "故事體驗": "story"
}

# 銷售文案風格選項
SELLING_STYLES = {
    "標準實用": "normal",
    "故事體驗": "storytelling",
    "簡約精要": "minimalist",
    "超值優惠": "bargain"
}

# 徵品文案風格選項
SEEKING_STYLES = {
    "標準親切": "normal",
    "急需緊急": "urgent",
    "預算有限": "budget",
    "收藏愛好": "collector"
}

# 徵品類型選項
SEEKING_TYPES = {
    "購買": "buy",
    "租借": "rent"
}

def process_online_sale(image, description, style):
    """處理拍賣網站文案請求"""
    try:
        # 檢查圖片格式並處理
        if image is None:
            return "錯誤: 請上傳商品圖片"
            
        # 將圖片轉換為二進制數據
        if isinstance(image, np.ndarray):
            img = Image.fromarray(image)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
        elif isinstance(image, Image.Image):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
        else:
            return "錯誤: 無效的圖片格式"
        # 準備請求資料
        files = {"image": ("image.jpg", img_byte_arr, "image/jpeg")}
        data = {
            "description": description,
            "style": CONTENT_STYLES[style]
        }
        
        # 發送請求
        response = requests.post(ONLINE_SALE_ENDPOINT, files=files, data=data, auth=(username, password))
        
        
        # 輸出回應內容以進行調試
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Content: {response.text[:500]}...")  # 只顯示前500個字元
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {str(e)}")
            return f"API回應解析錯誤: {str(e)}\n\n原始回應內容: {response.text[:1000]}..."
        
        if result["success"]:
            # 處理成功響應
            data = result["data"]
            
            # 取得各部分資料
            image_analysis = data["image_analysis"]
            optimized_content = data["optimized_content"]
            carbon_footprint = data["carbon_footprint"]
            
            # 構建標題和描述
            title = optimized_content["optimized_product_title"]
            descriptions = optimized_content["optimized_product_description"]
            
            # 構建碳足跡信息
            if "error" in carbon_footprint:
                carbon_info = f"碳足跡計算錯誤: {carbon_footprint['error']}"
            else:
                carbon_product = carbon_footprint["selected_product"]
                benefits = carbon_footprint["environmental_benefits"]
                carbon_info = f"""
### 碳足跡資訊

**選定產品**: {carbon_product["product_name"]}
**公司**: {carbon_product["company"]}
**原始碳足跡**: {carbon_product["carbon_footprint"]:.2f} kg CO2e
**節省碳排放**: {carbon_footprint["saved_carbon"]:.2f} kg CO2e

**環境效益**:
- 相當於 {benefits["trees"]} 棵樹一年的吸碳量
- 相當於減少開車 {benefits["car_km"]} 公里的碳排放
- 相當於減少吹冷氣 {benefits.get("ac_hours", "N/A")} 小時的碳排放
- 相當於減少手機充電 {benefits.get("phone_charges", "N/A")} 次的碳排放

**選擇原因**: {carbon_product["selection_reason"]}
"""
            
            # 組合結果
            result_markdown = f"""
## 圖片分析結果
{image_analysis}

## 優化商品標題
{title}

## 優化商品描述

### 📦 商品基本資訊
{descriptions["basic_information"]}

### ✨ 商品特色與賣點
{descriptions["features_and_benefits"]}

### 📝 商品現況詳細說明
{descriptions["current_status"]}

### 💚 永續價值
{descriptions["sustainable_value"]}

### 🔔 行動呼籲
{descriptions["call_to_action"]}

{carbon_info}
"""
            return result_markdown
        else:
            return f"處理失敗: {result['error']}"
    except Exception as e:
        return f"發生錯誤: {str(e)}"

def process_selling_post(image, description, price, contact_info, trade_method, style):
    """處理社群銷售貼文請求"""
    try:
        # 檢查圖片格式並處理
        if image is None:
            return "錯誤: 請上傳商品圖片"
            
        # 將圖片轉換為二進制數據
        if isinstance(image, np.ndarray):
            img = Image.fromarray(image)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
        elif isinstance(image, Image.Image):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
        else:
            return "錯誤: 無效的圖片格式"
        # 準備請求資料
        files = {"image": ("image.jpg", img_byte_arr, "image/jpeg")}
        data = {
            "description": description,
            "price": price,
            "contact_info": contact_info,
            "trade_method": trade_method,
            "style": SELLING_STYLES[style]
        }
        
        # 發送請求
        response = requests.post(SELLING_POST_ENDPOINT, files=files, data=data, auth=(username, password))
        
        # 輸出回應內容以進行調試
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Content: {response.text[:500]}...")  # 只顯示前500個字元
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {str(e)}")
            return f"API回應解析錯誤: {str(e)}\n\n原始回應內容: {response.text[:1000]}..."
        
        if result["success"]:
            # 處理成功響應
            data = result["data"]
            
            # 取得各部分資料
            image_analysis = data["image_analysis"]
            selling_post = data["selling_post"]
            carbon_footprint = data["carbon_footprint"]
            
            # 構建碳足跡信息
            if "error" in carbon_footprint:
                carbon_info = f"碳足跡計算錯誤: {carbon_footprint['error']}"
            else:
                carbon_product = carbon_footprint["selected_product"]
                benefits = carbon_footprint["environmental_benefits"]
                carbon_info = f"""
### 碳足跡資訊

**選定產品**: {carbon_product["product_name"]}
**公司**: {carbon_product["company"]}
**原始碳足跡**: {carbon_product["carbon_footprint"]:.2f} kg CO2e
**節省碳排放**: {carbon_footprint["saved_carbon"]:.2f} kg CO2e

**環境效益**:
- 相當於 {benefits["trees"]} 棵樹一年的吸碳量
- 相當於減少開車 {benefits["car_km"]} 公里的碳排放
- 相當於減少吹冷氣 {benefits.get("ac_hours", "N/A")} 小時的碳排放
- 相當於減少手機充電 {benefits.get("phone_charges", "N/A")} 次的碳排放

**選擇原因**: {carbon_product["selection_reason"]}
"""
            
            # 組合結果
            result_markdown = f"""
## 圖片分析結果
{image_analysis}

## 社群銷售貼文
{selling_post}

{carbon_info}
"""
            return result_markdown
        else:
            return f"處理失敗: {result['error']}"
    except Exception as e:
        return f"發生錯誤: {str(e)}"

def process_seeking_post(product_description, purpose, expected_price, contact_info, trade_method, seeking_type, deadline, image, style):
    """處理社群徵品貼文請求"""
    try:
        # 檢查必填欄位
        if not product_description:
            return "錯誤: 請填寫徵求商品描述"
        # 準備請求資料
        data = {
            "product_description": product_description,
            "purpose": purpose,
            "expected_price": expected_price,
            "contact_info": contact_info,
            "trade_method": trade_method,
            "seeking_type": SEEKING_TYPES[seeking_type],
            "deadline": deadline,
            "style": SEEKING_STYLES[style]
        }
        
        # 如果有上傳圖片
        files = {}
        if image is not None:
            # 將圖片轉換為二進制數據
            if isinstance(image, np.ndarray):
                img = Image.fromarray(image)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                files = {"image": ("image.jpg", img_byte_arr, "image/jpeg")}
            elif isinstance(image, Image.Image):
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                files = {"image": ("image.jpg", img_byte_arr, "image/jpeg")}
        
        # 發送請求
        response = requests.post(SEEKING_POST_ENDPOINT, files=files, data=data, auth=(username, password))
        
        # 輸出回應內容以進行調試
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Content: {response.text[:500]}...")  # 只顯示前500個字元
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {str(e)}")
            return f"API回應解析錯誤: {str(e)}\n\n原始回應內容: {response.text[:1000]}..."
        
        if result["success"]:
            # 處理成功響應
            data = result["data"]
            
            # 取得各部分資料
            image_analysis = data.get("image_analysis", "")
            seeking_post = data["seeking_post"]
            
            # 組合結果
            result_markdown = ""
            
            if image_analysis:
                result_markdown += f"""
## 參考圖片分析結果
{image_analysis}
"""
            
            result_markdown += f"""
## 社群徵品貼文
{seeking_post}
"""
            return result_markdown
        else:
            return f"處理失敗: {result['error']}"
    except Exception as e:
        return f"發生錯誤: {str(e)}"

def create_online_sale_interface():
    """創建拍賣網站文案介面"""
    with gr.Blocks() as interface:
        gr.Markdown("## 拍賣網站文案生成服務")
        gr.Markdown("上傳商品圖片，輸入基本描述，獲取優化的商品內容與環保效益")
        
        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(type="pil", label="商品圖片")
                description_input = gr.Textbox(lines=3, label="商品基本描述", placeholder="例如：macbook air m1 2020 8g 256g 使用兩年 背面小瑕疵")
                style_input = gr.Dropdown(choices=list(CONTENT_STYLES.keys()), value="標準專業", label="文案風格")
                submit_button = gr.Button("生成優化文案", variant="primary")
            
            with gr.Column(scale=2):
                output = gr.Markdown(label="生成結果")
        
        submit_button.click(
            fn=process_online_sale,
            inputs=[image_input, description_input, style_input],
            outputs=output
        )
    
    return interface

def create_selling_post_interface():
    """創建社群銷售貼文介面"""
    with gr.Blocks() as interface:
        gr.Markdown("## 社群銷售貼文生成服務")
        gr.Markdown("上傳商品圖片，輸入商品資訊，獲取適合社群平台發布的銷售貼文")
        
        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(type="pil", label="商品圖片")
                description_input = gr.Textbox(lines=3, label="商品基本描述", placeholder="例如：macbook air m1 2020 8g 256g 使用兩年 背面小瑕疵")
                price_input = gr.Textbox(label="售價", placeholder="例如：$18,000")
                contact_input = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                trade_input = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                style_input = gr.Dropdown(choices=list(SELLING_STYLES.keys()), value="標準實用", label="文案風格")
                submit_button = gr.Button("生成銷售貼文", variant="primary")
            
            with gr.Column(scale=2):
                output = gr.Markdown(label="生成結果")
        
        submit_button.click(
            fn=process_selling_post,
            inputs=[image_input, description_input, price_input, contact_input, trade_input, style_input],
            outputs=output
        )
    
    return interface

def create_seeking_post_interface():
    """創建社群徵品貼文介面"""
    with gr.Blocks() as interface:
        gr.Markdown("## 社群徵品貼文生成服務")
        gr.Markdown("輸入徵求的商品資訊，獲取適合社群平台發布的徵求貼文")
        
        with gr.Row():
            with gr.Column(scale=1):
                description_input = gr.Textbox(lines=2, label="徵求商品描述", placeholder="例如：iphone 13 pro max 256g")
                purpose_input = gr.Textbox(lines=2, label="徵求目的", placeholder="例如：工作需要穩定高效能手機，拍照功能需良好")
                expected_price_input = gr.Textbox(label="期望價格", placeholder="例如：15000-18000")
                contact_input = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                trade_input = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                seeking_type_input = gr.Dropdown(choices=list(SEEKING_TYPES.keys()), value="購買", label="徵求類型")
                deadline_input = gr.Textbox(label="徵求時效", value="越快越好")
                image_input = gr.Image(type="pil", label="參考圖片 (選填)")
                style_input = gr.Dropdown(choices=list(SEEKING_STYLES.keys()), value="標準親切", label="文案風格")
                submit_button = gr.Button("生成徵品貼文", variant="primary")
            
            with gr.Column(scale=2):
                output = gr.Markdown(label="生成結果")
        
        submit_button.click(
            fn=process_seeking_post,
            inputs=[description_input, purpose_input, expected_price_input, contact_input, trade_input, seeking_type_input, deadline_input, image_input, style_input],
            outputs=output
        )
    
    return interface

# 創建主界面
def create_main_interface():
    with gr.Blocks(title="ReviveAI 二手商品優化平台") as demo:
        gr.Markdown(
            """
            # 🌱 ReviveAI 二手商品優化平台
            
            這個平台使用 AI 技術優化二手商品資訊，提升銷售效果並展示環保價值。
            
            ## 主要服務
            
            1. **拍賣網站文案**：生成結構化的商品描述，適合在拍賣網站上使用
            2. **社群銷售貼文**：生成適合社交媒體發布的銷售貼文
            3. **社群徵品貼文**：生成適合社交媒體發布的徵求貼文
            
            使用方式：選擇需要的服務標籤頁，上傳圖片並填寫相關信息，系統將自動生成優化內容。
            """
        )
        
        with gr.Tabs():
            with gr.TabItem("拍賣網站文案"):
                online_sale_interface = create_online_sale_interface()
            
            with gr.TabItem("社群銷售貼文"):
                selling_post_interface = create_selling_post_interface()
            
            with gr.TabItem("社群徵品貼文"):
                seeking_post_interface = create_seeking_post_interface()
        
        gr.Markdown(
            """
            ### 注意事項
            
            - 確保 ReviveAI API 服務器已在本地 http://localhost:8000 運行
            - 圖片分析可能需要幾秒鐘時間，請耐心等待
            - 生成結果將包含商品分析、優化文案和碳足跡計算
            
            © 2025 ReviveAI 團隊 - 二手商品永續平台
            """
        )
    
    return demo

# 啟動 Gradio 界面
if __name__ == "__main__":
    demo = create_main_interface()
    demo.launch(share=True)