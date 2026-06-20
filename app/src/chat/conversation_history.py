"""
对话历史管理模块
负责管理聊天会话的短期记忆
"""

from typing import List, Dict

# 全局变量
MAX_HISTORY_LENGTH = 20
conversation_history: List[Dict[str, str]] = []


def add_to_history(role: str, content: str):
    """添加对话到历史记录"""
    global conversation_history
    conversation_history.append({
        "role": role,
        "content": content
    })
    # 如果超过最大长度，删除最早的对话
    if len(conversation_history) > MAX_HISTORY_LENGTH:
        conversation_history = conversation_history[-MAX_HISTORY_LENGTH:]


def clear_history() -> str:
    """清空对话历史"""
    global conversation_history
    conversation_history = []
    return "对话历史已清空"


def get_history_count() -> int:
    """获取当前对话历史条数"""
    return len(conversation_history)


def get_history() -> List[Dict[str, str]]:
    """获取完整的对话历史"""
    return conversation_history.copy()


def undo_last_message() -> str:
    """撤销最后一条对话"""
    global conversation_history
    if len(conversation_history) >= 2:
        conversation_history = conversation_history[:-2]
        return "已撤销上一条消息"
    elif len(conversation_history) == 1:
        conversation_history = []
        return "已撤销上一条消息"
    else:
        return "没有可撤销的消息"


def build_messages_for_agent(user_message: str) -> List[Dict[str, str]]:
    """构建包含历史的消息列表，供 Agent 使用"""
    messages = conversation_history.copy()
    messages.append({"role": "user", "content": user_message})
    return messages


__all__ = [
    "add_to_history",
    "clear_history",
    "get_history_count",
    "get_history",
    "undo_last_message",
    "build_messages_for_agent"
]
