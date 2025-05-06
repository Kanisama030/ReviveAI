from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import time
import json
import asyncio
from agent_client import search_product_info
from templates.content_styles import CONTENT_STYLES

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_product_content(product_description: str, style: str = "normal") -> dict:
    """
    根據選擇的風格生成優化的商品內容
    
    Args:
        product_description (str): 原始商品描述
        style (str): 選擇的文案風格，默認為"normal"
        
    Returns:
        dict: 優化後的商品內容
    """

    # 確保選擇的風格有效，否則使用默認風格
    if style not in CONTENT_STYLES:
        style = "normal"
    
    # 獲取對應的風格模板
    style_template = CONTENT_STYLES[style]

    search_start = time.time()

    # 直接使用商品描述調用agent進行搜尋和分析
    search_result = await search_product_info(product_description)
    
    # 獲取處理後的搜尋結果文本
    search_results = search_result["text"]
    
    search_end = time.time()

    # 生成優化內容，融入選定的風格
    prompt = f"""
    商品描述：{product_description}
    
    網路搜尋資訊：
    {search_results}
    
    請根據以上所有資訊，創建符合「{style_template["name"]}」風格的商品標題和描述。
    以下是這種風格的範例：
    {style_template["examples"][0]}
    {style_template["examples"][1]}
    
    特別注意：
    1. 善用網路搜尋資訊來強化商品描述的專業性和準確性
    2. 確保所有資訊的準確性，不要過度誇大
    3. 重點突出二手商品的價值和環保意義
    4. 嚴格遵循指定的風格要求
    """

    # 使用風格特定的系統消息
    system_message = f"""
    #zh-tw 使用台灣繁體中文回答。
    使用較口語的語氣，文字不要有機器人感。
    {style_template["system_prompt"]}

    【文案優化資訊來源】
    1. 用戶提供的基本資訊
    2. AI 圖像分析結果
    3. 網路搜尋資訊

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
    - 結合兩者提升自然搜尋排名，商品排名和自然流量

    4.資訊整合重點：
    - 優先採用用戶輸入的商品資訊內容，其次為圖片分析結果，接著是網路搜尋結果。
    - 參考圖片分析結果，描述圖片細節，標注任何使用痕跡或瑕疵，突出優勢特徵
    - 將網路資訊的產品資訊自然地融入描述中，保持真實性和準確性

    文案結構需包含：
    "optimized_product_title" （優化商品標題）(40-70字)
    1. 寫在 "optimized_product_title"
    2. 基本架構：商品名稱 + 商品規格 + 商品特色 + 商品狀況描述（全新/九成新等） + 相關關鍵字
    - 加入高搜尋量核心關鍵字
    - 整合長尾關鍵字
    - 清楚標示為二手商品（及使用時間）

    "optimized_product_description" （優化商品描述）
    寫在 "optimized_product_description"，分為以下段落：

    1. "basic_information" 段落：
        - 使用條列式，清楚列出商品完整的基本資訊（規格、材質、尺寸等）
        - 自然植入核心關鍵字

    2.  "features_and_benefits" 段落：
        - 突出商品獨特優勢特色和競爭力
        - 連結使用場景和情境
        - 自然融入相關長尾關鍵字

    3. "current_status" 段落：
        - 描述商品現況、保存狀況
        - 只需描述重點，不要太冗長
        - 若是科技產品，應較仔細寫功能、性能的保存狀態

    4. "sustainable_value" 段落：
        - 具體連結至相關 1~3 個 SDGs 目標並條列，如 SDGs 12
        - 說明選購二手商品對環境的正面影響
        - 連結消費者的環保意識
        
    5. "call_to_action" 最後段落：
    - 說服買家總結購買的優勢，呼籲行動
    - 創造稀缺性和急迫感
    - 在結尾用 # 記號加入SEO關鍵字

    【注意事項】
    1. 保持描述真實準確，不誇大或隱瞞缺陷，清楚標示為二手商品
    2. 適度使用 emoji 增加可讀性
    3. 根據平台特性調整文案風格，結合 SEO 優化原則
    4. 強調透過二手交易為永續發展做出的貢獻
    5. 以上文案是要放在拍賣平台上，你的目標讀者是二手買家，你的口吻需自然
    6. 如果是商品是科技產品，應減少規格、特色的敘述長度，較注重在保存狀態、性能狀態

    請根據以上準則，遵循文案風格要求，為每件商品創造最優化的標題和描述，讓潛在買家產生強烈的購買意願，同時認同其永續價值。
    """

    gpt_start = time.time()  

    response = await client.responses.create(
        model="gpt-4.1-nano",
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
                            "description": "商品基本資訊，條列式分行呈現，包括規格、材料、尺寸等。"
                        },
                        "features_and_benefits": {
                            "type": "string",
                            "description": "商品特色與賣點，強調產品的獨特優勢和競爭力。"
                        },
                        "current_status": {
                            "type": "string",
                            "description": "商品現況重點說明，包括使用痕跡等。"
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
    gpt_end = time.time()
    print(f"AI 搜尋網頁時間: {search_end - search_start:.2f} 秒")
    print(f"AI 生成最終內容時間: {gpt_end - gpt_start:.2f} 秒")
    
    # 將搜尋結果和風格信息加入到返回數據中
    output["search_results"] = search_results
    output["style"] = style
    
    return output

def print_product_content(output: dict):
    print(
        f'''
        網路搜尋結果:
        {output["search_results"]}

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

async def main():
    product_description = "macbook air m1 2020 8g 256g 使用三年 背面小瑕疵"
    print(f"\n開始為商品「{product_description}」生成優化內容")
    print("正在使用 AI 代理進行網路搜尋和分析，這可能需要一些時間...\n")
    
    try:
        output = await generate_product_content(product_description)
        print_product_content(output)
    except Exception as e:
        print(f"生成過程中發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())