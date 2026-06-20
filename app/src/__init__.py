"""
多模态商品智能系统 - src 包初始化
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "MultiModal Product System"

# 导出核心模块
from .models.clip_model import init_clip_model, encode_text, encode_image
from .db.vector_db import init_vector_db, generate_product_id, add_product_to_db, search_products_by_vector
from .chat.conversation_history import (
    add_to_history,
    clear_history,
    get_history_count,
    get_history,
    undo_last_message,
    build_messages_for_agent
)
from .chat.qwen_agent import set_api_key, init_qwen_agent, get_agent, run_agent
from .rag.context_builder import build_product_context, format_product_info
from .tools.search_tool import ProductSearchTool, search_products

__all__ = [
    # clip_model
    "init_clip_model",
    "encode_text",
    "encode_image",
    # vector_db
    "init_vector_db",
    "generate_product_id",
    "add_product_to_db",
    "search_products_by_vector",
    # conversation_history
    "add_to_history",
    "clear_history",
    "get_history_count",
    "get_history",
    "undo_last_message",
    "build_messages_for_agent",
    # qwen_agent
    "set_api_key",
    "init_qwen_agent",
    "get_agent",
    "run_agent",
    # context_builder
    "build_product_context",
    "format_product_info",
    # search_tool
    "ProductSearchTool",
    "search_products"
]
