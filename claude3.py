def generate_css():
    """產生自定義 CSS 樣式"""
    return """
    #online_output, #online_carbon_viz, #online_carbon_detail, #online_image_analysis, #online_web_search {
        min-height: 500px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        background-color: #27272A;
        overflow-y: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    #selling_output, #seeking_output {
        min-height: 500px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        background-color: #27272A;
        overflow-y: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .output-header {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 12px;
        color: #2c7873;
        text-align: center;
        padding: 10px;
    }
    
    .markdown-body h2 {
        margin-top: 20px;
        color: #2c7873;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 5px;
    }
    
    .markdown-body h3 {
        margin-top: 15px;
        color: #2c7873;
    }
    
    .processing-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
        margin-top: 30px;
    }
    
    button.primary {
        background-color: #2c7873 !important;
    }
    
    .footer {
        text-align: center;
        margin-top: 20px;
        color: #666;
    }
    """
import gradio as gr
import requests
import json
from PIL import Image
import io
import numpy as np
import time

# API 端點
API_BASE_URL = "http://127.0.0.1:8000"

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
        print("----- 開始處理拍賣網站文案 -----")
        print(f"圖片類型: {type(image)}")
        print(f"描述: {description}")
        print(f"風格: {style}")
        
        # 檢查圖片格式並處理
        if image is None:
            print("圖片為空")
            # 確保所有的標籤頁都顯示相同的錯誤訊息
            error_msg = "錯誤: 請上傳商品圖片"
            error_html = "<div class='error-message'>請上傳商品圖片</div>"
            return [error_msg, error_html, error_msg, error_msg, error_msg]
            
        # 將圖片轉換為二進制數據
        try:
            if isinstance(image, np.ndarray):
                print("處理 NumPy 陣列圖片")
                img = Image.fromarray(image)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                print(f"圖片轉換成功，大小: {len(img_byte_arr)} 字節")
            elif isinstance(image, Image.Image):
                print("處理 PIL Image 圖片")
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                print(f"圖片轉換成功，大小: {len(img_byte_arr)} 字節")
            else:
                print(f"未知圖片類型: {type(image)}")
                error_msg = f"錯誤: 無效的圖片格式 (類型: {type(image)})"
                error_html = "<div class='error-message'>無效的圖片格式</div>"
                return [error_msg, error_html, error_msg, error_msg, error_msg]
        except Exception as img_error:
            print(f"圖片處理錯誤: {str(img_error)}")
            error_msg = f"圖片處理錯誤: {str(img_error)}"
            error_html = "<div class='error-message'>圖片處理錯誤</div>"
            return [error_msg, error_html, error_msg, error_msg, error_msg]
            
        # 準備請求資料
        files = {"image": ("image.jpg", img_byte_arr, "image/jpeg")}
        data = {
            "description": description,
            "style": CONTENT_STYLES[style]
        }
        
        # 發送請求
        try:
            print("發送 API 請求...")
            if API_USERNAME and API_PASSWORD:
                response = requests.post(ONLINE_SALE_ENDPOINT, files=files, data=data, auth=(API_USERNAME, API_PASSWORD))
            else:
                response = requests.post(ONLINE_SALE_ENDPOINT, files=files, data=data)
            
            print(f"API 響應狀態碼: {response.status_code}")
            print(f"API 響應內容預覽: {response.text[:200]}...")
            
            if response.status_code != 200:
                print(f"API 請求失敗，狀態碼: {response.status_code}")
                error_msg = f"API 請求失敗: HTTP狀態碼 {response.status_code}"
                error_html = "<div class='error-message'>API 請求失敗</div>"
                return [error_msg, error_html, error_msg, error_msg, error_msg]
        except Exception as req_error:
            print(f"API 請求錯誤: {str(req_error)}")
            error_msg = f"API 請求錯誤: {str(req_error)}"
            error_html = "<div class='error-message'>API 請求錯誤</div>"
            return [error_msg, error_html, error_msg, error_msg, error_msg]
            
        # 為了更好的使用者體驗，確保API請求至少顯示加載狀態2秒
        time.sleep(2)
        
        # 解析 JSON 響應
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {str(e)}")
            print(f"響應內容: {response.text[:500]}...")
            error_msg = f"API回應解析錯誤: {str(e)}"
            error_html = "<div class='error-message'>API回應解析錯誤</div>"
            return [error_msg, error_html, error_msg, error_msg, error_msg]
        
        # 處理 API 響應
        print("處理 API 響應...")
        if result["success"]:
            # 處理成功響應
            data = result["data"]
            
            # 取得各部分資料（添加預設值，防止缺少某些字段）
            image_analysis = data.get("image_analysis", "未提供圖片分析")
            optimized_content = data.get("optimized_content", {})
            carbon_footprint = data.get("carbon_footprint", {})
            search_results = optimized_content.get("search_results", "未提供網路搜尋結果")
            
            # 構建標題和描述，添加預設值防止 KeyError
            title = optimized_content.get("optimized_product_title", "未生成標題")
            descriptions = optimized_content.get("optimized_product_description", {
                "basic_information": "未提供基本資訊",
                "features_and_benefits": "未提供特色與賣點",
                "current_status": "未提供現況說明",
                "sustainable_value": "未提供永續價值",
                "call_to_action": "未提供行動呼籲"
            })
            
            # 構建文案輸出
            output_content = f"""
## 優化商品標題
{title}

## 優化商品描述

### 📦 商品基本資訊
{descriptions.get("basic_information", "未提供基本資訊")}

### ✨ 商品特色與賣點
{descriptions.get("features_and_benefits", "未提供特色與賣點")}

### 📝 商品現況詳細說明
{descriptions.get("current_status", "未提供現況說明")}

### 💚 永續價值
{descriptions.get("sustainable_value", "未提供永續價值")}

### 🔔 行動呼籲
{descriptions.get("call_to_action", "未提供行動呼籲")}
"""
            
            # 構建碳足跡視覺化 HTML
            carbon_viz_html = ""
            if "error" in carbon_footprint:
                carbon_viz_html = f"<div class='error-message'>碳足跡計算錯誤: {carbon_footprint['error']}</div>"
            else:
                try:
                    carbon_product = carbon_footprint.get("selected_product", {})
                    benefits = carbon_footprint.get("environmental_benefits", {})
                    saved_carbon = carbon_footprint.get("saved_carbon", 0)
                    
                    # 確保所有需要的值都存在，並提供默認值
                    carbon_footprint_value = carbon_product.get("carbon_footprint", 0)
                    
                    # 創建碳足跡視覺化
                    carbon_viz_html = f"""
                    <div class="carbon-container">
                        <div class="carbon-header">
                            <h2>選擇二手商品的環保效益</h2>
                            <p>選擇這個二手商品可以減少 <span class="carbon-value">{saved_carbon:.2f}</span> kg CO2e 的碳排放</p>
                        </div>
                        
                        <div class="carbon-chart">
                            <div class="carbon-bar-container">
                                <div class="carbon-bar-label">新品</div>
                                <div class="carbon-bar carbon-bar-new" style="width: 100%;"></div>
                                <div class="carbon-value-label">{carbon_footprint_value:.2f} kg CO2e</div>
                            </div>
                            
                            <div class="carbon-bar-container">
                                <div class="carbon-bar-label">二手</div>
                                <div class="carbon-bar carbon-bar-used" style="width: {100 - (saved_carbon / max(carbon_footprint_value, 0.01) * 100)}%;"></div>
                                <div class="carbon-value-label">{carbon_footprint_value - saved_carbon:.2f} kg CO2e</div>
                            </div>
                            
                            <div class="carbon-saving">
                                <div class="carbon-saving-arrow">↓</div>
                                <div class="carbon-saving-label">節省 {saved_carbon:.2f} kg CO2e</div>
                            </div>
                        </div>
                        
                        <div class="carbon-benefits">
                            <h3>環境效益等同於：</h3>
                            <div class="benefits-grid">
                                <div class="benefit-item">
                                    <div class="benefit-icon">🌳</div>
                                    <div class="benefit-value">{benefits.get("trees", "N/A")}</div>
                                    <div class="benefit-label">棵樹一年的吸碳量</div>
                                </div>
                                <div class="benefit-item">
                                    <div class="benefit-icon">🚗</div>
                                    <div class="benefit-value">{benefits.get("car_km", "N/A")}</div>
                                    <div class="benefit-label">公里的汽車碳排放</div>
                                </div>
                                <div class="benefit-item">
                                    <div class="benefit-icon">❄️</div>
                                    <div class="benefit-value">{benefits.get("ac_hours", "N/A")}</div>
                                    <div class="benefit-label">小時的空調碳排放</div>
                                </div>
                                <div class="benefit-item">
                                    <div class="benefit-icon">📱</div>
                                    <div class="benefit-value">{benefits.get("phone_charges", "N/A")}</div>
                                    <div class="benefit-label">次手機充電的碳排放</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <style>
                    .carbon-container {{
                        font-family: Arial, sans-serif;
                        padding: 20px;
                        background-color: #f9f9f9;
                        border-radius: 10px;
                    }}
                    
                    .carbon-header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    
                    .carbon-header h2 {{
                        color: #2c7873;
                        margin-bottom: 10px;
                    }}
                    
                    .carbon-value {{
                        font-weight: bold;
                        color: #2c7873;
                        font-size: 1.2em;
                    }}
                    
                    .carbon-chart {{
                        margin: 30px 0;
                    }}
                    
                    .carbon-bar-container {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 15px;
                    }}
                    
                    .carbon-bar-label {{
                        width: 60px;
                        text-align: right;
                        padding-right: 10px;
                        font-weight: bold;
                    }}
                    
                    .carbon-bar {{
                        height: 30px;
                        border-radius: 4px;
                        transition: width 1s ease-in-out;
                    }}
                    
                    .carbon-bar-new {{
                        background-color: #ff6b6b;
                    }}
                    
                    .carbon-bar-used {{
                        background-color: #2c7873;
                    }}
                    
                    .carbon-value-label {{
                        margin-left: 10px;
                        font-weight: bold;
                    }}
                    
                    .carbon-saving {{
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 20px 0;
                    }}
                    
                    .carbon-saving-arrow {{
                        font-size: 30px;
                        color: #2c7873;
                        margin-right: 10px;
                    }}
                    
                    .carbon-saving-label {{
                        color: #2c7873;
                        font-weight: bold;
                        font-size: 1.2em;
                    }}
                    
                    .carbon-benefits {{
                        margin-top: 30px;
                    }}
                    
                    .carbon-benefits h3 {{
                        text-align: center;
                        margin-bottom: 20px;
                        color: #2c7873;
                    }}
                    
                    .benefits-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                        gap: 20px;
                    }}
                    
                    .benefit-item {{
                        text-align: center;
                        padding: 15px;
                        background-color: #fff;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    
                    .benefit-icon {{
                        font-size: 30px;
                        margin-bottom: 10px;
                    }}
                    
                    .benefit-value {{
                        font-size: 1.5em;
                        font-weight: bold;
                        color: #2c7873;
                        margin-bottom: 5px;
                    }}
                    
                    .benefit-label {{
                        font-size: 0.9em;
                        color: #666;
                    }}
                    
                    .error-message {{
                        color: #ff6b6b;
                        text-align: center;
                        padding: 20px;
                        background-color: #fff;
                        border: 1px solid #ff6b6b;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    
                    .placeholder-message {{
                        text-align: center;
                        padding: 40px 20px;
                        color: #888;
                        font-style: italic;
                    }}
                    </style>
                    """
                except Exception as viz_error:
                    print(f"生成碳足跡視覺化時出錯: {str(viz_error)}")
                    carbon_viz_html = f"<div class='error-message'>生成碳足跡視覺化時出錯: {str(viz_error)}</div>"
            
            # 構建碳足跡詳情
            try:
                if "error" in carbon_footprint:
                    carbon_detail = f"碳足跡計算錯誤: {carbon_footprint['error']}"
                else:
                    carbon_product = carbon_footprint.get("selected_product", {})
                    search_params = carbon_footprint.get("search_params", {})
                    
                    carbon_detail = f"""
### 碳足跡計算詳情

#### 搜尋參數
- 查詢文本: {search_params.get("query_text", "未提供")}
- 最小碳足跡值: {search_params.get("min_carbon_footprint", "未設定")}
- 最大碳足跡值: {search_params.get("max_carbon_footprint", "未設定")}
- 產業類別: {search_params.get("sector", "未設定")}

#### 選定產品資訊
- **名稱**: {carbon_product.get("product_name", "未知")}
- **公司**: {carbon_product.get("company", "未知")}
- **原始碳足跡**: {carbon_product.get("carbon_footprint", 0):.2f} kg CO2e
- **產業類別**: {carbon_product.get("sector", "未知")}
- **相似度分數**: {(1 - carbon_product.get("cosine_distance", 0)) * 100:.2f}%

#### 碳足跡計算方法
- 節省比例: 50%（基於使用過的二手商品的標準節省率）
- 節省的碳排放: {carbon_footprint.get("saved_carbon", 0):.2f} kg CO2e

#### 選擇原因
{carbon_product.get("selection_reason", "未提供選擇原因")}

#### 產品詳細資訊
{carbon_product.get("details", "未提供詳細資訊")}
"""
            except Exception as detail_error:
                print(f"生成碳足跡詳情時出錯: {str(detail_error)}")
                carbon_detail = f"生成碳足跡詳情時出錯: {str(detail_error)}"
            
            # 返回所有標籤的內容，確保每個標籤都有內容
            print("成功生成內容，返回5個結果")
            return [
                output_content,  # 文案輸出
                carbon_viz_html,  # 碳足跡視覺化
                carbon_detail,  # 碳足跡詳情
                image_analysis,  # 圖片分析
                search_results or "未提供網路搜尋結果"  # 網路搜尋
            ]
        else:
            error_message = f"處理失敗: {result.get('error', '未知錯誤')}"
            print(error_message)
            error_html = f"<div class='error-message'>{error_message}</div>"
            return [error_message, error_html, error_message, error_message, error_message]
    except Exception as e:
        error_message = f"發生錯誤: {str(e)}"
        print(f"處理過程中出現異常: {error_message}")
        import traceback
        traceback.print_exc()
        error_html = f"<div class='error-message'>{error_message}</div>"
        return [error_message, error_html, error_message, error_message, error_message]

