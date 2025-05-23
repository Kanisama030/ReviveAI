"""
ReviveAI 主應用程式
專為二手商品優化設計的系統，幫助您創建專業的商品描述
"""

import gradio as gr
from styles import css
from processing import (
    process_online_sale, 
    process_selling_post, 
    process_seeking_post, 
    reset_all
)

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
                        
                        # 二手商品表單區域
                        gr.Markdown("### 商品資訊", elem_classes=["form-section"])
                        
                        online_usage_time = gr.Slider(
                            minimum=0, 
                            maximum=20, 
                            value=2, 
                            step=0.5,
                            label="使用時間 (年)",
                            info="商品已使用多久時間"
                        )
                        
                        online_condition = gr.Dropdown(
                            choices=["全新未拆", "近全新", "九成新", "八成新", "七成新", "六成新", "功能正常"], 
                            value="八成新",
                            label="商品狀態",
                            info="請選擇商品的保存狀況"
                        )
                        
                        online_brand = gr.Textbox(
                            label="品牌", 
                            placeholder="例如：Apple、Sony、Nike...",
                            info="商品的品牌名稱"
                        )
                        
                        online_original_price = gr.Textbox(
                            label="原價 (選填)", 
                            placeholder="例如：NT$ 25,000",
                            info="商品的原始購買價格"
                        )
                        
                        online_desc = gr.Textbox(
                            label="其他補充說明 (選填)", 
                            placeholder="可以補充購買原因、使用心得、商品特色等...", 
                            lines=3,
                            info="任何額外的商品資訊或補充說明"
                        )
                        
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
                                online_basic_info = gr.Textbox(label="商品詳細內容", lines=45, interactive=False, show_copy_button=True)
                                
                            with gr.Tab("碳足跡圖表"):
                                online_carbon_chart = gr.Plot(label="環保效益視覺化")
                                
                            with gr.Tab("碳足跡數值"):
                                online_carbon = gr.Markdown()
                                
                            with gr.Tab("圖片分析"):
                                online_image_analysis = gr.Markdown(label="圖片分析結果")
                                
                            with gr.Tab("網路搜尋結果"):
                                online_search = gr.Markdown(label="網路搜尋結果")
                
                # 組合表單資訊函數
                def combine_form_info(desc, usage_time, condition, brand, original_price):
                    # 構建額外的描述資訊
                    extra_info = []
                    if usage_time > 0:
                        extra_info.append(f"使用{usage_time}年")
                    if condition:
                        extra_info.append(f"狀態：{condition}")
                    if brand:
                        extra_info.append(f"品牌：{brand}")
                    if original_price:
                        extra_info.append(f"原價：{original_price}")
                    
                    combined_desc = ""
                    if extra_info:
                        combined_desc = "商品資訊：" + "、".join(extra_info)
                    
                    if desc:
                        if combined_desc:
                            combined_desc += "\n\n其他補充：" + desc
                        else:
                            combined_desc = desc
                    
                    return combined_desc
                
                # 連接按鈕事件
                def start_online_processing():
                    gr.Info("開始處理拍賣文案，請稍候...")
                    return gr.update(interactive=False, value="生成中...")
                
                def finish_online_processing(result):
                    if result and "success" in result and result["success"]:
                        gr.Info("拍賣文案生成完成！")
                    elif result and "error" in result:
                        gr.Info(f"處理失敗：{result['error']}")
                    return gr.update(interactive=True, value="生成拍賣文案") if result and ("success" in result or "error" in result) else gr.update()
                
                def process_online_sale_with_form(desc, image, style, usage_time, condition, brand, original_price):
                    # 組合表單資訊
                    combined_desc = combine_form_info(desc, usage_time, condition, brand, original_price)
                    # 調用原有的處理函數並正確處理 generator
                    yield from process_online_sale(combined_desc, image, style)
                
                online_submit.click(
                    start_online_processing,
                    inputs=[],
                    outputs=[online_submit]
                ).then(
                    process_online_sale_with_form, 
                    inputs=[online_desc, online_image, online_style, online_usage_time, online_condition, online_brand, online_original_price],
                    outputs=[online_result_json, online_image_analysis, online_title, online_basic_info, online_carbon, online_search, online_carbon_chart]
                ).then(
                    finish_online_processing,
                    inputs=[online_result_json],
                    outputs=[online_submit]
                )
                
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
                                selling_content = gr.Textbox(label="社群銷售文案", lines=45, interactive=False, show_copy_button=True)
                                
                            with gr.Tab("碳足跡圖表"):
                                selling_carbon_chart = gr.Plot(label="環保效益視覺化")
                                
                            with gr.Tab("碳足跡數值"):
                                selling_carbon = gr.Markdown()
                                
                            with gr.Tab("圖片分析"):
                                selling_image_analysis = gr.Markdown(label="圖片分析結果")
                                
                            with gr.Tab("網路搜尋結果"):
                                selling_search = gr.Markdown(label="網路搜尋結果")
                
                # 連接按鈕事件
                def start_selling_processing():
                    gr.Info("開始生成社群賣文，正在分析圖片和處理內容...")
                    return None
                
                def finish_selling_processing(result):
                    if result and "success" in result and result["success"]:
                        gr.Info("社群賣文生成完成！")
                        return result["full_content"]
                    elif result and "error" in result:
                        gr.Info(f"處理失敗：{result['error']}")
                        return "處理失敗，請檢查輸入"
                    else:
                        return "處理失敗，請檢查輸入"
                
                selling_submit.click(
                    start_selling_processing,
                    inputs=[],
                    outputs=[]
                ).then(
                    process_selling_post, 
                    inputs=[selling_desc, selling_image, selling_price, selling_contact, selling_trade, selling_style],
                    outputs=[selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search]
                ).then(
                    finish_selling_processing,
                    inputs=[selling_result_json],
                    outputs=[selling_content]
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
                                seeking_content = gr.Textbox(label="社群徵求文案", lines=45, interactive=False, show_copy_button=True)
                                
                            with gr.Tab("圖片分析"):
                                seeking_image_analysis = gr.Markdown(label="參考圖片分析結果")
                
                # 連接按鈕事件
                def start_seeking_processing():
                    gr.Info("開始生成徵求文案，正在處理內容...")
                    return None
                
                def finish_seeking_processing(result):
                    if result and "success" in result and result["success"]:
                        gr.Info("徵求文案生成完成！")
                        return result["full_content"]
                    elif result and "error" in result:
                        gr.Info(f"處理失敗：{result['error']}")
                        return "處理失敗，請檢查輸入"
                    else:
                        return "處理失敗，請檢查輸入"
                
                seeking_submit.click(
                    start_seeking_processing,
                    inputs=[],
                    outputs=[]
                ).then(
                    process_seeking_post, 
                    inputs=[
                        seeking_desc, seeking_purpose, seeking_price, seeking_contact, 
                        seeking_trade, seeking_type, seeking_deadline, seeking_image, seeking_style
                    ],
                    outputs=[seeking_result_json, seeking_image_analysis]
                ).then(
                    finish_seeking_processing,
                    inputs=[seeking_result_json],
                    outputs=[seeking_content]
                )
                
        
        # 重置按鈕事件
        def reset_with_notification():
            gr.Info("已重置所有輸入和輸出！")
            return reset_all()
        
        reset_btn.click(
            reset_with_notification,
            inputs=[],
            outputs=[
                online_image, online_desc, online_style, online_result_json, online_image_analysis, 
                online_title, online_basic_info, online_carbon, online_search, online_usage_time, 
                online_condition, online_brand, online_original_price, online_carbon_chart,
                selling_image, selling_desc, selling_price, selling_contact, selling_trade, 
                selling_style, selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search,
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
        3. 在拍賣網站功能中，可填寫詳細的商品資訊表單（使用時間、狀態、品牌等）
        4. 選擇適合的文案風格
        5. 點擊「生成文案」按鈕
        6. 在右側查看生成的文案內容，文案框右上角有複製圖示可直接複製文案
        7. 查看「碳足跡數值」tab 了解環保效益的詳細數據
        8. 查看「碳足跡圖表」tab 觀看互動式環保效益視覺化圖表
        
        ### 系統特色：
        
        - **智能圖片分析**：自動分析商品圖片，提取關鍵特徵
        - **二手商品表單**：專為二手商品設計的詳細資訊表單，包含使用時間、狀態、品牌等
        - **優化內容生成**：根據不同平台特性生成最適合的文案
        - **碳足跡計算**：計算選購二手商品的環境效益，幫助您了解對環境的貢獻
        - **視覺化圖表**：使用互動式儀表板圖表展示環保效益，讓數據更直觀易懂
        - **串流生成**：實時生成和顯示文案內容，讓您能夠即時看到結果
        
        ### 永續價值
        
        使用 ReviveAI 系統不只是為了創建更好的二手商品描述，也是在為環境永續發展盡一份心力。
        每次選擇購買或銷售二手商品，都能減少新商品生產所帶來的碳排放和資源消耗。
        透過視覺化圖表，您可以更清楚地看到每次選擇二手商品對環境帶來的正面影響。
        
        感謝您選擇 ReviveAI，讓我們一起為永續未來努力！
        """, elem_classes=["footer-info"])
        
    return app

# 啟動應用程式
if __name__ == "__main__":
    app = create_app()
    app.launch()
