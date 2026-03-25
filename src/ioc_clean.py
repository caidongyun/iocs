#!/usr/bin/env python3
"""
IOC Cleaner - 清理备注中的隐私信息
"""

import json
import re
from pathlib import Path

def clean_remarks(input_file, output_file=None):
    if output_file is None:
        output_file = input_file
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned = 0
    for ioc in data:
        if ioc.get('备注'):
            remark = ioc['备注']
            
            # 清除括号内容 (公司名称等)
            remark = re.sub(r'[\（\(][^\)\)]*[\)\)]', '', remark)
            
            # 清除"来源：xxx"
            remark = re.sub(r'来源：[^\s,，]+', '', remark)
            
            # 清除公司名称
            remark = re.sub(r'[^\s,，]+公司', '', remark)
            
            # 清除邮箱
            remark = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', remark)
            
            # 清除URL
            remark = re.sub(r'https?://[^\s]+', '[URL]', remark)
            
            ioc['备注'] = remark.strip()
            cleaned += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'Cleaned {cleaned} records')
    return cleaned


if __name__ == '__main__':
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data/processed/iocs.json'
    clean_remarks(input_file)
