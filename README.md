# IOC 协作工具

威胁情报（IOC）协作项目，用于收集、整理、检索恶意指标。

## 当前数据规模

| 类型 | 数量 |
|------|------|
| 域名 | 898 |
| IP | 278 |
| Hash | 654 |
| **合计** | **1855** |

数据来源：`IOC情报协作_IOC_IOC-3.25-2.csv`（2026-03-25）

---

## 目录结构

```
D:\IOC-src\
├── index.json              # 主索引（SHA256 校验）
├── data/
│   └── processed/
│       └── iocs.json       # IOC 数据库
├── src/
│   ├── ioc_parser.py       # CSV → JSON 解析器
│   ├── ioc_indexer.py      # 索引生成器（SHA256）
│   ├── ioc_dedup.py        # 去重对比工具
│   ├── ioc_sync.py         # Git 同步脚本
│   ├── ioc_checker.py      # 本地 IOC 检测器
│   └── ioc_clean.py        # 备注清理工具
├── whitelist.txt            # 域名白名单（本地，不上传）
├── sync.sh                  # 一键同步脚本
├── SPEC.md                  # 本地规范（不上传）
└── README.md
```

---

## 工作流程

```
新 CSV 文件
    ↓ 放入 D:\IOC-src\
    ↓
python src/ioc_parser.py --input 新CSV.csv
    ↓ 生成 data/processed/iocs.json
    ↓
python src/ioc_clean.py data/processed/iocs.json
    ↓ 清理备注中的通用告警词
    ↓
python src/ioc_indexer.py
    ↓ 更新 index.json SHA256
    ↓
git add → commit → push
```

---

## 工具使用

### 检测域名
```bash
python src/ioc_checker.py --domain evil.com
```

### 检测 IP
```bash
python src/ioc_checker.py --ip 1.2.3.4
```

### 检测文件 Hash
```bash
python src/ioc_checker.py --file suspicious.exe
```

### 解析新 CSV
```bash
python src/ioc_parser.py --input data/raw/xxx.csv
```

### 清理备注
```bash
python src/ioc_clean.py data/processed/iocs.json
```

---

## 白名单机制

域名白名单用于排除权威可信站点，避免误报。

- **内置白名单**：`src/ioc_checker.py` 中硬编码（当前仅 `qq.com`）
- **用户白名单**：`whitelist.txt`（每行一个域名后缀，不上传 Git）

白名单域名在**加载时**和**检测时**均会过滤。

---

## 索引格式

```json
{
  "version": "2026-03-25",
  "last_updated": "2026-03-25T19:14:45Z",
  "total_count": 1855,
  "sha256": "05ee0945ad38f5143c86e9998676f63f...",
  "files": [
    {
      "filename": "IOC情报协作_IOC_IOC-3.25-2.csv",
      "sha256": "ff017eebbfa0dd26c2452203fd6c8050...",
      "added_date": "2026-03-25",
      "record_count": 1855
    }
  ]
}
```

---

## Git 提交规范

| 前缀 | 说明 |
|------|------|
| `feat:` | 新功能、新工具 |
| `clean:` | 清理数据、备注 |
| `regen:` | 重新生成 IOC 库 |
| `fix:` | 修复问题 |

---

## 项目历史

| Commit | 说明 | 日期 |
|--------|------|------|
| `37c8c4e` | feat: add whitelist support | 2026-03-26 |
| `27e3d53` | Regenerate and clean IOCs | 2026-03-25 |
| `7ee8fb7` | Clean lidar/tdp alerts from remarks | 2026-03-25 |
| `785abbc` | Regenerate from IOC情报协作_IOC_IOC-3.25-2.csv | 2026-03-25 |
| `bc6c537` | Clean private info from remarks | 2026-03-25 |
| `ed4bdff` | Ignore CSV source files | 2026-03-25 |
| `71b3a74` | Regenerate IOC database from new CSV | 2026-03-25 |
| `6c4de72` | Add Apifox poisoning IOCs | 2026-03-25 |
| `dd07460` | Add IOC sync tool | 2026-03-25 |
| `5ff4639` | Initial commit: IOC data 2026-03-25 | 2026-03-25 |

---

## IOC 数据格式

```json
{
  "ioc": "example.com",
  "type": "域名",
  "action": "拉黑",
  "threat_type": "钓鱼仿冒",
  "发现日期": "2026/03/25",
  "备注": "...",
  "source_file": "原始CSV文件名",
  "added_date": "2026-03-25"
}
```

**字段说明：**

| 字段 | 说明 | 上传 |
|------|------|------|
| ioc | IOC 值（域名/IP/Hash） | ✅ |
| type | IOC 类型 | ✅ |
| action | 处置动作 | ✅ |
| threat_type | 威胁类型 | ✅ |
| 发现日期 | 发现时间 | ✅ |
| 备注 | 备注信息 | ✅ |
| source_file | 原始 CSV 文件名 | ✅ |
| added_date | 入库日期 | ✅ |
| platform | 平台加黑 | ❌ 不采集 |
