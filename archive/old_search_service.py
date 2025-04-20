import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

async def search_brave(query: str) -> dict:
    """使用 Brave Search API 執行搜尋"""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_SEARCH_API_KEY
    }
    params = {
        "q": query,
        "count": 5,  # 限制結果數量以節省使用量
        "country": "TW",
        "result_filter": "web",  # 只回傳網頁結果
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"搜尋錯誤: {response.status}")
                    return {"error": f"搜尋錯誤: {response.status}"}
    except Exception as e:
        print(f"搜尋時發生錯誤: {str(e)}")
        return {"error": str(e)}

def extract_search_results(search_data: dict) -> str:
    """從搜尋結果中提取有用信息"""
    if "error" in search_data:
        return "搜尋過程中發生錯誤，無法獲取產品信息。"
    
    results = ""
    
    if "web" in search_data and "results" in search_data["web"]:
        results += "搜尋結果摘要:\n"
        for idx, result in enumerate(search_data["web"]["results"], 1):
            if idx > 5:  # 限制只使用前5個結果
                break
            results += f"- {result.get('title', '無標題')}: {result.get('description', '無描述')}\n"
    
    return results 