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
import uuid

# 獲取日誌記錄器
logger = logging.getLogger("reviveai_api")

# 導入服務模組
from image_service import analyze_image, validate_image
from content_service import generate_product_content
from streaming_content_service import generate_streaming_product_content
from calculate_carbon import calculate_carbon_footprint_async
from selling_post_service import generate_selling_post
from seeking_post_service import generate_seeking_post
from seeking_image import create_seeking_image, remake_seeking_image
from ai_image import remake_product_image

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

def format_carbon_footprint_for_content(carbon_results):
    """
    將碳足跡數據格式化為適合融入文案的內容
    """
    if not carbon_results:
        return ""
    
    selected_product = carbon_results.get("selected_product", {})
    saved_carbon = carbon_results.get("saved_carbon", 0)
    benefits = carbon_results.get("environmental_benefits", {})
    
    if saved_carbon <= 0:
        return ""
    
    content = f"""

## 🌱 環保效益

選擇這件二手商品，你為地球做了一件好事！

📊 **減少碳排放：{saved_carbon:.1f} kg CO2e**

🌍 **具體環保貢獻：**
🌳 相當於 {benefits.get('trees', '0')} 棵樹一年的吸碳量
🚗 相當於減少開車 {benefits.get('car_km', '0')} 公里的碳排放  
❄️ 相當於減少吹冷氣 {benefits.get('ac_hours', '0')} 小時的用電量
📱 相當於減少手機充電 {benefits.get('phone_charges', '0')} 次的用電量

💚 **永續意義：** 每一次選擇二手商品，都是對循環經濟的支持，讓好物延續生命週期，減少製造新品對環境的負擔！"""
    
    return content

