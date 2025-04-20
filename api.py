from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import tempfile
import os
from typing import Optional, Dict, Any

# 導入服務模組
from image_service import analyze_image
from content_service import generate_product_content
from agent_client import search_product_info
from calculate_carbon import calculate_carbon_footprint_async

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

# 定義請求和響應模型
class ProductDescriptionRequest(BaseModel):
    description: str

class ProductSearchRequest(BaseModel):
    query: str

class CarbonCalculationRequest(BaseModel):
    product_description: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# API 端點
@app.post("/api/image_service", response_model=ApiResponse)
async def image_analysis_endpoint(
    image: UploadFile = File(...)
):
    """
    分析商品圖片並提供詳細描述
    
    - **image**: 商品圖片檔案
    """
    try:
        # 保存上傳的圖片到臨時文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(await image.read())
            temp_path = temp_file.name
        
        # 分析圖片，使用image_service中的預設提示
        response = await analyze_image(temp_path)
        
        # 刪除臨時文件
        os.unlink(temp_path)
        
        return ApiResponse(
            success=True,
            data={"analysis": response.output_text}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/content_service", response_model=ApiResponse)
async def content_optimization_endpoint(request: ProductDescriptionRequest):
    """
    優化商品描述內容
    
    - **description**: 原始商品描述
    """
    try:
        optimized_content = await generate_product_content(request.description)
        return ApiResponse(
            success=True,
            data=optimized_content
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/search_agent", response_model=ApiResponse)
async def search_agent_endpoint(request: ProductSearchRequest):
    """
    使用 AI 代理搜尋產品相關資訊
    
    - **query**: 商品搜尋查詢
    """
    try:
        search_results = await search_product_info(request.query)
        return ApiResponse(
            success=True,
            data={"search_results": search_results["text"]}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/calculate_carbon", response_model=ApiResponse)
async def carbon_calculation_endpoint(request: CarbonCalculationRequest):
    """
    計算商品的碳足跡和環境效益
    
    - **product_description**: 商品描述
    """
    try:
        carbon_results = await calculate_carbon_footprint_async(request.product_description)
        return ApiResponse(
            success=True,
            data=carbon_results
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            error=str(e)
        )

# 啟動服務器
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 