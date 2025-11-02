"""
ReviveAI 產品搜尋客戶端

此客戶端連接到 WebTools MCP 服務器，使用 LangChain 和 LangGraph
實現一個能夠執行網路搜尋和分析產品資訊的 AI 代理。
"""

import asyncio
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import getpass
import os

# 提示輸入 Google AI API 金鑰（如果尚未設定環境變數）
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

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
    # model = ChatOpenAI(model="gpt-4o-mini")
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

    
    # 配置 MCP 客戶端並連接到 WebTools 服務器
    client = MultiServerMCPClient(
        {
            "web_tools": {
                "command": "python",
                "args": ["web_tools_server.py"],
                "transport": "stdio",
            }
        }
    )
    
    try:
        # 獲取所有工具（根據新 API 要求）
        tools = await client.get_tools()
        
        # 系統提示
        system_prompt = """你是一個專業的產品研究助手，請按照此流程執行：

【狀態機制】
狀態 1：【初始】→ 執行 brave_search（1次）→ 狀態 2
狀態 2：【已搜尋】→ 選擇最佳網頁，執行 fetch_webpage（1次同時 2 個網站）→ 狀態 3  
狀態 3：【已抓取】→ 生成最終報告 → 完成

【嚴格執行規則】
1. brave_search：僅執行 1 次
2. fetch_webpage：僅執行 1 次（選擇 2 個最權威的網站同時執行 fetch_webpage）
3. 禁止只說不做：每次工具調用必須立即執行
4. 強制報告：即使網頁抓取失敗也必須基於搜尋結果生成報告

【狀態轉換宣告】
- 執行 brave_search 後 → 「狀態轉換：進入狀態2」
- 執行 fetch_webpage 後 → 「狀態轉換：進入狀態3」

【錯誤處理】
- 如果網頁抓取失敗：基於搜尋結果摘要分析，不要重試其他網站
- 429 錯誤：繼續執行 fetch_webpage，不重試搜尋

【最終報告】（繁體中文，內容長度限 200 字以內）
- 產品基本介紹
- 產品規格  
- 主要功能特點
- 整體評價摘要
- 參考來源（不需要列出 URL）
"""
        
        # 創建代理（使用新的 create_agent API）
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt
        )
        
        # 執行代理並獲取結果
        response = await agent.ainvoke({
            "messages": [
                {"role": "user", "content": f"請研究「{query}」的詳細產品資訊。\n\n**簡化執行流程**：\n\n【步驟1】執行 brave_search（僅1次）→ 宣告「狀態轉換：進入狀態2」\n\n【步驟2】選擇最權威的網站，執行 fetch_webpage（僅1次）→ 宣告「狀態轉換：進入狀態3」\n\n【步驟3】生成完整產品報告\n\n**重要提醒**：\n- 每個工具只執行一次\n- 禁止說「即將執行」而不實際執行\n- 即使網頁抓取失敗也必須基於搜尋結果生成300字以內的繁體中文報告"}
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
    except Exception as e:
        # 捕獲並記錄任何錯誤
        print(f"搜尋產品資訊時發生錯誤：{str(e)}")
        raise

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
