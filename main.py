from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import combined_service_api
# import archive.single_service_api  # 已封存，暫不使用

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("reviveai_api")

# 建立 FastAPI 應用程序
app = FastAPI(
    title="ReviveAI API",
    description="二手商品優化 API 服務",
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加入路由 - 只使用組合服務路由
app.include_router(combined_service_api.router)
# app.include_router(archive.single_service_api.router)  # 已封存，單一功能 router

# 添加簡單的中間件記錄請求
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"收到請求: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"請求完成: {request.method} {request.url.path} - 狀態碼: {response.status_code}")
    return response

# 啟動服務器
if __name__ == "__main__":
    logger.info("ReviveAI API 服務啟動中...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False,log_level="info")