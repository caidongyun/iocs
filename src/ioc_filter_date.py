#!/usr/bin/env python3
"""
IOC Date Filter - 从 CSV 中提取指定日期之后的记录
用法: python src/ioc_filter_date.py <CSV文件> <起始日期> [输出文件]
示例: python src/ioc_filter_date.py "新文件.csv" "2026/03/25" "filtered.csv"
"""

import csv
import sys
from pathlib import Path
from datetime import datetime


def parse_date(value: str) -> datetime:
    """解析 CSV 中的日期，兼容多种格式"""
    value = value.strip()
    for fmt in ('%Y/%m/%d %H:%M', '%Y/%m/%d', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.min


def filter_csv(input_file: str, cutoff_date: str, output_file: str = None) -> dict:
    """过滤 CSV，保留 cutoff_date（含）之后的记录"""
    cutoff = parse_date(cutoff_date)
    if output_file is None:
        output_file = str(Path(input_file).with_name(
            f'{Path(input_file).stem}_from_{cutoff.strftime("%Y%m%d")}{Path(input_file).suffix}'
        ))

    kept = []
    skipped = 0
    fieldnames = None

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # 优先用详细日期字段，其次用发现日期
        date_field = '记录创建详细日期(检查是否历史已加黑工作流使用)'
        if date_field not in fieldnames:
            date_field = '发现日期'

        for row in reader:
            row_date = parse_date(row.get(date_field, ''))
            if row_date >= cutoff:
                kept.append(row)
            else:
                skipped += 1

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    return {
        'total': len(kept) + skipped,
        'kept': len(kept),
        'skipped': skipped,
        'cutoff': cutoff_date,
        'date_field': date_field,
        'output': output_file,
    }


def main():
    if len(sys.argv) < 3:
        print(f'用法: python {sys.argv[0]} <CSV文件> <起始日期> [输出文件]')
        print(f'示例: python {sys.argv[0]} "新情报.csv" "2026/03/25"')
        sys.exit(1)

    input_file = sys.argv[1]
    cutoff_date = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    result = filter_csv(input_file, cutoff_date, output_file)

    print(f'[FILTER] {Path(input_file).name}')
    print(f'  Cutoff date : {cutoff_date}')
    print(f'  Date field  : {result["date_field"]}')
    print(f'  Total rows  : {result["total"]}')
    print(f'  Kept (>= cutoff) : {result["kept"]}')
    print(f'  Skipped (< cutoff): {result["skipped"]}')
    print(f'  Output: {result["output"]}')


if __name__ == '__main__':
    main()
