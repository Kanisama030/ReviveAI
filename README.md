# ReviveAI API 服務

這是一個用於二手商品優化的 API 服務，提供圖片分析、內容優化、網路搜尋和碳足跡計算功能。

## 功能概述

本 API 服務提供四個主要端點：

1. **圖片分析服務** (`/api/image_service`): 分析商品圖片並提供詳細描述
2. **內容優化服務** (`/api/content_service`): 優化商品描述內容
3. **搜尋代理服務** (`/api/search_agent`): 使用 AI 代理搜尋產品相關資訊
4. **碳足跡計算服務** (`/api/calculate_carbon`): 計算商品的碳足跡和環境效益

## 安裝和設定

### 必要條件

- Python 3.8+
- 一個有效的 OpenAI API 金鑰
- 一個有效的 Brave Search API 金鑰

### 安裝步驟

1. 複製專案
2. 安裝所需套件:
```
pip install -r requirements.txt
```
3. 建立 `.env` 檔案並設定以下變數:
```
OPENAI_API_KEY=your_openai_api_key
BRAVE_SEARCH_API_KEY=your_brave_search_api_key
```

## 啟動 API 服務

執行以下命令啟動服務：

```
python api.py
```

或者使用 uvicorn 直接啟動：

```
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

服務預設會在 `http://localhost:8000` 啟動。

## API 端點說明

### 1. 圖片分析服務

**端點：** `POST /api/image_service`

**請求格式：**
- Content-Type: `multipart/form-data`
- 參數:
  - `image`: 商品圖片檔案 (必填)

**回應格式：**
```json
{
  "success": true,
  "data": {
    "analysis": "商品分析結果..."
  },
  "error": null
}
```

### 2. 內容優化服務

**端點：** `POST /api/content_service`

**請求格式：**
```json
{
  "description": "原始商品描述"
}
```

**回應格式：**
```json
{
  "success": true,
  "data": {
    "optimized_product_title": "優化標題",
    "optimized_product_description": {
      "basic_information": "基本資訊",
      "features_and_benefits": "特色與賣點",
      "current_status": "現況說明",
      "sustainable_value": "永續價值",
      "call_to_action": "行動呼籲"
    },
    "search_results": "搜尋結果"
  },
  "error": null
}
```

### 3. 搜尋代理服務

**端點：** `POST /api/search_agent`

**請求格式：**
```json
{
  "query": "商品查詢"
}
```

**回應格式：**
```json
{
  "success": true,
  "data": {
    "search_results": "搜尋結果..."
  },
  "error": null
}
```

### 4. 碳足跡計算服務

**端點：** `POST /api/calculate_carbon`

**請求格式：**
```json
{
  "product_description": "商品描述"
}
```

**回應格式：**
```json
{
  "success": true,
  "data": {
    "selected_product": {
      "product_name": "產品名稱",
      "company": "公司名稱",
      "carbon_footprint": 123.45,
      "similarity_score": 0.98,
      "details": "詳細資訊"
    },
    "saved_carbon": 61.73,
    "environmental_benefits": {
      "trees": "2.9",
      "car_km": "246.9"
    },
    "selection_reason": "選擇原因"
  },
  "error": null
}
```

## 錯誤處理

所有 API 回應都遵循以下格式：

```json
{
  "success": true|false,
  "data": {...} | null,
  "error": "錯誤訊息" | null
}
```

## 注意事項

- 圖片分析服務目前僅支援 JPG、PNG 和 WebP 格式的圖片
- 所有文字回應均為繁體中文
- API 請求中包含的所有資訊必須是準確的 