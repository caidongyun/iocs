#!/bin/bash
# IOC 一键处理管道
# 用法:
#   直接处理:
#     bash run_pipeline.sh "新CSV文件.csv"
#   按日期过滤后处理:
#     bash run_pipeline.sh "新CSV文件.csv" --from "2026/03/25"
#   指定版本号和说明:
#     bash run_pipeline.sh "新CSV文件.csv" --from "2026/03/25" -v "v1.2.0-20260401" -m "新增 4 月 IOC"
#
# 流程: 日期过滤 → 解析 → 合并去重 → 清洗 → 校验 → 发布报告 → 提交推送

set -e

cd "$(dirname "$0")"

# 解析参数
CSV_FILE=""
FROM_DATE=""
VERSION=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --from|-f)
            FROM_DATE="$2"; shift 2 ;;
        -v|--version)
            VERSION="$2"; shift 2 ;;
        -m|--message)
            MESSAGE="$2"; shift 2 ;;
        -*)
            echo "[ERROR] Unknown option: $1"; exit 1 ;;
        *)
            if [ -z "$CSV_FILE" ]; then
                CSV_FILE="$1"
            fi
            shift ;;
    esac
done

if [ -z "$CSV_FILE" ]; then
    echo "用法: bash run_pipeline.sh <CSV文件> [--from <起始日期>] [-v <版本号>] [-m <说明>]"
    exit 1
fi

VERSION="${VERSION:-v1.$(date +%m%d%H%M)}"
MESSAGE="${MESSAGE:-新增 IOC $(basename "$CSV_FILE")}"

echo "========================================"
echo "  IOC Pipeline: $(basename "$CSV_FILE")"
echo "  Version: $VERSION"
if [ -n "$FROM_DATE" ]; then
    echo "  Date filter: >= $FROM_DATE"
fi
echo "========================================"

WORK_CSV="$CSV_FILE"

# Step 1: 日期过滤（可选）
STEP_COUNT=6
if [ -n "$FROM_DATE" ]; then
    STEP_COUNT=7
    echo ""
    echo "[1/$STEP_COUNT] Filtering by date (>= $FROM_DATE)..."
    WORK_CSV=$(python -c "
import sys
sys.path.insert(0, 'src')
from ioc_filter_date import filter_csv
r = filter_csv('$CSV_FILE', '$FROM_DATE')
print(r['output'])
")
    echo "  Filtered CSV: $WORK_CSV"
fi

# Step 2: 合并去重
echo ""
echo "[$((STEP_COUNT == 7 && 2 || 1))/$STEP_COUNT] Merging and deduplicating..."
python -X utf8 << PYEOF
import csv, json
from pathlib import Path
from datetime import datetime

csv_file = '$WORK_CSV'
iocs_file = 'data/processed/iocs.json'

# 加载现有数据
existing = []
if Path(iocs_file).exists():
    with open(iocs_file, 'r', encoding='utf-8') as f:
        existing = json.load(f)

seen = {(i['ioc'], i.get('type', '')) for i in existing if i.get('ioc')}
new_count = 0

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row.get('IOC', '').strip(), row.get('类型', '').strip())
        if key[0] and key not in seen:
            existing.append({
                'ioc': key[0],
                'type': key[1],
                'action': row.get('处置动作', '').strip(),
                'threat_type': row.get('威胁类型', '').strip(),
                '发现日期': row.get('发现日期', '').strip(),
                '备注': row.get('备注', '').strip(),
                'source_file': Path(csv_file).name,
                'added_date': datetime.now().strftime('%Y-%m-%d')
            })
            seen.add(key)
            new_count += 1

with open(iocs_file, 'w', encoding='utf-8') as f:
    json.dump(existing, f, indent=2, ensure_ascii=False)

print(f'  Merged {new_count} new IOCs (total: {len(existing)})')
PYEOF

# Step 3: 清洗备注
echo ""
echo "[$((STEP_COUNT == 7 && 3 || 2))/$STEP_COUNT] Cleaning remarks..."
python -X utf8 src/ioc_clean.py data/processed/iocs.json

# Step 4: 数据校验
echo ""
echo "[$((STEP_COUNT == 7 && 4 || 3))/$STEP_COUNT] Validating data quality..."
python -X utf8 src/ioc_validate.py data/processed/iocs.json || {
    echo "[WARN] Validation found issues, continuing anyway"
}

# Step 5: 生成发布报告
echo ""
echo "[$((STEP_COUNT == 7 && 5 || 4))/$STEP_COUNT] Generating release report..."
python -X utf8 src/ioc_publish.py --version "$VERSION" --message "$MESSAGE"

# Step 6: Git 提交并推送
echo ""
echo "[$((STEP_COUNT == 7 && 6 || 5))/$STEP_COUNT] Committing and pushing..."
git add -A
git status
git commit -m "$(cat <<'MSG'
release: '"$VERSION"' - '"$MESSAGE"'

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
MSG
)" || echo "[INFO] No changes to commit"

git tag -f "$VERSION"
git push origin master "$VERSION" 2>/dev/null || echo "[WARN] Push to origin failed"
git push gitee master "$VERSION" 2>/dev/null || echo "[WARN] Push to gitee failed"

# 清理临时过滤文件
if [ -n "$FROM_DATE" ] && [ "$WORK_CSV" != "$CSV_FILE" ] && [ -f "$WORK_CSV" ]; then
    rm -f "$WORK_CSV"
    echo ""
    echo "  Cleaned up temporary filtered CSV"
fi

echo ""
echo "========================================"
echo "  Pipeline complete!"
echo "  Version: $VERSION"
echo "========================================"
