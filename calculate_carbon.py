import os
from dotenv import load_dotenv
from query_chroma import query_similar_products, gpt_rerank

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

def calculate_carbon_footprint(query: str) -> dict:
    """計算碳足跡並返回結果"""
    # 查詢相似產品
    results = query_similar_products(query)
    
    # 使用 GPT 重新排序
    reranked_result = gpt_rerank(query, results)
    
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
    results = calculate_carbon_footprint(query)
    print_results(results)
