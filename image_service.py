import base64
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import time
import asyncio

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))  

# 將圖片轉換為 Base64 編碼的函數 (I/O 操作，但不複雜，可保留同步)
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def analyze_image(image_path):
    # 固定的商品分析提示
    prompt = """
    #zh-tw
    回應時請使用 Markdown 格式
    請仔細分析圖片中的商品，並從以下幾個面向提供專業的觀察：

    1. 商品基本資訊：
    - 商品主要描述（**非常重要：必須明確標示這是什麼類型的產品**）
    - 商品顏色
    - 尺寸大小
    - 品牌標誌

    2. 商品狀況評估：
    - 新舊保存程度
    - 是否有明顯瑕疵
    - 清潔程度評估

    3. 商品特色重點
    - 獨特設計或特色
    - 視覺吸引點

    注意事項：
    - 產品類型識別很重要，請確保在分析中清楚說明這是什麼類型的產品，以利於資料庫中搜索。
    - 請以結構化、易讀的方式呈現以上資訊，注重細節描述的精準度。
    - 報告應只提供觀察到的具體資訊為基礎。
    - 回傳的結果只需要以上3個項目，請不要提供額外的建議或道歉訊息
    - 非常重要：回應時請使用 Markdown 格式
    """
    
    # 取得圖片的 Base64 字串
    base64_image = encode_image(image_path)
    
    start = time.time()  

    response = await client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {         
                "role": "developer",
                "content": "你是一位專業的電商平台二手商品圖像分析專家，專門協助賣家優化商品呈現。你的任務是詳細分析圖片中的商品，並提供產品描述。"
            },
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": prompt },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )

    end = time.time()
    print(response.output_text)
    print(f"執行時間: {end - start:.2f} 秒")
    return response

async def main():
    # 圖片路徑
    image_path = "pics/test.jpg"

    # 分析圖片
    await analyze_image(image_path)

if __name__ == "__main__":
    asyncio.run(main())
