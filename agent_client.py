"""
ReviveAI 產品搜尋客戶端

此客戶端連接到 WebTools MCP 服務器，使用 LangChain 和 LangGraph
實現一個能夠執行網路搜尋和分析產品資訊的 AI 代理。
"""

import asyncio
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# 載入環境變數
load_dotenv()

async def search_product_info(query):
    """
    使用 MCP 工具搜尋產品資訊並返回分析結果
    
    Args:
        query: 要搜尋的產品查詢
        
    Returns:
        dict: 包含以下內容的字典:
            - text: 處理後的文本內容
            - raw_response: 原始響應對象
    """
    # 使用 OpenAI 模型
    model = ChatOpenAI(model="gpt-4.1-nano")
    
    # 配置 MCP 客戶端並連接到 WebTools 服務器
    async with MultiServerMCPClient(
        {
            "web_tools": {
                "command": "python",
                "args": ["web_tools_server.py"],
                "transport": "stdio",
            }
        }
    ) as client:
        # 獲取所有工具
        tools = client.get_tools()
        
        # 創建 ReAct 代理
        agent = create_react_agent(model, tools)
        
        # 系統提示
        system_message = """
            你是一個專業的產品研究助手，專門幫助用戶尋找和分析產品的詳細資訊。
            
            請嚴格遵循以下工作流程，這是非常重要的：
            1. 首先，使用最精準一組的關鍵詞，僅送出 1 次 brave_search 工具搜尋。
               - 注意：絕對不要發送 2 次搜尋請求(禁止用兩組關鍵字同時搜尋)，這會導致系統錯誤！
            
            2. 分析搜尋結果後，繼續選擇 2-3 個最相關的權威網頁（官方網站、知名媒體或專業評測網站優先）
               - Brave Search 若因為重複跳出搜尋錯誤: HTTP狀態碼 429 時，請繼續使用 fetch_webpage 工具獲取詳細內容。
            
            3. 繼續對每個選擇的網頁使用 fetch_webpage 工具獲取詳細內容。
               注意：這一步是**強制性且必須執行**的！不要跳過！
               如果第一個網頁無法獲取，請嘗試其他網頁，直到成功獲取至少一個網頁的內容。
            
            4. 基於獲取的網頁內容，綜合分析並提供完整的產品報告。
            
            我將無法接受未包含 fetch_webpage 步驟的回應。請記住，搜尋結果摘要永遠不足以提供完整、準確的產品資訊，必須獲取並分析完整的網頁內容。
            
            你的報告應包含以下部分（以繁體中文回答）：
            - 產品的基本介紹
            - 產品規格
            - 主要功能和特點
            - 整體評價摘要
            - 資訊來源參考（列出你使用的網頁URLs）
            
            請保持客觀和準確，如果來源之間有衝突的資訊，請註明並提供多個觀點。
            """
        
        # 執行代理並獲取結果
        response = await agent.ainvoke({
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"請提供關於「{query}」的詳細產品資訊，依規定回答規格、特點和評價等，執行brave_search工具搜尋唯一1次，再用fetch_webpage工具獲取詳細內容。"}
            ]
        })
        
        # 處理 ReAct 代理返回的響應，提取搜尋結果
        formatted_text = ""
        if isinstance(response, dict) and "messages" in response:
            # 獲取最後一條訊息
            if response["messages"] and len(response["messages"]) > 0:
                last_message = response["messages"][-1]
                if hasattr(last_message, "content"):
                    formatted_text = last_message.content
                else:
                    formatted_text = str(last_message)
            else:
                formatted_text = "未找到產品資訊"
        else:
            # 直接獲取非標準格式的回應
            formatted_text = str(response)
        
        # 返回處理後的文本和原始響應
        return {
            "text": formatted_text,
            "raw_response": response
        }

async def main():
    """主程序入口點"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="ReviveAI 產品資訊搜尋")
    parser.add_argument("query", nargs="?", default=None, help="產品搜尋查詢")
    args = parser.parse_args()
    
    # 獲取搜尋查詢
    query = args.query
    if not query:
        query = input("請輸入要搜尋的產品 (例如 'Samsung Galaxy S21 規格'): ")
    
    print(f"\n正在搜尋：{query}")
    print("正在搜尋和分析網路資訊，這可能需要一些時間...\n")
    
    try:
        # 執行搜尋
        result = await search_product_info(query)
        
        # 顯示結果
        print("\n" + "="*60)
        print(f"「{query}」產品資訊報告")
        print("="*60 + "\n")
        
        # 直接使用處理後的文本
        print(result["text"])
        
        print("\n" + "="*60)
    except Exception as e:
        print(f"搜尋過程中發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
