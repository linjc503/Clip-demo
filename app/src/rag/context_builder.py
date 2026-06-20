"""
RAG 上下文构建模块
负责构建丰富的商品上下文信息
"""

from typing import List, Dict


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

        # 提取商品信息
        product_id = metadata.get("product_id", "unknown")
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        price = metadata.get("price", 0)
        category = metadata.get("category", "")
        material = metadata.get("material", "")
        color = metadata.get("color", "")
        tags = metadata.get("tags", "")
        stock = metadata.get("stock", 0)

        # 构建商品卡片
        card = []
        card.append(f"\n【商品 {i}】")

        # 商品名称
        if name:
            card.append(f"  📦 名称：{name}")

        # 价格（如果有）
        if price and price > 0:
            card.append(f"  💰 价格：¥{price:.2f}")

        # 分类
        if category:
            card.append(f"  🏷️ 分类：{category}")

        # 颜色
        if color:
            card.append(f"  🎨 颜色：{color}")

        # 面料材质
        if material:
            card.append(f"  ✨ 面料：{material}")

        # 库存
        if stock is not None:
            stock_text = "有货" if stock > 0 else "缺货"
            card.append(f"  📊 库存：{stock}件 ({stock_text})")

        # 商品描述
        if description:
            card.append(f"  📝 描述：{description}")

        # 标签
        if tags:
            card.append(f"  🏷️ 标签：{tags}")

        # 相似度
        card.append(f"  🎯 匹配度：{similarity:.0%}")

        # 商品ID
        card.append(f"  🆔 商品ID：{product_id}")

        context_parts.append("\n".join(card))

    context_parts.append("\n" + "=" * 60)
    context_parts.append(f"\n💡 提示：以上商品信息来自向量数据库检索，相似度越高匹配越准确。")

    return "\n".join(context_parts)


def format_product_info(product: Dict) -> str:
    """格式化单个商品信息"""
    metadata = product.get("metadata", {})
    
    info_lines = []
    info_lines.append(f"商品名称：{metadata.get('name', '未知')}")
    
    price = metadata.get("price", 0)
    if price > 0:
        info_lines.append(f"价格：¥{price:.2f}")
    
    if metadata.get("category"):
        info_lines.append(f"分类：{metadata.get('category')}")
    
    if metadata.get("color"):
        info_lines.append(f"颜色：{metadata.get('color')}")
    
    return "\n".join(info_lines)


__all__ = ["build_product_context", "format_product_info"]
