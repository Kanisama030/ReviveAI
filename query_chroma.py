import chromadb
from chromadb.utils import embedding_functions
from openai import AsyncOpenAI
import json
import os
from dotenv import load_dotenv
import asyncio
from typing import Optional, Dict, Any

# 設置 tokenizers 並行處理環境變數
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 載入環境變數
load_dotenv()

# 連接到現有的 Chroma 資料庫
chroma_client = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH"))

# 使用 OpenAI 的嵌入模型
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small",
    dimensions=1024
)

# 獲取現有的 collection
collection = chroma_client.get_collection(
    name="carbon_catalogue",
    embedding_function=openai_ef
)

# 初始化 OpenAI 客戶端
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def query_similar_products(
    query_text: str,
    n_results: int = 10,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None
):
    """
    查詢與輸入文本最相似的產品，並支援 metadata 和 document 過濾
    Args:
        query_text (str): 查詢文本
        n_results (int): 返回的結果數量，預設為 10
        where (Dict[str, Any], optional): metadata 過濾條件
        where_document (Dict[str, Any], optional): document 過濾條件
    
    Returns:
        dict: 包含相似產品信息的字典
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where,
        where_document=where_document
    )
    
    return results

async def ai_search_products(product_description: str):
    """
    使用 AI 搜尋產品資料，通過 function calling 執行查詢
    Args:
        product_description (str): 產品描述文字
    Returns:
        dict: 查詢結果包含最佳匹配產品信息
    """
    # 定義查詢函數工具
    tools = [{
        "type": "function",
        "name": "search_products",
        "description": "搜尋與輸入描述相似的產品，並可依碳足跡或產品類別過濾",
        "parameters": {
            "type": "object",
            "properties": {
                "query_text": {
                    "type": "string",
                    "description": "查詢文本，描述所要搜尋的產品"
                },
                "min_carbon_footprint": {
                    "type": ["number"],
                    "description": "最小碳足跡值 (kg CO2e)，僅返回碳足跡大於此值的產品"
                },
                "max_carbon_footprint": {
                    "type": ["number", "null"],
                    "description": "最大碳足跡值 (kg CO2e)，僅返回碳足跡小於此值的產品"
                },
                "sector": {
                    "type": ["string"],
                    "description": "產品行業分類，可選值：'Food & Beverage', 'Comm. equipm. & capital goods', 'Computer, IT & telecom', 'Chemicals', 'Construction & commercial materials', 'Home durables, textiles, & equipment', 'Packaging for consumer goods', 'Automobiles & components'"
                }
            },
            "required": ["query_text", "min_carbon_footprint", "max_carbon_footprint", "sector"],
            "additionalProperties": False
        },
        "strict": True
    }]
    
    system_prompt = """
    你是產品碳足跡搜索助手，你需要將用戶產品描述精確轉換為數據庫查詢參數。

    你需要執行以下任務：
    1. 分析產品描述，識別產品類型、品牌和關鍵特徵
    2. 生成精簡有效的搜索詞彙，移除不必要的細節規格
    3. 根據產品類型自動設定正確的行業分類過濾條件
    4. 設置適當的碳排放量過濾條件，避免設置過高或過低的值

    你需要嚴格遵守以下規則：
    - 不得將 min_carbon_footprint 設為 0，因為這沒有過濾效果
    - 搜索詞必須保留產品主要識別信息，但不包含詳細規格（如記憶體大小、螢幕尺寸）
    
    各產業典型產品碳足跡最低範圍參考（kg CO2e）：
    - 電子產品 (Computer, IT & telecom)：
    * 智慧型手機：最低約30
    * 筆記型電腦：最低約100
    * 桌上型電腦：最低約200
    * 平板電腦：最低約50
    * 顯示器：最低約200
    * 印表機：最低約100

    - 食品飲料 (Food & Beverage)：
    * 咖啡（每包）：最低約0.5
    * 巧克力（每塊）：最低約0.2
    * 瓶裝水（每瓶）：最低約0.1
    * 肉類產品（每公斤）：最低約5
    * 包裝食品（每包）：最低約0.5

    - 汽車與交通工具 (Automobiles & components)：
    * 轎車（整車）：最低約5,000
    * 電動車（整車）：最低約8,000
    * 自行車：最低約50
    * 汽車零組件：最低約10

    - 化學製品 (Chemicals)：
    * 清潔用品（每瓶）：最低約0.5
    * 個人護理品（每瓶）：最低約0.3
    * 工業化學品（每公斤）：最低約1

    - 建築材料 (Construction & commercial materials)：
    * 水泥（每公斤）：最低約0.5
    * 鋼材（每公斤）：最低約1
    * 木材（每公斤）：最低約0.2

    - 家居用品與紡織品 (Home durables, textiles, & equipment)：
    * 家具（每件）：一般為 20-100
    * 廚房電器：一般為 50-300
    * 紡織品/衣物（每件）：一般為 5-30
    * 鞋類（每雙）：一般為 10-30
    """

    # 調用 AI 進行查詢準備
    response = await client.responses.create(
        model="gpt-4.1-nano",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"你的任務是找這個產品的碳足跡資訊：{product_description}，你需要將此描述轉換為最佳搜尋參數，以便在Chroma向量碳足跡資料庫中找到最相關的結果。請設定合理的碳足跡過濾範圍，避免查不到結果。記得根據產品類型選擇正確的行業分類。"}
        ],
        tools=tools
    )

    # 處理 AI 的搜尋函數呼叫
    function_call = None
    for item in response.output:
        if item.type == "function_call":
            function_call = item
            break

    if not function_call:
        return {"error": "AI 未提供搜尋函數呼叫"}

    # 解析函數參數
    try:
        args = json.loads(function_call.arguments)
        query_text = args["query_text"]
        n_results = 10

        # 構建 metadata 過濾條件
        where_conditions = []
        if args.get("min_carbon_footprint") is not None:
            where_conditions.append({"carbon_footprint": {"$gte": args["min_carbon_footprint"]}})
        if args.get("max_carbon_footprint") is not None:
            where_conditions.append({"carbon_footprint": {"$lte": args["max_carbon_footprint"]}})
        if args.get("sector") is not None:
            where_conditions.append({"sector": args["sector"]})

        # 如果有多個條件，使用 $and 運算符組合
        where = None
        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}

        # 執行搜尋
        results = query_similar_products(
            query_text=query_text,
            n_results=n_results,
            where=where
        )

        # 檢查是否有搜尋結果
        if not results['ids'][0] or len(results['ids'][0]) == 0:
            return {"error": "沒有找到符合條件的產品"}
        # 使用 GPT 重新排序結果（簡化錯誤處理）
        try:
            reranked_result = await gpt_rerank_async(product_description, results)
            best_index = reranked_result.get("best_match_index", 0)

            # 簡單檢查索引是否有效
            if best_index < 0 or best_index >= len(results['ids'][0]):
                best_index = 0
                selection_reason = "索引無效，使用相似度最高的結果"
            else:
                selection_reason = reranked_result.get("reason", "使用 GPT 選擇的結果")
        except Exception as e:
            # 出現任何錯誤時，預設使用第一個結果
            best_index = 0
            selection_reason = "重排序過程出錯，使用相似度最高的結果"
            reranked_result = {"best_match_index": 0, "reason": selection_reason}

        # 準備結果物件
        best_match = {
            "product_name": results['metadatas'][0][best_index]['product_name'],
            "company": results['metadatas'][0][best_index]['company'],
            "carbon_footprint": float(results['metadatas'][0][best_index]['carbon_footprint']),
            "sector": results['metadatas'][0][best_index].get('sector', '未知'),
            "cosine_distance": results['distances'][0][best_index],
            "details": results['documents'][0][best_index],
            "selection_reason": selection_reason
        }

        # 返回包含搜尋參數、原始結果、重新排序結果和最佳匹配產品的完整結果
        return {
            "search_params": args,
            "raw_results": results,
            "reranked_result": reranked_result,
            "best_product": best_match  # 新增：直接包含最佳匹配產品
        }

    except (json.JSONDecodeError, KeyError) as e:
        return {"error": f"解析函數參數錯誤: {str(e)}"}
    except Exception as e:
        return {"error": f"搜尋過程中發生錯誤: {str(e)}"}


async def gpt_rerank_async(query: str, results: dict):
    """
    使用 GPT 重新排序查詢結果 (非同步版本)

    Args:
        query (str): 原始查詢
        results (dict): Chroma 查詢結果

    Returns:
        dict: 包含 GPT 選擇的最佳結果索引和原因
    """
    # 準備候選者列表
    candidates = []
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        candidates.append({
            "index": i,
            "product_name": metadata['product_name'],
            "company": metadata['company'],
            "carbon_footprint": metadata['carbon_footprint'],
            "sector": metadata.get('sector', '未知'),
            "cosine_distance": results['distances'][0][i],
            "details": doc
        })

    # 構建提示
    prompt = f"""
        請根據以下查詢和候選產品列表，選擇最符合的產品：
        查詢：{query}
        候選產品列表：
        {json.dumps(candidates, ensure_ascii=False, indent=2)}

        你的任務是：
        1. 先從產品描述中識別出查詢的產品類型，再從候選產品中識別出每個產品的類型，然後嚴格按照產品類型進行匹配。
        2. 選擇前請詳細分析每個產品的資訊，特別是產品名稱和詳細描述。永遠要選擇一個最佳候選產品，即使沒有完美匹配，也要選擇功能最相近的產品。
        3. 請給予簡短且清楚的 40 字以內的理由說明為何選擇該產品。

        【重要】產品類型必須嚴格匹配，這是所有條件中最優先的要求：
        - 如果查詢是筆記型電腦，你必須選擇筆記型電腦，絕對不可選擇列印機、鍵盤等其他類型產品
        - 如果查詢是手機，你必須選擇手機，絕對不可選擇平板、耳機等其他類型產品
        - 如果產品類型不匹配（例如查詢筆記型電腦但候選只有列印機），請選擇功能最接近的產品
        - 當選擇不完美時，請誠實寫出不盡相同但功能較接近的原因

        在考慮候選產品時，請按以下優先順序考慮：
        1. 產品類型（例如：鞋子、筆記型電腦、手機等）
        2. 產品功能相似度
        3. 品牌相似度（有相同品牌最好，但功能相似更重要）
        4. 碳足跡數值的合理性
        """

    # 調用 GPT (非同步)
    response = await client.responses.create(
        model="gpt-4.1-nano",
        input=[
            {"role": "system", "content": "你是一個極其嚴格的產品匹配專家，你的首要任務是確保產品類別的絕對正確匹配。產品類型不匹配是嚴重錯誤，必須避免。例如：\n\n- 如果查詢是筆記型電腦，你絕對不能選擇列印機、鍵盤或其他任何非筆記型電腦產品\n- 如果查詢是智慧型手機，你絕對不能選擇平板、耳機或其他任何非智慧型手機產品\n\n在選擇產品時，請首先識別查詢中的產品類型，然後確保只考慮相同類型的產品。只有在沒有完全相同類型的產品時，才考慮功能最相近的產品類型。碳足跡計算的準確性完全依賴於正確的產品類型匹配。"},
            {"role": "user", "content": prompt}
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "product_selection",
                "schema": {
                    "type": "object",
                    "properties": {
                        "best_match_index": {
                            "type": "integer",
                            "description": "最佳匹配產品的索引（從0開始）"
                        },
                        "reason": {
                            "type": "string",
                            "description": "40 字以內選擇該產品的原因"
                        }
                    },
                    "required": ["best_match_index", "reason"],
                    "additionalProperties": False
                },
                "strict": True
            },
        }
    )

    # 解析回應
    try:
        result = json.loads(response.output_text)
        return result
    except (json.JSONDecodeError, AttributeError) as e:
        return {"error": f"無法解析 GPT 回應: {str(e)}"}
    except Exception as e:
        return {"error": f"GPT 重新排序過程中發生錯誤: {str(e)}"}


# 主函數
async def main():
    # 示例查詢
    product_description = "macbook air 13吋 2020 16G 512G 筆記型電腦"

    # 使用 AI 搜尋產品
    search_results = await ai_search_products(product_description)

    # 打印 AI 搜尋參數
    print(f"原始查詢: {product_description}")
    print(f"AI 搜尋參數: {search_results.get('search_params', {})}")

    # 打印最佳匹配產品
    print("\n最佳匹配產品:")
    if "error" in search_results:
        print(f"錯誤: {search_results['error']}")
    else:
        best_product = search_results["best_product"]
        print(f"產品名稱: {best_product['product_name']}")
        print(f"公司: {best_product['company']}")
        print(f"產業類別: {best_product['sector']}")
        print(f"碳足跡: {best_product['carbon_footprint']} kg CO2e")
        print(f"相似度分數: {1 - best_product['cosine_distance']:.4f}")
        print(f"詳細信息: {best_product['details']}")
        print(f"\n選擇原因: {best_product['selection_reason']}")

    # 打印所有候選者
    print("\n所有候選產品:")
    for i, (doc, metadata) in enumerate(zip(search_results['raw_results']['documents'][0], search_results['raw_results']['metadatas'][0])):
        print(f"\n{i+1}. 產品名稱: {metadata['product_name']}")
        print(f"   碳足跡: {metadata['carbon_footprint']} kg CO2e")
        print(f"   產業類別: {metadata.get('sector', '未知')}")
        print(f"   相似度分數: {1 - search_results['raw_results']['distances'][0][i]:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
