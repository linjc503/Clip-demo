# 对话记忆功能说明

## ✅ 已实现的功能

### 1. 短期记忆机制
- ✅ 自动保存对话历史（最多20轮对话）
- ✅ 每次对话自动加载历史上下文
- ✅ 无需新增向量数据库，使用内存存储

### 2. 新增 API 接口
- `GET /chat/history` - 查看当前对话历史
- `POST /chat/clear` - 清空所有对话历史
- `POST /chat/undo` - 撤销上一条消息

### 3. 前端界面优化
- ✅ 实时显示对话条数
- ✅ 一键清空历史按钮
- ✅ 确认提示防止误操作

## 🚀 使用方法

### 1. 启动服务器
```bash
cd c:\Users\12991\Desktop\Aplus\三\选做
python app.py
```

### 2. 测试对话记忆
**基础测试**：
1. 发送第一条消息："我叫小明"
2. 发送第二条消息："我叫什么名字？"
3. **预期结果**：AI 应该记得你叫小明

**多轮对话测试**：
1. 发送："我喜欢红色的衣服"
2. 发送："帮我找一件我喜欢的东西"
3. **预期结果**：AI 应该能够关联到你喜欢红色衣服的信息

### 3. 管理对话历史
**查看历史**：
- 在界面右上角可以看到对话条数

**清空历史**：
- 点击红色的"清空历史"按钮
- 确认后清空所有对话记录和界面显示

**撤销功能**：
- 可以通过 API 撤销最后一条消息
- 每次撤销删除一对（用户消息 + AI回复）

## 📊 技术实现

### 后端实现
```python
# 对话历史存储
MAX_HISTORY_LENGTH = 20  # 最大保存20轮对话
conversation_history: List[Dict[str, str]] = []

# 添加到历史
def add_to_history(role: str, content: str):
    global conversation_history
    conversation_history.append({"role": role, "content": content})
    # 自动裁剪超出长度
    if len(conversation_history) > MAX_HISTORY_LENGTH:
        conversation_history = conversation_history[-MAX_HISTORY_LENGTH:]
```

### 上下文传递
```python
# 构建包含历史的消息列表
messages = conversation_history.copy()
messages.append({"role": "user", "content": message})

# 传入 Agent
for response in agent.run(messages):
    # 处理响应...
```

## 🎯 功能特点

### 优点
1. **简单高效**：纯内存操作，速度快
2. **无需配置**：不需要额外的数据库或存储服务
3. **自动管理**：自动裁剪历史，防止内存溢出
4. **用户可控**：可以随时清空或撤销

### 限制
1. **会话级别**：服务器重启后历史丢失
2. **内存占用**：长时间会话可能占用较多内存
3. **Token 限制**：如果历史过长，可能超出模型输入限制

## 🔍 测试场景

### 场景1：基础记忆
```
用户：你好，我叫小明
AI：你好小明！很高兴认识你。

用户：我叫什么名字？
AI：您叫小明。
```

### 场景2：上下文理解
```
用户：我想要一件红色的上衣
AI：好的，我帮您搜索红色上衣...

用户：帮我找类似的
AI：根据您刚才说的红色上衣，我帮您找到了以下商品...
```

### 场景3：多轮对话
```
用户：推荐一些商品
AI：好的，我为您推荐...

用户：有没有更便宜的？
AI：当然，我帮您筛选价格更低的...

用户：把这些加入购物车
AI：好的，已为您添加...
```

## 📝 API 详细说明

### GET /chat/history
**响应示例**：
```json
{
  "count": 4,
  "max_length": 20,
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮您？"},
    {"role": "user", "content": "我叫小明"},
    {"role": "assistant", "content": "你好小明！"}
  ]
}
```

### POST /chat/clear
**响应示例**：
```json
{
  "message": "对话历史已清空"
}
```

### POST /chat/undo
**响应示例**：
```json
{
  "message": "已撤销上一条消息"
}
```

## ⚠️ 注意事项

1. **服务器重启**：历史记录存储在内存中，重启后会清空
2. **最大长度**：超过20轮对话会自动删除最早的记录
3. **Token 限制**：如果历史过长，可能需要调整 MAX_HISTORY_LENGTH
4. **敏感信息**：不要在对话中输入敏感信息

## 🎉 预期效果

正常情况下，你应该能够：
1. ✅ 与 AI 进行多轮连续对话
2. ✅ AI 能够记住之前对话的内容
3. ✅ 随时查看和清空对话历史
4. ✅ 实时看到对话条数统计

现在你可以启动服务器测试对话记忆功能了！
