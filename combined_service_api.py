from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
import tempfile
import os
import logging
from typing import Optional, Dict, Any
import asyncio
import json
from fastapi.responses import StreamingResponse
from pathlib import Path
import filetype  # 使用 filetype 代替 imghdr

# 獲取日誌記錄器
logger = logging.getLogger("reviveai_api")

# 導入服務模組
from image_service import analyze_image, validate_image
from content_service import generate_product_content
from streaming_content_service import generate_streaming_product_content
from calculate_carbon import calculate_carbon_footprint_async
from selling_post_service import generate_selling_post
from seeking_post_service import generate_seeking_post

# 建立 Router
router = APIRouter(
    prefix="/combined_service",
    tags=["ReviveAI Combined Services"]
)

# 定義響應模型
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 驗證並保存上傳的圖片到臨時文件
async def save_and_validate_image(image: UploadFile):
    if not image:
        raise HTTPException(status_code=400, detail="未提供圖片文件")
    
    # 檢查檔案是否為空
    file_content = await image.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="圖片文件為空")
    
    # 根據常見的圖片擴展名確定臨時文件的副檔名
    # 注意：這裡我們只使用副檔名來幫助建立臨時文件，實際的格式驗證在後續進行
    file_extension = Path(image.filename).suffix.lower() if image.filename else ".tmp"
    
    # 保存上傳的圖片到臨時文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(file_content)
        temp_path = temp_file.name
    
    try:
        # 驗證圖片格式和大小
        validate_image(temp_path)
        return temp_path
    except Exception as e:
        # 如果驗證失敗，刪除臨時文件並拋出錯誤
        os.unlink(temp_path)
        raise HTTPException(status_code=400, detail=str(e))

# API 端點
@router.post("/online_sale", response_model=ApiResponse)
async def combined_online_sale_endpoint(
    description: str = Form(None),
    image: UploadFile = File(...),
    style: str = Form("normal")  # 添加風格參數，默認為 normal
):
    """
    拍賣網站文案服務：分析圖片、優化內容並計算碳足跡

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案 (支持 PNG, JPEG, WEBP，最大 20MB)
    - **style**: 文案風格，可選值：normal(標準專業)、casual(輕鬆活潑)、formal(正式商務)、story(故事體驗)
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收拍賣網站文案服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 風格={style}")

    try:
        # 保存和驗證上傳的圖片
        temp_path = await save_and_validate_image(image)

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
    except HTTPException as he:
        logger.error(f"拍賣網站文案服務處理失敗: {str(he)}")
        return ApiResponse(
            success=False,
            error=str(he.detail)
        )
    except Exception as e:
        logger.error(f"拍賣網站文案服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )

@router.post("/online_sale_stream")
async def combined_online_sale_stream_endpoint(
    description: str = Form(None),
    image: UploadFile = File(...),
    style: str = Form("normal")  # 添加風格參數，默認為 normal
):
    """
    拍賣網站文案服務（串流版）：分析圖片、優化內容並計算碳足跡，以串流方式回應

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案 (支持 PNG, JPEG, WEBP，最大 20MB)
    - **style**: 文案風格，可選值：normal(標準專業)、casual(輕鬆活潑)、formal(正式商務)、story(故事體驗)
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收拍賣網站文案串流服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 風格={style}")

    try:
        # 保存和驗證上傳的圖片
        temp_path = await save_and_validate_image(image)

        logger.info(f"開始分析圖片")
        image_analysis = await analyze_image(temp_path)
        image_analysis_text = image_analysis.output_text

        # 刪除臨時文件
        os.unlink(temp_path)

        # 將圖片分析結果與原始描述結合
        combined_description = description or ""
        if image_analysis_text:
            combined_description = f"商品資訊：\n{combined_description}\n\n圖片分析結果:\n{image_analysis_text}"
        
        # 啟動碳足跡計算任務（不等待完成）
        logger.info(f"開始計算碳足跡")
        carbon_task = asyncio.create_task(calculate_carbon_footprint_async(combined_description))
        
        # 獲取串流內容生成器
        logger.info(f"開始生成串流式內容優化，使用風格: {style}")
        streaming_result = await generate_streaming_product_content(combined_description, style=style)
        search_results = streaming_result["search_results"]
        content_generator = streaming_result["content_generator"]
        
        # 等待碳足跡計算完成
        carbon_results = await carbon_task
        
        # 創建一個生成器函數，首先發送初始數據，然後串流內容
        async def response_generator():
            # 首先發送初始數據（圖片分析和碳足跡）
            initial_data = {
                "type": "metadata",
                "image_analysis": image_analysis_text,
                "search_results": search_results,
                "carbon_footprint": carbon_results
            }
            yield json.dumps(initial_data) + "\n"
            
            # 然後串流文案內容
            async for content in content_generator:
                chunk_data = {
                    "type": "content",
                    "chunk": content
                }
                yield json.dumps(chunk_data) + "\n"
            
            # 結束標記
            yield json.dumps({"type": "end"}) + "\n"
        
        logger.info(f"返回串流回應")
        return StreamingResponse(
            response_generator(),
            media_type="application/json"
        )
    
    except HTTPException as he:
        logger.error(f"拍賣網站文案串流服務處理失敗: {str(he)}")
        # 對於串流請求的錯誤，我們也需要返回一個有效的串流響應
        async def error_response():
            yield json.dumps({
                "type": "error",
                "error": str(he.detail)
            }) + "\n"
        
        return StreamingResponse(
            error_response(),
            media_type="application/json"
        )
    
    except Exception as e:
        logger.error(f"拍賣網站文案串流服務處理失敗: {str(e)}", exc_info=True)
        # 對於串流請求的錯誤，我們也需要返回一個有效的串流響應
        async def error_response():
            yield json.dumps({
                "type": "error",
                "error": str(e)
            }) + "\n"
        
        return StreamingResponse(
            error_response(),
            media_type="application/json"
        )

