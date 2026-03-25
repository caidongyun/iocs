#!/usr/bin/env python3
"""
IOC Sync - 自动同步 IOC 到 Gitee/Github
功能:
1. 监听新文件
2. 解析 + 去重
3. 更新索引
4. Git commit + push
"""

import os
import json
import hashlib
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class IOCSync:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.data_dir = self.repo_path / 'data'
        self.raw_dir = self.data_dir / 'raw'
        self.processed_dir = self.data_dir / 'processed'
        self.index_file = self.repo_path / 'index.json'
        self.iocs_file = self.processed_dir / 'iocs.json'
    
    def run_command(self, cmd: list, cwd=None) -> tuple:
        """执行 shell 命令"""
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd or self.repo_path,
                capture_output=True, 
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, '', str(e)
    
    def get_file_sha256(self, filepath: Path) -> str:
        """计算文件 SHA256"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def load_index(self) -> dict:
        """加载索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'version': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': '',
            'total_count': 0,
            'sha256': '',
            'files': []
        }
    
    def save_index(self, index: dict):
        """保存索引"""
        index['last_updated'] = datetime.now().isoformat() + 'Z'
        
        # 计算整个 iocs.json 的 SHA256
        if self.iocs_file.exists():
            index['sha256'] = self.get_file_sha256(self.iocs_file)
            index['total_count'] = len(json.load(open(self.iocs_file, 'r', encoding='utf-8')))
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def check_new_files(self) -> list:
        """检查新增文件"""
        index = self.load_index()
        known_files = {f['filename'] for f in index.get('files', [])}
        
        new_files = []
        for f in self.raw_dir.glob('*.csv'):
            if f.name not in known_files:
                new_files.append(f)
        for f in self.raw_dir.glob('*.json'):
            if f.name not in known_files:
                new_files.append(f)
        
        return new_files
    
    def parse_and_merge(self, new_files: list) -> int:
        """解析新文件并合并"""
        all_iocs = []
        
        # 加载现有 IOC
        if self.iocs_file.exists():
            all_iocs = json.load(open(self.iocs_file, 'r', encoding='utf-8'))
        
        existing_keys = {(ioc['ioc'], ioc.get('type', '')) for ioc in all_iocs if ioc.get('ioc')}
        
        new_count = 0
        for filepath in new_files:
            print(f"[PARSE] {filepath.name}")
            
            if filepath.suffix == '.csv':
                import csv
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ioc_value = row.get('IOC', '').strip()
                        ioc_type = row.get('类型', '').strip()
                        key = (ioc_value, ioc_type)
                        
                        if ioc_value and key not in existing_keys:
                            all_iocs.append({
                                'ioc': ioc_value,
                                'type': ioc_type,
                                'platform': row.get('平台加黑', '').strip(),
                                'action': row.get('处置动作', '').strip(),
                                'threat_type': row.get('威胁类型', '').strip(),
                                '发现日期': row.get('发现日期', '').strip(),
                                '备注': row.get('备注', '').strip(),
                                'source_file': filepath.name,
                                'added_date': datetime.now().strftime('%Y-%m-%d')
                            })
                            existing_keys.add(key)
                            new_count += 1
            
            elif filepath.suffix == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                iocs = data.get('iocs', data) if isinstance(data, dict) else data
                
                for ioc in iocs:
                    key = (ioc.get('ioc', ''), ioc.get('type', ''))
                    if key[0] and key not in existing_keys:
                        all_iocs.append(ioc)
                        existing_keys.add(key)
                        new_count += 1
        
        # 保存合并后的 IOC
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        with open(self.iocs_file, 'w', encoding='utf-8') as f:
            json.dump(all_iocs, f, indent=2, ensure_ascii=False)
        
        return new_count
    
    def git_commit_push(self, message: str) -> bool:
        """Git 提交并推送"""
        # Add all changes
        code, out, err = self.run_command(['git', 'add', '.'])
        if code != 0:
            print(f"[ERROR] git add failed: {err}")
            return False
        
        # Check if there are changes
        code, out, err = self.run_command(['git', 'status', '--porcelain'])
        if not out.strip():
            print("[INFO] No changes to commit")
            return True
        
        # Commit
        code, out, err = self.run_command(['git', 'commit', '-m', message])
        if code != 0:
            print(f"[ERROR] git commit failed: {err}")
            return False
        
        # Push
        code, out, err = self.run_command(['git', 'push', 'origin', 'main'])
        if code != 0:
            print(f"[ERROR] git push failed: {err}")
            return False
        
        return True
    
    def sync(self, commit_message: str = None) -> dict:
        """执行同步"""
        result = {
            'new_files': 0,
            'new_iocs': 0,
            'committed': False
        }
        
        # 检查新文件
        new_files = self.check_new_files()
        result['new_files'] = len(new_files)
        
        if not new_files:
            print("[OK] No new files")
            return result
        
        print(f"[INFO] Found {len(new_files)} new files")
        
        # 解析并合并
        new_count = self.parse_and_merge(new_files)
        result['new_iocs'] = new_count
        print(f"[OK] Added {new_count} new IOCs")
        
        # 更新索引
        index = self.load_index()
        
        # 添加新文件到索引
        for f in new_files:
            index['files'].append({
                'filename': f.name,
                'sha256': self.get_file_sha256(f),
                'added_date': datetime.now().strftime('%Y-%m-%d'),
                'record_count': sum(1 for ioc in json.load(open(self.iocs_file, 'r', encoding='utf-8')) if ioc.get('source_file') == f.name)
            })
        
        self.save_index(index)
        print(f"[OK] Index updated: {self.index_file}")
        
        # Git 提交
        if commit_message is None:
            commit_message = f"Add {len(new_files)} new IOC files - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if self.git_commit_push(commit_message):
            result['committed'] = True
            print("[OK] Pushed to remote")
        
        return result


def main():
    parser = argparse.ArgumentParser(description='IOC Sync Tool')
    parser.add_argument('--path', '-p', default='.', help='Repository path')
    parser.add_argument('--message', '-m', help='Commit message')
    parser.add_argument('--init', action='store_true', help='Initialize repository')
    args = parser.parse_args()
    
    sync = IOCSync(args.path)
    
    if args.init:
        # 初始化目录
        sync.data_dir.mkdir(parents=True, exist_ok=True)
        sync.raw_dir.mkdir(parents=True, exist_ok=True)
        sync.processed_dir.mkdir(parents=True, exist_ok=True)
        print("[OK] Directories created")
        
        # 初始化 Git
        code, out, err = sync.run_command(['git', 'init'])
        if code == 0:
            print("[OK] Git initialized")
        else:
            print(f"[WARN] {err}")
        return
    
    result = sync.sync(args.message)
    print(f"\n[SUMMARY]")
    print(f"  New files: {result['new_files']}")
    print(f"  New IOCs: {result['new_iocs']}")
    print(f"  Committed: {result['committed']}")


if __name__ == '__main__':
    main()