def format_carbon_footprint_for_social_content(carbon_results):
    """
    將碳足跡數據格式化為適合社群平台的簡潔內容
    """
    if not carbon_results:
        return ""
    
    saved_carbon = carbon_results.get("saved_carbon", 0)
    benefits = carbon_results.get("environmental_benefits", {})
    
    if saved_carbon <= 0:
        return ""
    
    content = f"""

🌱 選擇二手，愛護地球！買這個商品，減少 {saved_carbon:.1f} kg 碳排放，相當於減少開車 🚗 {benefits.get('car_km', '0')} 公里的碳排放"""

    return content

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
    style: str = Form("normal"),  # 添加風格參數，默認為 normal
    generate_image: bool = Form(False)  # 新增生成美化圖片選項
):
    """
    拍賣網站文案服務：分析圖片、優化內容並計算碳足跡

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案 (支持 PNG, JPEG, WEBP，最大 20MB)
    - **style**: 文案風格，可選值：normal(標準專業)、casual(輕鬆活潑)、formal(正式商務)、story(故事體驗)
    - **generate_image**: 是否同時生成AI美化圖片（預設為 false）
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收拍賣網站文案服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 風格={style}, 生成美化圖片={generate_image}")

    try:
        # 保存和驗證上傳的圖片
        temp_path = await save_and_validate_image(image)

        # 準備並行任務
        tasks = []
        task_types = []
        
        # 圖片分析任務
        logger.info(f"開始分析圖片")
        image_analysis_task = analyze_image(temp_path)
        tasks.append(image_analysis_task)
        task_types.append("analysis")
        
        # AI 美化圖片任務（如果需要）
        beautified_image_path = None
        if generate_image:
            logger.info(f"開始生成AI美化圖片")
            beautify_task = remake_product_image(temp_path)
            tasks.append(beautify_task)
            task_types.append("beautify")
        
        # 並行執行圖片相關任務
        image_results = await asyncio.gather(*tasks)
        
        # 處理結果
        image_analysis = image_results[0]
        image_analysis_text = image_analysis.text
        
        if generate_image and len(image_results) > 1:
            beautified_image_path = image_results[1]
            if beautified_image_path:
                logger.info(f"AI美化圖片生成完成: {beautified_image_path}")

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
                "carbon_footprint": carbon_results,
                "beautified_image": beautified_image_path
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
    style: str = Form("normal"),  # 添加風格參數，默認為 normal
    generate_image: bool = Form(False)  # 新增生成美化圖片選項
):
    """
    拍賣網站文案服務（串流版）：分析圖片、優化內容並計算碳足跡，以串流方式回應

    - **description**: 商品描述文字
    - **image**: 商品圖片檔案 (支持 PNG, JPEG, WEBP，最大 20MB)
    - **style**: 文案風格，可選值：normal(標準專業)、casual(輕鬆活潑)、formal(正式商務)、story(故事體驗)
    - **generate_image**: 是否同時生成AI美化圖片（預設為 false）
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收拍賣網站文案串流服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 風格={style}, 生成美化圖片={generate_image}")

    try:
        # 保存和驗證上傳的圖片
        temp_path = await save_and_validate_image(image)

        # 準備並行任務
        tasks = []
        task_types = []
        
        # 圖片分析任務
        logger.info(f"開始分析圖片")
        image_analysis_task = analyze_image(temp_path)
        tasks.append(image_analysis_task)
        task_types.append("analysis")
        
        # AI 美化圖片任務（如果需要）
        beautify_task = None
        if generate_image:
            logger.info(f"開始生成AI美化圖片")
            beautify_task = remake_product_image(temp_path)
            tasks.append(beautify_task)
            task_types.append("beautify")
        
        # 並行執行圖片相關任務
        image_results = await asyncio.gather(*tasks)
        
        # 處理結果
        image_analysis = image_results[0]
        image_analysis_text = image_analysis.text
        
        beautified_image_path = None
        if generate_image and len(image_results) > 1:
            beautified_image_path = image_results[1]
            if beautified_image_path:
                logger.info(f"AI美化圖片生成完成: {beautified_image_path}")

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
            # 首先發送初始數據（圖片分析、碳足跡、搜尋結果和美化圖片）
            initial_data = {
                "type": "metadata",
                "image_analysis": image_analysis_text,
                "search_results": search_results,
                "carbon_footprint": carbon_results,
                "beautified_image": beautified_image_path
            }
            yield json.dumps(initial_data) + "\n"
            
            # 然後串流文案內容
            async for content in content_generator:
                chunk_data = {
                    "type": "content",
                    "chunk": content
                }
                yield json.dumps(chunk_data) + "\n"
            
            # 文案串流完成後，追加碳足跡內容到文案中
            carbon_content = format_carbon_footprint_for_content(carbon_results)
            if carbon_content:
                chunk_data = {
                    "type": "content",
                    "chunk": carbon_content
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
        error_message = str(he.detail)
        # 對於串流請求的錯誤，我們也需要返回一個有效的串流響應
        async def error_response_http():
            yield json.dumps({
                "type": "error",
                "error": error_message
            }) + "\n"
        
        return StreamingResponse(
            error_response_http(),
            media_type="application/json"
        )
    
    except Exception as e:
        logger.error(f"拍賣網站文案串流服務處理失敗: {str(e)}", exc_info=True)
        error_message = str(e)
        # 對於串流請求的錯誤，我們也需要返回一個有效的串流響應
        async def error_response_general():
            yield json.dumps({
                "type": "error",
                "error": error_message
            }) + "\n"
        
        return StreamingResponse(
            error_response_general(),
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
    stream: bool = Form(False),  # 新增串流選項
    generate_image: bool = Form(False)  # 新增生成美化圖片選項
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
    - **generate_image**: 是否同時生成AI美化圖片（預設為 false）
    """
    desc_preview = description[:50] + "..." if description and len(description) > 50 else description
    logger.info(f"接收社群銷售貼文服務請求: 圖片={image.filename}, 描述預覽={desc_preview}, 價格={price}, 串流={stream}, 生成美化圖片={generate_image}")

    try:
        # 保存和驗證上傳的圖片
        temp_path = await save_and_validate_image(image)

        # 準備並行任務
        tasks = []
        task_types = []
        
        # 圖片分析任務
        logger.info(f"開始分析圖片")
        image_analysis_task = analyze_image(temp_path)
        tasks.append(image_analysis_task)
        task_types.append("analysis")
        
        # AI 美化圖片任務（如果需要）
        beautify_task = None
        if generate_image:
            logger.info(f"開始生成AI美化圖片")
            beautify_task = remake_product_image(temp_path)
            tasks.append(beautify_task)
            task_types.append("beautify")
        
        # 並行執行圖片相關任務
        image_results = await asyncio.gather(*tasks)
        
        # 處理結果
        image_analysis = image_results[0]
        image_analysis_text = image_analysis.text
        
        beautified_image_path = None
        if generate_image and len(image_results) > 1:
            beautified_image_path = image_results[1]
            if beautified_image_path:
                logger.info(f"AI美化圖片生成完成: {beautified_image_path}")

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
                # 首先發送初始數據（圖片分析、碳足跡、搜尋結果和美化圖片）
                initial_data = {
                    "type": "metadata",
                    "image_analysis": image_analysis_text,
                    "carbon_footprint": carbon_results,
                    "search_results": search_results,
                    "beautified_image": beautified_image_path
                }
                yield json.dumps(initial_data) + "\n"
                
                # 然後串流文案內容
                async for content in stream_generator():
                    chunk_data = {
                        "type": "content",
                        "chunk": content
                    }
                    yield json.dumps(chunk_data) + "\n"
                
                # 文案串流完成後，追加碳足跡內容到文案中
                carbon_content = format_carbon_footprint_for_social_content(carbon_results)
                if carbon_content:
                    chunk_data = {
                        "type": "content",
                        "chunk": carbon_content
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
                        "carbon_footprint": carbon_results,
                        "beautified_image": beautified_image_path
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
    stream: bool = Form(False),  # 新增串流選項
    generate_image: bool = Form(False)  # 新增生成圖片選項
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
    - **generate_image**: 是否同時生成商品參考圖片（預設為 false）
    """
    desc_preview = product_description[:50] + "..." if len(product_description) > 50 else product_description
    logger.info(f"接收社群徵品貼文服務請求: 描述預覽={desc_preview}, 類型={seeking_type}, 串流={stream}, 生成圖片={generate_image}")

    try:
        image_analysis_text = ""
        generated_image_path = None
        temp_image_path_for_generation = None  # 保存圖片路徑供圖片生成使用

        # 如果有上傳圖片，則進行分析
        if image and image.filename:  # 確保 image 存在且有檔案名稱
            # 保存和驗證上傳的圖片
            temp_path = await save_and_validate_image(image)

            logger.info(f"開始分析參考圖片")
            image_analysis = await analyze_image(temp_path)
            image_analysis_text = image_analysis.text

            # 保存圖片路徑供圖片生成使用（不刪除臨時文件）
            temp_image_path_for_generation = temp_path
        else:
            image_analysis_text = ""
        
        # 將參考圖片分析結果與原始描述結合 (如果有圖片分析)
        combined_description = product_description
        if image_analysis_text:
            combined_description = f"徵求商品：\n{product_description}\n\n參考圖片分析:\n{image_analysis_text}"
        
        # 準備圖片生成任務（如果需要）
        image_generation_mode = None  # 用於標記使用的圖片生成模式
        if generate_image:
            if temp_image_path_for_generation:
                # 模式 2：圖片修圖模式 - 使用已保存的圖片進行修圖
                logger.info(f"開始進行圖片修圖模式，使用上傳的參考圖片")
                # 創建包裝任務來處理圖片修圖
                async def process_image_remake():
                    # 複製臨時文件到我們自己的臨時目錄，以避免文件被意外刪除
                    import shutil
                    temp_copy_path = os.path.join("ui", "temp_images", f"temp_seeking_{uuid.uuid4()}.jpg")
                    os.makedirs(os.path.dirname(temp_copy_path), exist_ok=True)
                    shutil.copy2(temp_image_path_for_generation, temp_copy_path)
                    
                    try:
                        return await remake_seeking_image(temp_copy_path, product_description)
                    finally:
                        # 清理臨時文件
                        for temp_file in [temp_image_path_for_generation, temp_copy_path]:
                            if temp_file and os.path.exists(temp_file):
                                try:
                                    os.unlink(temp_file)
                                except Exception as e:
                                    logger.warning(f"清理臨時文件失敗 {temp_file}: {str(e)}")
                image_generation_task = process_image_remake()
                image_generation_mode = "image-to-image"
            else:
                # 模式 1：文字生成模式 - 根據描述生成圖片
                logger.info(f"開始生成商品參考圖片（文字生成模式）")
                # 組合生成圖片的描述
                image_generation_prompt = f"{product_description} - {purpose} - 預算: {expected_price}"
                image_generation_task = create_seeking_image(image_generation_prompt)
                image_generation_mode = "text-to-image"
        
        if stream:
            # 串流模式處理
            logger.info(f"開始生成串流式徵品文案，使用風格: {style}")
            
            # 準備並行任務
            tasks = []
            task_types = []
            
            # 文案生成任務（串流）
            seeking_post_task = generate_seeking_post(
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
            tasks.append(seeking_post_task)
            task_types.append("text")
            
            # 圖片生成任務（如果需要）
            if generate_image:
                tasks.append(image_generation_task)
                task_types.append("image")
            
            # 如果只有文案任務，直接處理串流
            if len(tasks) == 1:
                stream_generator = await tasks[0]
                
                # 創建一個生成器函數，首先發送其他數據，然後串流文案內容
                async def response_generator():
                    # 首先發送初始數據（圖片分析，生成的圖片初始為 None）
                    initial_data = {
                        "type": "metadata",
                        "image_analysis": image_analysis_text,
                        "generated_image": None  # 沒有圖片生成任務
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
            
            # 如果有圖片任務，使用並行處理
            else:
                # 並行啟動所有任務
                running_tasks = []
                for task in tasks:
                    running_tasks.append(asyncio.create_task(task))
                
                # 獲取文案生成器（第一個任務）
                text_task = running_tasks[0]
                image_task = running_tasks[1] if len(running_tasks) > 1 else None
                
                # 創建一個生成器函數，首先發送其他數據，然後串流文案內容
                async def response_generator():
                    # 首先發送初始數據（圖片分析，生成的圖片初始為 None）
                    initial_data = {
                        "type": "metadata",
                        "image_analysis": image_analysis_text,
                        "generated_image": None,  # 初始時圖片還沒生成完成
                        "image_generation_mode": image_generation_mode
                    }
                    yield json.dumps(initial_data) + "\n"
                    
                    # 然後串流文案內容
                    try:
                        stream_generator = await text_task
                        async for content in stream_generator():
                            chunk_data = {
                                "type": "content",
                                "chunk": content
                            }
                            yield json.dumps(chunk_data) + "\n"
                    except Exception as e:
                        logger.error(f"文案串流失敗: {str(e)}")
                    
                    # 等待圖片生成完成（如果有的話）
                    if image_task:
                        try:
                            generated_image_path = await image_task
                            logger.info(f"商品參考圖片生成完成: {generated_image_path}")
                            
                            # 將路徑轉換為絕對路徑並統一分隔符
                            if generated_image_path:
                                generated_image_path = os.path.abspath(generated_image_path).replace('\\', '/')
                            
                            # 發送圖片生成完成的更新
                            image_update_data = {
                                "type": "image_update",
                                "generated_image": generated_image_path
                            }
                            yield json.dumps(image_update_data) + "\n"
                        except Exception as e:
                            logger.error(f"圖片生成失敗: {str(e)}")
                    
                    # 結束標記
                    yield json.dumps({"type": "end"}) + "\n"
                
                logger.info(f"返回並行串流回應")
                return StreamingResponse(
                    response_generator(),
                    media_type="application/json"
                )
        else:
            # 非串流模式：並行執行圖片生成和文案生成
            logger.info(f"開始並行生成徵品文案和圖片，使用風格: {style}")
            
            # 準備並行任務
            tasks = []
            
            # 文案生成任務
            seeking_post_task = generate_seeking_post(
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
            tasks.append(seeking_post_task)
            
            # 圖片生成任務（如果需要）
            if generate_image:
                if temp_image_path_for_generation:
                    # 模式 2：圖片修圖模式 - 使用已保存的圖片進行修圖
                    logger.info(f"開始進行圖片修圖模式，使用上傳的參考圖片")
                    # 創建包裝任務來處理圖片修圖
                    async def process_image_remake():
                        try:
                            return await remake_seeking_image(temp_image_path_for_generation, product_description)
                        finally:
                            # 清理臨時文件
                            if os.path.exists(temp_image_path_for_generation):
                                os.unlink(temp_image_path_for_generation)
                    tasks.append(process_image_remake())
                else:
                    # 模式 1：文字生成模式 - 根據描述生成圖片
                    logger.info(f"開始生成商品參考圖片（文字生成模式）")
                    # 組合生成圖片的描述
                    image_generation_prompt = f"{product_description} - {purpose} - 預算: {expected_price}"
                    tasks.append(create_seeking_image(image_generation_prompt))
                task_types.append("image")
            # 並行執行所有任務
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            seeking_post_result = results[0] if len(results) > 0 else None
            generated_image_path = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None
            
            if isinstance(results[0], Exception):
                logger.error(f"文案生成失敗: {str(results[0])}")
                seeking_post_result = {"seeking_post": "文案生成失敗"}
            
            if len(results) > 1 and isinstance(results[1], Exception):
                logger.error(f"圖片生成失敗: {str(results[1])}")
                generated_image_path = None
            elif generated_image_path:
                logger.info(f"商品參考圖片生成完成: {generated_image_path}")
                # 將路徑轉換為絕對路徑並統一分隔符
                generated_image_path = os.path.abspath(generated_image_path).replace('\\', '/')

            logger.info(f"社群徵品貼文服務處理完成")

            return ApiResponse(
                    success=True,
                    data={
                        "image_analysis": image_analysis_text if image else "",
                        "seeking_post": seeking_post_result["seeking_post"] if seeking_post_result else "",
                        "generated_image": generated_image_path,
                        "image_generation_mode": image_generation_mode
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
    finally:
        # 確保臨時文件被清理
        # 如果有圖片生成任務，文件清理由圖片任務負責；否則在這裡清理
        if temp_image_path_for_generation and os.path.exists(temp_image_path_for_generation) and not generate_image:
            try:
                os.unlink(temp_image_path_for_generation)
            except Exception as e:
                logger.warning(f"清理臨時文件失敗: {str(e)}")
