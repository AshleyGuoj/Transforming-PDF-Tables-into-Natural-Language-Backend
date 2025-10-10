#!/bin/bash
# 测试文件上传和解析功能
# 使用方法: ./test_upload_parse.sh

set -e

API_BASE="http://localhost:8000/api/v1"
PROJECT_ID=1

# 生成开发 token
echo "🔑 生成开发环境 JWT Token..."
TOKEN=$(python3 -c "
import sys
sys.path.insert(0, 'backend')
from app.security.auth_stub import get_dev_admin_token
print(get_dev_admin_token())
")

if [ -z "$TOKEN" ]; then
    echo "❌ 无法生成 token"
    exit 1
fi

echo "✅ Token 已生成"
echo ""

echo "🧪 测试上传 PDF 并自动触发解析"
echo "=================================="
echo ""

# 创建测试 PDF 文件（如果不存在）
if [ ! -f "test.pdf" ]; then
    echo "📝 创建测试 PDF 文件..."
    # 使用 echo 创建一个简单的文本文件作为测试
    echo "%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
187
%%EOF" > test.pdf
    echo "✅ 测试 PDF 已创建"
fi

echo ""
echo "1️⃣ 上传 PDF 到项目 $PROJECT_ID"
echo "-----------------------------------"
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/projects/$PROJECT_ID/files" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf")

echo "响应: $UPLOAD_RESPONSE"
FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":[0-9]*' | grep -o '[0-9]*')

if [ -z "$FILE_ID" ]; then
    echo "❌ 上传失败，未获取到 file_id"
    exit 1
fi

echo "✅ 上传成功！文件 ID: $FILE_ID"
echo ""

echo "2️⃣ 触发文件解析"
echo "-----------------------------------"
PARSE_RESPONSE=$(curl -s -X POST "$API_BASE/files/$FILE_ID/parse" \
  -H "Authorization: Bearer $TOKEN")
echo "响应: $PARSE_RESPONSE"
echo ""

echo "3️⃣ 检查解析状态"
echo "-----------------------------------"
for i in {1..5}; do
    echo "检查 #$i..."
    STATUS_RESPONSE=$(curl -s "$API_BASE/files/$FILE_ID/parse-status" \
      -H "Authorization: Bearer $TOKEN")
    echo "响应: $STATUS_RESPONSE"

    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo "当前状态: $STATUS"

    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        break
    fi

    sleep 2
done
echo ""

echo "4️⃣ 获取解析的表格"
echo "-----------------------------------"
TABLES_RESPONSE=$(curl -s "$API_BASE/files/$FILE_ID/tables" \
  -H "Authorization: Bearer $TOKEN")
echo "响应: $TABLES_RESPONSE"
echo ""

echo "✅ 测试完成！"
echo ""
echo "📊 总结："
echo "  - 文件 ID: $FILE_ID"
echo "  - 解析状态: $STATUS"
echo "  - 前端访问: http://localhost:3000/console/project"
