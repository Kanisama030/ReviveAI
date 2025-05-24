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
        # 添加頁面標題與logo
        with gr.Row(elem_classes=["header-row"]):
            # Logo 圖片
            gr.Image(
                value="/Users/chenyirui/Project/ReviveAI/pics/small_logo.png",
                show_label=False,
                container=False,
                height=100,
                width=100,
                interactive=False,
                show_fullscreen_button=False,
                show_download_button=False,
                elem_classes=["logo-image"]
            )
            # 標題文字區域
            with gr.Column():
                gr.Markdown("# ReviveAI - 二手商品文案優化助手", elem_classes=["page-title"])
                gr.Markdown("### AI 驅動的智能文案助手，讓每件二手商品都有最佳故事！", elem_classes=["sub-title"])
                

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
                        
                        online_product_name = gr.Textbox(
                            label="商品名稱", 
                            placeholder="例如：iPhone 14 Pro、MacBook Pro、Nike Air Jordan...",
                            info="請輸入商品的名稱或型號"
                        )
                        
                        online_usage_time = gr.Slider(
                            minimum=0, 
                            maximum=10, 
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
                        
                        online_desc = gr.Textbox(
                            label="其他補充說明 (選填)", 
                            placeholder="可以補充商品保存狀況、購買原因、使用心得、商品特色、原價等...", 
                            lines=3,
                            info="任何額外的商品資訊或補充說明"
                        )
                        
                        online_style = gr.Radio(
                            ["標準專業", "輕鬆活潑", "正式商務", "故事體驗"], 
                            label="文案風格", 
                            value="標準專業"
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
                
                # 範例功能
                gr.Markdown("### 📝 快速範例")
                online_examples = gr.Examples(
                    examples=[
                        [
                            "pics/test1.jpg",  # 圖片路徑
                            "MacBook Air M1 2020",  # 商品名稱
                            2.0,  # 使用時間
                            "八成新",  # 商品狀態
                            "Apple",  # 品牌
                            "256GB 儲存空間，8GB 記憶體，玫瑰金色。平時主要用於文書處理和上網，保存良好，但背後有輕微使用痕跡。原價約32,000元，現在想換新機所以出售。",  # 補充說明
                            "輕鬆活潑"  # 文案風格
                        ]
                    ],
                    inputs=[
                        online_image, 
                        online_product_name, 
                        online_usage_time, 
                        online_condition, 
                        online_brand, 
                        online_desc, 
                        online_style
                    ],
                    examples_per_page=1,
                    label="點擊範例快速填入表單",
                    cache_examples=False
                )
                
                # 組合表單資訊函數
                def combine_form_info(product_name, desc, usage_time, condition, brand):
                    # 構建額外的描述資訊
                    extra_info = []
                    if product_name:
                        extra_info.append(f"商品名稱：{product_name}")
                    if usage_time > 0:
                        extra_info.append(f"使用{usage_time}年")
                    if condition:
                        extra_info.append(f"狀態：{condition}")
                    if brand:
                        extra_info.append(f"品牌：{brand}")
                    
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
                
                def process_online_sale_with_form(product_name, desc, image, style, usage_time, condition, brand):
                    # 組合表單資訊
                    combined_desc = combine_form_info(product_name, desc, usage_time, condition, brand)
                    # 調用原有的處理函數並正確處理 generator
                    yield from process_online_sale(combined_desc, image, style)
                
                online_submit.click(
                    start_online_processing,
                    inputs=[],
                    outputs=[online_submit]
                ).then(
                    process_online_sale_with_form, 
                    inputs=[online_product_name, online_desc, online_image, online_style, online_usage_time, online_condition, online_brand],
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
                        
                        # 二手商品表單區域
                        gr.Markdown("### 商品資訊", elem_classes=["form-section"])
                        
                        selling_product_name = gr.Textbox(
                            label="商品名稱", 
                            placeholder="例如：iPhone 14 Pro、MacBook Pro、Nike Air Jordan...",
                            info="請輸入商品的名稱或型號"
                        )
                        
                        selling_usage_time = gr.Slider(
                            minimum=0, 
                            maximum=10, 
                            value=2, 
                            step=0.5,
                            label="使用時間 (年)",
                            info="商品已使用多久時間"
                        )
                        
                        selling_condition = gr.Dropdown(
                            choices=["全新未拆", "近全新", "九成新", "八成新", "七成新", "六成新", "功能正常"], 
                            value="八成新",
                            label="商品狀態",
                            info="請選擇商品的保存狀況"
                        )
                        
                        selling_brand = gr.Textbox(
                            label="品牌", 
                            placeholder="例如：Apple、Sony、Nike...",
                            info="商品的品牌名稱"
                        )
                        
                        selling_price = gr.Textbox(label="商品售價", placeholder="例如：$18,000")
                        selling_contact = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                        selling_trade = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                        
                        selling_desc = gr.Textbox(
                            label="其他補充說明 (選填)", 
                            placeholder="可以補充商品保存狀況、購買原因、使用心得、商品特色、原價等...", 
                            lines=3,
                            info="任何額外的商品資訊或補充說明"
                        )
                        
                        selling_style = gr.Radio(
                            ["標準實用", "故事體驗", "簡約精要", "超值優惠"], 
                            label="文案風格", 
                            value="標準實用"
                        )
                        selling_submit = gr.Button("生成社群賣文", variant="primary", elem_classes=["submit-btn"])
                    
                    # 右側輸出區域
                    with gr.Column(scale=2):
                        with gr.Tabs() as selling_output_tabs:
                            with gr.Tab("文案輸出"):
                                selling_result_json = gr.JSON(visible=False)  # 儲存完整結果
                                selling_content = gr.Textbox(label="社群銷售文案", lines=20, interactive=False, show_copy_button=True)
                                
                            with gr.Tab("碳足跡圖表"):
                                selling_carbon_chart = gr.Plot(label="環保效益視覺化")
                                
                            with gr.Tab("碳足跡數值"):
                                selling_carbon = gr.Markdown()
                                
                            with gr.Tab("圖片分析"):
                                selling_image_analysis = gr.Markdown(label="圖片分析結果")
                                
                            with gr.Tab("網路搜尋結果"):
                                selling_search = gr.Markdown(label="網路搜尋結果")
                
                # 範例功能
                gr.Markdown("### 📝 快速範例")
                selling_examples = gr.Examples(
                    examples=[
                        [
                            "pics/test1.jpg",  # 圖片
                            "MacBook Air M1 2020",  # 商品名稱
                            3.0,  # 使用時間
                            "八成新",  # 商品狀態
                            "Apple",  # 品牌
                            "$10,000",  # 商品售價
                            "請私訊詳詢",  # 聯絡方式
                            "面交/郵寄/交貨便",  # 交易方式
                            "256GB 儲存空間，8GB 記憶體，玫瑰金色。平時主要用於文書處理，保存良好但背後有小瑕疵。誠心出售，可議價。",  # 補充說明
                            "超值優惠"  # 文案風格
                        ]
                    ],
                    inputs=[
                        selling_image,
                        selling_product_name,
                        selling_usage_time,
                        selling_condition,
                        selling_brand,
                        selling_price,
                        selling_contact,
                        selling_trade,
                        selling_desc,
                        selling_style
                    ],
                    examples_per_page=1,
                    label="點擊範例快速填入表單",
                    cache_examples=False
                )
                
                # 連接按鈕事件 - 使用串流模式，參考拍賣網站的實現
                def start_selling_processing():
                    gr.Info("開始處理社群賣文，請稍候...")
                    return gr.update(interactive=False, value="生成中...")
                
                def finish_selling_processing(result):
                    if result and "success" in result and result["success"]:
                        gr.Info("社群賣文生成完成！")
                    elif result and "error" in result:
                        gr.Info(f"處理失敗：{result['error']}")
                    return gr.update(interactive=True, value="生成社群賣文") if result and ("success" in result or "error" in result) else gr.update()
                
                # 組合社群賣文表單資訊函數
                def combine_selling_form_info(product_name, desc, usage_time, condition, brand):
                    # 構建額外的描述資訊
                    extra_info = []
                    if product_name:
                        extra_info.append(f"商品名稱：{product_name}")
                    if usage_time > 0:
                        extra_info.append(f"使用{usage_time}年")
                    if condition:
                        extra_info.append(f"狀態：{condition}")
                    if brand:
                        extra_info.append(f"品牌：{brand}")
                    
                    combined_desc = ""
                    if extra_info:
                        combined_desc = "商品資訊：" + "、".join(extra_info)
                    
                    if desc:
                        if combined_desc:
                            combined_desc += "\n\n其他補充：" + desc
                        else:
                            combined_desc = desc
                    
                    return combined_desc
                
                def process_selling_post_with_streaming(product_name, desc, image, price, contact_info, trade_method, usage_time, condition, brand, style):
                    """處理社群賣文並直接串流輸出到各個組件"""
                    # 組合表單資訊
                    combined_desc = combine_selling_form_info(product_name, desc, usage_time, condition, brand)
                    for result in process_selling_post(combined_desc, image, price, contact_info, trade_method, style):
                        if len(result) == 5:  # 正常回應：(json, image_analysis, carbon, carbon_chart, search)
                            result_json, image_analysis, carbon, carbon_chart, search = result
                            
                            # 從 result_json 中提取文案內容
                            if result_json and "success" in result_json and result_json["success"]:
                                content = result_json.get("full_content", "")
                            else:
                                content = ""
                            
                            yield result_json, image_analysis, carbon, carbon_chart, search, content
                        else:
                            # 錯誤情況
                            yield result + (None,)  # 補齊長度
                
                selling_submit.click(
                    start_selling_processing,
                    inputs=[],
                    outputs=[selling_submit]
                ).then(
                    process_selling_post_with_streaming, 
                    inputs=[selling_product_name, selling_desc, selling_image, selling_price, selling_contact, selling_trade, selling_usage_time, selling_condition, selling_brand, selling_style],
                    outputs=[selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search, selling_content]
                ).then(
                    finish_selling_processing,
                    inputs=[selling_result_json],
                    outputs=[selling_submit]
                )
                
            
            # =============== 社群徵文 TAB ===============
            with gr.Tab("社群徵文"):
                with gr.Row():
                    # 左側輸入區域
                    with gr.Column(scale=1):
                        seeking_image = gr.Image(label="上傳參考圖片 (選填)", type="filepath")
                        
                        # 徵求商品表單區域
                        gr.Markdown("### 徵求資訊", elem_classes=["form-section"])
                        
                        seeking_product_name = gr.Textbox(
                            label="商品名稱", 
                            placeholder="例如：iPhone 14 Pro、MacBook Pro、Nike Air Jordan...",
                            info="請輸入想徵求的商品名稱或型號"
                        )
                        
                        seeking_purpose = gr.Textbox(label="徵求目的", placeholder="請說明徵求目的...", lines=2)
                        seeking_price = gr.Textbox(label="期望價格", placeholder="例如：希望不超過 $5,000")
                        seeking_contact = gr.Textbox(label="聯絡方式", value="請私訊詳詢")
                        seeking_trade = gr.Textbox(label="交易方式", value="面交/郵寄皆可")
                        
                        seeking_deadline = gr.Textbox(label="徵求時效", value="越快越好")
                        seeking_type = gr.Radio(
                            ["購買", "租借"], 
                            label="徵求類型", 
                            value="購買"
                        )
                        
                        seeking_desc = gr.Textbox(
                            label="其他補充說明 (選填)", 
                            placeholder="可以補充徵求的詳細需求、使用目的、希望的品牌或型號等...", 
                            lines=3,
                            info="任何額外的徵求需求或補充說明"
                        )
                        
                        seeking_style = gr.Radio(
                            ["標準親切", "急需緊急", "預算有限", "收藏愛好"], 
                            label="文案風格", 
                            value="標準親切"
                        )
                        seeking_submit = gr.Button("生成徵求文案", variant="primary", elem_classes=["submit-btn"])
                    
                    # 右側輸出區域
                    with gr.Column(scale=2):
                        with gr.Tabs() as seeking_output_tabs:
                            with gr.Tab("文案輸出"):
                                seeking_result_json = gr.JSON(visible=False)  # 儲存完整結果
                                seeking_content = gr.Textbox(label="社群徵求文案", lines=20, interactive=False, show_copy_button=True)
                                
                            with gr.Tab("圖片分析"):
                                seeking_image_analysis = gr.Markdown(label="參考圖片分析結果")
                
                # 範例功能
                gr.Markdown("### 📝 快速範例")
                seeking_examples = gr.Examples(
                    examples=[
                        [
                            "MacBook Air M1",  # 商品名稱
                            "學習程式設計",  # 徵求目的
                            "希望不超過 $7,000",  # 期望價格
                            "Line: 0900000000",  # 聯絡方式
                            "台北面交佳",  # 交易方式
                            "兩週內",  # 徵求時效
                            "購買",  # 徵求類型
                            "pics/test1.jpg",  # 參考圖片
                            "剛開始學程式設計，需要一台輕薄的筆電。希望找到狀況良好的 MacBook Air M1，256GB 以上佳。預算有限，但會好好愛惜！",  # 補充說明
                            "預算有限"  # 文案風格
                        ]
                    ],
                    inputs=[
                        seeking_product_name,
                        seeking_purpose,
                        seeking_price,
                        seeking_contact,
                        seeking_trade,
                        seeking_deadline,
                        seeking_type,
                        seeking_image,
                        seeking_desc,
                        seeking_style
                    ],
                    examples_per_page=1,
                    label="點擊範例快速填入表單",
                    cache_examples=False
                )
                
                # 連接按鈕事件 - 使用串流模式，參考拍賣網站和社群賣文的實現
                def start_seeking_processing():
                    gr.Info("開始生成徵求文案，請稍候...")
                    return gr.update(interactive=False, value="生成中...")
                
                def finish_seeking_processing(result):
                    if result and "success" in result and result["success"]:
                        gr.Info("徵求文案生成完成！")
                    elif result and "error" in result:
                        gr.Info(f"處理失敗：{result['error']}")
                    return gr.update(interactive=True, value="生成徵求文案") if result and ("success" in result or "error" in result) else gr.update()
                
                # 組合社群徵文表單資訊函數
                def combine_seeking_form_info(product_name, desc):
                    # 構建描述資訊
                    combined_desc = ""
                    if product_name:
                        combined_desc = f"徵求商品：{product_name}"
                    
                    if desc:
                        if combined_desc:
                            combined_desc += "\n\n其他補充說明：" + desc
                        else:
                            combined_desc = desc
                    
                    return combined_desc
                
                def process_seeking_post_with_streaming(product_name, desc, purpose, price, contact_info, trade_method, type_val, deadline, image, style):
                    """處理社群徵文並直接串流輸出到各個組件"""
                    # 組合表單資訊
                    combined_desc = combine_seeking_form_info(product_name, desc)
                    for result in process_seeking_post(combined_desc, purpose, price, contact_info, trade_method, type_val, deadline, image, style):
                        if len(result) == 2:  # 正常回應：(json, image_analysis)
                            result_json, image_analysis = result
                            
                            # 從 result_json 中提取文案內容
                            if result_json and "success" in result_json and result_json["success"]:
                                content = result_json.get("full_content", "")
                            else:
                                content = ""
                            
                            yield result_json, image_analysis, content
                        else:
                            # 錯誤情況
                            yield result + (None,)  # 補齊長度
                
                seeking_submit.click(
                    start_seeking_processing,
                    inputs=[],
                    outputs=[seeking_submit]
                ).then(
                    process_seeking_post_with_streaming, 
                    inputs=[
                        seeking_product_name, seeking_desc, seeking_purpose, seeking_price, seeking_contact, 
                        seeking_trade, seeking_type, seeking_deadline, seeking_image, seeking_style
                    ],
                    outputs=[seeking_result_json, seeking_image_analysis, seeking_content]
                ).then(
                    finish_seeking_processing,
                    inputs=[seeking_result_json],
                    outputs=[seeking_submit]
                )
                
        
        # 重置按鈕事件
        def reset_with_notification():
            gr.Info("已重置所有輸入和輸出！")
            return reset_all()
        
        reset_btn.click(
            reset_with_notification,
            inputs=[],
            outputs=[
                online_image, online_product_name, online_desc, online_style, online_result_json, online_image_analysis, 
                online_title, online_basic_info, online_carbon, online_search, online_usage_time, 
                online_condition, online_brand, online_carbon_chart,
                selling_image, selling_product_name, selling_desc, selling_price, selling_contact, selling_trade, 
                selling_usage_time, selling_condition, selling_brand,
                selling_style, selling_result_json, selling_image_analysis, selling_carbon, selling_carbon_chart, selling_search, selling_content,
                seeking_product_name, seeking_desc, seeking_purpose, seeking_price, seeking_contact, seeking_trade,
                seeking_type, seeking_deadline, seeking_image, seeking_style, seeking_result_json,
                seeking_image_analysis, seeking_content
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
