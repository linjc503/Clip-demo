"""
FastAPI 路由模块 - 分类相关接口
"""

from fastapi import APIRouter, UploadFile, File
from typing import Dict, Any
import io
import numpy as np
from PIL import Image

# 导入自定义模块
from src.models.clip_model import encode_text, encode_image

router = APIRouter(prefix="", tags=["分类服务"])

# 零样本分类的类别
CATEGORIES = ["Topwear", "Bottomwear", "Accessories", "Footwear", "PersonalCare"]


@router.post("/classify_image")
async def classify_image(image: UploadFile = File(...)) -> Dict[str, Any]:
    """零样本分类图片"""
    image_data = await image.read()
    img = Image.open(io.BytesIO(image_data))

    image_vector = encode_image(img)

    category_vectors = []
    for category in CATEGORIES:
        category_vector = encode_text(category)
        category_vectors.append(category_vector)

    image_vector_np = np.array(image_vector)
    similarities = []

    for category, vec in zip(CATEGORIES, category_vectors):
        vec_np = np.array(vec)
        similarity = np.dot(image_vector_np, vec_np)
        similarities.append((category, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)
    top_category, top_confidence = similarities[0]

    return {
        "category": top_category,
        "confidence": float(top_confidence),
        "all_categories": [
            {"category": cat, "confidence": float(conf)}
            for cat, conf in similarities
        ]
    }


__all__ = ["router"]
