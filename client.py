"""
ReviveAI 產品搜尋客戶端

此客戶端連接到 WebTools MCP 服務器，使用 LangChain 和 LangGraph
實現一個能夠執行網路搜尋和分析產品資訊的 AI 代理。
"""

import os
import asyncio
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
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
        處理後的回應內容
    """
    # 使用 OpenAI 模型
    model = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    print("使用 OpenAI GPT-4.1-mini 模型")
    
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
        system_message = """你是一個專業的產品研究助手，專門幫助用戶尋找和分析產品的詳細資訊。

請按照以下步驟執行產品資訊搜尋：
1. 使用 brave_search 工具搜尋產品的相關資訊
2. 仔細分析搜尋結果，找出最相關和權威的網頁
3. 使用 fetch_webpage 工具獲取這些網頁的詳細內容
4. 綜合分析所有獲取的資訊，提供完整的產品報告

你的報告應包含以下部分（以繁體中文回答）：
- 產品的基本介紹
- 產品規格
- 主要功能和特點
- 使用者評價摘要
- 資訊來源參考

請保持客觀和準確，如果來源之間有衝突的資訊，請註明並提供多個觀點。
"""
        
        # 執行代理並獲取結果
        response = await agent.ainvoke({
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"請提供關於「{query}」的詳細產品資訊，特別是技術規格、特點、優缺點和評價。"}
            ]
        })
        
        return response

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
        
        # 根據不同的響應結構顯示內容
        if isinstance(result, str):
            # 如果直接返回字符串
            print(result)
            
        elif isinstance(result, dict):
            # 處理字典類型的響應
            # 首先嘗試尋找 messages 中的 AI 消息
            if "messages" in result:
                ai_messages = [msg for msg in result["messages"] if msg.type == "ai"]
                if ai_messages:
                    print(ai_messages[-1].content)
                    
                # 如果找不到 AI 消息但有其他消息
                elif result["messages"]:
                    last_message = result["messages"][-1]
                    print(last_message.content)
                    
                # 沒有任何消息
                else:
                    print("回應中沒有找到任何消息。")
                    
            # 處理其他常見的回應格式
            elif "output" in result:
                print(result["output"])
            elif "output_text" in result:
                print(result["output_text"])
            elif "steps" in result and result["steps"] and "output" in result["steps"][-1]:
                print(result["steps"][-1]["output"])
            elif "content" in result:
                print(result["content"])
            else:
                # 無法識別的格式直接輸出
                print(result)
        else:
            # 其他類型的響應
            print(result)
        
        print("\n" + "="*60)
    except Exception as e:
        print(f"搜尋過程中發生錯誤：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
