from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import clip
import chromadb
import torch
from PIL import Image
import io
import uuid
import requests
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

# 初始化FastAPI应用
app = FastAPI(title="多模态商品智能系统")

# 初始化CLIP模型
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# 连接ChromaDB
client = chromadb.PersistentClient(path="./vector_db")
collection = client.get_or_create_collection(
    name="products",
    metadata={"hnsw:space": "cosine"}
)

# Qwen Agent配置
DASHSCOPE_API_KEY = "your-dashscope-api-key-here"  # 请替换为您的阿里云DashScope API Key

# 零样本分类的类别
CATEGORIES = ["Topwear", "Bottomwear", "Accessories", "Footwear", "PersonalCare"]

# 生成新的商品ID
def generate_product_id() -> str:
    """生成唯一的商品ID"""
    # 这个uuid是给用户添加进来的商品用的，完全随机，取八位
    return str(uuid.uuid4())[:8]

# 文本编码函数
def encode_text(text: str) -> List[float]:
    """将文本编码为向量"""
    with torch.no_grad():
        text_features = model.encode_text(clip.tokenize([text]).to(device))
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return text_features[0].cpu().numpy().tolist()

# 图片编码函数
def encode_image(image: Image.Image) -> List[float]:
    """将图片编码为向量"""
    image = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features[0].cpu().numpy().tolist()




# search_products工具函数（增强版）
def search_products(query: str) -> str:
    """搜索商品的Tool，构建丰富的上下文给LLM使用"""

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




# 初始化Qwen Agent
llm = None
agent = None

# 对话历史存储（短期记忆）
MAX_HISTORY_LENGTH = 20  # 最大保存20轮对话
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

def clear_history():
    """清空对话历史"""
    global conversation_history
    conversation_history = []
    return "对话历史已清空"

def get_history_count():
    """获取当前对话历史条数"""
    return len(conversation_history)

def init_qwen_agent():
    """初始化Qwen Agent"""
    global llm, agent
    
    if not DASHSCOPE_API_KEY:
        print("警告: DASHSCOPE_API_KEY未设置，聊天功能将不可用")
        return
    
    try:
        from qwen_agent.tools.base import BaseTool
        from qwen_agent.agents import ReActChat 
        
        # 定义商品搜索工具（不需要 @register_tool 装饰器）
        class ProductSearchTool(BaseTool):
            name = "search_products"
            description = "搜索商品信息，当需要查找商品时使用此工具"
            
            def call(self, query: str, **kwargs) -> str:   # 注意加上 **kwargs
                return search_products(query)
        
        # 初始化LLM配置
        llm = {
            "model": "qwen-max",
            "api_key": DASHSCOPE_API_KEY
        }
        
        # 关键：直接传入工具实例，而不是字符串
        agent = ReActChat(
            llm=llm,
            function_list=[ProductSearchTool()],   # 传实例，不是字符串
            system_message="你是一个商品客服助手，可以帮助用户搜索和推荐商品。"
        )
        
        print("Qwen Agent初始化成功")
    except ImportError as e:
        print(f"警告: qwen_agent模块未安装，聊天功能将不可用: {e}")
    except Exception as e:
        print(f"警告: Qwen Agent初始化失败: {e}")

# 启动时初始化Agent
init_qwen_agent()




