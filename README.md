<div align="center">

# 🛍️ ClipCommerce

### 多模态商品智能系统

基于 CLIP + ChromaDB + Qwen-Agent 的商品智能检索与客服系统

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/CLIP-ViT--B%2F32-purple?style=flat-square" alt="CLIP">
  <img src="https://img.shields.io/badge/ChromaDB-latest-orange?style=flat-square" alt="ChromaDB">
</p>

</div>

## ✨ 功能特性

- 🎨 **产品级前端页面**：深色科技风落地页设计，玻璃态效果，流畅交互动效
- 🧠 **多模态编码**：使用 CLIP 模型将图片和文本编码到统一向量空间
- 💾 **向量数据库**：使用 ChromaDB 持久化存储商品向量，支持高效相似度检索
- 🔍 **智能检索**：支持文本搜索和图片搜索两种方式查找相似商品
- 📊 **零样本分类**：无需训练，直接将商品图片分类到预设类别
- 🤖 **智能客服**：基于 Qwen 大模型的对话式商品问答助手，支持流式输出
- 📚 **RAG 检索增强**：聊天时自动检索商品库，提供准确的商品推荐

## 🖼️ 页面展示

产品落地页风格设计，包含四大核心区域：

- **Hero 区**：大标题 + 数据统计卡片，直观展示产品价值
- **功能展示**：三栏特性卡片，清晰呈现核心能力
- **在线演示**：Tab 切换的商品入库 / 零样本分类，即开即用
- **AI 客服**：独立聊天界面，7x24 小时智能服务

设计亮点：深色科技风主题 · 玻璃态卡片效果 · 翡翠绿强调色 · 流畅交互动效 · 响应式布局

## 🛠️ 技术栈

| 类别 | 技术 |
|---|---|
| 多模态模型 | CLIP (ViT-B/32) |
| 向量数据库 | ChromaDB |
| Web 框架 | FastAPI |
| 大模型 Agent | Qwen-Agent（通义千问） |
| 前端 | HTML5 + TailwindCSS + 原生 JavaScript |
| 设计风格 | 深色科技风 · 玻璃态 · 落地页布局 |
| 语言 | Python 3.10+ |

## 📁 项目结构

```
clip/
├── app/                          # 主应用目录（模块化版本）
│   ├── main.py                   # 主入口文件（推荐使用）
│   ├── app.py                    # 单文件版本（备用）
│   └── src/
│       ├── models/               # 模型层
│       │   └── clip_model.py     # CLIP 模型封装
│       ├── db/                   # 数据层
│       │   └── vector_db.py      # 向量数据库操作
│       ├── chat/                 # 聊天模块
│       │   ├── qwen_agent.py     # Qwen Agent 封装
│       │   └── conversation_history.py
│       ├── rag/                  # RAG 检索增强
│       │   └── context_builder.py
│       ├── routes/               # API 路由
│       │   ├── product_routes.py # 商品相关接口
│       │   ├── classify_routes.py # 分类相关接口
│       │   └── chat_routes.py    # 聊天相关接口
│       ├── frontend/             # 前端页面
│       │   ├── page_template.py  # 页面模板模块
│       │   └── index.html        # 前端页面代码
│       └── tools/                # 工具模块
│           └── search_tool.py
├── 入库/                          # 向量数据库构建脚本
│   ├── build_vector_db.py
│   └── vector_db/
├── image/                         # 测试图片（已忽略）
├── vector_db/                     # 向量数据库文件（已忽略）
├── .gitignore
├── README.md
├── 接口文档.md
├── chromadb存储结构.md
├── 考核三.pdf                      # 考核文档（已忽略）
└── 说明.md                         # 说明文档（已忽略）
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装基础依赖
pip install clip chromadb fastapi uvicorn torch torchvision pillow requests

# 安装聊天功能依赖（可选）
pip install qwen-agent
```

### 2. 配置 API Key

编辑 `app/main.py`，填写通义千问 API Key：

```python
DASHSCOPE_API_KEY = "your-api-key-here"  # 第 20 行
```

> 如果没有 API Key，聊天功能将不可用，但其他功能（商品录入、搜索、分类）正常使用。

### 3. 启动服务

**推荐使用模块化版本：**

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**或使用单文件版本：**

```bash
cd app
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问

- 🌐 **前端页面**：http://localhost:8000
- 📖 **API 文档**：http://localhost:8000/docs

## 📦 功能模块

### 1. 商品录入（文本）
输入商品名称、价格、分类、颜色、材质等信息，自动编码存入向量数据库。

### 2. 商品录入（图片）
上传商品图片，可附带文字描述，同时存储图片向量和文本向量。

### 3. 零样本分类
上传商品图片，自动识别所属类别：
- Topwear（上装）
- Bottomwear（下装）
- Accessories（配饰）
- Footwear（鞋类）
- PersonalCare（个护）

### 4. 相似性搜索
- **文本搜索**：输入文字描述，查找最相似的商品
- **图片搜索**：上传图片，查找视觉相似的商品

### 5. 智能客服
基于 Qwen 大模型的对话助手，可：
- 回答商品相关问题
- 自动检索商品库进行推荐
- 支持流式输出，打字机效果
- 维护多轮对话历史

## 🔧 构建向量数据库

如需批量导入商品数据，使用入库脚本：

```bash
cd 入库
python build_vector_db.py
```

## 📝 相关文档

- [接口文档.md](接口文档.md) - API 接口详细说明
- [chromadb存储结构.md](chromadb存储结构.md) - ChromaDB 存储结构解析
- [app/PROJECT_STRUCTURE.md](app/PROJECT_STRUCTURE.md) - 模块化版本项目结构说明

## 📄 License

MIT License
