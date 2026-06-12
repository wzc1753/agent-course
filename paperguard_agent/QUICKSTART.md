# PaperGuard Agent - 快速启动指南

## 项目概述

PaperGuard Agent 是一个智能论文审查系统，专门用于检测AI辅助学术写作中的引用幻觉、元数据错误和论断一致性问题。

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- streamlit (Web界面)
- pydantic (数据验证)
- requests/httpx (API调用)
- rapidfuzz (文本相似度)
- openai (LLM验证)
- pandas (数据处理)

### 2. 配置API密钥

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，至少配置：
```
OPENAI_API_KEY=your_openai_api_key_here
```

可选配置（提高验证质量）：
```
CROSSREF_EMAIL=your_email@example.com
SEMANTIC_SCHOLAR_API_KEY=your_s2_api_key
```

## 运行方式

### 方法1: Streamlit Web界面（推荐）

```bash
streamlit run app.py
```

然后在浏览器打开 http://localhost:8501

### 方法2: 命令行测试

```bash
python test_paperguard.py
```

### 方法3: Python API调用

```python
from paperguard.pipeline import run_audit

# 读取论文
with open('your_paper.md', 'r') as f:
    paper_content = f.read()

# 运行审查
report = run_audit(
    paper_content, 
    mode="Full",  # Fast/Standard/Full
    max_claims=10
)

# 查看结果
for issue in report.issues:
    print(f"{issue.severity}: {issue.diagnosis}")
```

## 审查模式

### Fast Mode (快速模式)
- ✓ 引用完整性检查
- ✓ 正文引用与参考文献列表一致性
- ⚡ 速度最快，无需API调用

### Standard Mode (标准模式)
- ✓ Fast模式所有功能
- ✓ 外部数据库验证（Crossref, Semantic Scholar, OpenAlex）
- ✓ 元数据一致性评分
- ⏱️ 中等速度，需要网络连接

### Full Mode (完整模式)
- ✓ Standard模式所有功能
- ✓ 论断-引用支持性验证（使用LLM）
- ✓ 过强论断检测
- ✓ 修改建议生成
- 🐢 较慢，需要OpenAI API

## Demo演示

### 使用预设的错误论文

1. 启动Streamlit：`streamlit run app.py`
2. 上传 `data/demo_bad_paper.md`
3. 选择审查模式：Full
4. 点击"Run Audit"
5. 查看检测到的8种错误

### Demo论文中的预设错误

| 编号 | 错误类型 | 位置 | 描述 |
|-----|---------|------|------|
| E1 | 虚构引用 | [23] | 不存在的NeurIPS 2025论文 |
| E2 | 年份错误 | [5] | Toolformer标记为2024（实际2023） |
| E3 | DOI错误 | [7] | DOI指向错误论文 |
| E4 | 引用缺失 | [12] | 正文引用但参考文献列表没有 |
| E5 | 未使用引用 | [18] | 参考文献有但正文未引用 |
| E6 | 引用不支持论断 | [23] | "完全解决"的过强论断引用虚构文献 |
| E7 | 数字不一致 | 摘要vs表格 | 摘要说15%，表格显示8% |
| E8 | 过强论断 | [5] | "我们是第一个"缺乏充分证据 |

## 项目结构

```
paperguard_agent/
├── app.py                      # Streamlit前端
├── test_paperguard.py          # 测试脚本
├── requirements.txt            # 依赖
├── .env.example                # 环境变量模板
├── README.md                   # 项目文档
├── QUICKSTART.md               # 本文件
│
├── paperguard/                 # 核心包
│   ├── __init__.py
│   ├── schemas.py              # 数据模型
│   ├── config.py               # 配置管理
│   ├── parser.py               # 论文解析
│   ├── citation_extractor.py   # 引用提取
│   ├── reference_parser.py     # 参考文献解析
│   ├── metadata_clients.py     # 外部API客户端
│   ├── matcher.py              # 元数据匹配
│   ├── claim_extractor.py      # 论断提取
│   ├── claim_verifier.py       # 论断验证
│   ├── report.py               # 报告生成
│   ├── cache.py                # API结果缓存
│   ├── pipeline.py             # 主流程编排
│   └── utils.py                # 工具函数
│
├── data/                       # 数据目录
│   └── demo_bad_paper.md       # Demo论文
│
├── outputs/                    # 输出目录
│   └── metadata_cache.json     # API缓存
│
└── tests/                      # 测试
    └── (单元测试)
```

## 支持的输入格式

- ✓ Markdown (.md)
- ✓ Plain Text (.txt)  
- ✓ LaTeX (.tex)
- ✓ BibTeX (.bib) - 作为参考文献补充

## 检测的问题类型

1. **引用完整性问题**
   - 正文引用但参考文献缺失
   - 参考文献未被引用
   - 引用编号超出范围

2. **引用真实性问题**
   - 虚构引用（数据库中找不到）
   - DOI错误
   - 元数据不一致（标题、作者、年份、会议）

3. **论断一致性问题**
   - 引用不支持论断
   - 过强论断（first, solve, prove, all, always）
   - 数字不一致

## 常见问题

### Q: 为什么Fast模式没有检测到所有问题？
A: Fast模式只检查引用完整性，不调用外部API。使用Standard或Full模式进行完整验证。

### Q: 如何提高验证准确率？
A: 
1. 配置Semantic Scholar API Key
2. 使用Full模式
3. 提供BibTeX文件以获得更准确的参考文献解析

### Q: API调用太慢怎么办？
A: 系统会自动缓存API结果到 `outputs/metadata_cache.json`，重复运行会更快。

### Q: 支持中文论文吗？
A: 当前主要针对英文学术论文优化，中文论文的引用格式可能无法完全识别。

## 视频演示

录制5分钟演示视频建议流程：
1. (0:00-0:30) 介绍问题背景
2. (0:30-1:00) 展示系统架构
3. (1:00-2:00) 上传demo论文
4. (2:00-3:30) 展示检测结果（8种错误）
5. (3:30-4:20) 展示验证轨迹和修改建议
6. (4:20-5:00) 总结与对比baseline

## 技术支持

如遇问题，请检查：
1. Python版本 >= 3.10
2. 所有依赖已正确安装
3. .env文件配置正确
4. 网络连接正常（Standard/Full模式）

## 下一步

✅ 系统已完全搭建完成！

建议操作：
1. 运行 `python test_paperguard.py` 验证安装
2. 运行 `streamlit run app.py` 启动Web界面
3. 使用demo论文测试所有功能
4. 准备录制演示视频
5. 撰写6页项目报告
