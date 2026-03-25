#!/usr/bin/env python3
"""
IOC Checker - 检查本地系统是否匹配已知 IOC
支持:
- 域名检查
- IP 检查
- Hash 检查
- 文件路径检查
"""

import subprocess
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Set


class IOCChecker:
    def __init__(self, ioc_file: str = None):
        self.ioc_file = ioc_file or 'data/processed/iocs.json'
        self.domains: Set[str] = set()
        self.ips: Set[str] = set()
        self.hashes: Set[str] = set()
        self.load_iocs()
    
    def load_iocs(self):
        """加载 IOC 数据"""
        ioc_path = Path(self.ioc_file)
        if not ioc_path.exists():
            # 尝试相对于脚本目录
            script_dir = Path(__file__).parent.parent
            ioc_path = script_dir / self.ioc_file
        
        if ioc_path.exists():
            with open(ioc_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for ioc in data if isinstance(data, list) else data.get('iocs', []):
                ioc_value = ioc.get('ioc', '')
                ioc_type = ioc.get('type', '')
                
                if not ioc_value:
                    continue
                
                if ioc_type == 'IP' or self._is_ip(ioc_value):
                    self.ips.add(ioc_value)
                elif ioc_type == 'Hash' or len(ioc_value) == 64:
                    self.hashes.add(ioc_value.lower())
                elif ioc_type == '域名' or '.' in ioc_value and not self._is_ip(ioc_value):
                    self.domains.add(ioc_value.lower())
        
        print(f"[OK] Loaded {len(self.domains)} domains, {len(self.ips)} IPs, {len(self.hashes)} hashes")
    
    def _is_ip(self, value: str) -> bool:
        """判断是否为 IP 地址"""
        parts = value.split('.')
        if len(parts) != 4:
            return False
        return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
    
    def check_domain(self, domain: str) -> bool:
        """检查域名是否在黑名单"""
        domain = domain.lower()
        if domain in self.domains:
            return True
        # 检查域名后缀
        for blocked in self.domains:
            if domain.endswith(blocked) or blocked.endswith(domain):
                return True
        return False
    
    def check_ip(self, ip: str) -> bool:
        """检查 IP 是否在黑名单"""
        return ip in self.ips
    
    def check_hash(self, file_hash: str) -> bool:
        """检查文件 hash"""
        return file_hash.lower() in self.hashes
    
    def check_file(self, filepath: str) -> dict:
        """检查文件是否匹配已知恶意 hash"""
        result = {
            'path': filepath,
            'matched': False,
            'hash': ''
        }
        
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            result['hash'] = file_hash
            result['matched'] = file_hash.lower() in self.hashes
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def check_env(self) -> dict:
        """检查环境变量中的敏感信息"""
        import os
        findings = []
        
        # 检查常见敏感环境变量
        sensitive_vars = ['AWS_ACCESS_KEY', 'AWS_SECRET', 'AZURE', 'GCP', 'SECRET', 'PASSWORD', 'API_KEY', 'TOKEN']
        
        for key, value in os.environ.items():
            if any(s in key.upper() for s in sensitive_vars):
                findings.append(f"Environment variable: {key}")
        
        return {'sensitive_env_count': len(findings), 'details': findings}


def main():
    parser = argparse.ArgumentParser(description='IOC Checker')
    parser.add_argument('--domain', '-d', help='Check domain')
    parser.add_argument('--ip', '-i', help='Check IP')
    parser.add_argument('--hash', '-H', help='Check file hash')
    parser.add_argument('--file', '-f', help='Check file')
    parser.add_argument('--ioc-file', default='data/processed/iocs.json', help='IOC database file')
    parser.add_argument('--json', '-J', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    checker = IOCChecker(args.ioc_file)
    
    results = []
    
    if args.domain:
        matched = checker.check_domain(args.domain)
        results.append({'type': 'domain', 'value': args.domain, 'matched': matched})
        if not args.json:
            print(f"[{'MATCH' if matched else 'OK'}] Domain: {args.domain}")
    
    if args.ip:
        matched = checker.check_ip(args.ip)
        results.append({'type': 'ip', 'value': args.ip, 'matched': matched})
        if not args.json:
            print(f"[{'MATCH' if matched else 'OK'}] IP: {args.ip}")
    
    if args.hash:
        matched = checker.check_hash(args.hash)
        results.append({'type': 'hash', 'value': args.hash, 'matched': matched})
        if not args.json:
            print(f"[{'MATCH' if matched else 'OK'}] Hash: {args.hash}")
    
    if args.file:
        result = checker.check_file(args.file)
        results.append(result)
        if not args.json:
            print(f"[{'MATCH' if result['matched'] else 'OK'}] File: {args.file}")
            print(f"  SHA256: {result.get('hash', 'N/A')}")
    
    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
