from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  

system_message = """
    #zh-tw
    您是一位專精於永續發展的二手商品行銷專家，擅長運用AIDA模型和FAB銷售來優化商品文案，同時具備豐富的電商平台優化經驗。

    【文案優化資訊來源】
    1. 用戶提供的基本資訊
    2. AI 圖像分析結果
    3. 網路搜尋資訊（若有）

    【文案策略核心】
    1. AIDA模型應用：
    - Attention(注意力)：使用吸引眼球的標題關鍵字和emoji
    - Interest(興趣)：突出商品獨特賣點和稀有性
    - Desire(慾望)：強調使用者痛點解決和情感連結
    - Action(行動)：創造購買急迫感和獨特價值主張

    2. FAB銷售法整合：
    - Feature(特色)：詳述商品具體規格和特點
    - Advantage(優勢)：說明此特色帶來的競爭優勢
    - Benefit(效益)：強調對買家生活的實際效益

    3. 關鍵字 SEO 策略：
    - 自然融入核心關鍵字：通用名詞、高搜尋量
    - 加入相關長尾關鍵字：特定需求、競爭較低
    - 避免關鍵字堆砌
    - 結合兩者提升自然搜尋排名

    4.資訊整合重點：
    - 優先採用用戶輸入的商品資訊內容，其次為圖片分析結果，接著是網路搜尋結果。
    - 將網路搜尋到的產品資訊自然地融入描述中
    - 使用搜尋結果來補充和驗證產品規格
    - 保持網路資訊加入描述的真實性和準確性

    "optimized_product_title" （優化商品標題）(40-70字)
    1. 寫在 "optimized_product_title"
    2. 基本架構：商品名稱 + 商品規格 + 商品特色 + 商品狀況描述（全新/九成新等） + 相關關鍵字
    - 加入高搜尋量核心關鍵字
    - 整合長尾關鍵字
    - 清楚標示為二手商品（及使用時間）

    "optimized_product_description" （優化商品描述）
    寫在 "optimized_product_description"，依AIDA架構分為以下：

    1. "basic_information" 注意力(A)段落：
        - 使用條列式，清楚列出商品完整的基本資訊（規格、材質、尺寸等）
        - 使用 FAB 法則說明主要特色
        - 核心關鍵字自然植入

    2.  "features_and_benefits" 興趣(I)段落：
        - 突出獨特優勢和競爭力
        - 連結使用場景和情境
        - 加入相關長尾關鍵字

    3. "current_status" 慾望(D)段落：
        - 描述商品現況、保存狀況
        - 描述使用體驗和效益
        - 加入社會認同元素

    4. "sustainable_value" 行動(A)段落：
        - 具體連結至相關 SDGs 目標
        - 對應到 1~3 個 SDGs 目標，用符號表現條列式，如 * SDGs 12
        - 說明選購二手商品對環境的正面影響
        - 連結消費者的環保意識
        
    5. "call_to_action" 最後段落：
    - 說服買家總結購買的優勢，呼籲行動
    - 創造稀缺性和急迫感
    - 在結尾用 # 記號加入SEO關鍵字

    【注意事項】
    1. 保持描述真實準確，不誇大或隱瞞缺陷，清楚標示為二手商品
    2. 適度使用 emoji 增加可讀性，但不過度
    3. 根據平台特性調整文案風格，結合 SEO 優化原則，如使用關鍵字、長尾關鍵字，提升商品排名和自然流量
    4. 整合圖片訊息，描述圖片中可見的細節，標注任何使用痕跡或瑕疵，突出商品優勢特徵
    5. 強調透過二手交易為永續發展做出的貢獻
    6. 適當在文案中加入網路搜尋的結果，例如商品規格、特色等等，但要確定其真實性。

    請根據以上準則，為每件商品創造最優化的標題和描述，讓潛在買家產生強烈的購買意願，同時認同其永續價值。
    """


    # 商品類型: {item_type}
    # 商品名稱: {item_name}
    # 商品描述: {item_description}
    # 圖片分析: {image_analysis}
    
    # 搜尋資訊: {search_results if search_results else "無可用的搜尋資訊"}

# 組合所有資訊

prompt = f"""
    商品名稱：samsung Galaxy S21
    請根據以上所有資訊，創建優化的商品標題和描述。
    特別注意：
    1. 如果有搜尋資訊，請善用這些資訊來強化商品描述的專業性和準確性
    2. 確保所有資訊的準確性，不要過度誇大
    3. 重點突出二手商品的價值和環保意義
    """
start = time.time()  

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ],
    text={
        "format": {
            "type": "json_schema",
            "name": "product_schema",
            "schema": {
                "type": "object",
                "properties": {
                "optimized_product_title": {
                    "type": "string",
                    "description": "優化商品標題，具有吸引力"
                },
                "optimized_product_description": {
                    "type": "object",
                    "properties": {
                    "basic_information": {
                        "type": "string",
                        "description": "商品基本資訊，包括規格、材料、尺寸等。"
                    },
                    "features_and_benefits": {
                        "type": "string",
                        "description": "商品特色與賣點，強調產品的獨特優勢和競爭力。"
                    },
                    "current_status": {
                        "type": "string",
                        "description": "商品現況詳細說明，包括使用痕跡等。"
                    },
                    "sustainable_value": {
                        "type": "string",
                        "description": "永續價值，連結至相關的 SDGs 目標，並解釋購買二手產品的正面影響。"
                    },
                    "call_to_action": {
                        "type": "string",
                        "description": "呼籲行動，令人信服的結論，總結購買優勢，並使用 SEO 關鍵字創造迫切性。"
                    }
                    },
                    "required": [
                    "basic_information",
                    "features_and_benefits",
                    "current_status",
                    "sustainable_value",
                    "call_to_action"
                    ],
                    "additionalProperties": False
                }
                },
                "required": [
                "optimized_product_title",
                "optimized_product_description"
                ],
                "additionalProperties": False
            },
            "strict": True
        }
    }
)

output = json.loads(response.output_text)

print(
f'''
優化商品標題:
{output["optimized_product_title"]}

優化商品描述:
---📦 商品基本資訊：---
{output["optimized_product_description"]["basic_information"]}

---✨ 商品特色與賣點：---
{output["optimized_product_description"]["features_and_benefits"]}

---📝 商品現況詳細說明：---
{output["optimized_product_description"]["current_status"]}

---💚 永續價值：--- 
{output["optimized_product_description"]["sustainable_value"]}

{output["optimized_product_description"]["call_to_action"]}
'''
)

end=time.time()
print(f"執行時間: {end - start:.2f} 秒")
