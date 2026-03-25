#!/usr/bin/env python3
"""
IOC Cleaner - 清理备注中的通用告警信息
"""

import json
import re
import sys

def clean_iocs(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 需要移除的通用告警词
    patterns_to_remove = [
        'lidar告警',
        'tdp告警',
        '来源：',
        '云枢告警',
        '安全卫士',
    ]
    
    cleaned = 0
    for ioc in data:
        if ioc.get('备注'):
            remark = ioc['备注']
            original = remark
            
            # 移除通用告警词
            for pattern in patterns_to_remove:
                remark = remark.replace(pattern, '')
            
            # 清除多余空格
            remark = ' '.join(remark.split())
            
            if remark != original:
                ioc['备注'] = remark
                cleaned += 1
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'Cleaned {cleaned} records')
    return cleaned


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data/processed/iocs.json'
    clean_iocs(input_file)
