"""
多模态商品智能系统 - 主入口文件
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# 导入自定义模块
from src.models.clip_model import init_clip_model
from src.db.vector_db import init_vector_db
from src.chat.qwen_agent import init_qwen_agent, set_api_key
from src.frontend.page_template import get_html_content

# 导入路由模块
from src.routes.product_routes import router as product_router
from src.routes.classify_routes import router as classify_router
from src.routes.chat_routes import router as chat_router

# 配置
DASHSCOPE_API_KEY = "your-dashscope-api-key-here"  # 请替换为您的阿里云DashScope API Key

# 初始化应用
app = FastAPI(title="多模态商品智能系统", version="1.0.0")

# 注册路由
app.include_router(product_router)
app.include_router(classify_router)
app.include_router(chat_router)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回前端页面"""
    return get_html_content()


def init_services():
    """初始化所有服务"""
    print("正在初始化服务...")

    # 初始化向量数据库
    init_vector_db()

    # 初始化 CLIP 模型
    init_clip_model()

    # 设置 API Key 并初始化 Qwen Agent
    set_api_key(DASHSCOPE_API_KEY)
    init_qwen_agent()

    print("所有服务初始化完成！")


# 启动时初始化服务
init_services()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
