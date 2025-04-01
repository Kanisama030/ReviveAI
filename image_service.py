import base64
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Path to your image
image_path = "pics/test.jpg"

# Getting the Base64 string
base64_image = encode_image(image_path)


user_prompt = """
            #zh-tw
            回應時請使用 Markdown 格式
            請仔細分析圖片中的商品，並從以下幾個面向提供專業的觀察：

            1. 商品基本資訊：
            - 商品主要描述
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
            - 請以結構化、易讀的方式呈現以上資訊，注重細節描述的精準度。
            - 報告應只提供觀察到的具體資訊為基礎。
            - 回傳的結果只需要以上3個項目，請不要提供額外的建議或道歉訊息
            - 非常重要：回應時請使用 Markdown 格式"""
        

start = time.time()  

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {         
            "role": "developer",
            "content": "你是一位專業的電商平台二手商品圖像分析專家，專門協助賣家優化商品呈現。"
        },
        {
            "role": "user",
            "content": [
                { "type": "input_text", "text": user_prompt },
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        }
        
    ],
)
end=time.time()

print(response.output_text)
print(f"執行時間: {end - start:.2f} 秒")
