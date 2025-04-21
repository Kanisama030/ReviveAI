import chromadb
from chromadb.utils import embedding_functions
from openai import AsyncOpenAI
import json
import os
from dotenv import load_dotenv
import asyncio

# 設置 tokenizers 並行處理環境變數
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 載入環境變數
load_dotenv()

# 連接到現有的 Chroma 資料庫
chroma_client = chromadb.PersistentClient(path="/Users/chenyirui/Project/ReviveAI/data/chroma")

# 使用相同的 embedding 函數
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-m3"
)

# 獲取現有的 collection
collection = chroma_client.get_collection(
    name="carbon_catalogue",
    embedding_function=sentence_transformer_ef
)

# 初始化 OpenAI 客戶端
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 這個函數不涉及網路 I/O，保持同步也可以
def query_similar_products(query_text: str, n_results: int = 10):
    """
    查詢與輸入文本最相似的產品
    
    Args:
        query_text (str): 查詢文本
        n_results (int): 返回的結果數量，預設為 10
    
    Returns:
        dict: 包含相似產品信息的字典
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    return results

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
            "similarity_score": results['distances'][0][i],
            "details": doc
        })
    
    # 構建提示
    prompt = f"""請根據以下查詢和候選產品列表，選擇最符合的產品：
        查詢：{query}
        候選產品列表：
        {json.dumps(candidates, ensure_ascii=False, indent=2)}
        
        【重要】產品類型必須嚴格匹配，這是所有條件中最優先的要求：
        - 如果查詢是筆記型電腦，你必須選擇筆記型電腦，絕對不可選擇列印機、鍵盤等其他類型產品
        - 如果查詢是手機，你必須選擇手機，絕對不可選擇平板、耳機等其他類型產品
        - 如果產品類型不匹配（例如查詢筆記型電腦但候選只有列印機），請選擇功能最接近的產品

        在完成產品類型匹配後，請按以下優先順序考慮其他因素：
        1. 產品品牌的匹配度（例如：查詢Apple產品時，優先選擇Apple品牌）
        2. 產品規格的相似度（例如：存儲容量、處理器性能等）
        3. 碳足跡數值的合理性（避免選擇碳足跡異常高或異常低的產品）
        
        先從產品描述中識別出查詢的產品類型，再從候選產品中識別出每個產品的類型，然後嚴格按照產品類型進行匹配。
        選擇前請詳細分析每個產品的資訊，特別是產品名稱和詳細描述。
        請提供清晰的理由說明為何選擇該產品，特別是如何匹配產品類型。"""

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
                            "description": "選擇該產品的原因"
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
    except (json.JSONDecodeError, AttributeError):
        return {"error": "無法解析 GPT 回應"}

# 主函數
async def main():
    # 示例查詢
    query = "macbook air 13吋 2020 16G 512G 筆記型電腦"
    results = query_similar_products(query)
    
    # 使用 GPT 重新排序 (非同步)
    reranked_result = await gpt_rerank_async(query, results)
    
    # 打印 GPT 選擇的最佳結果
    print(f"查詢: {query}")
    print("\nGPT 選擇的最佳匹配:")
    if "error" in reranked_result:
        print(f"錯誤: {reranked_result['error']}")
    else:
        best_index = reranked_result["best_match_index"]
        best_match = {
            "product_name": results['metadatas'][0][best_index]['product_name'],
            "company": results['metadatas'][0][best_index]['company'],
            "carbon_footprint": results['metadatas'][0][best_index]['carbon_footprint'],
            "similarity_score": results['distances'][0][best_index],
            "details": results['documents'][0][best_index]
        }
        
        print(f"產品名稱: {best_match['product_name']}")
        print(f"公司: {best_match['company']}")
        print(f"碳足跡: {best_match['carbon_footprint']} kg CO2e")
        print(f"相似度分數: {best_match['similarity_score']:.4f}")
        print(f"詳細信息: {best_match['details']}")
        print(f"\n選擇原因: {reranked_result['reason']}")
    
    # 打印所有候選者
    print("\n所有候選產品:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n{i+1}. 產品名稱: {metadata['product_name']}")
        print(f"\n   碳足跡: {metadata['carbon_footprint']} kg CO2e")
        print(f"   相似度分數: {results['distances'][0][i]:.4f}") 
        
if __name__ == "__main__":
    asyncio.run(main())
