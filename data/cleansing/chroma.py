import chromadb
import pandas as pd
from chromadb.utils import embedding_functions

chroma_client = chromadb.PersistentClient(path="/Users/chenyirui/Project/ReviveAI/data/chroma")


sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-m3"
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


df = pd.read_csv("/Users/chenyirui/Project/ReviveAI/data/cleaned_carbon_catalogue.csv")

# Create a collection
collection = chroma_client.create_collection(
    name="carbon_catalogue", 
    embedding_function=sentence_transformer_ef,
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
