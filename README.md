# IOC 协作工具链

## 目录结构

```
ioc-repo/
├── src/                      # 源代码
│   ├── ioc_parser.py        # CSV/JSON 解析器
│   ├── ioc_indexer.py      # 索引生成器 (SHA256)
│   ├── ioc_dedup.py        # 去重对比工具
│   ├── ioc_sync.py         # Git 同步脚本
│   └── ioc_checker.py      # 本地 IOC 检测器
├── data/                     # IOC 数据目录
│   ├── raw/                # 原始上传文件
│   ├── processed/          # 处理后数据
│   └── index/              # 索引文件
├── index.json               # 主索引 (含 SHA256)
├── ioc.db                   # SQLite 数据库 (可选)
├── config.yaml             # 配置文件
├── sync.sh                 # 同步脚本
└── README.md
```

## 索引格式 (index.json)

```json
{
  "version": "2026-03-25",
  "last_updated": "2026-03-25T14:30:00Z",
  "total_count": 1234,
  "sha256": "abc123...",
  "files": [
    {
      "filename": "IOC情报协作_IOC_IOC-3.25.csv",
      "sha256": "def456...",
      "added_date": "2026-03-25",
      "record_count": 500,
      "threat_types": ["钓鱼仿冒", "供应链攻击", "银狐", ...]
    }
  ]
}
```

## 工作流程

```
1. 上传 CSV → src/raw/
2. 解析 + 去重 → src/processed/
3. 生成索引 (SHA256) → index.json
4. Git commit + push → Gitee/Github
```

## 使用方法

### 解析 CSV
```bash
python src/ioc_parser.py --input data/raw/yourfile.csv
```

### 去重对比
```bash
python src/ioc_dedup.py --new data/new.csv --existing data/processed/iocs.json
```

### 同步到 Git
```bash
python src/ioc_sync.py --commit "Add IOCs 2026-03-25"
```

### 检查本地
```bash
python src/ioc_checker.py --domain evil.com
```

## 压缩包方案

对于大文件使用 gzip 压缩：
```bash
# 压缩
gzip -k iocs.csv

# 解压
gunzip iocs.csv.gz
```

压缩后自动更新索引中的 `compressed_sha256` 字段。
