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
from selling_post_service import generate_selling_post
from seeking_post_service import generate_seeking_post

# 建立 Router
router = APIRouter(
    prefix="/service",
    tags=["ReviveAI"]
)

# 定義請求和響應模型
class ContentRequest(BaseModel):
    description: str
    style: Optional[str] = "normal"  # 默認使用標準風格

class ProductSearchRequest(BaseModel):
    query: str

class CarbonCalculationRequest(BaseModel):
    product_description: str

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
async def content_optimization_endpoint(request: ContentRequest):
    """
    優化商品描述內容，支持多種文案風格

    - **description**: 原始商品描述
    - **style**: 文案風格，可選值：normal(標準專業)、fun(輕鬆活潑)、meme(網路迷因)、formal(正式商務)、story(故事體驗)
    """
    desc_preview = request.description[:50] + "..." if len(request.description) > 50 else request.description
    logger.info(f"接收內容優化請求, 內容預覽: {desc_preview}, 風格: {request.style}")

    try:
        logger.info(f"開始進行內容優化，使用風格: {request.style}")
        optimized_content = await generate_product_content(
            request.description, 
            style=request.style
        )
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

@router.post("/combined_online_sale", response_model=ApiResponse)
async def combined_online_sale_endpoint(
    description: str = Form(None),
    image: UploadFile = File(...),
    style: str = Form("normal")  # 添加風格參數，默認為 normal
):
    """
    拍賣網站文案服務：分析圖片、優化內容並計算碳足跡

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案
    - **style**: 文案風格，可選值：normal(標準專業)、fun(輕鬆活潑)、meme(網路迷因)、formal(正式商務)、story(故事體驗)
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收拍賣網站文案服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 風格={style}")

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
            combined_description = f"商品資訊：\n{combined_description}\n\n圖片分析結果:\n{image_analysis_text}"

        # 並行執行多個非同步操作
        logger.info(f"開始並行執行內容優化和碳足跡計算，使用風格: {style}")
        optimized_content, carbon_results = await asyncio.gather(
            generate_product_content(combined_description, style=style),  # 傳遞風格參數
            calculate_carbon_footprint_async(combined_description)
        )
        logger.info(f"拍賣網站文案服務處理完成")

        return ApiResponse(
            success=True,
            data={
                "image_analysis": image_analysis_text,
                "optimized_content": optimized_content,
                "carbon_footprint": carbon_results
            }
        )
    except Exception as e:
        logger.error(f"拍賣網站文案服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )

@router.post("/combined_selling_post", response_model=ApiResponse)
async def combined_selling_post_endpoint(
    description: str = Form(None),
    image: UploadFile = File(...),
    price: str = Form(...),
    contact_info: str = Form("請私訊詳詢"),
    trade_method: str = Form("面交/郵寄皆可")
):
    """
    社群銷售貼文服務：分析圖片、計算碳足跡並生成社群平台銷售文案

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案
    - **price**: 商品售價
    - **contact_info**: 聯絡方式
    - **trade_method**: 交易方式
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收社群銷售貼文服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 價格={price}")

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
            combined_description = f"商品資訊：\n{combined_description}\n\n圖片分析結果:\n{image_analysis_text}"
        
        # 並行執行多個非同步操作
        logger.info(f"開始並行生成社群文案和碳足跡計算")
        selling_post_result, carbon_results = await asyncio.gather(
            generate_selling_post(
                product_description=combined_description,
                price=price,
                contact_info=contact_info,
                trade_method=trade_method,
            ),  # 先不傳遞風格參數
            calculate_carbon_footprint_async(combined_description)
        )

        logger.info(f"社群銷售貼文服務處理完成")

        return ApiResponse(
            success=True,
            data={
                "image_analysis": image_analysis_text,
                "selling_post": selling_post_result["selling_post"],
                "carbon_footprint": carbon_results
            }
        )
    except Exception as e:
        logger.error(f"社群銷售貼文服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )
    
@router.post("/combined_seeking_post", response_model=ApiResponse)
async def combined_seeking_post_endpoint(
    product_description: str = Form(...),
    purpose: str = Form(...),
    expected_price: str = Form(...),
    contact_info: str = Form("請私訊詳詢"),
    location: str = Form("台北市"),
    seeking_type: str = Form("buy"),  # "buy" 或 "rent"
    deadline: str = Form("越快越好"),
    image: Optional[UploadFile] = File(None), 
    style: str = Form("normal")
):
    """
    社群徵品貼文服務：分析圖片(可選)、計算碳足跡並生成社群平台徵求文案
    
    - **product_description**: 徵求的商品描述
    - **purpose**: 徵求目的/用途
    - **expected_price**: 期望價格
    - **contact_info**: 聯絡方式
    - **location**: 交易地點
    - **seeking_type**: 徵求類型，購買(buy)或租借(rent)
    - **deadline**: 徵求時效
    - **image**: 參考圖片檔案 (可選)
    - **style**: 文案風格
    """
    desc_preview = product_description[:50] + "..." if len(product_description) > 50 else product_description
    logger.info(f"接收社群徵品貼文服務請求: 描述預覽={desc_preview}, 類型={seeking_type}")

    try:
        image_analysis_text = ""

        # 如果有上傳圖片，則進行分析
        if image and image.filename:  # 確保 image 存在且有檔案名稱
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(await image.read())
                temp_path = temp_file.name

            logger.info(f"開始分析參考圖片")
            image_analysis = await analyze_image(temp_path)
            image_analysis_text = image_analysis.output_text

            # 刪除臨時文件
            os.unlink(temp_path)
        
        # 將參考圖片分析結果與原始描述結合 (如果有圖片分析)
        combined_description = product_description
        if image_analysis_text:
            combined_description = f"徵求商品：\n{product_description}\n\n參考圖片分析:\n{image_analysis_text}"
        
        # 生成徵品文案
        logger.info(f"開始生成徵品文案，使用風格: {style}")
        seeking_post_result = await generate_seeking_post(
            product_description=combined_description,
            purpose=purpose,
            expected_price=expected_price,
            contact_info=contact_info,
            location=location,
            seeking_type=seeking_type,
            deadline=deadline,
            style=style
        )

        logger.info(f"社群徵品貼文服務處理完成")

        return ApiResponse(
            success=True,
            data={
                "image_analysis": image_analysis_text if image else "",
                "seeking_post": seeking_post_result["seeking_post"]
            }
        )
    except Exception as e:
        logger.error(f"社群徵品貼文服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )