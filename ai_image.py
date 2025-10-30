
import os
import uuid
from PIL import Image
from io import BytesIO
from google import genai
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 初始化 Gemini Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Prompt 模板 ---
PROMPT = """
Please process this product image with the following steps:

1. **Background Removal**:
   - Precisely identify and preserve the main product object in the image
   - Remove the original background to make the product the focal point
   - Maintain all details, textures, and colors of the product unchanged

2. **Sustainable Background Generation**:
   - Create a minimalist, modern background with a strong sense of sustainability
   - The background should include one or more of the following elements:
     * Soft green plants (such as blurred leaves, small potted plants)
     * Natural lighting creating a warm atmosphere
     * Minimalist wooden or eco-friendly material surfaces
     * Soft beige or light green tones
   - The background should be softly focused, not competing for visual attention
   - Overall style should convey the concept of "second-hand is beautiful" and "sustainable and eco-friendly"

3. **Composition Requirements**:
   - The product should naturally blend into the new background
   - Maintain appropriate lighting effects and shadows
   - Ensure natural edge treatment with no obvious cut-out artifacts
   - Overall presentation should be professional and appealing, suitable for e-commerce or social media

Please generate a high-quality product display image.
"""

# --- Core Functions ---

async def remake_product_image(image_path: str, output_dir="ui/temp_images") -> str:
    """
    使用 Gemini 2.5 Flash Image 進行 AI 圖片去背與背景更換。
    
    流程:
    1. 讀取原始商品圖片
    2. 使用 Gemini API 進行去背和背景生成
    3. 儲存處理後的圖片
    
    Args:
        image_path (str): 輸入的原始圖片路徑。
        output_dir (str): 輸出圖片的儲存目錄。
        
    Returns:
        str: 處理完成後的新圖片路徑，失敗則返回 None。
    """
    print(f"開始為圖片 {os.path.basename(image_path)} 進行 AI 去背與背景替換...")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 讀取原始圖片
        original_image = Image.open(image_path)
        
        # 調用 Gemini 2.5 Flash Image API
        print("正在呼叫 Gemini API 進行圖片處理...")
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[PROMPT, original_image],
        )
        
        # 提取生成的圖片
        image_parts = [
            part.inline_data.data
            for part in response.candidates[0].content.parts
            if part.inline_data
        ]
        
        if not image_parts:
            print("API 回應中沒有找到生成的圖片")
            return None
        
        # 將生成的圖片儲存
        generated_image = Image.open(BytesIO(image_parts[0]))
        output_filename = f"remade_{uuid.uuid4()}.png"
        output_path = os.path.join(output_dir, output_filename)
        generated_image.save(output_path)
        
        print(f"✅ AI 美化圖片完成，已儲存至: {output_path}")
        # 返回統一格式的絕對路徑
        return os.path.abspath(output_path).replace('\\', '/')

    except Exception as e:
        print(f"❌ AI 圖片美化失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    import asyncio
    # 測試程式碼 (需要一張測試圖片在 `ui/pics` 資料夾中)
    # 請確保 ui/pics/test1.jpg 存在
    test_image_path = "ui/pics/test1.jpg"
    if os.path.exists(test_image_path):
        asyncio.run(remake_product_image(test_image_path))
    else:
        print(f"測試圖片不存在: {test_image_path}")
