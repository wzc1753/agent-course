#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       PaperGuard Agent - 项目结构验证                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查必需的文件
echo "📋 检查必需文件..."
required_files=(
    "app.py"
    "test_paperguard.py"
    "requirements.txt"
    ".env"
    ".env.example"
    "README.md"
    "paperguard/__init__.py"
    "paperguard/config.py"
    "paperguard/schemas.py"
    "paperguard/parser.py"
    "paperguard/pipeline.py"
    "data/demo_bad_paper.md"
)

all_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - 缺失"
        all_present=false
    fi
done

echo ""
echo "📦 核心模块统计..."
module_count=$(ls -1 paperguard/*.py 2>/dev/null | wc -l)
echo "  Python模块数: $module_count"

echo ""
echo "📊 代码统计..."
total_lines=$(find paperguard -name "*.py" -exec cat {} \; 2>/dev/null | wc -l)
echo "  总代码行数: $total_lines"

echo ""
echo "🗂️ 目录结构..."
if command -v tree &> /dev/null; then
    tree -L 2 -I '__pycache__|*.pyc|.git' --dirsfirst
else
    find . -maxdepth 2 -type d | grep -v "__pycache__\|.git" | sort
fi

echo ""
if $all_present; then
    echo "✅ 项目结构验证通过！"
    echo ""
    echo "🚀 可以开始使用："
    echo "   python test_paperguard.py"
    echo "   streamlit run app.py"
else
    echo "⚠️ 有文件缺失，请检查！"
fi
