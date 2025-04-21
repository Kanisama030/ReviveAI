"""
ReviveAI 的 MCP 服務器 - 提供網路搜尋和網頁抓取工具

此服務器提供兩個主要工具：
1. brave_search: 使用 Brave Search API 進行網路搜尋
2. fetch_webpage: 獲取網頁內容並轉換為 Markdown 格式
"""

import os
import aiohttp
from dotenv import load_dotenv
import markdownify
import readabilipy.simple_json
from mcp.server.fastmcp import FastMCP
import asyncio

# 載入環境變數
load_dotenv()
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")

# 建立 MCP 服務器
mcp = FastMCP("WebTools")

@mcp.tool()
async def brave_search(query: str, count: int = 5, country: str = "TW") -> str:
    """
    使用 Brave Search API 執行網路搜尋
    
    Args:
        query: 搜尋查詢字串
        count: 要返回的結果數量 (1-20)
        country: 本地化結果的國家代碼 (例如 TW、US)
        
    Returns:
        格式化的搜尋結果，包括標題、描述和 URL
    """
    if not BRAVE_SEARCH_API_KEY:
        return "錯誤: 找不到 Brave Search API 金鑰。請在 .env 文件中設定 BRAVE_SEARCH_API_KEY。"
        
    print(f"使用 Brave Search API 搜尋: {query}")
    
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": BRAVE_SEARCH_API_KEY
                },
                params={
                    "q": query,
                    "count": min(count, 5),  # 最多 5 個結果
                    "country": country,
                    "result_filter": "web",
                }
            )
            
            if response.status != 200:
                return f"搜尋錯誤: HTTP狀態碼 {response.status}"
                
            data = await response.json()
            formatted_results = f"## 搜尋結果：\"{query}\"\n\n"
            
            # 檢查並處理結果
            results = data.get("web", {}).get("results", [])
            if not results:
                return formatted_results + "找不到相關結果。\n"
            
            # 格式化結果
            for idx, result in enumerate(results, 1):
                if idx > count:
                    break
                formatted_results += f"### {idx}. {result.get('title', '無標題')}\n"
                formatted_results += f"{result.get('description', '無描述')}\n"
                formatted_results += f"URL: {result.get('url', '')}\n\n"
            
            return formatted_results
    except Exception as e:
        return f"搜尋時發生錯誤: {str(e)}"

@mcp.tool()
async def fetch_webpage(url: str, raw_html: bool = False) -> str:
    """
    抓取網頁內容並轉換為 Markdown 格式
    
    Args:
        url: 要抓取的網頁 URL
        raw_html: 是否返回原始 HTML 而不是 Markdown
        
    Returns:
        網頁內容的 Markdown 格式（或原始 HTML，如果 raw_html=True）
    """
    headers = {
        "User-Agent": "Mozilla/5.0 ReviveAI Web Fetcher (+https://github.com/ReviveAI)"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # 設定 4 秒的超時限制
            async with session.get(url, headers=headers, timeout=4) as response:
                if response.status != 200:
                    return f"錯誤: 無法獲取頁面，HTTP狀態碼 {response.status}"
                
                html = await response.text()
                content_type = response.headers.get("Content-Type", "")
                
                # 如果要求原始 HTML 或不是 HTML 內容
                if raw_html or not any(ct in content_type for ct in ["text/html", "application/xhtml+xml"]):
                    return f"## 網頁原始內容: {url}\n\n```html\n{html[:10000]}...\n```"
                
                # 處理 HTML 並轉換為 Markdown
                try:
                    # 使用 readabilipy 來提取主要內容
                    extracted = readabilipy.simple_json.simple_json_from_html_string(
                        html, use_readability=True
                    )
                    
                    if not extracted.get("content"):
                        return f"錯誤: 無法從網頁提取有意義的內容: {url}"
                    
                    # 轉換為 Markdown
                    markdown = markdownify.markdownify(
                        extracted["content"],
                        heading_style="ATX"
                    )
                    
                    title = extracted.get("title", "無標題")
                    
                    return f"## 網頁內容: {title}\n\n來源: {url}\n\n{markdown}"
                except Exception as e:
                    return f"處理 HTML 時出錯: {str(e)}\n\n網頁: {url}"
    except asyncio.TimeoutError:
        return f"錯誤: 網頁載入超時（超過4秒）:此網頁可能響應速度較慢或暫時無法訪問。"
    except Exception as e:
        return f"抓取網頁時發生錯誤: {str(e)}\n\n網頁: {url}"

if __name__ == "__main__":
    # 根據命令行參數決定運行方式
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
        print(f"以 HTTP 模式啟動 WebTools MCP 服務器，監聽端口 {port}...")
        mcp.run(transport="http", host="0.0.0.0", port=port)
    else:
        print("以 stdio 模式啟動 WebTools MCP 服務器...")
        mcp.run(transport="stdio")