def process_selling_post(image, description, price, contact_info, trade_method, style):
    """處理社群銷售貼文請求"""
    try:
        # 顯示處理中的訊息
        processing_message = "### 正在處理...\n\n📋 正在分析商品圖片並生成銷售貼文，這可能需要幾分鐘時間，請耐心等待..."
        
        # 檢查圖片格式並處理
        if image is None:
            return [
                "錯誤: 請上傳商品圖片", 
                "<div class='error-message'>請上傳商品圖片</div>",
                "錯誤: 請上傳商品圖片",
                "錯誤: 請上傳商品圖片",
                "錯誤: 請上傳商品圖片"
            ]
            
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
            return [
                "錯誤: 無效的圖片格式", 
                "<div class='error-message'>無效的圖片格式</div>",
                "錯誤: 無效的圖片格式",
                "錯誤: 無效的圖片格式",
                "錯誤: 無效的圖片格式"
            ]
            
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
        if API_USERNAME and API_PASSWORD:
            response = requests.post(SELLING_POST_ENDPOINT, files=files, data=data, auth=(API_USERNAME, API_PASSWORD))
        else:
            response = requests.post(SELLING_POST_ENDPOINT, files=files, data=data)
        
        # 為了更好的使用者體驗，確保API請求至少顯示加載狀態2秒
        time.sleep(2)
        
        # 輸出回應內容以進行調試
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Content: {response.text[:500]}...")  # 只顯示前500個字元
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {str(e)}")
            return [
                f"API回應解析錯誤: {str(e)}\n\n原始回應內容: {response.text[:1000]}...",
                "<div class='error-message'>API回應解析錯誤</div>",
                f"API回應解析錯誤: {str(e)}",
                f"API回應解析錯誤: {str(e)}",
                f"API回應解析錯誤: {str(e)}"
            ]
        
        if result["success"]:
            # 處理成功響應
            data = result["data"]
            
            # 取得各部分資料
            image_analysis = data["image_analysis"]
            selling_post = data["selling_post"]
            carbon_footprint = data["carbon_footprint"]
            
            # 構建文案輸出
            output_content = f"""
## 社群銷售貼文

{selling_post}
"""
            
            # 構建碳足跡視覺化 HTML
            carbon_viz_html = ""
            if "error" in carbon_footprint:
                carbon_viz_html = f"<div class='error-message'>碳足跡計算錯誤: {carbon_footprint['error']}</div>"
            else:
                carbon_product = carbon_footprint["selected_product"]
                benefits = carbon_footprint["environmental_benefits"]
                saved_carbon = carbon_footprint["saved_carbon"]
                
                # 創建碳足跡視覺化
                carbon_viz_html = f"""
                <div class="carbon-container">
                    <div class="carbon-header">
                        <h2>選擇二手商品的環保效益</h2>
                        <p>選擇這個二手商品可以減少 <span class="carbon-value">{saved_carbon:.2f}</span> kg CO2e 的碳排放</p>
                    </div>
                    
                    <div class="carbon-chart">
                        <div class="carbon-bar-container">
                            <div class="carbon-bar-label">新品</div>
                            <div class="carbon-bar carbon-bar-new" style="width: 100%;"></div>
                            <div class="carbon-value-label">{carbon_product["carbon_footprint"]:.2f} kg CO2e</div>
                        </div>
                        
                        <div class="carbon-bar-container">
                            <div class="carbon-bar-label">二手</div>
                            <div class="carbon-bar carbon-bar-used" style="width: {100 - (saved_carbon / carbon_product["carbon_footprint"] * 100)}%;"></div>
                            <div class="carbon-value-label">{carbon_product["carbon_footprint"] - saved_carbon:.2f} kg CO2e</div>
                        </div>
                        
                        <div class="carbon-saving">
                            <div class="carbon-saving-arrow">↓</div>
                            <div class="carbon-saving-label">節省 {saved_carbon:.2f} kg CO2e</div>
                        </div>
                    </div>
                    
                    <div class="carbon-benefits">
                        <h3>環境效益等同於：</h3>
                        <div class="benefits-grid">
                            <div class="benefit-item">
                                <div class="benefit-icon">🌳</div>
                                <div class="benefit-value">{benefits["trees"]}</div>
                                <div class="benefit-label">棵樹一年的吸碳量</div>
                            </div>
                            <div class="benefit-item">
                                <div class="benefit-icon">🚗</div>
                                <div class="benefit-value">{benefits["car_km"]}</div>
                                <div class="benefit-label">公里的汽車碳排放</div>
                            </div>
                            <div class="benefit-item">
                                <div class="benefit-icon">❄️</div>
                                <div class="benefit-value">{benefits.get("ac_hours", "N/A")}</div>
                                <div class="benefit-label">小時的空調碳排放</div>
                            </div>
                            <div class="benefit-item">
                                <div class="benefit-icon">📱</div>
                                <div class="benefit-value">{benefits.get("phone_charges", "N/A")}</div>
                                <div class="benefit-label">次手機充電的碳排放</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <style>
                .carbon-container {
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 10px;
                }
                
                .carbon-header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .carbon-header h2 {
                    color: #2c7873;
                    margin-bottom: 10px;
                }
                
                .carbon-value {
                    font-weight: bold;
                    color: #2c7873;
                    font-size: 1.2em;
                }
                
                .carbon-chart {
                    margin: 30px 0;
                }
                
                .carbon-bar-container {
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                }
                
                .carbon-bar-label {
                    width: 60px;
                    text-align: right;
                    padding-right: 10px;
                    font-weight: bold;
                }
                
                .carbon-bar {
                    height: 30px;
                    border-radius: 4px;
                    transition: width 1s ease-in-out;
                }
                
                .carbon-bar-new {
                    background-color: #ff6b6b;
                }
                
                .carbon-bar-used {
                    background-color: #2c7873;
                }
                
                .carbon-value-label {
                    margin-left: 10px;
                    font-weight: bold;
                }
                
                .carbon-saving {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 20px 0;
                }
                
                .carbon-saving-arrow {
                    font-size: 30px;
                    color: #2c7873;
                    margin-right: 10px;
                }
                
                .carbon-saving-label {
                    color: #2c7873;
                    font-weight: bold;
                    font-size: 1.2em;
                }
                
                .carbon-benefits {
                    margin-top: 30px;
                }
                
                .carbon-benefits h3 {
                    text-align: center;
                    margin-bottom: 20px;
                    color: #2c7873;
                }
                
                .benefits-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 20px;
                }
                
                .benefit-item {
                    text-align: center;
                    padding: 15px;
                    background-color: #fff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .benefit-icon {
                    font-size: 30px;
                    margin-bottom: 10px;
                }
                
                .benefit-value {
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #2c7873;
                    margin-bottom: 5px;
                }
                
                .benefit-label {
                    font-size: 0.9em;
                    color: #666;
                }
                
                .error-message {
                    color: #ff6b6b;
                    text-align: center;
                    padding: 20px;
                    background-color: #fff;
                    border: 1px solid #ff6b6b;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                
                .placeholder-message {
                    text-align: center;
                    padding: 40px 20px;
                    color: #888;
                    font-style: italic;
                }
                </style>
                """
            
            # 構建碳足跡詳情
            if "error" in carbon_footprint:
                carbon_detail = f"碳足跡計算錯誤: {carbon_footprint['error']}"
            else:
                carbon_product = carbon_footprint["selected_product"]
                search_params = carbon_footprint.get("search_params", {})
                
                carbon_detail = f"""
### 碳足跡計算詳情

#### 搜尋參數
- 查詢文本: {search_params.get("query_text", "未提供")}
- 最小碳足跡值: {search_params.get("min_carbon_footprint", "未設定")}
- 最大碳足跡值: {search_params.get("max_carbon_footprint", "未設定")}
- 產業類別: {search_params.get("sector", "未設定")}

#### 選定產品資訊
- **名稱**: {carbon_product["product_name"]}
- **公司**: {carbon_product["company"]}
- **原始碳足跡**: {carbon_product["carbon_footprint"]:.2f} kg CO2e
- **產業類別**: {carbon_product["sector"]}
- **相似度分數**: {(1 - carbon_product.get("cosine_distance", 0)) * 100:.2f}%

#### 碳足跡計算方法
- 節省比例: 50%（基於使用過的二手商品的標準節省率）
- 節省的碳排放: {carbon_footprint["saved_carbon"]:.2f} kg CO2e

#### 選擇原因
{carbon_product["selection_reason"]}

#### 產品詳細資訊
{carbon_product["details"]}
"""
            
            # 構建網路搜尋內容
            web_search_content = "未提供網路搜尋結果"
            
            # 返回所有標籤的內容
            return [
                output_content,  # 文案輸出
                carbon_viz_html,  # 碳足跡視覺化
                carbon_detail,  # 碳足跡詳情
                image_analysis,  # 圖片分析
                web_search_content  # 網路搜尋
            ]
        else:
            error_message = f"處理失敗: {result['error']}"
            return [error_message, f"<div class='error-message'>{error_message}</div>", error_message, error_message, error_message]
    except Exception as e:
        error_message = f"發生錯誤: {str(e)}"
        return [error_message, f"<div class='error-message'>{error_message}</div>", error_message, error_message, error_message]

