# 🚀 PaperGuard Agent - 启动指南

## 方法1: 启动Web界面（推荐）

### Step 1: 打开终端
- Windows: 按 `Win + R`，输入 `cmd` 或 `powershell`
- 或在VS Code中按 `Ctrl + ~` 打开终端

### Step 2: 进入项目目录
```bash
cd "d:\agent course\paperguard_agent"
```

### Step 3: 安装依赖（首次运行）
```bash
pip install -r requirements.txt
```

### Step 4: 启动Streamlit应用
```bash
streamlit run app.py
```

### Step 5: 访问Web界面
- 浏览器会自动打开，如果没有，访问：
- **http://localhost:8501**

### Step 6: 使用Demo
1. 在界面中点击"Upload manuscript"
2. 选择 `data/demo_bad_paper.md`
3. 选择审查模式（推荐先用"Fast"测试）
4. 点击"🚀 Run Audit"
5. 查看检测结果

## 方法2: 命令行测试

```bash
cd "d:\agent course\paperguard_agent"
python test_paperguard.py
```

## 常见问题

### Q: 提示"streamlit: command not found"
```bash
pip install streamlit
```

### Q: 端口8501已被占用
```bash
streamlit run app.py --server.port 8502
```

### Q: 依赖安装失败
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Q: Full模式需要OpenAI API Key
- 编辑 `.env` 文件
- 设置 `OPENAI_API_KEY=your_key_here`
- Fast和Standard模式不需要API key

## 快捷方式

创建一个启动脚本：

**Windows (start.bat):**
```batch
@echo off
cd /d "d:\agent course\paperguard_agent"
streamlit run app.py
pause
```

**运行:** 双击 `start.bat`
