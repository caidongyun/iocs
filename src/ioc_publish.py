#!/usr/bin/env python3
"""
IOC Publish - 生成发布变更报告、更新版本记录
每次发布运行一次，输出 CHANGELOG-<version>.json 并更新 RELEASES.md。
"""

import json
import hashlib
import sys
import argparse
from pathlib import Path
from datetime import datetime


INDEX_FILE = 'index.json'
IOCS_FILE = 'data/processed/iocs.json'
RELEASES_FILE = 'RELEASES.md'


def load_previous_index() -> dict:
    """加载上一次的 index.json（从 git）"""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'show', 'HEAD:index.json'],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return json.loads(result.stdout.decode('utf-8'))
    except Exception:
        pass
    return None


def load_previous_iocs() -> list:
    """加载上一次的 iocs.json（从 git）"""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'show', 'HEAD:data/processed/iocs.json'],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout.decode('utf-8'))
    except Exception:
        pass
    return []


def compute_stats(iocs: list) -> dict:
    """按类型统计 IOC"""
    by_type = {}
    for ioc in iocs:
        t = ioc.get('type', '(empty)')
        by_type[t] = by_type.get(t, 0) + 1
    return by_type


def compute_diff(old_iocs: list, new_iocs: list) -> dict:
    """计算两次之间的差异"""
    old_set = {(i.get('ioc', ''), i.get('type', '')) for i in old_iocs if i.get('ioc')}
    new_set = {(i.get('ioc', ''), i.get('type', '')) for i in new_iocs if i.get('ioc')}

    added_keys = new_set - old_set
    removed_keys = old_set - new_set

    # 按类型统计新增和移除
    added_by_type = {}
    removed_by_type = {}

    for key in added_keys:
        t = key[1] if key[1] else '(empty)'
        added_by_type[t] = added_by_type.get(t, 0) + 1

    for key in removed_keys:
        t = key[1] if key[1] else '(empty)'
        removed_by_type[t] = removed_by_type.get(t, 0) + 1

    return {
        'added': len(added_keys),
        'removed': len(removed_keys),
        'added_by_type': added_by_type,
        'removed_by_type': removed_by_type,
    }


def file_sha256(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_changelog(version: str, message: str) -> dict:
    """生成变更报告"""
    with open(IOCS_FILE, 'r', encoding='utf-8') as f:
        new_iocs = json.load(f)

    prev_iocs = load_previous_iocs()
    prev_index = load_previous_index()

    diff = compute_diff(prev_iocs, new_iocs)
    by_type = compute_stats(new_iocs)

    sha = file_sha256(IOCS_FILE)

    changelog = {
        'version': version,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'message': message,
        'previous_version': prev_index.get('version', '') if prev_index else None,
        'summary': {
            'total_before': len(prev_iocs),
            'total_after': len(new_iocs),
            'added': diff['added'],
            'removed': diff['removed'],
        },
        'by_type': by_type,
        'diff': diff,
        'sha256': sha,
    }

    return changelog


def update_releases(version: str, changelog: dict):
    """追加版本记录到 RELEASES.md"""
    by_type = changelog['by_type']
    summary = changelog['summary']
    diff = changelog['diff']

    type_table = ''
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        added = diff['added_by_type'].get(t, 0)
        removed = diff['removed_by_type'].get(t, 0)
        change = f'+{added}' if added else ''
        if removed:
            change += f' -{removed}'
        type_table += f'| {t} | {count} | {change} |\n'

    section = f"""
## {version}

**发布日期**: {changelog['date']}
**说明**: {changelog['message']}

### 统计

| 类型 | 数量 | 变更 |
|------|------|------|
{type_table}
| **合计** | **{summary['total_after']}** | +{summary['added']} -{summary['removed']} |

### 变更摘要

- 新增 {summary['added']} 条 IOC
- 移除 {summary['removed']} 条 IOC

### SHA256 指纹

```
data/processed/iocs.json : {changelog['sha256']}
```

---
"""

    releases_path = Path(RELEASES_FILE)
    content = releases_path.read_text(encoding='utf-8')
    # 在文件末尾追加
    content = content.rstrip() + section
    releases_path.write_text(content, encoding='utf-8')


def write_changelog_json(version: str, changelog: dict):
    """写入 CHANGELOG-<version>.json"""
    filename = f'CHANGELOG-{version}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(changelog, f, indent=2, ensure_ascii=False)
    return filename


def main():
    parser = argparse.ArgumentParser(description='IOC Publish Tool')
    parser.add_argument('--version', '-v', required=True, help='Version tag, e.g. v1.2.0-20260401')
    parser.add_argument('--message', '-m', default='', help='Release message')
    parser.add_argument('--dry-run', action='store_true', help='Print without writing')
    args = parser.parse_args()

    changelog = generate_changelog(args.version, args.message)

    print(f'[PUBLISH] {args.version}')
    print(f'  Total before: {changelog["summary"]["total_before"]}')
    print(f'  Total after : {changelog["summary"]["total_after"]}')
    print(f'  Added       : {changelog["summary"]["added"]}')
    print(f'  Removed     : {changelog["summary"]["removed"]}')

    if args.dry_run:
        print(f'\n[DRY RUN] No files written')
        print(json.dumps(changelog, indent=2, ensure_ascii=False))
        return

    # 写入变更报告
    cl_file = write_changelog_json(args.version, changelog)
    print(f'[OK] Written {cl_file}')

    # 更新 RELEASES.md
    update_releases(args.version, changelog)
    print(f'[OK] Updated {RELEASES_FILE}')


if __name__ == '__main__':
    main()
