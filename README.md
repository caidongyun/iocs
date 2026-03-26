# IOC 协作工具

威胁情报（IOC — Indicators of Compromise）协作项目，用于收集、整理、检索恶意指标。

---

## 一、需求

### 1.1 背景
- 团队通过多方渠道采集威胁情报 IOC（域名、IP、文件 Hash）
- 原始数据以 CSV 格式提供，需要统一解析、去重、清洗后入库
- 入库后供本地检测使用（检测主机/网络流量中是否存在已知恶意指标）

### 1.2 核心功能

| 功能 | 说明 |
|------|------|
| CSV 解析 | 将原始 CSV 转换为统一 JSON 格式 |
| 去重合并 | 新旧 IOC 对比，去除重复条目 |
| 备注清洗 | 移除备注中的通用告警词（lidar告警、tdp告警等） |
| 完整性校验 | SHA256 索引文件，验证 IOC 库未被篡改 |
| 本地检测 | 给定域名/IP/Hash/文件，查询是否在黑名单中 |
| 白名单过滤 | 排除权威可信站点（.qq.com），避免误报 |
| Git 协作 | 同步到 GitHub/Gitee，多人协作 |

### 1.3 数据规模

| 类型 | 数量 |
|------|------|
| 域名 | 898 |
| IP | 278 |
| Hash | 654 |
| **合计** | **1855** |

数据来源：`IOC情报协作_IOC_IOC-3.25-2.csv`（2026-03-25）

---

## 二、架构

### 2.1 技术栈
- **语言**：Python 3
- **版本管理**：Git（GitHub + Gitee 双平台）
- **数据格式**：JSON
- **校验方式**：SHA256

### 2.2 目录结构

```
D:\IOC-src\
├── index.json              # 主索引（SHA256 校验）
├── data/
│   └── processed/
│       └── iocs.json       # IOC 数据库（核心产出）
├── src/
│   ├── ioc_parser.py       # CSV → JSON 解析器
│   ├── ioc_indexer.py      # 索引生成器（SHA256）
│   ├── ioc_dedup.py        # 去重对比工具
│   ├── ioc_sync.py          # Git 同步脚本
│   ├── ioc_checker.py       # 本地 IOC 检测器 ⭐
│   └── ioc_clean.py         # 备注清洗工具
├── whitelist.txt            # 域名白名单（本地，不上传）
├── sync.sh                  # 一键同步脚本
└── README.md
```

### 2.3 数据流

```
CSV 文件（原始）
    ↓
ioc_parser.py  →  data/processed/iocs.json（统一 JSON）
    ↓
ioc_clean.py   →  清洗备注中的通用告警词
    ↓
ioc_indexer.py →  更新 index.json（SHA256）
    ↓
git add → commit → push → GitHub / Gitee
```

### 2.4 IOC 检测流程（checker）

```
输入：域名 / IP / Hash / 文件路径
    ↓
加载 iocs.json（白名单域名在加载时过滤）
    ↓
匹配检测 → 输出 MATCH / OK
```

### 2.5 白名单机制

- **内置**：`src/ioc_checker.py` 硬编码（当前仅 `qq.com`）
- **用户自定义**：`whitelist.txt`（每行一个域名后缀，不上传 Git）
- **作用时机**：加载时过滤 + 检测时二次验证

---

## 三、发布要求

### 3.1 上传规则

| 文件 | 说明 | 上传 |
|------|------|------|
| `index.json` | 主索引（SHA256） | ✅ |
| `data/processed/iocs.json` | IOC 数据库 | ✅ |
| `src/*.py` | 工具脚本 | ✅ |
| `whitelist.txt` | 白名单 | ❌ 本地 |
| `*.csv` | CSV 原始文件 | ❌ 不上传 |
| `SPEC.md` | 本地规范 | ❌ 不上传 |
| `.env` | Token 配置 | ❌ 不上传 |

### 3.2 完整性校验

每次发布前必须更新 `index.json` 中的 SHA256：

```bash
python src/ioc_indexer.py
```

验证方法：
```bash
python -c "
import hashlib, json
with open('data/processed/iocs.json','rb') as f:
    sha = hashlib.sha256(f.read()).hexdigest()
with open('index.json','r') as f:
    idx = json.load(f)
print('SHA256 Match:', sha == idx['sha256'])
"
```

### 3.3 Git 提交规范

| 前缀 | 说明 | 示例 |
|------|------|------|
| `feat:` | 新功能、工具 | `feat: add whitelist support` |
| `clean:` | 数据清理 | `clean: remove lidar alerts from remarks` |
| `regen:` | 重新生成 IOC 库 | `regen: from new CSV` |
| `fix:` | 修复问题 | `fix: dedup logic error` |
| `docs:` | 文档更新 | `docs: rewrite README` |

### 3.4 版本节奏

- **日常**：检测器实时可用，无需频繁更新
- **数据更新**：有新 CSV 时重新解析、去重、清洗、push
- **工具迭代**：功能改动后单独 commit，附言说明

---

## 四、使用指南

### 4.1 检测域名
```bash
python src/ioc_checker.py --domain evil.com
```

### 4.2 检测 IP
```bash
python src/ioc_checker.py --ip 1.2.3.4
```

### 4.3 检测文件（SHA256 匹配）
```bash
python src/ioc_checker.py --file suspicious.exe
```

### 4.4 解析新 CSV
```bash
python src/ioc_parser.py --input data/raw/xxx.csv
```

### 4.5 清理备注
```bash
python src/ioc_clean.py data/processed/iocs.json
```

### 4.6 一键同步
```bash
bash sync.sh
```

---

## 五、项目历史

| Commit | 说明 | 日期 |
|--------|------|------|
| `0f8a361` | docs: rewrite README | 2026-03-26 |
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

## 六、数据格式

### IOC JSON 条目
```json
{
  "ioc": "evil.com",
  "type": "域名",
  "action": "拉黑",
  "threat_type": "钓鱼仿冒",
  "发现日期": "2026/03/25",
  "备注": "钓鱼仿冒知名企业",
  "source_file": "IOC情报协作_IOC_IOC-3.25-2.csv",
  "added_date": "2026-03-25"
}
```

### index.json 索引
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
