"""
Qwen Agent 模块
负责初始化和管理 Qwen Agent
"""

import os
from typing import List, Dict, Any, Optional

# 全局变量
llm = None
agent = None
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")


def set_api_key(api_key: str):
    """设置 DashScope API Key"""
    global DASHSCOPE_API_KEY
    DASHSCOPE_API_KEY = api_key


def init_qwen_agent():
    """初始化 Qwen Agent"""
    global llm, agent

    if not DASHSCOPE_API_KEY:
        print("警告: DASHSCOPE_API_KEY 未设置，聊天功能将不可用")
        return

    try:
        from qwen_agent.tools.base import BaseTool
        from qwen_agent.agents import ReActChat

        # 延迟导入，避免启动时依赖问题
        from src.tools.search_tool import ProductSearchTool

        # 初始化 LLM 配置
        llm = {
            "model": "qwen-max",
            "api_key": DASHSCOPE_API_KEY
        }

        # 初始化 Agent
        agent = ReActChat(
            llm=llm,
            function_list=[ProductSearchTool()],
            system_message="你是一个商品客服助手，可以帮助用户搜索和推荐商品。"
        )

        print("Qwen Agent 初始化成功")
    except ImportError as e:
        print(f"警告: qwen_agent 模块未安装，聊天功能将不可用: {e}")
    except Exception as e:
        print(f"警告: Qwen Agent 初始化失败: {e}")


def get_agent():
    """获取 Agent 实例"""
    return agent


def run_agent(messages: List[Dict[str, str]]) -> Any:
    """运行 Agent 并返回响应"""
    global agent
    if agent is None:
        return None

    try:
        responses = []
        for response in agent.run(messages):
            responses.append(response)
        return responses
    except Exception as e:
        print(f"Agent 运行出错: {e}")
        return None


__all__ = [
    "set_api_key",
    "init_qwen_agent",
    "get_agent",
    "run_agent"
]
