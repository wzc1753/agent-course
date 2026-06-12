# PaperGuard Agent

**面向 AI 辅助论文写作的引用幻觉与论断一致性验证智能体**

PaperGuard Agent 是一个论文审查智能体，用于检测AI辅助写作中的引用幻觉、元数据错误和论断一致性问题。

## 功能特性

✅ **引用完整性检查** - 检测正文引用与参考文献列表的不一致  
✅ **引用真实性验证** - 通过外部学术数据库验证参考文献是否存在  
✅ **元数据一致性评分** - 检查标题、作者、年份、DOI等是否匹配  
✅ **论断-引用支持性验证** - 使用LLM验证引用是否真正支持论断  
✅ **过强论断检测** - 识别缺乏证据的强结论  
✅ **修改建议生成** - 提供可执行的修复建议  
✅ **审查轨迹可视化** - 展示每一步验证过程  

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置API密钥

复制 `.env.example` 为 `.env` 并填入你的API密钥：

```bash
cp .env.example .env
```

至少需要配置 `OPENAI_API_KEY` 用于论断验证。

### 运行应用

```bash
streamlit run app.py
```

然后在浏览器中打开 http://localhost:8501

### 使用Demo数据

1. 上传 `data/demo_bad_paper.md`
2. 选择审查模式（Fast/Standard/Full）
3. 点击"Run Audit"
4. 查看检测到的问题和修改建议

## 审查模式

- **Fast** - 仅检查引用完整性和真实性
- **Standard** - 增加元数据一致性评分
- **Full** - 完整审查，包括论断-引用支持性验证

## 项目结构

```
paperguard_agent/
├── app.py                      # Streamlit前端
├── requirements.txt            # 依赖包
├── paperguard/                 # 核心包
│   ├── schemas.py              # 数据模型
│   ├── parser.py               # 论文解析
│   ├── citation_extractor.py   # 引用提取
│   ├── reference_parser.py     # 参考文献解析
│   ├── metadata_clients.py     # 外部API客户端
│   ├── matcher.py              # 元数据匹配
│   ├── claim_extractor.py      # 论断提取
│   ├── claim_verifier.py       # 论断验证
│   ├── report.py               # 报告生成
│   ├── cache.py                # API缓存
│   └── pipeline.py             # 主流程编排
├── data/                       # Demo数据
│   └── demo_bad_paper.md       # 带错误的示例论文
├── outputs/                    # 输出目录
└── tests/                      # 测试
```

## 支持的输入格式

- Markdown (`.md`)
- Plain text (`.txt`)
- LaTeX (`.tex`)
- BibTeX (`.bib`)
- PDF (实验性支持)

## 支持的引用格式

- 数字引用：`[1]`, `[1,2]`, `[1-3]`
- LaTeX引用：`\cite{key}`, `\citep{key}`, `\citet{key}`

## 外部数据源

- Crossref - 学术文献元数据
- Semantic Scholar - AI论文搜索
- OpenAlex - 开放学术图谱
- arXiv - 预印本数据库

## 检测的错误类型

1. **虚构引用** - 参考文献不存在
2. **元数据拼接** - 标题真实但作者/年份/会议错误
3. **引用误用** - 引用不支持正文论断
4. **过强论断** - 缺乏充分证据的强结论
5. **引用缺失** - 正文引用但参考文献列表没有
6. **未使用引用** - 参考文献列表有但正文未引用
7. **DOI错误** - DOI指向错误论文
8. **数字不一致** - 摘要和表格中的数字矛盾

## 技术栈

- **Frontend**: Streamlit
- **Backend**: Python 3.10+
- **LLM API**: OpenAI
- **Data Validation**: Pydantic
- **Text Matching**: RapidFuzz
- **BibTeX Parsing**: bibtexparser

## 开发团队

课程项目 - 智能体及应用

## License

MIT License
