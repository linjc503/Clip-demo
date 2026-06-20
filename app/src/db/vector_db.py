"""
向量数据库模块
负责与 ChromaDB 的交互
"""

import chromadb
from typing import List, Dict, Any, Optional
import uuid

# 全局变量
client = None
collection = None


def init_vector_db(path: str = "./vector_db"):
    """初始化向量数据库连接"""
    global client, collection
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(
        name="products",
        metadata={"hnsw:space": "cosine"}
    )
    print("向量数据库初始化成功")


def generate_product_id() -> str:
    """生成唯一的商品ID"""
    return str(uuid.uuid4())[:8]


def add_product_to_db(
    product_id: str,
    vector: List[float],
    metadata: Dict[str, Any],
    vector_type: str = "text"
) -> bool:
    """添加商品到向量数据库"""
    try:
        collection.add(
            ids=[f"{product_id}_{vector_type}"],
            embeddings=[vector],
            metadatas=[metadata]
        )
        return True
    except Exception as e:
        print(f"添加商品失败: {e}")
        return False


def search_products_by_vector(
    query_vector: List[float],
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """通过向量搜索商品"""
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        where={"type": "product"}
    )

    search_results = []
    if results and results['ids']:
        for id_, distance, metadata in zip(
            results['ids'][0],
            results['distances'][0],
            results['metadatas'][0]
        ):
            search_results.append({
                "id": id_,
                "similarity": 1 - distance,
                "metadata": metadata
            })
    return search_results


def get_collection_stats() -> Dict[str, Any]:
    """获取集合统计信息"""
    return collection.count()


__all__ = [
    "init_vector_db",
    "generate_product_id",
    "add_product_to_db",
    "search_products_by_vector",
    "get_collection_stats"
]
