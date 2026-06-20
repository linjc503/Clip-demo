"""
CLIP 模型模块
负责图像和文本的向量编码
"""

import clip
import torch
from PIL import Image
from typing import List

# 全局变量
device = "cuda" if torch.cuda.is_available() else "cpu"
model = None
preprocess = None


def init_clip_model():
    """初始化 CLIP 模型"""
    global model, preprocess
    model, preprocess = clip.load("ViT-B/32", device=device)
    print(f"CLIP 模型初始化成功，使用设备: {device}")


def encode_text(text: str) -> List[float]:
    """将文本编码为向量"""
    if model is None:
        init_clip_model()
    
    with torch.no_grad():
        text_features = model.encode_text(clip.tokenize([text]).to(device))
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return text_features[0].cpu().numpy().tolist()


def encode_image(image: Image.Image) -> List[float]:
    """将图片编码为向量"""
    if model is None:
        init_clip_model()
    
    image = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features[0].cpu().numpy().tolist()


__all__ = ["init_clip_model", "encode_text", "encode_image"]
