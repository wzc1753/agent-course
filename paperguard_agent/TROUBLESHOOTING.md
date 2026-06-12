# 🔧 PaperGuard Agent - 故障排除指南

## 常见问题及解决方案

### 1. Streamlit启动失败

**问题**: `streamlit: command not found` 或 `'streamlit' 不是内部或外部命令`

**解决方案**:
```bash
pip install streamlit
```

或安装所有依赖:
```bash
pip install -r requirements.txt
```

---

### 2. Multi-Agent模式报错

**问题**: `AttributeError: 'dict' object has no attribute 'replace'`

**原因**: Agent模式下的数据传递问题

**解决方案**: 使用Functional Pipeline模式（同样功能）
1. 启动应用后
2. 在侧边栏选择 **"Functional Pipeline ⚙️"**
3. 继续正常使用

**说明**: Pipeline模式提供相同的所有核心功能（引用验证、论断检测等），只是不显示Agent执行轨迹。

---

### 3. Full模式无法使用

**问题**: 提示需要LLM API

**解决方案**:
- **选项A**: 使用Standard模式（推荐，无需API）
  - 包含引用验证和元数据检查
  - 不需要任何API密钥
  
- **选项B**: 配置MiniMax或OpenAI
  - 编辑 `.env` 文件
  - 添加相应的API Key
  - 参考 `MINIMAX_SETUP.md`

---

### 4. 依赖安装失败

**问题**: pip安装报错

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 逐个安装核心依赖
pip install streamlit
pip install pydantic
pip install requests
pip install pandas
pip install python-dotenv
```

---

### 5. 端口8501被占用

**问题**: `Address already in use`

**解决方案**:
```bash
# 使用不同端口
streamlit run app_enhanced.py --server.port 8502
```

或者关闭占用8501端口的程序。

---

### 6. 上传文件后无响应

**问题**: 点击"Run Audit"后卡住

**解决方案**:
1. 检查文件大小（建议<1MB）
2. 确认文件格式正确（.md, .txt, .tex）
3. 查看命令行终端是否有错误信息
4. 尝试使用Fast模式（最快）

---

### 7. Demo文件找不到

**问题**: `data/demo_bad_paper.md not found`

**解决方案**:
```bash
# 确认在正确的目录
cd "d:\agent course\paperguard_agent"

# 检查文件是否存在
ls data/demo_bad_paper.md

# 如果不存在，文件可能在其他位置
find . -name "demo_bad_paper.md"
```

---

## 推荐配置

### 快速开始（无需任何配置）

1. 启动应用:
   ```bash
   streamlit run app_enhanced.py
   ```

2. 选择设置:
   - 架构: **Functional Pipeline ⚙️** (稳定)
   - 模式: **Standard** (无需API)

3. 上传论文，运行审查

### 完整功能（需要配置）

1. 配置MiniMax API (参考 MINIMAX_SETUP.md)
2. 选择架构: **Multi-Agent System 🤖**
3. 选择模式: **Full**
4. 查看Agent执行轨迹

---

## 模式对比

| 模式 | 需要API | 功能 | 推荐场景 |
|------|---------|------|----------|
| Fast | ❌ | 引用完整性 | 快速检查 |
| Standard | ❌ | Fast + 元数据验证 | 日常使用 ⭐ |
| Full | ✅ | Standard + 论断验证 | 完整审查 |

---

## 架构对比

| 架构 | 稳定性 | Agent轨迹 | 推荐场景 |
|------|--------|-----------|----------|
| Functional Pipeline | ⭐⭐⭐ | ❌ | 日常使用 |
| Multi-Agent System | ⭐⭐ | ✅ | 演示/研究 |

---

## 获取帮助

1. 查看文档:
   - START_GUIDE.md - 启动指南
   - MINIMAX_SETUP.md - MiniMax配置
   - PROJECT_STRUCTURE.md - 项目结构

2. 检查日志:
   - 命令行终端显示详细错误信息

3. 降级使用:
   - Agent模式 → Pipeline模式
   - Full模式 → Standard模式
   - Standard模式 → Fast模式

---

## 最小可用配置

**只需要这3步就能运行**:

```bash
# 1. 安装streamlit
pip install streamlit

# 2. 启动应用
streamlit run app_enhanced.py

# 3. 使用Standard模式（无需API）
```

就这么简单！🎉

---

**如果以上方案都无法解决问题，请使用原始app.py**:

```bash
streamlit run app.py
```

这是最稳定的版本，保证可用。
