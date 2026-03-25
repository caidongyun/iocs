#!/usr/bin/env python3
"""
IOC Parser - 解析 CSV/JSON 格式的 IOC 文件
支持格式:
- 你的 CSV 格式 (IOC情报协作)
- 标准 JSON 格式
- OpenIOC 格式
"""

import csv
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class IOCParser:
    def __init__(self):
        self.iocs = []
    
    def parse_csv(self, filepath: str, encoding='utf-8-sig') -> List[Dict]:
        """解析你的 CSV 格式"""
        iocs = []
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ioc = {
                        'ioc': row.get('IOC', '').strip(),
                        'type': row.get('类型', '').strip(),
                        'platform': row.get('平台加黑', '').strip(),
                        'action': row.get('处置动作', '').strip(),
                        'threat_type': row.get('威胁类型', '').strip(),
                        '发现日期': row.get('发现日期', '').strip(),
                        '备注': row.get('备注', '').strip(),
                        '附件': row.get('附件', '').strip(),
                        'is_historical': '历史已加黑' in row.get('是否历史已加黑', ''),
                        'created_date': row.get('记录创建详细日期(检查是否历史已加黑工作流使用)', '').strip(),
                        'source_file': Path(filepath).name,
                        'sha256': ''
                    }
                    # 计算 IOC 本身的 SHA256
                    if ioc['ioc']:
                        ioc['sha256'] = hashlib.sha256(ioc['ioc'].encode()).hexdigest()
                    if ioc['ioc']:  # 只添加非空 IOC
                        iocs.append(ioc)
        except Exception as e:
            print(f"[ERROR] Failed to parse {filepath}: {e}")
        return iocs
    
    def parse_json(self, filepath: str) -> List[Dict]:
        """解析 JSON 格式"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'iocs' in data:
            return data['iocs']
        return []
    
    def generate_index(self, iocs: List[Dict], source_file: str) -> Dict:
        """生成索引信息"""
        threat_types = set(ioc.get('threat_type', '') for ioc in iocs if ioc.get('threat_type'))
        
        # 计算整个文件的 SHA256
        with open(source_file, 'rb') as f:
            file_sha256 = hashlib.sha256(f.read()).hexdigest()
        
        index = {
            'filename': Path(source_file).name,
            'parsed_date': datetime.now().isoformat() + 'Z',
            'record_count': len(iocs),
            'sha256': file_sha256,
            'threat_types': sorted(list(threat_types)),
            'sample_count': min(5, len(iocs)),
            'samples': [ioc['ioc'] for ioc in iocs[:5] if ioc.get('ioc')]
        }
        return index
    
    def deduplicate(self, new_iocs: List[Dict], existing_iocs: List[Dict]) -> tuple:
        """去重对比，返回 (新增, 重复, 现有总数)"""
        existing_set = set()
        for ioc in existing_iocs:
            if ioc.get('ioc'):
                existing_set.add((ioc['ioc'], ioc.get('type', '')))
        
        new_only = []
        duplicates = []
        
        for ioc in new_iocs:
            key = (ioc.get('ioc', ''), ioc.get('type', ''))
            if key[0] and key not in existing_set:
                new_only.append(ioc)
                existing_set.add(key)
            elif key[0]:
                duplicates.append(ioc)
        
        return new_only, duplicates, len(existing_set)


def main():
    parser = argparse.ArgumentParser(description='IOC Parser')
    parser.add_argument('--input', '-i', required=True, help='Input file path')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--format', '-f', choices=['csv', 'json'], default='csv', help='Input format')
    parser.add_argument('--index', action='store_true', help='Generate index only')
    args = parser.parse_args()
    
    ioc_parser = IOCParser()
    
    if args.format == 'csv':
        iocs = ioc_parser.parse_csv(args.input)
    else:
        iocs = ioc_parser.parse_json(args.input)
    
    print(f"[OK] Parsed {len(iocs)} IOCs from {Path(args.input).name}")
    
    if args.index:
        index = ioc_parser.generate_index(iocs, args.input)
        print(f"[INDEX]")
        print(json.dumps(index, indent=2, ensure_ascii=False))
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({
                'iocs': iocs,
                'index': ioc_parser.generate_index(iocs, args.input)
            }, f, indent=2, ensure_ascii=False)
        print(f"[OK] Written to {args.output}")
    else:
        # Print sample
        print(f"\n[SAMPLES]")
        for ioc in iocs[:3]:
            print(f"  [{ioc['type']}] {ioc['ioc'][:60]}... - {ioc['threat_type']}")


if __name__ == '__main__':
    main()