@router.post("/selling_post")
async def combined_selling_post_endpoint(
    description: str = Form(None),
    image: UploadFile = File(...),
    price: str = Form(...),
    contact_info: str = Form("請私訊詳詢"),
    trade_method: str = Form("面交/郵寄皆可"),
    style: str = Form("normal"),
    stream: bool = Form(False)  # 新增串流選項
):
    """
    社群銷售貼文服務：分析圖片、計算碳足跡並生成社群平台銷售文案

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案 (支持 PNG, JPEG, WEBP，最大 20MB)
    - **price**: 商品售價
    - **contact_info**: 聯絡方式
    - **trade_method**: 交易方式
    - **style**: 文案風格，可選值:normal (標準實用)、storytelling (故事體驗)、minimalist (簡約精要)、bargain (超值優惠)
    - **stream**: 是否使用串流回應（預設為 false）
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收社群銷售貼文服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 價格={price}, 串流={stream}")

    try:
        # 保存和驗證上傳的圖片
        temp_path = await save_and_validate_image(image)

        logger.info(f"開始分析圖片")
        image_analysis = await analyze_image(temp_path)
        image_analysis_text = image_analysis.output_text

        # 刪除臨時文件
        os.unlink(temp_path)

        # 將圖片分析結果與原始描述結合
        combined_description = description or ""
        if image_analysis_text:
            combined_description = f"商品資訊：\n{combined_description}\n\n圖片分析結果:\n{image_analysis_text}"
        
        # 開始碳足跡計算 (不管是否串流，都先開始計算，實現並行處理)
        logger.info(f"開始計算碳足跡")
        carbon_task = asyncio.create_task(calculate_carbon_footprint_async(combined_description))
        
        if stream:
            # 串流模式處理
            logger.info(f"開始生成串流式銷售文案，使用風格: {style}")
            
            # 獲取搜尋結果（與拍賣網站功能相同）
            logger.info(f"開始生成串流式內容優化以獲取搜尋結果")
            streaming_result = await generate_streaming_product_content(combined_description, style=style)
            search_results = streaming_result["search_results"]
            
            # 獲取生成器函數
            stream_generator = await generate_selling_post(
                product_description=combined_description,
                price=price,
                contact_info=contact_info,
                trade_method=trade_method,
                style=style,
                stream=True
            )
            
            # 等待碳足跡計算完成
            carbon_results = await carbon_task

            # 創建一個生成器函數，首先發送其他數據，然後串流文案內容
            async def response_generator():
                # 首先發送初始數據（圖片分析、碳足跡和搜尋結果）
                initial_data = {
                    "type": "metadata",
                    "image_analysis": image_analysis_text,
                    "carbon_footprint": carbon_results,
                    "search_results": search_results
                }
                yield json.dumps(initial_data) + "\n"
                
                # 然後串流文案內容
                async for content in stream_generator():
                    chunk_data = {
                        "type": "content",
                        "chunk": content
                    }
                    yield json.dumps(chunk_data) + "\n"
                
                # 結束標記
                yield json.dumps({"type": "end"}) + "\n"
            
            logger.info(f"返回串流回應")
            return StreamingResponse(
                response_generator(),
                media_type="application/json"
            )
        else:
            # 非串流模式（原有功能）
            logger.info(f"開始生成銷售文案，使用風格: {style}")
            selling_post_task = asyncio.create_task(generate_selling_post(
                product_description=combined_description,
                price=price,
                contact_info=contact_info,
                trade_method=trade_method,
                style=style,
                stream=False
            ))
            # 等待兩個任務完成
            selling_post_result, carbon_results = await asyncio.gather(
                selling_post_task,
                carbon_task
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
        
    except HTTPException as he:
        logger.error(f"社群銷售貼文服務處理失敗: {str(he)}")
        return ApiResponse(
            success=False,
            error=str(he.detail)
        )
    except Exception as e:
        logger.error(f"社群銷售貼文服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )
    
@router.post("/seeking_post")
async def combined_seeking_post_endpoint(
    product_description: str = Form(...),
    purpose: str = Form(...),
    expected_price: str = Form(...),
    contact_info: str = Form("請私訊詳詢"),
    trade_method: str = Form("面交/郵寄皆可"),
    seeking_type: str = Form("buy"),  # "buy" 或 "rent"
    deadline: str = Form("越快越好"),
    image: Optional[UploadFile] = File(None), 
    style: str = Form("normal"),
    stream: bool = Form(False)  # 新增串流選項
):
    """
    社群徵品貼文服務：分析圖片(可選)、計算碳足跡並生成社群平台徵求文案
    
    - **product_description**: 徵求的商品描述
    - **purpose**: 徵求目的/用途
    - **expected_price**: 期望價格
    - **contact_info**: 聯絡方式
    - **trade_method**: 交易方式
    - **seeking_type**: 徵求類型，購買(buy)或租借(rent)
    - **deadline**: 徵求時效
    - **image**: 參考圖片檔案 (可選，支持 PNG, JPEG, WEBP，最大 20MB)
    - **style**: 文案風格，可選值:normal (標準親切)、urgent (急需緊急)、 budget (預算有限)、collector (收藏愛好)
    - **stream**: 是否使用串流回應（預設為 false）
    """
    desc_preview = product_description[:50] + "..." if len(product_description) > 50 else product_description
    logger.info(f"接收社群徵品貼文服務請求: 描述預覽={desc_preview}, 類型={seeking_type}, 串流={stream}")

    try:
        image_analysis_text = ""

        # 如果有上傳圖片，則進行分析
        if image and image.filename:  # 確保 image 存在且有檔案名稱
            # 保存和驗證上傳的圖片
            temp_path = await save_and_validate_image(image)

            logger.info(f"開始分析參考圖片")
            image_analysis = await analyze_image(temp_path)
            image_analysis_text = image_analysis.output_text

            # 刪除臨時文件
            os.unlink(temp_path)
        
        # 將參考圖片分析結果與原始描述結合 (如果有圖片分析)
        combined_description = product_description
        if image_analysis_text:
            combined_description = f"徵求商品：\n{product_description}\n\n參考圖片分析:\n{image_analysis_text}"
        
        if stream:
            # 串流模式處理
            logger.info(f"開始生成串流式徵品文案，使用風格: {style}")
            
            # 獲取生成器函數
            stream_generator = await generate_seeking_post(
                product_description=combined_description,
                purpose=purpose,
                expected_price=expected_price,
                contact_info=contact_info,
                trade_method=trade_method,
                seeking_type=seeking_type,
                deadline=deadline,
                style=style,
                stream=True
            )
            
            # 創建一個生成器函數，首先發送其他數據，然後串流文案內容
            async def response_generator():
                # 首先發送初始數據（圖片分析）
                initial_data = {
                    "type": "metadata",
                    "image_analysis": image_analysis_text
                }
                yield json.dumps(initial_data) + "\n"
                
                # 然後串流文案內容
                async for content in stream_generator():
                    chunk_data = {
                        "type": "content",
                        "chunk": content
                    }
                    yield json.dumps(chunk_data) + "\n"
                
                # 結束標記
                yield json.dumps({"type": "end"}) + "\n"
            
            logger.info(f"返回串流回應")
            return StreamingResponse(
                response_generator(),
                media_type="application/json"
            )
        else:
            # 非串流模式（原有功能）
            logger.info(f"開始生成徵品文案，使用風格: {style}")
            seeking_post_result = await generate_seeking_post(
                product_description=combined_description,
                purpose=purpose,
                expected_price=expected_price,
                contact_info=contact_info,
                trade_method=trade_method,
                seeking_type=seeking_type,
                deadline=deadline,
                style=style,
                stream=False
            )

            logger.info(f"社群徵品貼文服務處理完成")

            return ApiResponse(
                    success=True,
                    data={
                        "image_analysis": image_analysis_text if image else "",
                        "seeking_post": seeking_post_result["seeking_post"]
                    }
                )
        
    except HTTPException as he:
        logger.error(f"社群徵品貼文服務處理失敗: {str(he)}")
        return ApiResponse(
            success=False,
            error=str(he.detail)
        )
    except Exception as e:
        logger.error(f"社群徵品貼文服務處理失敗: {str(e)}", exc_info=True)
        return ApiResponse(
            success=False,
            error=str(e)
        )