# 根路由 - 前端页面
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """返回前端页面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>多模态商品智能系统</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; }
            .container { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            input[type="text"], input[type="file"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
            button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            .result { margin-top: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 4px; max-height: 200px; overflow-y: auto; }
            
            /* 聊天区域样式 */
            .chat-container { 
                grid-column: 1 / -1; 
                background: white; 
                border-radius: 12px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                padding: 20px;
                margin-top: 20px;
            }
            .chat-header { font-size: 1.5rem; font-weight: bold; margin-bottom: 15px; color: #333; }
            .chat-messages { 
                height: 400px; 
                overflow-y: auto; 
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                padding: 15px;
                margin-bottom: 15px;
                background-color: #f9f9f9;
            }
            .chat-message { margin-bottom: 15px; display: flex; }
            .chat-message.user { justify-content: flex-end; }
            .chat-message.ai { justify-content: flex-start; }
            .message-bubble { 
                max-width: 70%; 
                padding: 12px 16px; 
                border-radius: 12px; 
                line-height: 1.5;
            }
            .chat-message.user .message-bubble { 
                background-color: #4CAF50; 
                color: white; 
                border-bottom-right-radius: 4px;
            }
            .chat-message.ai .message-bubble { 
                background-color: white; 
                color: #333; 
                border: 1px solid #ddd;
                border-bottom-left-radius: 4px;
            }
            .chat-input-area { display: flex; gap: 10px; }
            .chat-input-area input { flex: 1; margin: 0; }
            .chat-input-area button { background-color: #2196F3; }
            .chat-input-area button:hover { background-color: #1976D2; }
        </style>
    </head>
    <body>
        <h1 class="text-3xl font-bold mb-6">多模态商品智能系统</h1>
        
        <div class="container">
            <!-- 文本录入区域 -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">添加商品（文本）</h2>
                <div style="display: grid; gap: 10px;">
                    <input type="text" id="productName" placeholder="商品名称 *" required>
                    <input type="number" id="productPrice" placeholder="价格（元）" step="0.01" min="0">
                    <input type="text" id="productCategory" placeholder="分类（如：上衣、裤子、鞋子）">
                    <input type="text" id="productColor" placeholder="颜色（如：红色、蓝色）">
                    <input type="text" id="productMaterial" placeholder="面料材质（如：纯棉、涤纶）">
                    <input type="text" id="productTags" placeholder="标签（用逗号分隔，如：休闲,时尚）">
                    <textarea id="productDesc" placeholder="商品详细描述" rows="3" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"></textarea>
                    <button onclick="addText()" style="background-color: #4CAF50;">添加商品</button>
                </div>
                <div id="textResult" class="result"></div>
            </div>

            <!-- 图片录入区域 -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">添加商品（图片）</h2>
                <div style="display: grid; gap: 10px;">
                    <input type="file" id="imageInput" accept="image/*" style="width: 100%;">
                    <input type="text" id="productNameImg" placeholder="商品名称 *">
                    <input type="number" id="productPriceImg" placeholder="价格（元）" step="0.01" min="0">
                    <input type="text" id="productCategoryImg" placeholder="分类">
                    <input type="text" id="productColorImg" placeholder="颜色">
                    <input type="text" id="productMaterialImg" placeholder="面料材质">
                    <input type="text" id="productTagsImg" placeholder="标签（用逗号分隔）">
                    <textarea id="imageDesc" placeholder="商品详细描述" rows="3" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"></textarea>
                    <button onclick="addImage()" style="background-color: #2196F3;">添加商品图片</button>
                </div>
                <div id="imageResult" class="result"></div>
            </div>
            
            <!-- 零样本分类区域 -->
            <div class="card">
                <h2 class="text-xl font-semibold mb-4">零样本分类</h2>
                <input type="file" id="classifyInput" accept="image/*">
                <button onclick="classifyImage()">分类图片</button>
                <div id="classifyResult" class="result"></div>
            </div>
            
            <!-- 聊天区域 -->
            <div class="chat-container">
                <div class="chat-header" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>商品客服助手</span>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span id="historyCount" style="font-size: 0.875rem; color: #666;">对话: 0 条</span>
                        <button onclick="clearChatHistory()" style="background-color: #f44336; font-size: 0.75rem; padding: 5px 10px;">清空历史</button>
                    </div>
                </div>
                <div class="chat-messages" id="chatMessages"></div>
                <div class="chat-input-area">
                    <input type="text" id="chatInput" placeholder="请输入您的问题..." onkeypress="handleChatKeyPress(event)">
                    <button onclick="sendMessage()">发送</button>
                </div>
            </div>
        </div>
        
        <script>
            // 添加文本
            async function addText() {
                const name = document.getElementById('productName').value.trim();
                if (!name) { alert('请输入商品名称'); return; }

                const formData = new FormData();
                formData.append('name', name);
                formData.append('price', document.getElementById('productPrice').value || 0);
                formData.append('category', document.getElementById('productCategory').value);
                formData.append('color', document.getElementById('productColor').value);
                formData.append('material', document.getElementById('productMaterial').value);
                formData.append('tags', document.getElementById('productTags').value);
                formData.append('description', document.getElementById('productDesc').value);

                const response = await fetch('/add_text', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (result.product_id) {
                    document.getElementById('textResult').innerHTML =
                        `<div style="color: #4CAF50; font-weight: bold;">✓ 商品添加成功！<br>商品ID: ${result.product_id}<br>名称: ${result.name}</div>`;
                    // 清空表单
                    document.querySelectorAll('#addTextForm input, #addTextForm textarea').forEach(el => el.value = '');
                } else {
                    document.getElementById('textResult').innerText = JSON.stringify(result, null, 2);
                }
            }

            // 添加图片商品
            async function addImage() {
                const fileInput = document.getElementById('imageInput');
                if (!fileInput.files[0]) { alert('请选择图片'); return; }

                const name = document.getElementById('productNameImg').value.trim();
                if (!name) { alert('请输入商品名称'); return; }

                const formData = new FormData();
                formData.append('image', fileInput.files[0]);
                formData.append('name', name);
                formData.append('price', document.getElementById('productPriceImg').value || 0);
                formData.append('category', document.getElementById('productCategoryImg').value);
                formData.append('color', document.getElementById('productColorImg').value);
                formData.append('material', document.getElementById('productMaterialImg').value);
                formData.append('tags', document.getElementById('productTagsImg').value);
                formData.append('description', document.getElementById('imageDesc').value);

                const response = await fetch('/add_image', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (result.product_id) {
                    document.getElementById('imageResult').innerHTML =
                        `<div style="color: #2196F3; font-weight: bold;">✓ 商品图片添加成功！<br>商品ID: ${result.product_id}<br>名称: ${result.name}</div>`;
                } else {
                    document.getElementById('imageResult').innerText = JSON.stringify(result, null, 2);
                }
            }
            
            // 分类图片
            async function classifyImage() {
                const fileInput = document.getElementById('classifyInput');
                
                if (!fileInput.files[0]) { alert('请选择图片'); return; }
                
                const formData = new FormData();
                formData.append('image', fileInput.files[0]);
                
                const response = await fetch('/classify_image', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                document.getElementById('classifyResult').innerText = JSON.stringify(result, null, 2);
            }
            
            // 添加消息到聊天区域
            function addMessage(message, isUser) {
                const messagesContainer = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message ' + (isUser ? 'user' : 'ai');
                messageDiv.innerHTML = '<div class="message-bubble">' + message.replace(/\\n/g, '<br>') + '</div>';
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                return messageDiv;
            }
            
            // 更新现有消息
            function updateMessage(messageDiv, message) {
                const bubble = messageDiv.querySelector('.message-bubble');
                if (bubble) {
                    bubble.innerHTML = message.replace(/\\n/g, '<br>');
                }
                const messagesContainer = document.getElementById('chatMessages');
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            // 发送消息（流式输出）
            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                
                addMessage(message, true);
                input.value = '';
                
                // 先添加一个空的 AI 消息占位符
                const aiMessageDiv = addMessage('', false);
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });

                    // 检查响应类型
                    const contentType = response.headers.get('content-type');
                    
                    if (contentType && contentType.includes('text/event-stream')) {
                        // 流式响应
                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        let buffer = '';
                        let fullText = '';
                        
                        while (true) {
                            const { done, value } = await reader.read();
                            
                            if (done) break;
                            
                            buffer += decoder.decode(value, { stream: true });
                            
                            // 解析 SSE 数据
                            const lines = buffer.split('\\n\\n');
                            buffer = lines.pop(); // 保留不完整的部分
                            
                            for (const line of lines) {
                                if (line.startsWith('data: ')) {
                                    try {
                                        const data = JSON.parse(line.substring(6));
                                        
                                        if (data.error) {
                                            updateMessage(aiMessageDiv, data.error);
                                            return;
                                        }
                                        
                                        if (data.delta) {
                                            fullText += data.delta;
                                            updateMessage(aiMessageDiv, fullText);
                                        }
                                        
                                        if (data.done) {
                                            if (data.full) {
                                                updateMessage(aiMessageDiv, data.full);
                                            }
                                            // 更新对话计数
                                            updateHistoryCount();
                                            return;
                                        }
                                    } catch (e) {
                                        console.error('解析数据失败:', e);
                                    }
                                }
                            }
                        }
                    } else {
                        // 非流式响应（降级处理）
                        const result = await response.json();
                        
                        let replyText = '处理失败';
                        if (result && typeof result === 'object') {
                            replyText = result.reply || result.error || result.message || result.text || JSON.stringify(result);
                        } else if (typeof result === 'string') {
                            replyText = result;
                        }
                        
                        if (typeof replyText === 'object') {
                            replyText = JSON.stringify(replyText, null, 2);
                        }
                        
                        updateMessage(aiMessageDiv, replyText);
                        // 更新对话计数
                        updateHistoryCount();
                    }
                } catch (error) {
                    updateMessage(aiMessageDiv, '发送失败: ' + error.message);
                }
            }
            
            // 处理回车键
            function handleChatKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            // 清空对话历史
            async function clearChatHistory() {
                if (!confirm('确定要清空所有对话历史吗？')) return;

                try {
                    const response = await fetch('/chat/clear', {
                        method: 'POST'
                    });

                    const result = await response.json();

                    // 清空前端显示的聊天记录
                    const messagesContainer = document.getElementById('chatMessages');
                    messagesContainer.innerHTML = '';

                    // 更新对话计数
                    updateHistoryCount();

                    alert(result.message);
                } catch (error) {
                    alert('清空历史失败: ' + error.message);
                }
            }

            // 更新对话历史计数
            async function updateHistoryCount() {
                try {
                    const response = await fetch('/chat/history');
                    const result = await response.json();

                    const historyCount = document.getElementById('historyCount');
                    if (historyCount) {
                        historyCount.textContent = `对话: ${result.count} 条`;
                    }
                } catch (error) {
                    console.error('获取历史计数失败:', error);
                }
            }

            // 页面加载完成后滚动到最新消息并获取历史计数
            window.onload = function() {
                const messagesContainer = document.getElementById('chatMessages');
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                updateHistoryCount();
            };
        </script>
    </body>
    </html>
    """
    return html_content


