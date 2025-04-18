from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import time
import json
import asyncio
from search_service import search_brave, extract_search_results

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_search_queries(item_name: str) -> str:
    """使用 OpenAI function calling 生成一個綜合搜尋查詢"""
    search_tools = [
        {
        "type": "function",
        "name": "search_products",
            "description": "搜尋產品相關信息，包括規格、特點、評價等",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "一個綜合性的搜尋查詢，能夠獲取產品的規格、特點、評價等全面信息"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }
    ]
    
    response = await client.responses.create(
        model="gpt-4.1-nano",
        input=[
            {"role": "system", "content": "#zh-tw您是一位產品搜尋專家，能根據產品名稱生成最佳的繁體中文的搜尋查詢，到搜尋引擎上搜尋，以獲取產品的全面信息。"},
            {"role": "user", "content": f"請為這個二手產品生成一個綜合性的搜尋查詢，以獲取其詳細信息：{item_name}。查詢應該能夠同時獲取產品的規格、特點、優缺點和使用體驗等全面信息。"}
        ],
        tools=search_tools,
        tool_choice={"type": "function", "name": "search_products"}
    )
    
    default_query = f"{item_name} 詳細規格 特點 評價 優缺點"
    
    try:
        # 獲取第一個 tool_call
        tool_call = response.output[0]
        args = json.loads(tool_call.arguments)
        query = args['query']
        print(f"成功獲取查詢: {query}")
        return query
    except Exception as e:
        pass
    
    # 如果出現任何問題，返回默認查詢
    return default_query


async def generate_product_content(item_name: str) -> dict:
    # 步驟1: 生成搜尋查詢
    search_query = await generate_search_queries(item_name)
    
    # 步驟2: 執行搜尋
    result = await search_brave(search_query)
    search_results = extract_search_results(result)
    
    # 步驟3: 生成優化內容
    prompt = f"""
    商品名稱：{item_name}
    
    網路搜尋資訊：
    {search_results}
    
    請根據以上所有資訊，創建優化的商品標題和描述。
    特別注意：
    1. 善用網路搜尋資訊來強化商品描述的專業性和準確性
    2. 確保所有資訊的準確性，不要過度誇大
    3. 重點突出二手商品的價值和環保意義
    """

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
        - 使用條列式，清楚列出商品完整的基本資訊、特色（規格、材質、尺寸等）
        - 自然植入核心關鍵字

    2.  "features_and_benefits" 興趣(I)段落：
        - 突出獨特優勢和競爭力
        - 連結使用場景和情境
        - 自然融入相關長尾關鍵字

    3. "current_status" 慾望(D)段落：
        - 描述商品現況、保存狀況
        - 描述使用體驗和效益
        - 自然融入社會認同元素

    4. "sustainable_value" 行動(A)段落：
        - 具體連結至相關 SDGs 目標
        - 對應到 1~3 個 SDGs 目標，條列出來，如 SDGs 12
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
    6. 適當在文案中加入網路搜尋的結果，例如商品規格、特色等等，但要確定其真實性
    7. 在文案中自然利用 AIDA 與 FAB 行銷理論的架構
    8. 注意以上文案是要直接放在拍賣平台上，所以你的目標讀者是二手買家，請注意你的口吻

    請根據以上準則，為每件商品創造最優化的標題和描述，讓潛在買家產生強烈的購買意願，同時認同其永續價值。
    """

    start = time.time()  

    response = await client.responses.create(
        model="gpt-4.1-mini",
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
    end = time.time()
    print(f"執行時間: {end - start:.2f} 秒")
    
    # 將搜尋查詢和結果加入到返回數據中
    output["search_query"] = search_query
    output["search_results"] = search_results
    
    return output

def print_product_content(output: dict):
    print(
        f'''
        搜尋查詢:
        {output["search_query"]}
        
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
    item_name = "samsung Galaxy S21"
    output = await generate_product_content(item_name)
    print_product_content(output)

if __name__ == "__main__":
    asyncio.run(main())