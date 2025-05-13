from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import time
import asyncio
from agent_client import search_product_info
from templates.selling_styles import SELLING_STYLES

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_selling_post(
    product_description: str, 
    price: str, 
    contact_info: str = "請私訊詳詢",
    trade_method: str = "面交/郵寄皆可",
    style: str = "normal",  # 使用 selling_styles.py 中的風格
    stream: bool = False    # 新增串流參數
) -> dict:
    """
    生成適合社群平台發布的二手商品銷售文案
    
    Args:
        product_description (str): 原始商品描述
        price (str): 售價
        contact_info (str): 聯絡方式
        trade_method (str): 交易方式
        style (str): 文案風格
        stream (bool): 是否使用串流回應
    Returns:
        dict: 包含生成的社群銷售文案的字典，或者是串流響應物件
    """
    # 確保選擇的風格有效，否則使用默認風格
    if style not in SELLING_STYLES:
        style = "normal"
    
    # 獲取對應的風格模板
    style_template = SELLING_STYLES[style]

    search_start = time.time()
    
    # 獲取商品網路資訊
    search_result = await search_product_info(product_description)
    search_results = search_result["text"]
    
    search_end = time.time()
    
    gpt_start = time.time()
    
    # 系統提示詞，專為社群平台發文設計
    system_message = f"""
    #zh-tw
    你是專業的社群平台二手商品銷售文案專家。

    【文案特點】
    1. 口語化、自然，就像朋友之間聊天的語氣
    2. 簡短有力，避免過長或分段
    3. 不要商業感，避免使用過度專業術語
    4. 適量使用表情符號增加親和力
    5. 突出商品狀況、價格和交易方式等實用信息
    6. 突出購買二手商品的環保價值

    【{style_template["name"]}風格指引】
    {style_template["system_prompt"]}

    【範例參考】
    {style_template["examples"][0]},
    {style_template["examples"][1]}


    【文案結構指引】
    - 開頭簡短吸引注意力，可使用輕鬆的問候或引言
    - 中間部分簡潔描述商品特點、狀況
    - 結尾清楚標示價格、交易方式、聯絡方式
    - 簡短加入環保效益，讓買家感覺做了好事
    - 適當使用hashtag增加曝光度 (2-3個相關標籤)

    生成的內容必須是單一段落，整體篇幅控制在300字以內，就像一般人在社群上發文的風格，既親切又清楚。
    請直接回覆完整的社群貼文內容，包含末尾的hashtag。
    """
    
    # 用戶提示詞
    prompt = f"""
    商品描述：{product_description}
    
    售價：{price}
    
    聯絡方式：{contact_info}
    
    交易方式：{trade_method}
    
    網路搜尋資訊：
    {search_results}
    
    請根據以上所有資訊，創建一段適合在社群平台(如Facebook、Instagram等)發佈的二手商品銷售文案。
    依照系統提示中的【{style_template["name"]}風格指引】來撰寫。
    文案風格要自然、口語化，避免商業感，就像朋友之間分享一樣。
    文案不需要分段，應該是一段連貫的文字。
    請確保包含售價、聯絡方式和交易方式等重要資訊。
    以輕鬆有趣的方式簡短呈現買二手商品的環保價值。
    適當使用表情符號增加親和力，結尾加上2-3個相關hashtag。
    """
    
    if stream:
        # 串流模式
        async def stream_response():
            streaming_response = await client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            
            async for chunk in streaming_response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            gpt_end = time.time()
            print(f"AI 搜尋網頁時間: {search_end - search_start:.2f} 秒")
            print(f"AI 生成社群文案時間: {gpt_end - gpt_start:.2f} 秒")
        
        return stream_response
    else:
        # 非串流模式 (原有功能)
        response = await client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
        )
        
        selling_post = {"selling_post": response.choices[0].message.content}
        gpt_end = time.time()
        
        print(f"AI 搜尋網頁時間: {search_end - search_start:.2f} 秒")
        print(f"AI 生成社群文案時間: {gpt_end - gpt_start:.2f} 秒")

    return selling_post

async def main():
    # 測試範例
    product_description = "macbook air m1 2020 8g 256g 使用兩年 背面小瑕疵"
    price = "$18,000"
    contact_info = "留言或私訊皆可"
    trade_method = "可台北面交或郵寄"
    
    print(f"\n開始為商品「{product_description}」生成社群銷售文案")
    print("正在使用 AI 代理進行網路搜尋和分析，這可能需要一些時間...\n")
    
    try:
        result = await generate_selling_post(
            product_description=product_description,
            price=price,
            contact_info=contact_info,
            trade_method=trade_method,
        )
        print("\n=== 社群銷售文案 ===\n")
        print(result)
        
    except Exception as e:
        print(f"生成過程中發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())