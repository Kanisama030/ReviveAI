from dotenv import load_dotenv
import asyncio
from query_chroma import ai_search_products 

# 載入環境變數
load_dotenv()

# 常數定義
DEFAULT_SAVING_RATIO = 0.50

def calculate_environmental_benefits(saved_carbon: float) -> dict:
    """計算環境效益等值"""
    trees = saved_carbon / 21.0  # 每棵樹每年吸收的 CO2 (kg)
    car_km = saved_carbon / 0.25   # 每公里汽車排放的 CO2 (kg)
    ac_hours = saved_carbon / 0.5  # 吹每小時空調的 CO2 (kg) 
    phone_charges = saved_carbon / 0.01  # 每充滿電一次手機的 CO2 (kg)

    return {
        "trees": "少於0.01" if trees < 0.01 else f"{trees:.1f}",
        "car_km": "少於0.1" if car_km < 0.1 else f"{car_km:.1f}",
        "ac_hours": "少於0.1" if ac_hours < 0.1 else f"{ac_hours:.1f}",
        "phone_charges": "少於1" if phone_charges < 1 else f"{phone_charges:.0f}"
    }

async def calculate_carbon_footprint_async(product_description: str) -> dict:
    """使用 AI 計算碳足跡並返回結果 (非同步版本)"""
    # 使用 AI 搜尋產品
    search_results = await ai_search_products(product_description)
    
    # 檢查是否有錯誤
    if "error" in search_results:
        # 返回錯誤訊息，但包含一個預設的環境效益資訊，避免前端顯示問題
        default_benefits = calculate_environmental_benefits(0)
        return {
            "error": search_results["error"],
            "search_params": search_results.get('search_params', {}),
            "selected_product": {
                "product_name": "未找到匹配產品",
                "company": "未知",
                "carbon_footprint": 0,
                "sector": "未知",
                "similarity_score": 0,
                "details": "無詳細資訊",
                "selection_reason": "未找到匹配產品"
            },
            "saved_carbon": 0,
            "environmental_benefits": default_benefits
        }

    # 直接從搜尋結果中獲取最佳匹配產品
    best_product = search_results["best_product"]

    # 計算節省的碳排放
    original_footprint = best_product['carbon_footprint']
    saved_carbon = original_footprint * DEFAULT_SAVING_RATIO

    # 計算環境效益
    benefits = calculate_environmental_benefits(saved_carbon)

    return {
        "search_params": search_results.get('search_params', {}),
        "selected_product": best_product,
        "saved_carbon": saved_carbon,
        "environmental_benefits": benefits
        # 移除這裡的重複 selection_reason，因為已經包含在 best_product 中
    }


def print_results(results: dict) -> None:
    """打印計算結果"""
    if "error" in results:
        print(f"錯誤: {results['error']}")
        return
    
    product = results["selected_product"]
    benefits = results["environmental_benefits"]
    
    print("\n=== 碳足跡計算結果 ===")
    print(f"\n選定的產品: {product['product_name']}")
    print(f"公司: {product['company']}")
    print(f"相似度分數: {product['similarity_score']:.2f}")
    print(f"原始碳足跡: {product['carbon_footprint']:.2f} kg CO2e")
    print(f"節省的碳排放: {results['saved_carbon']:.2f} kg CO2e")
    print(f"\n環境效益:")
    print(f"• 相當於 {benefits['trees']} 棵樹一年的吸碳量")
    print(f"• 相當於減少開車 {benefits['car_km']} 公里的碳排放")
    print(f"• 相當於減少吹冷氣 {benefits['ac_hours']} 小時的碳排放")
    print(f"• 相當於幫手機充電 {benefits['phone_charges']} 次的碳排放")
    print(f"\n選擇原因: {product['selection_reason']}")

if __name__ == "__main__":
    # 示例查詢
    query = "macbook air 13吋 2020 16G 512G 筆記型電腦"
    # 使用asyncio.run執行非同步函數
    results = asyncio.run(calculate_carbon_footprint_async(query))
    print_results(results)
