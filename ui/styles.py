"""
ReviveAI 應用程式的 CSS 樣式配置
"""

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

/* 自定義標籤頁選擇顏色 - 強化綠色版本 */
.gradio-container .tabs .tab-nav button.selected,
.gradio-container .tabs .tab-nav button[data-tab-select="true"],
.gradio-container .tabs button.selected,
.gradio-container div.tab-nav button.selected,
.gradio-container div.tab-nav button[aria-selected="true"],
.gradio-container .tab-nav button.selected,
.gradio-container button.selected[data-testid]:not(.reset-btn):not(.submit-btn):not(.copy-btn) {
    border-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
    background-color: rgba(109, 226, 156, 0.15) !important;
    border-bottom: 2px solid var(--primary-color) !important;
    border-bottom-color: var(--primary-color) !important;
}

/* 強制覆蓋所有可能的藍色樣式 */
.gradio-container button.selected:not(.reset-btn):not(.submit-btn):not(.copy-btn),
.gradio-container .tabs button[aria-selected="true"],
.gradio-container .tabs button[data-tab-id].selected {
    color: var(--primary-color) !important;
    border-bottom: 2px solid var(--primary-color) !important;
    border-bottom-color: var(--primary-color) !important;
    background-color: rgba(109, 226, 156, 0.1) !important;
}

/* 針對所有 tab 相關元素的底線顏色 */
.gradio-container .tabs [role="tab"][aria-selected="true"],
.gradio-container .tabs button[role="tab"][aria-selected="true"],
.gradio-container [data-testid*="tab"] button.selected,
.gradio-container .tab-nav > button.selected {
    border-bottom: 2px solid var(--primary-color) !important;
    border-bottom-color: var(--primary-color) !important;
    color: var(--primary-color) !important;
}

/* hover 效果 */
.gradio-container .tabs .tab-nav button:hover,
.gradio-container .tabs > .tab-nav > button:hover,
.gradio-container .tab-nav button:hover {
    color: var(--primary-color) !important;
    background-color: rgba(109, 226, 156, 0.05) !important;
    border-bottom-color: rgba(109, 226, 156, 0.5) !important;
}

/* 針對 Gradio v4+ 的額外樣式 */
.gradio-container .tabs > div > .tab-nav > button.selected,
.gradio-container .tabitem button.selected,
.gradio-container button[data-tab-select="true"],
.gradio-container .tabs > .tab-nav > button[aria-selected="true"] {
    color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
    border-bottom-color: var(--primary-color) !important;
    background: rgba(109, 226, 156, 0.15) !important;
}

/* 全域覆蓋任何藍色底線 */
.gradio-container * {
    --primary-600: var(--primary-color) !important;
    --primary-500: var(--primary-color) !important;
}

/* 特別針對藍色樣式的覆蓋 */
.gradio-container .tabs button {
    --color-accent: var(--primary-color) !important;
}

.tabs {
    margin-bottom: 20px;
}

/* Tab 樣式優化：大字體、均分寬度、置中對齊 */
.gradio-container .tabs .tab-nav,
.gradio-container .tabs > .tab-nav,
.gradio-container div.tab-nav {
    display: flex !important;
    width: 100% !important;
}

/* 只針對頂層 tab 按鈕，排除包含 SVG 或上傳功能的按鈕 */
.gradio-container .tabs .tab-nav button:not(:has(svg)):not(:has(.feather-upload)),
.gradio-container .tabs > .tab-nav > button:not(:has(svg)):not(:has(.feather-upload)) {
    flex: 1 !important;
    font-size: 1.2em !important;
    font-weight: 600 !important;
    text-align: center !important;
    padding: 12px 20px !important;
    margin: 0 !important;
    min-width: 0 !important;
    border-radius: 8px 8px 0 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* 確保 tab 按鈕平均分配寬度和文字置中，排除上傳相關 */
.gradio-container .tabs button[role="tab"]:not(:has(svg)):not(:has(.feather-upload)),
.gradio-container .tabs [role="tab"]:not(:has(svg)):not(:has(.feather-upload)) {
    flex: 1 !important;
    font-size: 1.2em !important;
    font-weight: 600 !important;
    text-align: center !important;
    padding: 12px 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* 針對 tab 內的文字元素，排除上傳相關 */
.gradio-container .tabs button:not(:has(svg)) span,
.gradio-container .tabs [role="tab"]:not(:has(svg)) span {
    text-align: center !important;
    width: 100% !important;
    display: block !important;
}

/* 確保上傳 SVG 圖示保持正常大小 */
.gradio-container svg.feather-upload,
.gradio-container .feather-upload {
    width: 90% !important;
    height: 90% !important;
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

/* 文案輸出區域的標題樣式 - 針對正確的 DOM 元素，使用更適合閱讀的顏色 */
.gradio-container span[data-testid="block-info"] {
    font-size: 1.3em !important;
    font-weight: 700 !important;
    color: #e8e8e8 !important;
    margin-bottom: 12px !important;
    display: block !important;
}

/* 通用 label 樣式 */
.gradio-container label {
    font-size: 1.1em !important;
    font-weight: 600 !important;
    color: var(--primary-color) !important;
}

/* Copy 按鈕樣式 - 放大尺寸 */
.gradio-container .copy-button {
    width: 28px !important;
    height: 28px !important;
    min-width: 28px !important;
    min-height: 28px !important;
    padding: 6px !important;
}

/* Copy 按鈕內的 SVG 圖示 */
.gradio-container .copy-button svg {
    width: 100% !important;
    height: 100% !important;
}

/* Copy 按鈕 hover 效果 */
.gradio-container .copy-button:hover {
    background-color: rgba(109, 226, 156, 0.1) !important;
    border-color: var(--primary-color) !important;
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

/* 頁首區域樣式 */
.header-row {
    margin-bottom: 1.5rem !important;
    align-items: center !important;
    gap: 1rem !important;
}

/* Logo 圖片樣式 */
.logo-image {
    max-width: 100px !important;
    max-height: 100px !important;
    width: 100px !important;
    height: 100px !important;
    border-radius: 12px !important;
    box-shadow: none !important;
    border: none !important;
}

/* Logo 圖片容器樣式 */
.logo-image button,
.logo-image .image-frame,
.logo-image img {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* 針對 Gradio 圖片組件的額外樣式 */
.gradio-container .logo-image button {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: none !important;
    background: none !important;
}

.gradio-container .logo-image .image-frame {
    border-radius: 12px !important;
    overflow: hidden !important;
}

.gradio-container .logo-image img {
    border-radius: 12px !important;
}

/* 頁面標題樣式 - 綠色 */
.page-title h1 {
    color: var(--primary-color) !important;
    font-weight: 700 !important;
}

/* 副標題樣式 - 淺灰色，不粗體 */
.sub-title h3 {
    color: #a0a0a0 !important;
    font-weight: 400 !important;
    }

"""
