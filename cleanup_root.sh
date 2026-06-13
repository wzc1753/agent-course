#!/bin/bash

echo "🧹 清理根目录杂乱文件..."

# 删除散落的Python文件
echo "删除散落的Python模块..."
rm -f cache.py citation_extractor.py claim_extractor.py claim_verifier.py 
rm -f config.py matcher.py metadata_clients.py parser.py 
rm -f reference_parser.py repairer.py report.py schemas.py
rm -f app.py demo_bad_paper.md README.md

# 删除多余的paperguard目录（保留paperguard_agent）
if [ -d "paperguard" ]; then
    echo "删除多余的paperguard/目录..."
    rm -rf paperguard
fi

# 删除多余的tests目录（保留paperguard_agent/tests）
if [ -d "tests" ]; then
    echo "删除根目录tests/目录..."
    rm -rf tests
fi

# 清理脚本自身
rm -f reorganize.sh

echo ""
echo "✅ 清理完成！"
echo ""
echo "📁 根目录现在只包含："
ls -1 | head -10

