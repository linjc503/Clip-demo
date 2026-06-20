"""
前端页面模板模块
提供HTML页面内容
"""
import os


def get_html_content() -> str:
    """获取前端页面HTML内容"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


__all__ = ["get_html_content"]
