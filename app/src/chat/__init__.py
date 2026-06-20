# 聊天模块初始化
from .conversation_history import (
    add_to_history,
    clear_history,
    get_history_count,
    get_history,
    undo_last_message,
    build_messages_for_agent
)
from .qwen_agent import set_api_key, init_qwen_agent, get_agent, run_agent

__all__ = [
    "add_to_history",
    "clear_history",
    "get_history_count",
    "get_history",
    "undo_last_message",
    "build_messages_for_agent",
    "set_api_key",
    "init_qwen_agent",
    "get_agent",
    "run_agent"
]
