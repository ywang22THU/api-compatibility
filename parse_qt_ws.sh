#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
LIB_PARSE="$ROOT_DIR/src/lib_parse.py"
ANALYZER="$ROOT_DIR/src/api_compatibility_analyzer.py"

# 创建输出目录
if [ ! -d "$ROOT_DIR/output" ]; then
    mkdir -p "$ROOT_DIR/output"
fi

echo "1. 解析 qtws-5.15.0"
echo "========================================"

python "$LIB_PARSE" \
    --root_path "$ROOT_DIR/qtwebsockets-5.15.0/src" \
    --output_path "$ROOT_DIR/output/qtwebsockets-5.15.0.json" \
    --verbose \
    --max_workers 4

echo
echo "2. 解析 qtwebsockets-6.9.0"
echo "========================================"

python "$LIB_PARSE" \
    --root_path "$ROOT_DIR/qtwebsockets-6.9.0/src" \
    --output_path "$ROOT_DIR/output/qtwebsockets-6.9.0.json" \
    --verbose \
    --max_workers 4

echo
echo "3. 生成 JSON 格式的详细报告"
echo "========================================"

# 生成JSON格式报告
python "$ANALYZER" \
    "$ROOT_DIR/output/qtwebsockets-5.15.0.json" \
    "$ROOT_DIR/output/qtwebsockets-6.9.0.json" \
    --output "$ROOT_DIR/output/qtwebsockets-compatibility_report.json" \
    --format json

echo
echo "=== 分析完成 ==="
echo "生成的文件："
echo "  - API数据: $ROOT_DIR/output/qtwebsockets-5.15.0.json"
echo "  - API数据: $ROOT_DIR/output/qtwebsockets-6.9.0.json"
echo "  - JSON报告: $ROOT_DIR/output/qtwebsockets-compatibility_report.json"
echo
