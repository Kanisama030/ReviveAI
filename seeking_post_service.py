from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import time
import asyncio
from templates.seeking_styles import SEEKING_STYLES

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_seeking_post(
    product_description: str, 
    purpose: str,
    expected_price: str,
    contact_info: str = "請私訊詳詢",
    trade_method: str = "面交/郵寄皆可",
    seeking_type: str = "buy",  # "buy" 或 "rent"
    deadline: str = "越快越好",
    style: str = "normal"  # 參考 seeking_styles.py 風格
) -> dict:
    """
    生成適合社群平台發布的二手商品徵求文案
    
    Args:
        product_description (str): 徵求的商品描述
        purpose (str): 徵求目的/用途
        expected_price (str): 期望價格
        contact_info (str): 聯絡方式
        trade_method (str): 交易方式
        seeking_type (str): 徵求類型，購買或租借
        deadline (str): 徵求時效
        style (str): 文案風格
    Returns:
        dict: 包含生成的社群徵品文案的字典
    """
    # 確保選擇的風格有效，否則使用默認風格
    if style not in SEEKING_STYLES:
        style = "normal"
    
    # 獲取對應的風格模板
    style_template = SEEKING_STYLES[style]

    # 系統提示詞，專為徵品文案設計
    system_message = f"""
    #zh-tw
    你是專業的社群平台二手商品徵求文案專家。

    【文案特點】
    1. 對話感強，親切自然，就像跟朋友聊天，不要太討好、諂媚
    2. 清晰表達需求和用途，讓讀者明確知道徵求什麼和為什麼需要
    3. 突出環保價值和資源共享理念
    4. 適量使用表情符號增加親和力
    5. 清楚標示期望價格、交易地點、聯絡方式和時效性

    【徵求類型差異】
    {'- 租借型：強調暫時性需求，說明使用時間，強調物盡其用、資源共享的永續理念' if seeking_type == 'rent' else '- 購買型：強調長期需求，說明使用計畫，強調二手選購減少新品生產的環保價值'}

    【{style_template["name"]}風格指引】
    {style_template["system_prompt"]}

    【範例參考】
    {style_template["examples"][0]},
    {style_template["examples"][1]}
    
    【文案結構】
    - 開頭：友善問候 + 簡短自我介紹 + 徵求目的
    - 中間：詳細描述需求（品項/規格/狀況）+ 使用目的
    - 結尾：清楚標示期望價格、交易地點、聯絡方式和時效性
    - 末尾：簡短環保理念 + 2-3個相關標籤

    生成的內容必須是單一段落，整體篇幅控制在300字以內，語氣親切自然。
    請直接回覆完整的社群徵品貼文內容，包含末尾的hashtag。
    """
    
    # 用戶提示詞
    prompt = f"""
    徵求商品描述：{product_description}
    
    徵求目的：{purpose}
    
    期望價格：{expected_price}
    
    交易方式：{trade_method}

    聯絡方式：{contact_info}
    
    徵求時效：{deadline}
    
    徵求類型：{'租借' if seeking_type == 'rent' else '購買'}
        
    請根據以上所有資訊，創建一段適合在社群平台(如Facebook、Instagram等)發佈的二手商品徵求文案。
    文案風格要自然、親切有對話感，就像朋友之間分享一樣。
    文案不需要分段，應該是一段連貫的文字。
    請確保包含徵求目的、期望價格、聯絡方式和交易方式等重要資訊。
    依照系統提示中的【{style_template["name"]}風格指引】來撰寫。
    以輕鬆有趣的方式簡短呈現{'租借共享' if seeking_type == 'rent' else '購買二手商品'}的環保價值。
    適當使用表情符號增加親和力，結尾加上2-3個相關hashtag。
    """

    gpt_start = time.time()

    # 執行 GPT 生成
    response = await client.responses.create(
        model="gpt-4.1-nano",
        input=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
    )
    
    gpt_end = time.time()
    print(f"GPT 執行時間: {gpt_end - gpt_start:.2f} 秒")

    seeking_post = {"seeking_post": response.output_text}
    
    return seeking_post


async def main():
    # 測試範例
    product_description = "iphone 13 pro max"
    purpose = "buy"
    expected_price = "10000"
    contact_info = "請私訊詳詢"
    trade_method = "面交/郵寄皆可"
    seeking_type = 'buy'
    deadline = "星期五之前"
    style = "normal"

    print(f"\n開始為商品「{product_description}」生成社群銷售文案")

    try:
        result = await generate_seeking_post(
            product_description=product_description,
            purpose=purpose,
            expected_price=expected_price,
            contact_info=contact_info,
            trade_method=trade_method,
            seeking_type=seeking_type,
            deadline=deadline,
            style=style,
        )
        print("\n=== 社群銷售文案 ===\n")
        print(result)

    except Exception as e:
        print(f"生成過程中發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
