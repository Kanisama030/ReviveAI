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
