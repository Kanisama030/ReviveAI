from fastapi import APIRouter, File, UploadFile, Form
from pydantic import BaseModel
import tempfile
import os
import logging
from typing import Optional, Dict, Any
import asyncio

# 獲取日誌記錄器
logger = logging.getLogger("reviveai_api")

# 導入服務模組
from image_service import analyze_image
from content_service import generate_product_content
from agent_client import search_product_info
from calculate_carbon import calculate_carbon_footprint_async

# 建立 Router
router = APIRouter(
    prefix="/service",
    tags=["ReviveAI"]
)

# 定義請求和響應模型
class ProductDescriptionRequest(BaseModel):
    description: str

class ProductSearchRequest(BaseModel):
    query: str

class CarbonCalculationRequest(BaseModel):
    product_description: str

class CombinedServiceRequest(BaseModel):
    description: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# API 端點
@router.post("/image_service", response_model=ApiResponse)
async def image_analysis_endpoint(
    image: UploadFile = File(...)
):
    """
    分析商品圖片並提供詳細描述
    - **image**: 商品圖片檔案
    """
    logger.info(f"接收圖片分析請求: {image.filename}")

    try:
        # 保存上傳的圖片到臨時文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(await image.read())
            temp_path = temp_file.name

        logger.info(f"開始分析圖片: {temp_path}")
        response = await analyze_image(temp_path)
        # 刪除臨時文件
        os.unlink(temp_path)
        logger.info(f"圖片分析完成")

        return ApiResponse(
            success=True,
            data={"analysis": response.output_text}
        )
    except Exception as e:
        logger.error(f"圖片分析失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )

@router.post("/content_service", response_model=ApiResponse)
async def content_optimization_endpoint(request: ProductDescriptionRequest):
    """
    優化商品描述內容

    - **description**: 原始商品描述
    """
    desc_preview = request.description[:50] + "..." if len(request.description) > 50 else request.description
    logger.info(f"接收內容優化請求, 內容預覽: {desc_preview}")

    try:
        logger.info(f"開始進行內容優化")
        optimized_content = await generate_product_content(request.description)
        logger.info(f"內容優化完成")

        return ApiResponse(
            success=True,
            data=optimized_content
        )
    except Exception as e:
        logger.error(f"內容優化失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )

@router.post("/search_agent", response_model=ApiResponse)
async def search_agent_endpoint(request: ProductSearchRequest):
    """
    使用 AI 代理搜尋產品相關資訊

    - **query**: 商品搜尋查詢
    """
    logger.info(f"接收搜尋請求: {request.query}")

    try:
        logger.info(f"開始執行搜尋")
        search_results = await search_product_info(request.query)
        logger.info(f"搜尋完成")

        return ApiResponse(
            success=True,
            data={"search_results": search_results["text"]}
        )
    except Exception as e:
        logger.error(f"搜尋失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )

@router.post("/calculate_carbon", response_model=ApiResponse)
async def carbon_calculation_endpoint(request: CarbonCalculationRequest):
    """
    計算商品的碳足跡和環境效益

    - **product_description**: 商品描述
    """
    desc_preview = request.product_description[:50] + "..." if len(request.product_description) > 50 else request.product_description
    logger.info(f"接收碳足跡計算請求, 商品描述預覽: {desc_preview}")

    try:
        logger.info(f"開始計算碳足跡")
        carbon_results = await calculate_carbon_footprint_async(request.product_description)
        logger.info(f"碳足跡計算完成")

        return ApiResponse(
            success=True,
            data=carbon_results
        )
    except Exception as e:
        logger.error(f"碳足跡計算失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )

@router.post("/combined_service", response_model=ApiResponse)
async def combined_service_endpoint(
    description: str = Form(None),
    image: UploadFile = File(...)
):
    """
    綜合服務：分析圖片、優化內容並計算碳足跡

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收綜合服務請求: 圖片={image.filename}, 描述預覽={desc_preview}")

    try:
        # 保存上傳的圖片到臨時文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file.write(await image.read())
            temp_path = temp_file.name

        logger.info(f"開始分析圖片")
        image_analysis = await analyze_image(temp_path)
        image_analysis_text = image_analysis.output_text

        # 刪除臨時文件
        os.unlink(temp_path)

        # 將圖片分析結果與原始描述結合
        combined_description = description or ""
        if image_analysis_text:
            combined_description = f"{combined_description}\n\n圖片分析結果:\n{image_analysis_text}"

        # 並行執行多個非同步操作
        logger.info(f"開始並行執行內容優化和碳足跡計算")
        optimized_content, carbon_results = await asyncio.gather(
            generate_product_content(combined_description),
            calculate_carbon_footprint_async(combined_description)
        )
        logger.info(f"綜合服務處理完成")

        return ApiResponse(
            success=True,
            data={
                "image_analysis": image_analysis_text,
                "optimized_content": optimized_content,
                "carbon_footprint": carbon_results
            }
        )
    except Exception as e:
        logger.error(f"綜合服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )