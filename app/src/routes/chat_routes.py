"""
FastAPI 路由模块 - 聊天相关接口
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any
import json

# 导入自定义模块
from src.chat.qwen_agent import get_agent, run_agent
from src.chat.conversation_history import (
    add_to_history,
    clear_history,
    get_history_count,
    get_history,
    undo_last_message,
    build_messages_for_agent
)

router = APIRouter(prefix="/chat", tags=["聊天服务"])


async def chat_stream_generator(message: str) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    if not message:
        yield f"data: {json.dumps({'error': '消息不能为空'}, ensure_ascii=False)}\n\n"
        return

    agent = get_agent()
    if not agent:
        yield f"data: {json.dumps({'error': '抱歉，Qwen Agent未初始化。请检查DASHSCOPE_API_KEY是否正确设置。'}, ensure_ascii=False)}\n\n"
        return

    try:
        full_reply = ""

        # 构建包含历史的消息列表
        messages = build_messages_for_agent(message)

        # 遍历生成器获取响应
        responses = run_agent(messages)
        if responses:
            for response in responses:
                # 尝试从响应中提取增量文本
                if isinstance(response, list) and len(response) > 0:
                    last_item = response[-1]

                    if isinstance(last_item, dict):
                        content = last_item.get("content", "")

                        # 处理不同类型的 content
                        text_chunk = None
                        if isinstance(content, str):
                            text_chunk = content
                        elif isinstance(content, list):
                            # 提取文本块
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_chunk = block.get("text", "")
                                    break
                                elif isinstance(block, str):
                                    text_chunk = block
                                    break

                        if text_chunk and len(text_chunk) > len(full_reply):
                            # 计算增量文本
                            delta = text_chunk[len(full_reply):]
                            if delta:
                                full_reply = text_chunk
                                # 发送增量更新
                                yield f"data: {json.dumps({'delta': delta, 'full': full_reply}, ensure_ascii=False)}\n\n"

        # 发送完成信号
        if not full_reply:
            full_reply = "抱歉，我没有收到有效回复。"
            yield f"data: {json.dumps({'delta': full_reply, 'full': full_reply, 'done': True}, ensure_ascii=False)}\n\n"
            # 即使回复为空，也记录到历史
            add_to_history("user", message)
            add_to_history("assistant", full_reply)
        else:
            yield f"data: {json.dumps({'done': True, 'full': full_reply}, ensure_ascii=False)}\n\n"
            # 将对话添加到历史记录
            add_to_history("user", message)
            add_to_history("assistant", full_reply)

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"处理出错: {str(e)}"
        yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
        # 即使出错，也记录用户消息
        add_to_history("user", message)


@router.post("")
async def chat(request: Request):
    """商品客服聊天接口（流式输出）"""
    try:
        body = await request.json()
        message = body.get("message", "")
    except Exception:
        message = ""

    return StreamingResponse(
        chat_stream_generator(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/history")
async def get_chat_history():
    """获取当前对话历史"""
    return {
        "count": get_history_count(),
        "max_length": 20,
        "history": get_history()
    }


@router.post("/clear")
async def clear_chat_history():
    """清空对话历史"""
    message = clear_history()
    return {"message": message}


@router.post("/undo")
async def undo_last():
    """撤销上一条消息"""
    message = undo_last_message()
    return {"message": message}


__all__ = ["router"]
