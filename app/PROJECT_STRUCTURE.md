# 项目目录结构说明

## 新的文件结构

```
选做/
├── main.py                 # 主入口文件
├── app.py                  # 原始文件（保留备份）
├── vector_db/              # 向量数据库存储目录
├── src/                    # 源代码目录
│   ├── __init__.py         # 包初始化
│   ├── models/             # 模型模块
│   │   ├── __init__.py
│   │   └── clip_model.py   # CLIP 模型封装
│   ├── db/                 # 数据库模块
│   │   ├── __init__.py
│   │   └── vector_db.py    # ChromaDB 操作封装
│   ├── rag/                # RAG 模块
│   │   ├── __init__.py
│   │   └── context_builder.py  # 上下文构建
│   ├── chat/               # 聊天模块
│   │   ├── __init__.py
│   │   ├── conversation_history.py  # 对话历史管理
│   │   └── qwen_agent.py   # Qwen Agent 封装
│   ├── tools/              # 工具模块
│   │   ├── __init__.py
│   │   └── search_tool.py  # 商品搜索工具
│   ├── frontend/           # 前端模块
│   │   ├── __init__.py
│   │   └── page_template.py  # HTML 页面模板
│   └── routes/             # 路由模块
│       ├── __init__.py
│       ├── product_routes.py    # 商品相关接口
│       ├── classify_routes.py   # 分类相关接口
│       └── chat_routes.py       # 聊天相关接口
└── README.md               # 项目说明文档
```

## 模块职责说明

### 1. models/clip_model.py
- 负责 CLIP 模型的初始化和推理
- 提供文本和图片的向量编码功能

### 2. db/vector_db.py
- 负责与 ChromaDB 的交互
- 提供商品的增删查改操作

### 3. rag/context_builder.py
- 负责构建丰富的商品上下文信息
- 格式化商品信息供 LLM 使用

### 4. chat/conversation_history.py
- 管理对话历史（短期记忆）
- 提供历史记录的增删查操作

### 5. chat/qwen_agent.py
- 封装 Qwen Agent 的初始化和调用
- 处理 Agent 的配置和运行

### 6. tools/search_tool.py
- 提供商品搜索工具
- 供 Agent 调用进行商品检索

### 7. frontend/page_template.py
- 提供前端 HTML 页面内容
- 包含所有前端 JavaScript 代码

### 8. routes/*.py
- 定义 FastAPI 路由
- 处理 HTTP 请求和响应

## 启动方式

```bash
# 进入项目目录
cd c:\Users\12991\Desktop\Aplus\三\选做

# 运行主入口文件
python main.py
```

## 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| / | GET | 返回前端页面 |
| /add_text | POST | 添加文本商品 |
| /add_image | POST | 添加图片商品 |
| /search_text | POST | 文本搜索商品 |
| /search_image | POST | 图片搜索商品 |
| /classify_image | POST | 零样本分类 |
| /chat | POST | 聊天接口（流式） |
| /chat/history | GET | 获取对话历史 |
| /chat/clear | POST | 清空对话历史 |
| /chat/undo | POST | 撤销上一条消息 |

## 注意事项

1. **API Key**：需要在 `main.py` 中配置 DASHSCOPE_API_KEY
2. **依赖安装**：需要安装 clip、chromadb、qwen_agent 等依赖
3. **首次运行**：CLIP 模型需要下载，可能需要较长时间
4. **向量数据库**：数据存储在 `./vector_db` 目录下

## 迁移说明

- 原 `app.py` 文件已保留作为备份
- 新的入口文件是 `main.py`
- 所有功能保持不变，只是代码结构更清晰
