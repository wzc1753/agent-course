# PaperGuard Agent - 项目结构

本文档描述项目的标准目录结构，严格遵循开发指导文档要求。

## 标准目录结构

```
paperguard_agent/
│
├── app.py                         # Streamlit前端入口
├── README.md                      # 项目说明文档
├── QUICKSTART.md                  # 快速启动指南
├── PROJECT_SUMMARY.md             # 项目完成总结
├── FILE_MANIFEST.txt              # 文件清单
├── requirements.txt               # Python依赖
├── .env                           # 环境变量配置（本地）
├── .env.example                   # 环境变量模板
├── test_paperguard.py             # 快速测试脚本
│
├── paperguard/                    # 核心Python包
│   ├── __init__.py                # 包初始化
│   ├── config.py                  # 配置管理
│   ├── schemas.py                 # Pydantic数据模型
│   ├── parser.py                  # 论文解析
│   ├── citation_extractor.py      # 引用提取
│   ├── reference_parser.py        # 参考文献解析
│   ├── metadata_clients.py        # 外部API客户端
│   ├── matcher.py                 # 元数据匹配
│   ├── claim_extractor.py         # 论断提取
│   ├── claim_verifier.py          # 论断验证
│   ├── report.py                  # 报告生成
│   ├── cache.py                   # API缓存
│   ├── pipeline.py                # 主流程编排
│   └── utils.py                   # 工具函数
│
├── data/                          # 数据目录
│   └── demo_bad_paper.md          # Demo论文（含8种错误）
│
├── outputs/                       # 输出目录
│   ├── audit_reports/             # 审查报告
│   └── metadata_cache.json        # API缓存
│
└── tests/                         # 测试目录
    ├── __init__.py
    ├── test_config.py
    ├── test_schemas.py
    └── test_utils.py
```

## 目录说明

### 根目录文件

- **app.py**: Streamlit Web应用主入口
- **test_paperguard.py**: 快速测试脚本，验证系统运行
- **requirements.txt**: Python依赖包列表
- **.env**: 本地环境变量（包含API密钥，不提交到Git）
- **.env.example**: 环境变量模板（提交到Git）
- **README.md**: 项目概述和使用说明
- **QUICKSTART.md**: 快速启动指南
- **PROJECT_SUMMARY.md**: 项目完成总结

### paperguard/ 核心包

所有核心功能模块，按照文档第7节建议的目录结构组织：

1. **config.py**: 加载环境变量，定义阈值和配置
2. **schemas.py**: 定义所有Pydantic数据模型
3. **parser.py**: 解析论文文本，分离正文和参考文献
4. **citation_extractor.py**: 提取[n]和\cite{}引用
5. **reference_parser.py**: 解析参考文献和BibTeX
6. **metadata_clients.py**: Crossref/Semantic Scholar/OpenAlex/arXiv API客户端
7. **matcher.py**: 元数据相似度匹配和评分
8. **claim_extractor.py**: 提取高风险论断
9. **claim_verifier.py**: LLM论断验证
10. **report.py**: 审查报告生成
11. **cache.py**: API结果缓存
12. **pipeline.py**: 主流程编排
13. **utils.py**: 工具函数

### data/ 数据目录

- **demo_bad_paper.md**: 示例论文，包含8种预设错误

### outputs/ 输出目录

运行时生成的文件：
- 审查报告（Markdown和JSON格式）
- API查询缓存

### tests/ 测试目录

单元测试和集成测试

## 文件命名规范

- Python模块: 小写下划线命名 (citation_extractor.py)
- 类名: 驼峰命名 (CitationMention)
- 函数名: 小写下划线命名 (extract_citations)
- 常量: 大写下划线命名 (MAX_CLAIMS_DEFAULT)

## 导入规范

```python
# 标准库
import os
from typing import List, Optional

# 第三方库
import streamlit as st
from pydantic import BaseModel

# 本地模块
from .schemas import ReferenceEntry
from .config import Config
```

## 不应该存在的文件/目录

❌ 根目录下散落的Python文件
❌ 重复的paperguard/目录
❌ 根目录下的demo_bad_paper.md
❌ 根目录下的.env（应该在paperguard_agent/下）

## 验证命令

检查项目结构是否正确：

```bash
cd paperguard_agent
python test_paperguard.py
```

启动应用：

```bash
cd paperguard_agent
streamlit run app.py
```
