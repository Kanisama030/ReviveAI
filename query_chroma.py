import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import json
import os
from dotenv import load_dotenv

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
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def gpt_rerank(query: str, results: dict):
    """
    使用 GPT 重新排序查詢結果
    
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
        
        請注意以下選擇標準（按優先順序）：
        1. 產品類別的匹配度（例如：查詢手機時優先選擇手機產品）
        2. 產品功能的相似度（例如：查詢 iPhone 時，優先選擇具有相似功能的智慧型手機）
        3. 產品規格的相似度（例如：存儲容量、處理器性能等）
        4. 其他相關特徵
        
        請仔細分析每個產品的詳細信息，特別注意：
        - 產品的主要功能和用途
        - 產品的技術規格和性能
        - 產品的目標使用場景
        
        選擇最符合查詢的產品。"""

    # 調用 GPT
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "你是一個專業的產品匹配助手，請根據查詢選擇最符合的產品。特別注意產品類別和功能的匹配度，確保選擇的產品能夠滿足查詢的主要需求。"},
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

if __name__ == "__main__":
    # 示例查詢
    query = "macbook air 13吋 2020 16G 512G 筆記型電腦"
    results = query_similar_products(query)
    
    # 使用 GPT 重新排序
    reranked_result = gpt_rerank(query, results)
    
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
        