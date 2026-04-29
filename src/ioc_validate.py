#!/usr/bin/env python3
"""
IOC Validator - 校验 IOC 数据质量
在发布前运行，确保数据符合规范。
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

VALID_TYPES = {'域名', 'IP', 'Hash', 'URL', '路径', '邮箱', '签名', '其他'}

IP_PATTERN = re.compile(
    r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
)
HASH_MD5 = re.compile(r'^[0-9a-fA-F]{32}$')
HASH_SHA256 = re.compile(r'^[0-9a-fA-F]{64}$')


def validate_ip(value: str) -> bool:
    m = IP_PATTERN.match(value)
    if not m:
        return False
    return all(0 <= int(g) <= 255 for g in m.groups())


def validate_hash(value: str) -> bool:
    return bool(HASH_MD5.match(value) or HASH_SHA256.match(value))


def validate_domain(value: str) -> bool:
    return '.' in value and not value.startswith('http') and not value.startswith('/')


def validate_email(value: str) -> bool:
    return '@' in value and '.' in value.split('@')[-1]


def validate_path(value: str) -> bool:
    return value.startswith('/') or value.startswith('%') or ':' in value and ('\\' in value or '/' in value)


def validate_ioc(ioc: Dict) -> List[str]:
    """校验单条 IOC，返回错误列表"""
    errors = []
    value = ioc.get('ioc', '').strip()
    ioc_type = ioc.get('type', '')

    if not value:
        errors.append('empty ioc value')
        return errors

    if ioc_type not in VALID_TYPES:
        errors.append(f'unknown type "{ioc_type}" (valid: {", ".join(sorted(VALID_TYPES))})')

    if ioc_type == 'IP' and not validate_ip(value):
        errors.append(f'invalid IP format: {value}')

    if ioc_type == 'Hash' and not validate_hash(value):
        errors.append(f'invalid hash format: {value}')

    if ioc_type == '域名' and not validate_domain(value):
        errors.append(f'suspicious domain format: {value}')

    if ioc_type == '邮箱' and not validate_email(value):
        errors.append(f'invalid email format: {value}')

    if ioc_type == '路径' and not validate_path(value):
        errors.append(f'invalid path format: {value}')

    return errors


def run(filepath: str) -> Tuple[bool, List[str], Dict]:
    """运行校验，返回 (是否通过, 错误列表, 统计)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    errors = []
    stats = {
        'total': len(data),
        'by_type': {},
        'invalid_count': 0,
        'empty_type_count': 0,
    }

    seen = set()
    dupes = 0

    for idx, ioc in enumerate(data):
        # 类型统计
        t = ioc.get('type', '(empty)')
        stats['by_type'][t] = stats['by_type'].get(t, 0) + 1
        if not ioc.get('type'):
            stats['empty_type_count'] += 1

        # 去重检查
        key = (ioc.get('ioc', ''), ioc.get('type', ''))
        if key[0] in seen:
            dupes += 1
        seen.add(key[0])

        # 单条校验
        entry_errors = validate_ioc(ioc)
        if entry_errors:
            stats['invalid_count'] += 1
            errors.append(f'  [{idx+1}] {key[0][:60]}: {", ".join(entry_errors)}')

    # 汇总
    ok = len(errors) == 0
    lines = []
    lines.append(f'[VALIDATE] {filepath}')
    lines.append(f'  Total records : {stats["total"]}')
    lines.append(f'  Invalid records: {stats["invalid_count"]}')
    lines.append(f'  Duplicate iocs : {dupes}')
    lines.append(f'  Empty types    : {stats["empty_type_count"]}')
    lines.append(f'  By type: {dict(sorted(stats["by_type"].items(), key=lambda x: -x[1]))}')

    if errors:
        lines.append(f'\n  Errors:')
        lines.extend(errors)
        lines.append(f'\n[FAIL] {len(errors)} validation errors')
    else:
        lines.append(f'[OK] All records pass validation')

    return ok, lines, stats


def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'data/processed/iocs.json'
    ok, lines, stats = run(filepath)
    for line in lines:
        print(line)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