def process_seeking_post(product_description, purpose, expected_price, contact_info, trade_method, seeking_type, deadline, image, style):
    """處理社群徵品貼文請求"""
    try:
        # 顯示處理中的訊息
        processing_message = "### 正在處理...\n\n📋 正在分析商品資訊並生成徵品貼文，這可能需要幾分鐘時間，請耐心等待..."
        
        # 檢查必填欄位
        if not product_description:
            return [
                "錯誤: 請填寫徵求商品描述",
                "錯誤: 請填寫徵求商品描述",
                "錯誤: 請填寫徵求商品描述"
            ]
            
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
        if API_USERNAME and API_PASSWORD:
            response = requests.post(SEEKING_POST_ENDPOINT, files=files, data=data, auth=(API_USERNAME, API_PASSWORD))
        else:
            response = requests.post(SEEKING_POST_ENDPOINT, files=files, data=data)
        
        # 為了更好的使用者體驗，確保API請求至少顯示加載狀態2秒
        time.sleep(2)
        
        # 輸出回應內容以進行調試
        print(f"API Response Status Code: {response.status_code}")
        print(f"API Response Content: {response.text[:500]}...")  # 只顯示前500個字元
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {str(e)}")
            return [
                f"API回應解析錯誤: {str(e)}\n\n原始回應內容: {response.text[:1000]}...",
                f"API回應解析錯誤: {str(e)}",
                f"API回應解析錯誤: {str(e)}"
            ]
        
        if result["success"]:
            # 處理成功響應
            data = result["data"]
            
            # 取得各部分資料
            image_analysis = data.get("image_analysis", "")
            seeking_post = data["seeking_post"]
            
            # 構建網路搜尋內容
            web_search_content = "未提供網路搜尋結果"
            
            # 構建文案輸出
            output_content = f"""
## 社群徵品貼文

{seeking_post}
"""
            
            # 返回所有標籤的內容
            return [
                output_content,  # 文案輸出
                image_analysis,  # 圖片分析
                web_search_content  # 網路搜尋
            ]
        else:
            error_message = f"處理失敗: {result['error']}"
            return [error_message, error_message, error_message]
    except Exception as e:
        error_message = f"發生錯誤: {str(e)}"
        return [error_message, error_message, error_message]

