
import os
import uuid
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
            print("No image generated in response")
            return None
        
        # 儲存生成的圖片
        image_filename = f"{uuid.uuid4()}.png"
        image_path = os.path.join(output_dir, image_filename)
        
        # 將圖片數據寫入檔案
        with open(image_path, 'wb') as f:
            f.write(image_parts[0])
        
        return image_path
    except Exception as e:
        print(f"Error calling Gemini Image API: {e}")
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
        print("生成提示詞失敗。")
        return None
    
    print(f"生成的提示詞: {detailed_prompt}")
    
    # 2. 使用詳細提示詞生成圖片
    image_path = await generate_image_with_gemini(detailed_prompt, output_dir="/Users/chenyirui/project/ReviveAI/ui/temp_images")
    
    if not image_path:
        print("生成圖片失敗。")
        return None
        
    print(f"圖片已儲存至: {image_path}")
    return image_path

if __name__ == '__main__':
    # 測試程式碼
    test_input = "a vintage mechanical keyboard"
    create_seeking_image(test_input)
