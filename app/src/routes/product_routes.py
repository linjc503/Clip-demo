"""
FastAPI 路由模块 - 商品相关接口
"""

from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional, Dict, Any
import io
from PIL import Image

# 导入自定义模块
from src.models.clip_model import encode_text, encode_image
from src.db.vector_db import generate_product_id, add_product_to_db, search_products_by_vector

router = APIRouter(prefix="", tags=["商品管理"])


@router.post("/add_text")
async def add_text(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(0.0),
    category: str = Form(""),
    material: str = Form(""),
    color: str = Form(""),
    tags: str = Form("")
) -> Dict[str, Any]:
    """添加商品到向量数据库（文本方式）"""
    product_id = generate_product_id()

    # 构建完整的商品描述文本
    full_description = f"{name} {description} {category} {material} {color} {tags}".strip()

    # 准备元数据
    metadata = {
        "type": "product",
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags,
        "stock": 100
    }

    # 添加到向量数据库
    text_vector = encode_text(full_description)
    add_product_to_db(product_id, text_vector, metadata, "text")

    return {
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags
    }


@router.post("/add_image")
async def add_image(
    image: UploadFile = File(...),
    name: str = Form(""),
    description: str = Form(""),
    price: float = Form(0.0),
    category: str = Form(""),
    material: str = Form(""),
    color: str = Form(""),
    tags: str = Form("")
) -> Dict[str, Any]:
    """添加图片商品到向量数据库"""
    product_id = generate_product_id()

    # 读取图片并编码
    image_data = await image.read()
    img = Image.open(io.BytesIO(image_data))
    image_vector = encode_image(img)

    # 构建完整的商品描述文本
    full_description = f"{name} {description} {category} {material} {color} {tags}".strip()

    # 准备元数据
    metadata = {
        "type": "product",
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags,
        "has_image": True,
        "stock": 100
    }

    # 添加图片向量
    add_product_to_db(product_id, image_vector, metadata, "image")

    # 添加文本向量（用于文本搜索）
    if full_description:
        text_vector = encode_text(full_description)
        add_product_to_db(product_id, text_vector, metadata, "text")

    return {
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags
    }


@router.post("/search_text")
async def search_text(text: str) -> Dict[str, Any]:
    """搜索相似商品（文本方式）"""
    text_vector = encode_text(text)
    results = search_products_by_vector(text_vector, 5)
    return {"query": text, "results": results}


@router.post("/search_image")
async def search_image(image: UploadFile = File(...)) -> Dict[str, Any]:
    """搜索相似商品（图片方式）"""
    image_data = await image.read()
    img = Image.open(io.BytesIO(image_data))
    image_vector = encode_image(img)
    results = search_products_by_vector(image_vector, 5)
    return {"results": results}


__all__ = ["router"]
