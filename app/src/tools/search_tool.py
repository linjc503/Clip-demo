"""
搜索工具模块
提供商品搜索功能供 Agent 使用
"""

import requests
from typing import List, Dict


class ProductSearchTool:
    """商品搜索工具"""
    name = "search_products"
    description = "搜索商品信息，当需要查找商品时使用此工具"

    def call(self, query: str, **kwargs) -> str:
        """调用搜索工具"""
        return search_products(query)


def search_products(query: str) -> str:
    """搜索商品"""
    try:
        response = requests.post(
            "http://localhost:8000/search_text",
            json={"text": query},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            # 构建丰富的上下文
            return build_product_context(results)
        else:
            return f"搜索失败，请稍后重试。错误代码：{response.status_code}"

    except requests.exceptions.ConnectionError:
        return "无法连接到搜索服务，请确保服务器正在运行。"
    except requests.exceptions.Timeout:
        return "搜索超时，请稍后重试。"
    except Exception as e:
        return f"搜索出错：{str(e)}"


def build_product_context(results: List[Dict]) -> str:
    """构建商品上下文"""
    if not results:
        return "未找到相关商品"

    context_parts = []
    context_parts.append(f"根据您的需求，我为您找到了 {len(results)} 件相关商品：\n")
    context_parts.append("=" * 60)

    for i, item in enumerate(results, 1):
        metadata = item.get("metadata", {})
        similarity = item.get("similarity", 0)

        product_id = metadata.get("product_id", "unknown")
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        price = metadata.get("price", 0)
        category = metadata.get("category", "")
        material = metadata.get("material", "")
        color = metadata.get("color", "")
        tags = metadata.get("tags", "")
        stock = metadata.get("stock", 0)

        card = []
        card.append(f"\n【商品 {i}】")

        if name:
            card.append(f"  📦 名称：{name}")

        if price and price > 0:
            card.append(f"  💰 价格：¥{price:.2f}")

        if category:
            card.append(f"  🏷️ 分类：{category}")

        if color:
            card.append(f"  🎨 颜色：{color}")

        if material:
            card.append(f"  ✨ 面料：{material}")

        if stock is not None:
            stock_text = "有货" if stock > 0 else "缺货"
            card.append(f"  📊 库存：{stock}件 ({stock_text})")

        if description:
            card.append(f"  📝 描述：{description}")

        if tags:
            card.append(f"  🏷️ 标签：{tags}")

        card.append(f"  🎯 匹配度：{similarity:.0%}")
        card.append(f"  🆔 商品ID：{product_id}")

        context_parts.append("\n".join(card))

    context_parts.append("\n" + "=" * 60)
    context_parts.append(f"\n💡 提示：以上商品信息来自向量数据库检索，相似度越高匹配越准确。")

    return "\n".join(context_parts)


__all__ = ["ProductSearchTool", "search_products"]
