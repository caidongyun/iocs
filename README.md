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
| 备注清洗 | 移除备注中的内部告警词和来源标识 |
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

## 二、规范

### 2.1 上传规则

| 文件 | 说明 | 上传 |
|------|------|------|
| `index.json` | 主索引（SHA256） | ✅ |
| `data/processed/iocs.json` | IOC 数据库 | ✅ |
| `src/*.py` | 工具脚本 | ✅ |
| `whitelist.txt` | 白名单 | ❌ 本地 |
| `*.csv` | CSV 原始文件 | ❌ 不上传 |
| `SPEC.md` | 本地规范 | ❌ 不上传 |
| `.env` | Token 配置 | ❌ 不上传 |

### 2.2 数据规范

**IOC JSON 条目格式：**
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

**字段规则：**

| 字段 | 必填 | 说明 |
|------|------|------|
| ioc | ✅ | IOC 值（域名/IP/Hash） |
| type | ✅ | 类型：域名 / IP / Hash |
| action | ❌ | 处置动作，如"拉黑" |
| threat_type | ❌ | 威胁类型，如"钓鱼仿冒" |
| 发现日期 | ❌ | 原始发现日期 |
| 备注 | ❌ | 备注信息，将被清洗 |
| source_file | ✅ | 来源 CSV 文件名 |
| added_date | ✅ | 入库日期（自动） |
| platform | ❌ | 平台加黑，**不采集** |

### 2.3 备注清洗规范

以下关键词在入库时将被自动移除：
- 内部告警产品标识
- 来源标识
- 外部产品标识

### 2.4 白名单规范

- **来源**：用户编辑 `whitelist.txt`，不上传 Git
- **格式**：每行一个域名或后缀
- **匹配**：
  - 精确匹配：`qq.com` → 匹配 `qq.com`
  - 后缀匹配：`.qq.com` → 匹配 `api.qq.com`、`mp.weixin.qq.com`
- **作用时机**：加载时过滤 + 检测时二次验证

### 2.5 Git 提交规范

| 前缀 | 说明 | 示例 |
|------|------|------|
| `feat:` | 新功能、工具 | `feat: add whitelist support` |
| `clean:` | 数据清理 | `clean: remove lidar alerts from remarks` |
| `regen:` | 重新生成 IOC 库 | `regen: from new CSV` |
| `fix:` | 修复问题 | `fix: dedup logic error` |
| `docs:` | 文档更新 | `docs: rewrite README` |

---

## 三、架构

### 3.1 技术栈
- **语言**：Python 3
- **版本管理**：Git（GitHub + Gitee 双平台）
- **数据格式**：JSON
- **校验方式**：SHA256

### 3.2 目录结构

```
D:\IOC-src\
├── index.json              # 主索引（SHA256 校验）
├── data/
│   └── processed/
│       └── iocs.json       # IOC 数据库（核心产出）
├── src/
│   ├── ioc_parser.py       # CSV → JSON 解析器
│   ├── ioc_sync.py         # Git 同步脚本
│   ├── ioc_checker.py      # 本地 IOC 检测器
│   ├── ioc_clean.py        # 备注清洗工具
│   ├── ioc_validate.py     # 数据质量校验
│   ├── ioc_publish.py      # 发布报告生成
│   └── ioc_filter_date.py  # 日期过滤
├── RELEASES.md             # 版本发布记录
├── AUTOMATION.md           # 运维操作指南
├── run_pipeline.sh         # 一键处理管道
├── sync.sh                 # 快捷同步脚本
├── whitelist.txt           # 域名白名单（本地，不上传）
├── .gitignore              # 忽略规则
├── README.md               # 本文件
├── SPEC.md                 # 本地规范（不上传）
└── .env                    # Token 配置（不上传）
```

### 3.3 数据流

```
CSV 文件（原始）
    ↓
ioc_filter_date.py → 按日期过滤老数据（可选）
    ↓
ioc_parser.py   →  解析为统一 JSON 并合并去重
    ↓
ioc_clean.py    →  清洗备注中的通用告警词
    ↓
ioc_validate.py →  数据质量校验（格式、去重、白名单）
    ↓
ioc_publish.py  →  生成 CHANGELOG + 更新 RELEASES.md
    ↓
git add → commit → tag → push → GitHub / Gitee
```