# 添加文本接口 X
@app.post("/add_text")
async def add_text(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(0.0),
    category: str = Form(""),
    material: str = Form(""),
    color: str = Form(""),
    tags: str = Form("")
) -> Dict[str, Any]:
    """添加商品到向量数据库（增强版）"""
    product_id = generate_product_id()

    # 构建完整的商品描述文本，用于向量检索
    full_description = f"{name} {description} {category} {material} {color} {tags}".strip()

    # 准备元数据
    metadata = {
        "type": "product",
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags,
        "stock": 100  # 默认库存
    }

    # 添加到向量数据库
    text_vector = encode_text(full_description)
    collection.add(
        ids=[f"{product_id}_text"],
        embeddings=[text_vector],
        metadatas=[metadata]
    )

    return {
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags
    }

# 添加图片接口 X
@app.post("/add_image")
async def add_image(
    image: UploadFile = File(...),
    name: str = Form(""),
    description: str = Form(""),
    price: float = Form(0.0),
    category: str = Form(""),
    material: str = Form(""),
    color: str = Form(""),
    tags: str = Form("")
) -> Dict[str, Any]:
    """添加图片商品到向量数据库（增强版）"""
    product_id = generate_product_id()

    # 读取图片并编码
    image_data = await image.read()
    img = Image.open(io.BytesIO(image_data))
    image_vector = encode_image(img)

    # 构建完整的商品描述文本
    full_description = f"{name} {description} {category} {material} {color} {tags}".strip()

    # 准备元数据
    metadata = {
        "type": "product",
        "product_id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "material": material,
        "color": color,
        "tags": tags,
        "has_image": True,
        "stock": 100
    }

    # 添加图片向量
    collection.add(
        ids=[f"{product_id}_image"],
        embeddings=[image_vector],
        metadatas=[metadata]
    )

    # 添加文本向量（用于文本搜索）
    if full_description:
        text_vector = encode_text(full_description)
        collection.add(
            ids=[f"{product_id}_text"],
            embeddings=[text_vector],
            metadatas=[metadata]
        )

    return {
         "product_id": product_id,
         "name": name,
         "description": description,
         "price": price,
         "category": category,
         "material": material,
         "color": color,
         "tags": tags
     }

