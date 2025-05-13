import chromadb
import pandas as pd
import os
import shutil
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import sys

# 載入環境變數
load_dotenv()

# 設定 ChromaDB 路徑
CHROMA_PATH = "E:/Projects/ReviveAI/data/chroma"

# 刪除現有的 ChromaDB (如果存在)
if os.path.exists(CHROMA_PATH):
    print(f"正在刪除現有的 ChromaDB: {CHROMA_PATH}")
    try:
        shutil.rmtree(CHROMA_PATH)
        print("已刪除現有的 ChromaDB")
    except Exception as e:
        print(f"刪除資料庫時發生錯誤: {e}")
        sys.exit(1)

# 創建一個新的持久化客戶端
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# 使用 OpenAI 的嵌入模型
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small",
    dimensions=1024
)

def prepare_product_text(row):
    """
    將產品數據轉換為結構化文本，將 product_detail 放在最後
    """
    text = f"產品: {row['product_name']}, "
    text += f"公司: {row['company']}, "
    text += f"行業: {row['sector']}, "
    text += f"重量: {row['weight_kg']} kg, "
    text += f"碳足跡: {row['carbon_footprint']} kg CO2e, "
    text += f"國家: {row['country']}, "
    text += f"年份: {row['year']}"
    
    # 將 product_detail 放在最後，避免重要信息被截斷
    text += f", 詳情: {row['product_detail']}"
    
    return text


df = pd.read_csv("E:/Projects/ReviveAI/data/cleaned_carbon_catalogue.csv")

# Create a collection
collection = chroma_client.create_collection(
    name="carbon_catalogue", 
    embedding_function=openai_ef,
    metadata={
        "hnsw:space": "cosine",
        "hnsw:search_ef": 100
    }
)

# 準備元數據
metadatas = []
for _, row in df.iterrows():
    metadata = {
        'product_name': row['product_name'],
        'company': row['company'],
        'sector': row['sector'],
        'weight_kg': float(row['weight_kg']),
        'carbon_footprint': float(row['carbon_footprint']),
        'country': row['country'],
        'year': int(row['year'])
    }
    metadatas.append(metadata)

# Add documents to the collection
ids = df['product_id'].astype(str).tolist()
documents = df.apply(prepare_product_text, axis=1).tolist()

# 添加到集合
collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)
print(f"已添加 {len(ids)} 個產品到集合")