# 創建主界面
def create_main_interface():
    with gr.Blocks(title="ReviveAI 二手商品優化平台", css=generate_css()) as demo:
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
            # 拍賣網站文案標籤頁
            with gr.TabItem("拍賣網站文案"):
                gr.Markdown("## 拍賣網站文案生成服務")
                gr.Markdown("上傳商品圖片，輸入基本描述，獲取優化的商品內容與環保效益")
                
                with gr.Row():
                    # 左側輸入欄位
                    with gr.Column(scale=1):
                        online_image_input = gr.Image(type="pil", label="商品圖片")
                        online_description_input = gr.Textbox(lines=3, label="商品基本描述", placeholder="例如：macbook air m1 2020 8g 256g 使用兩年 背面小瑕疵")
                        online_style_input = gr.Dropdown(choices=list(CONTENT_STYLES.keys()), value="標準專業", label="文案風格")
                        online_submit_button = gr.Button("生成優化文案", variant="primary")
                    
                    # 右側結果顯示 - 使用 Tabs 來組織不同的輸出內容
                    with gr.Column(scale=2):
                        with gr.Tabs() as online_result_tabs:
                            with gr.TabItem("文案輸出", id="online_output_tab"):
                                online_output = gr.Markdown(
                                    value="### 文案將顯示在這裡\n\n上傳圖片、填寫描述並點擊「生成優化文案」按鈕後，結果將在此區域顯示。",
                                    label="文案輸出", 
                                    elem_id="online_output"
                                )
                            with gr.TabItem("碳足跡視覺化", id="online_carbon_viz_tab"):
                                online_carbon_viz = gr.HTML(
                                    value="<div class='placeholder-message'>點擊「生成優化文案」按鈕後，這裡將顯示碳足跡視覺化結果。</div>",
                                    label="碳足跡視覺化",
                                    elem_id="online_carbon_viz"
                                )
                            with gr.TabItem("碳足跡詳情", id="online_carbon_detail_tab"):
                                online_carbon_detail = gr.Markdown(
                                    value="### 碳足跡計算詳情\n\n點擊「生成優化文案」按鈕後，這裡將顯示碳足跡計算的詳細資訊。",
                                    label="碳足跡詳情",
                                    elem_id="online_carbon_detail"
                                )
                            with gr.TabItem("圖片分析", id="online_image_analysis_tab"):
                                online_image_analysis = gr.Markdown(
                                    value="### 圖片分析結果\n\n點擊「生成優化文案」按鈕後，這裡將顯示圖片分析的結果。",
                                    label="圖片分析",
                                    elem_id="online_image_analysis"
                                )
                            with gr.TabItem("網路搜尋", id="online_web_search_tab"):
                                online_web_search = gr.Markdown(
                                    value="### 網路搜尋結果\n\n點擊「生成優化文案」按鈕後，這裡將顯示網路搜尋的結果。",
                                    label="網路搜尋",
                                    elem_id="online_web_search"
                                )
                
                # 注冊事件處理 - 更新輸出為多個標籤內的內容
                online_submit_button.click(
                    fn=process_online_sale,
                    inputs=[online_image_input, online_description_input, online_style_input],
                    outputs=[online_output, online_carbon_viz, online_carbon_detail, online_image_analysis, online_web_search],
                    js="""
                        () => { 
                            document.querySelector('#online_output').innerHTML = `
                                <div class="output-header">正在處理您的請求</div>
                                <div class="processing-indicator">
                                    <div style="text-align: center;">
                                        <div style="border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #2c7873; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto;"></div>
                                        <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
                                        <p>正在分析圖片並生成優化文案，請稍候...</p>
                                    </div>
                                </div>
                            `;
                        }
                        """
                )
            
            
            # 社群銷售貼文標籤頁
            with gr.TabItem("社群銷售貼文"):
                gr.Markdown("## 社群銷售貼文生成服務")
                gr.Markdown("上傳商品圖片，輸入商品資訊，獲取適合社群平台發布的銷售貼文")
                
                with gr.Row():
                    # 左側輸入欄位
                    with gr.Column(scale=1):
                        selling_image_input = gr.Image(type="pil", label="商品圖片")
                        selling_description_input = gr.Textbox(lines=3, label="商品基本描述", placeholder="例如：macbook air m1 2020 8g 256g 使用兩年 背面小瑕疵")
                        selling_price_input = gr.Textbox(label="售價", placeholder="例如：$18,000")
                        selling_contact_input = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                        selling_trade_input = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                        selling_style_input = gr.Dropdown(choices=list(SELLING_STYLES.keys()), value="標準實用", label="文案風格")
                        selling_submit_button = gr.Button("生成銷售貼文", variant="primary")
                    
                    # 右側結果顯示 - 使用 Tabs 來組織不同的輸出內容
                    with gr.Column(scale=2):
                        with gr.Tabs() as selling_result_tabs:
                            with gr.TabItem("文案輸出", id="selling_output_tab"):
                                selling_output = gr.Markdown(
                                    value="### 文案將顯示在這裡\n\n上傳圖片、填寫商品資訊並點擊「生成銷售貼文」按鈕後，結果將在此區域顯示。",
                                    label="文案輸出", 
                                    elem_id="selling_output"
                                )
                            with gr.TabItem("碳足跡視覺化", id="selling_carbon_viz_tab"):
                                selling_carbon_viz = gr.HTML(
                                    value="<div class='placeholder-message'>點擊「生成銷售貼文」按鈕後，這裡將顯示碳足跡視覺化結果。</div>",
                                    label="碳足跡視覺化",
                                    elem_id="selling_carbon_viz"
                                )
                            with gr.TabItem("碳足跡詳情", id="selling_carbon_detail_tab"):
                                selling_carbon_detail = gr.Markdown(
                                    value="### 碳足跡計算詳情\n\n點擊「生成銷售貼文」按鈕後，這裡將顯示碳足跡計算的詳細資訊。",
                                    label="碳足跡詳情",
                                    elem_id="selling_carbon_detail"
                                )
                            with gr.TabItem("圖片分析", id="selling_image_analysis_tab"):
                                selling_image_analysis = gr.Markdown(
                                    value="### 圖片分析結果\n\n點擊「生成銷售貼文」按鈕後，這裡將顯示圖片分析的結果。",
                                    label="圖片分析",
                                    elem_id="selling_image_analysis"
                                )
                            with gr.TabItem("網路搜尋", id="selling_web_search_tab"):
                                selling_web_search = gr.Markdown(
                                    value="### 網路搜尋結果\n\n點擊「生成銷售貼文」按鈕後，這裡將顯示網路搜尋的結果。",
                                    label="網路搜尋",
                                    elem_id="selling_web_search"
                                )
                
                # 注冊事件處理 - 更新輸出為多個標籤內的內容
                selling_submit_button.click(
                    fn=process_selling_post,
                    inputs=[selling_image_input, selling_description_input, selling_price_input, 
                           selling_contact_input, selling_trade_input, selling_style_input],
                    outputs=[selling_output, selling_carbon_viz, selling_carbon_detail, selling_image_analysis, selling_web_search],
                    js="""
                    () => { 
                        document.querySelector('#selling_output').innerHTML = `
                            <div class="output-header">正在處理您的請求</div>
                            <div class="processing-indicator">
                                <div style="text-align: center;">
                                    <div style="border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #2c7873; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto;"></div>
                                    <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
                                    <p>正在分析圖片並生成銷售貼文，請稍候...</p>
                                </div>
                            </div>
                        `;
                    }
                    """
                )
            
            # 社群徵品貼文標籤頁
            with gr.TabItem("社群徵品貼文"):
                gr.Markdown("## 社群徵品貼文生成服務")
                gr.Markdown("輸入徵求的商品資訊，獲取適合社群平台發布的徵求貼文")
                
                with gr.Row():
                    # 左側輸入欄位
                    with gr.Column(scale=1):
                        seeking_description_input = gr.Textbox(lines=2, label="徵求商品描述", placeholder="例如：iphone 13 pro max 256g")
                        seeking_purpose_input = gr.Textbox(lines=2, label="徵求目的", placeholder="例如：工作需要穩定高效能手機，拍照功能需良好")
                        seeking_price_input = gr.Textbox(label="期望價格", placeholder="例如：15000-18000")
                        seeking_contact_input = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                        seeking_trade_input = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                        seeking_type_input = gr.Dropdown(choices=list(SEEKING_TYPES.keys()), value="購買", label="徵求類型")
                        seeking_deadline_input = gr.Textbox(label="徵求時效", value="越快越好")
                        seeking_image_input = gr.Image(type="pil", label="參考圖片 (選填)")
                        seeking_style_input = gr.Dropdown(choices=list(SEEKING_STYLES.keys()), value="標準親切", label="文案風格")
                        seeking_submit_button = gr.Button("生成徵品貼文", variant="primary")
                    
                    # 右側結果顯示 - 使用 Tabs 來組織不同的輸出內容
                    with gr.Column(scale=2):
                        with gr.Tabs() as seeking_result_tabs:
                            with gr.TabItem("文案輸出", id="seeking_output_tab"):
                                seeking_output = gr.Markdown(
                                    value="### 文案將顯示在這裡\n\n填寫徵求資訊並點擊「生成徵品貼文」按鈕後，結果將在此區域顯示。",
                                    label="文案輸出", 
                                    elem_id="seeking_output"
                                )
                            # 徵品服務不包含碳足跡計算，所以移除相關標籤
                            with gr.TabItem("圖片分析", id="seeking_image_analysis_tab"):
                                seeking_image_analysis = gr.Markdown(
                                    value="### 圖片分析結果\n\n如果上傳參考圖片並點擊「生成徵品貼文」按鈕後，這裡將顯示圖片分析的結果。",
                                    label="圖片分析",
                                    elem_id="seeking_image_analysis"
                                )
                            with gr.TabItem("網路搜尋", id="seeking_web_search_tab"):
                                seeking_web_search = gr.Markdown(
                                    value="### 網路搜尋結果\n\n點擊「生成徵品貼文」按鈕後，這裡將顯示網路搜尋的結果。",
                                    label="網路搜尋",
                                    elem_id="seeking_web_search"
                                )
                
                # 注冊事件處理 - 更新輸出為多個標籤內的內容
                seeking_submit_button.click(
                    fn=process_seeking_post,
                    inputs=[seeking_description_input, seeking_purpose_input, seeking_price_input,
                           seeking_contact_input, seeking_trade_input, seeking_type_input,
                           seeking_deadline_input, seeking_image_input, seeking_style_input],
                    outputs=[seeking_output, seeking_image_analysis, seeking_web_search],
                    js="""
                    () => { 
                        document.querySelector('#seeking_output').innerHTML = `
                            <div class="output-header">正在處理您的請求</div>
                            <div class="processing-indicator">
                                <div style="text-align: center;">
                                    <div style="border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #2c7873; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto;"></div>
                                    <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
                                    <p>正在分析資訊並生成徵品貼文，請稍候...</p>
                                </div>
                            </div>
                        `;
                    }
                    """
                )
        
        gr.Markdown(
            """
            ### 注意事項
            
            - 此應用程式連接到 ngrok 端點: tough-aardvark-suddenly.ngrok-free.app
            - 圖片分析可能需要幾秒鐘時間，請耐心等待
            - 生成結果將包含商品分析、優化文案和碳足跡計算
            
            © 2025 ReviveAI 團隊 - 二手商品永續平台

            """
        )
    
    return demo

# 啟動 Gradio 界面
if __name__ == "__main__":
    # 創建並啟動介面
    demo = create_main_interface()
    
    # 啟動服務
    demo.launch(share=True)