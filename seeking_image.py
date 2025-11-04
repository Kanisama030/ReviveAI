import os
import uuid
from PIL import Image
from io import BytesIO
from openai import OpenAI
from google import genai
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定 API 金鑰
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Helper Functions ---
def get_openai_completion(prompt, model="gpt-4.1-nano"):
    """使用 OpenAI GPT 模型生成文字。"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in writing detailed, vivid, and effective image generation prompts."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

async def generate_image_with_gemini(prompt, output_dir="temp_images"):
    """使用 Gemini 2.5 Flash Image 模型生成圖片並儲存。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        # 使用 Gemini 2.5 Flash Image模型生成圖片（非同步版本）
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=[prompt],
        )
        
        # 從回應中提取圖片數據
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
        output_filename = f"generated_{uuid.uuid4()}.png"
        output_path = os.path.join(output_dir, output_filename)
        generated_image.save(output_path)
        
        print(f"圖片已儲存至: {output_path}")
        return os.path.abspath(output_path).replace('\\', '/')
    
    except Exception as e:
        print(f"Gemini API 調用失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

# --- Core Functions ---
def generate_seeking_image_prompt(user_input: str) -> str:
    """
    根據使用者輸入，生成一個詳細的、適合圖片生成的英文提示詞。
    輸入現在包含完整的徵文信息：商品描述、用途、預算等。
    生成風格模擬台灣使用者用手機拍攝的真實照片。
    """
    prompt = f"""
    Based on the user's detailed seeking post information, create a detailed and specific English prompt for an image generation model (like Gemini). 
    The target audience is Taiwanese users seeking second-hand items, and the image should look like a realistic photo taken with a smartphone.
    
    Follow these guidelines:
    1.  **Realistic Smartphone Photography Style**: The image should look like it was taken with a modern smartphone (iPhone or Android). Include natural imperfections like slight blur, natural lighting, casual composition.
    2.  **Aspect Ratio**: Specify either "1:1 square format" or "4:3 landscape format" depending on what suits the item best.
    3.  **Taiwanese Context**: Consider typical Taiwanese home/office settings - items might be photographed on wooden tables, tiled floors, or against simple walls. Natural daylight from windows is common.
    4.  **Be Specific and Detailed**: Parse the seeking information to describe the item clearly with realistic details, textures, and any visible wear that shows it's second-hand.
    5.  **Casual but Clear**: The photo should be clear enough to see details, but maintain that authentic "user-taken" feel - not professional studio quality.
    6.  **Natural Lighting**: Emphasize natural indoor lighting, window light, or everyday home lighting - avoid studio setup descriptions.
    7.  **Simple Background**: Typical home environments - wooden desks, plain walls, tile floors, or simple fabric backgrounds.
    8.  **Second-hand Appearance**: Since this is for seeking second-hand items, show realistic wear, use, and aging that would be expected from pre-owned items.

    User's Seeking Information: "{user_input}"

    Parse this information to understand:
    - What specific item they want
    - The purpose/use case
    - Budget constraints (if mentioned)
    - Any other relevant details

    Generate a single, concise paragraph prompt in English. MUST include the aspect ratio specification at the start.
    
    Example:
    User's Seeking Information: "MacBook Air M1 - 學習程式設計 - 希望不超過 $7,000"
    Generated Prompt: "4:3 landscape format. A realistic smartphone photo of a well-used silver MacBook Air M1 laptop placed on a wooden desk in a Taiwanese student's room. Natural afternoon sunlight streams through a nearby window, creating soft shadows. The laptop shows authentic wear - slight scuffs on the aluminum body, fingerprints on the screen, and a few small dents on the corners from daily use. The screen is open showing a code editor with some programming work in progress. In the background, slightly out of focus, you can see a plain white wall, some books, and a coffee mug. The photo is taken from a casual top-down angle, typical of someone quickly photographing their current laptop to show what they're looking for. The image has the natural color balance and slight grain characteristic of modern smartphone cameras."
    """
    
    detailed_prompt = get_openai_completion(prompt)
    return detailed_prompt

async def create_seeking_image(user_input: str):
    """
    主函式：接收使用者輸入，生成提示詞，然後生成圖片。
    現在是異步函數。
    """
    print(f"開始為 '{user_input}' 生成參考圖片...")
    
    # 1. 生成詳細的提示詞
    detailed_prompt = generate_seeking_image_prompt(user_input)
    if not detailed_prompt:
        print("❌ 提示詞生成失敗")
        return None
    
    print(f"生成的提示詞: {detailed_prompt}")
    
    # 2. 使用詳細提示詞生成圖片
    image_path = await generate_image_with_gemini(detailed_prompt, output_dir="ui/temp_images")
    
    if not image_path:
        print("❌ 圖片生成失敗")
        return None
        
    print(f"圖片已儲存至: {image_path}")
    return image_path

async def remake_seeking_image(image_path: str, product_description: str = "", output_dir="ui/temp_images") -> str:
    """
    使用 Gemini 2.5 Flash Image 進行 AI 圖片修圖，專為 seeking 場景設計。
    
    將用戶上傳的參考圖片優化成「尋找中」風格：
    - 模擬台灣用戶用手機拍攝的自然風格
    - 強調二手商品的真實感
    - 適合社群平台徵求貼文的參考圖片
    
    Args:
        image_path (str): 用戶上傳的原始圖片路徑
        product_description (str): 商品描述文字（可選，用於優化提示詞）
        output_dir (str): 輸出圖片的儲存目錄
        
    Returns:
        str: 處理完成後的新圖片路徑，失敗則返回 None
    """
    print(f"開始為圖片 {os.path.basename(image_path)} 進行 seeking 風格修圖...")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 讀取原始圖片
        original_image = Image.open(image_path)
        
        # 生成修圖提示詞
        prompt = f"""
Please optimize this product image into a reference image suitable for social media seeking posts, simulating the natural style of Taiwanese users taking photos with their smartphones:

1. **Realistic smartphone photography style**:
   - Simulate modern smartphone camera effects
   - Add appropriate natural lighting and slight blur
   - Maintain casual, natural composition

2. **Taiwanese home environment**:
   - Background can be simple wooden tables, tile floors, or light-colored walls
   - Natural light coming through windows, creating a warm atmosphere
   - Avoid professional studio feel, emphasize everyday life feel

3. **Second-hand product characteristics**:
   - Preserve the real wear marks and texture of the product
   - Show natural wear and aging marks
   - Emphasize the "make the most of things" sustainable concept

4. **Social media seeking purpose**:
   - Image should be clear enough to identify product details
   - Suitable for sharing on platforms like Facebook, Instagram
   - Create a visual effect of "I'm looking for this kind of product"

Product description: {product_description or "No detailed description provided, please optimize naturally based on the image content"}

Please generate a high-quality product display image suitable for reference images when seeking second-hand products.
"""
        
        # 調用 Gemini 2.5 Flash Image API
        print("正在呼叫 Gemini API 進行圖片修圖...")
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, original_image],
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
        output_filename = f"seeking_remade_{uuid.uuid4()}.png"
        output_path = os.path.join(output_dir, output_filename)
        generated_image.save(output_path)
        
        print(f"✅ Seeking 風格修圖完成，已儲存至: {output_path}")
        # 返回統一格式的絕對路徑
        return os.path.abspath(output_path).replace('\\', '/')

    except Exception as e:
        print(f"❌ Seeking 圖片修圖失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # 測試程式碼
    test_input = "a vintage mechanical keyboard"
    create_seeking_image(test_input)
