# 路由模块初始化
from .product_routes import router as product_router
from .classify_routes import router as classify_router
from .chat_routes import router as chat_router

__all__ = ["product_router", "classify_router", "chat_router"]
