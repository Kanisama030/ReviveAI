from dotenv import load_dotenv
import asyncio
from query_chroma import (
    query_similar_products,
    gpt_rerank_async,
    ai_search_products,
    get_best_product_from_results
)
# 載入環境變數
load_dotenv()

# 常數定義
DEFAULT_SAVING_RATIO = 0.50
TREE_ABSORPTION = 21.0  # 每棵樹每年吸收的 CO2 (kg)
CAR_EMISSION = 0.25   # 每公里汽車排放的 CO2 (kg)

def calculate_environmental_benefits(saved_carbon: float) -> dict:
    """計算環境效益等值"""
    trees = saved_carbon / TREE_ABSORPTION
    car_km = saved_carbon / CAR_EMISSION
    return {
        "trees": "少於0.01" if trees < 0.01 else f"{trees:.1f}",
        "car_km": "少於0.1" if car_km < 0.1 else f"{car_km:.1f}"
    }

async def old_calculate_carbon_footprint_async(query: str) -> dict:
    """計算碳足跡並返回結果 (舊版本，使用直接查詢)"""
    # 查詢相似產品
    results = query_similar_products(query)

    # 使用 GPT 重新排序 (非同步)
    reranked_result = await gpt_rerank_async(query, results)

    if "error" in reranked_result:
        return {"error": reranked_result["error"]}
    # 獲取最佳匹配的產品
    best_index = reranked_result["best_match_index"]
    best_match = {
        "product_name": results['metadatas'][0][best_index]['product_name'],
        "company": results['metadatas'][0][best_index]['company'],
        "carbon_footprint": float(results['metadatas'][0][best_index]['carbon_footprint']),
        "similarity_score": results['distances'][0][best_index],
        "details": results['documents'][0][best_index]
    }
    # 計算節省的碳排放
    original_footprint = best_match['carbon_footprint']
    saved_carbon = original_footprint * DEFAULT_SAVING_RATIO

    # 計算環境效益
    benefits = calculate_environmental_benefits(saved_carbon)

    return {
        "selected_product": best_match,
        "saved_carbon": saved_carbon,
        "environmental_benefits": benefits,
        "selection_reason": reranked_result["reason"]
    }

async def calculate_carbon_footprint_async(product_description: str) -> dict:
    """使用 AI 計算碳足跡並返回結果 (非同步版本)"""
    # 使用 AI 搜尋產品
    search_results = await ai_search_products(product_description)

    # 獲取最佳匹配產品
    best_product = get_best_product_from_results(search_results)

    if "error" in best_product:
        return {"error": best_product["error"]}

    # 計算節省的碳排放
    original_footprint = best_product['carbon_footprint']
    saved_carbon = original_footprint * DEFAULT_SAVING_RATIO

    # 計算環境效益
    benefits = calculate_environmental_benefits(saved_carbon)

    return {
        "search_params": search_results.get('search_params', {}),
        "selected_product": best_product,
        "saved_carbon": saved_carbon,
        "environmental_benefits": benefits,
        "selection_reason": best_product['selection_reason']
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
    print(f"\n選擇原因: {results['selection_reason']}")

if __name__ == "__main__":
    # 示例查詢
    query = "macbook air 13吋 2020 16G 512G 筆記型電腦"
    # 使用asyncio.run執行非同步函數
    results = asyncio.run(calculate_carbon_footprint_async(query))
    print_results(results)

async def calculate_carbon_footprint_async(product_description: str) -> dict:
    """使用 AI 計算碳足跡並返回結果 (非同步版本)"""
    # 使用 AI 搜尋產品
    search_results = await ai_search_products(product_description)

    # 獲取最佳匹配產品
    best_product = get_best_product_from_results(search_results)

    if "error" in best_product:
        return {"error": best_product["error"]}

    # 計算節省的碳排放
    original_footprint = best_product['carbon_footprint']
    saved_carbon = original_footprint * DEFAULT_SAVING_RATIO

    # 計算環境效益
    benefits = calculate_environmental_benefits(saved_carbon)

    return {
        "search_params": search_results.get('search_params', {}),
        "selected_product": best_product,
        "saved_carbon": saved_carbon,
        "environmental_benefits": benefits,
        "selection_reason": best_product.get("selection_reason", "無提供選擇原因")
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
    print(f"\n選擇原因: {results['selection_reason']}")

if __name__ == "__main__":
    # 示例查詢
    query = "macbook air 13吋 2020 16G 512G 筆記型電腦"
    # 使用asyncio.run執行非同步函數
    results = asyncio.run(calculate_carbon_footprint_async(query))
    print_results(results)