---

## 四、对外监控接口

外部消费者（下游系统、合作方、自动化监控）通过以下方式追踪 IOC 变化：

### 4.1 监控 index.json

`index.json` 是轻量级入口，字段变化即表示发布更新：

| 字段 | 含义 | 监控方式 |
|------|------|---------|
| `sha256` | iocs.json 的文件指纹 | 值变化 = 数据变更 |
| `total_count` | IOC 总数 | 数值变化 = 数量增减 |
| `last_updated` | 最后更新时间 | 时间变化 = 有新发布 |
| `version` | 版本号 | 与 `RELEASES.md` 交叉验证 |

### 4.2 监控 RELEASES.md

每次发布在文件末尾追加版本记录，消费者通过 Git diff 获取变更：

```bash
git diff HEAD~1 -- RELEASES.md
```

### 4.3 监控 CHANGELOG-*.json

每次发布生成机器可读的变更报告 `CHANGELOG-<version>.json`，包含：

```json
{
  "version": "v1.2.0-20260401",
  "summary": { "total_before": 1855, "total_after": 2100, "added": 250, "removed": 5 },
  "by_type": { "域名": 1200, "IP": 358, "Hash": 704 },
  "diff": { "added": 250, "removed": 5, "added_by_type": {...}, "removed_by_type": {...} },
  "sha256": "..."
}
```

### 4.4 Git 标签

每次发布打语义化版本标签，消费者可订阅 tag 推送：

```bash
# 列出所有版本
git tag -l 'v*'

# 查看某个版本的数据
git show v1.2.0-20260401:data/processed/iocs.json | wc -l
```

### 4.5 兼容性保证

| 承诺 | 说明 |
|------|------|
| 字段不删 | 已发布的 JSON 字段不会被移除，只会新增 |
| 类型不增删 | `域名`/`IP`/`Hash`/`URL` 类型枚举稳定 |
| 文件名不变 | `data/processed/iocs.json` 路径不变 |
| 索引结构不变 | `index.json` 顶层字段稳定 |

---

## 五、运维操作

### 5.1 一键处理新 CSV

```bash
# 新 CSV 不含老数据，直接处理
bash run_pipeline.sh "IOC情报协作_IOC_IOC-4.01.csv" "v1.2.0-20260401" "新增 4 月 IOC"

# 新 CSV 包含老数据，按日期过滤（从 2026-03-25 开始提取）
bash run_pipeline.sh "新文件.csv" --from "2026/03/25" -v "v1.2.0-20260401" -m "新增 4 月 IOC"
```

自动完成：日期过滤 → 解析 → 合并去重 → 清洗 → 校验 → 发布报告 → 提交推送。

### 5.2 单步操作（调试用）

```bash
# 日期过滤（从指定日期开始提取）
python src/ioc_filter_date.py "新文件.csv" "2026/03/25"

# 解析
python src/ioc_parser.py --input "IOC情报协作_IOC_IOC-4.01.csv" --output data/processed/iocs.json

# 清洗备注
python src/ioc_clean.py data/processed/iocs.json

# 校验数据质量
python src/ioc_validate.py data/processed/iocs.json

# 生成发布报告
python src/ioc_publish.py --version v1.2.0-20260401 --message "新增 4 月 IOC"
```

### 5.3 IOC 检测

输入：域名 / IP / Hash / 文件路径
    ↓
加载 iocs.json（白名单域名在加载时过滤）
    ↓
匹配检测 → 输出 MATCH（命中）/ OK（通过）

---

## 六、版本历史

详见 [RELEASES.md](RELEASES.md)。

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2026-04-29 | v1.1.0 | 新增发布规范、监控接口、数据校验 |
| 2026-03-26 | v2.0 | 新增白名单机制、重写 README |
| 2026-03-25 | v1.0 | 初始版本，含 CSV 解析、检测、清洗、同步 |
