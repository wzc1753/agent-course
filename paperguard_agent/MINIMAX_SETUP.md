# 🚀 PaperGuard Agent - MiniMax-M3 配置指南

## 为什么使用MiniMax-M3？

✅ **国内可用** - 无需科学上网  
✅ **响应快速** - 国内服务器  
✅ **中文支持** - 原生支持中文论文  
✅ **成本低** - 比OpenAI便宜  

## 配置步骤

### 1. 获取MiniMax API Key

1. 访问 [MiniMax开放平台](https://api.minimax.chat/)
2. 注册/登录账号
3. 进入控制台
4. 创建API Key
5. 记录你的：
   - API Key
   - Group ID

### 2. 配置环境变量

编辑项目根目录的 `.env` 文件：

```bash
# MiniMax-M3 配置
MINIMAX_API_KEY=你的API_KEY
MINIMAX_GROUP_ID=你的GROUP_ID

# 可选：OpenAI作为备用
OPENAI_API_KEY=你的OpenAI_Key（可选）
```

### 3. 验证配置

启动应用后，在侧边栏会显示：

```
✅ MiniMax API Key configured
   Model: MiniMax-M3 (abab6.5s-chat)
```

## API优先级

PaperGuard会按以下顺序选择LLM：

1. **MiniMax-M3** (如果配置了MINIMAX_API_KEY)
2. **OpenAI GPT-4** (如果配置了OPENAI_API_KEY)
3. **关键词检测** (无需API，功能有限)

## 使用MiniMax的模式

- **Fast模式**: 不使用LLM，无需API
- **Standard模式**: 不使用LLM，无需API
- **Full模式**: 使用MiniMax-M3进行论断验证 ⭐

## 成本估算

以demo论文为例（约10个论断验证）：

- **MiniMax-M3**: 约 ¥0.01-0.05
- **OpenAI GPT-4**: 约 $0.10-0.50

## MiniMax-M3 模型信息

```
模型ID: abab6.5s-chat
上下文: 245K tokens
擅长: 中文理解、推理、JSON生成
```

## 常见问题

### Q: MiniMax API调用失败怎么办？

1. 检查API Key和Group ID是否正确
2. 确认账户余额充足
3. 查看控制台是否有限流
4. 系统会自动降级到OpenAI或关键词检测

### Q: 可以只用MiniMax不用OpenAI吗？

可以！只配置MINIMAX_API_KEY即可，不需要OpenAI。

### Q: Fast/Standard模式需要API吗？

不需要！只有Full模式才需要LLM API。

### Q: 如何查看使用的是哪个模型？

在审查结果的"Evidence"字段中会显示：
- "Verified by: MiniMax-M3"
- "Verified by: GPT-4"
- "Fallback verification used"

## 测试配置

运行测试脚本验证MiniMax配置：

```bash
cd "d:\agent course\paperguard_agent"
python test_minimax.py
```

## API文档

MiniMax官方文档: https://api.minimax.chat/document/guides/chat-model/V2

## 技术细节

PaperGuard使用MiniMax的配置：

```python
{
    "model": "abab6.5s-chat",
    "temperature": 0.01,  # 低温度确保一致性
    "top_p": 0.95,
    "messages": [
        {"role": "system", "content": "学术论文审查专家"},
        {"role": "user", "content": "验证论断..."}
    ]
}
```

## 优势对比

| 特性 | MiniMax-M3 | OpenAI GPT-4 |
|------|-----------|--------------|
| 国内访问 | ✅ 直连 | ⚠️ 需科学上网 |
| 中文支持 | ✅ 原生 | ✅ 支持 |
| 响应速度 | ⚡ 快 | ⚠️ 较慢（跨国） |
| 成本 | 💰 低 | 💰💰 较高 |
| JSON格式 | ✅ 稳定 | ✅ 稳定 |

---

**配置完成后，就可以使用Full模式进行完整的论文审查了！** 🎉
