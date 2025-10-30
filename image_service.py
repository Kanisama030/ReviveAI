import base64
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import time
import asyncio
import mimetypes
from pathlib import Path
import filetype  # 使用 filetype 代替 imghdr

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))  

# 將圖片轉換為 Base64 編碼的函數 (I/O 操作，但不複雜，可保留同步)
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# 確定圖片的 MIME 類型
def get_image_mime_type(image_path):
    # 使用 filetype 庫檢測文件類型
    kind = filetype.guess(image_path)
    
    # 如果檢測成功且是圖片類型
    if kind is not None and kind.mime.startswith('image/'):
        return kind.mime
    
    # 如果檢測失敗，嘗試使用副檔名
    file_extension = Path(image_path).suffix.lower()
    mime_mapping = {
        '.jpeg': 'image/jpeg',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp'
    }
    
    if file_extension in mime_mapping:
        return mime_mapping[file_extension]
    
    # 最後嘗試使用 mimetypes 模組
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type and mime_type.startswith('image/'):
        return mime_type
    
    # 如果都無法檢測，預設為 jpeg
    return 'image/jpeg'

# 驗證圖片格式和大小
def validate_image(image_path):
    # 檢查文件大小（限制為 20MB）
    file_size = os.path.getsize(image_path)
    max_size = 20 * 1024 * 1024  # 20MB
    
    if file_size > max_size:
        raise ValueError(f"圖片大小超過限制：{file_size/(1024*1024):.2f}MB > 20MB")
    
    # 檢查圖片格式
    kind = filetype.guess(image_path)
    
    # 如果無法辨識檔案類型
    if kind is None:
        raise ValueError("無法識別圖片格式，請確保上傳的是有效的圖片文件")
    
    # 檢查是否為支援的圖片格式 (排除 GIF)
    valid_mimes = ['image/jpeg', 'image/png', 'image/webp']
    
    if kind.mime not in valid_mimes:
        raise ValueError(f"不支援的圖片格式：{kind.mime}。請使用 JPEG, PNG 或 WEBP 格式")
    
    return kind.mime

async def analyze_image(image_path):
    # 簡化的商品分析提示 - 專注於關鍵資訊
    prompt = """
    #zh-tw
    請簡潔分析圖片中的商品，提供以下關鍵資訊：

    1. 商品類型：明確說明這是什麼產品（例如：筆記型電腦、智慧手機、衣服等）
    2. 品牌：如果能識別出品牌，請標明
    3. 顏色：主要顏色
    4. 狀況：新舊程度（全新/九成新/八成新等）
    5. 明顯特點：任何特殊的視覺特點或瑕疵

    請用簡潔的條列式回答，只提供觀察到的具體資訊。
    """
    
    try:
        # 驗證圖片及獲取 MIME 類型
        mime_type = validate_image(image_path)
        
        # 取得圖片的 Base64 字串
        base64_image = encode_image(image_path)
        
        start = time.time()  

        response = await client.responses.create(
            model="gpt-4.1-nano",
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
                            "image_url": f"data:{mime_type};base64,{base64_image}",
                        },
                    ],
                }
            ],
        )

        end = time.time()
        print(response.output_text)
        print(f"執行時間: {end - start:.2f} 秒")
        return response
    
    except Exception as e:
        print(f"分析圖片時發生錯誤: {str(e)}")
        raise

async def main():
    # 圖片路徑
    image_path = "pics/test3.webp"

    # 分析圖片
    await analyze_image(image_path)

if __name__ == "__main__":
    asyncio.run(main())