# 文本搜索接口
@app.post("/search_text")
async def search_text(text: str) -> Dict[str, Any]:
    """搜索相似商品"""
    text_vector = encode_text(text)

    # 只搜索商品类型
    results = collection.query(
        query_embeddings=[text_vector],
        n_results=5,
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

    return {"query": text, "results": search_results}

# 图片搜索接口 X
@app.post("/search_image")
async def search_image(image: UploadFile = File(...)) -> Dict[str, Any]:
    """搜索相似图片"""
    image_data = await image.read()
    img = Image.open(io.BytesIO(image_data))
    
    image_vector = encode_image(img)
    
    results = collection.query(
        query_embeddings=[image_vector],
        n_results=5,
        where={"type": {"$in": ["text", "image"]}}
    )
    
    search_results = []
    for i, (id_, distance, metadata) in enumerate(zip(
        results['ids'][0],
        results['distances'][0],
        results['metadatas'][0]
    )):
        search_results.append({
            "id": id_,
            "similarity": 1 - distance,
            "metadata": metadata
        })
    
    return {"results": search_results}

# 零样本分类接口
@app.post("/classify_image")
async def classify_image(image: UploadFile = File(...)) -> Dict[str, Any]:
    """零样本分类图片"""
    image_data = await image.read()
    img = Image.open(io.BytesIO(image_data))
    
    image_vector = encode_image(img)
    
    category_vectors = []
    for category in CATEGORIES:
        category_vector = encode_text(category)
        category_vectors.append(category_vector)
    
    import numpy as np
    image_vector_np = np.array(image_vector)
    similarities = []
    
    for category, vec in zip(CATEGORIES, category_vectors):
        vec_np = np.array(vec)
        similarity = np.dot(image_vector_np, vec_np)
        similarities.append((category, similarity))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_category, top_confidence = similarities[0]
    
    return {
        "category": top_category,
        "confidence": float(top_confidence),
        "all_categories": [
            {"category": cat, "confidence": float(conf)} 
            for cat, conf in similarities
        ]
    }

# 流式聊天生成器
async def chat_stream_generator(message: str) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    global agent, conversation_history
    
    if not message:
        yield f"data: {json.dumps({'error': '消息不能为空'}, ensure_ascii=False)}\n\n"
        return
    
    if not agent:
        yield f"data: {json.dumps({'error': '抱歉，Qwen Agent未初始化。请检查DASHSCOPE_API_KEY是否正确设置。'}, ensure_ascii=False)}\n\n"
        return
    
    try:
        full_reply = ""
        
        # 构建包含历史的消息列表
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": message})
        
        # 遍历生成器获取响应，传入完整的对话历史
        for response in agent.run(messages):
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

# 聊天接口（流式输出）
@app.post("/chat")
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

# 获取对话历史
@app.get("/chat/history")
async def get_chat_history():
    """获取当前对话历史"""
    return {
        "count": get_history_count(),
        "max_length": MAX_HISTORY_LENGTH,
        "history": conversation_history
    }

# 清空对话历史
@app.post("/chat/clear")
async def clear_chat_history():
    """清空对话历史"""
    message = clear_history()
    return {"message": message}

# 删除最后一条对话
@app.post("/chat/undo")
async def undo_last_message():
    """删除最后一条对话记录（撤销）"""
    global conversation_history
    if len(conversation_history) >= 2:
        conversation_history = conversation_history[:-2]  # 删除用户和助手的最后一条消息
        return {"message": "已撤销上一条消息"}
    elif len(conversation_history) == 1:
        conversation_history = []
        return {"message": "已撤销上一条消息"}
    else:
        return {"message": "没有可撤销的消息"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)