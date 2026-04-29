# IOC 运维自动化指南

> 本文档描述从接收新 IOC CSV 到发布版本的完整流程。
> 目标：一条命令完成新增、清洗、验证、发布。

---

## 一、核心数据流

```
CSV 文件 ──┐
           ├─→ ioc_filter_date.py → 按日期过滤老数据
           ├─→ ioc_parser.py   → 解析为统一 JSON
           ├─→ ioc_clean.py    → 清洗备注
           ├─→ ioc_validate.py → 校验数据质量
           ├─→ ioc_publish.py  → 生成变更报告、更新版本记录
           └─→ git + sync.sh   → 提交并推送
```

## 二、目录规范

```
D:\IOC-src\
├── index.json                  # SHA256 索引 ✅ 发布
├── data/
│   └── processed/
│       └── iocs.json           # IOC 数据库 ✅ 发布
├── src/
│   ├── ioc_parser.py           # CSV 解析 ✅ 发布
│   ├── ioc_clean.py            # 备注清洗 ✅ 发布
│   ├── ioc_checker.py          # 本地检测 ✅ 发布
│   ├── ioc_sync.py             # Git 同步   ✅ 发布
│   ├── ioc_validate.py         # 数据校验 ✅ 发布
│   ├── ioc_publish.py          # 发布工具 ✅ 发布
│   └── ioc_filter_date.py      # 日期过滤 ✅ 发布
├── whitelist.txt               # 白名单 ❌ 本地
├── sync.sh                     # 快捷同步 ✅ 发布
├── README.md                   # 项目说明 ✅ 发布
├── RELEASES.md                 # 版本记录 ✅ 发布
├── AUTOMATION.md               # 运维指南 ✅ 发布
├── .gitignore                  # 忽略规则 ✅ 发布
├── .env                        # Token 配置 ❌ 不上传
└── SPEC.md                     # 本地规范 ❌ 不上传
```

## 三、标准操作流程

### 3.1 接收新 IOC 情报

```bash
# 1. 将新 CSV 文件放到项目根目录
#    例如: IOC情报协作_IOC_IOC-4.01.csv

# 2a. 新 CSV 不含老数据 → 直接处理
bash run_pipeline.sh "IOC情报协作_IOC_IOC-4.01.csv"

# 2b. 新 CSV 包含老数据 → 按日期过滤后处理
bash run_pipeline.sh "新文件.csv" --from "2026/03/25"
```

### 3.2 单步执行（调试用）

```bash
# 日期过滤（新 CSV 包含老数据时）
python src/ioc_filter_date.py "新文件.csv" "2026/03/25"

# 解析
python src/ioc_parser.py --input "IOC情报协作_IOC_IOC-4.01.csv" --output data/processed/iocs.json

# 清洗
python src/ioc_clean.py data/processed/iocs.json

# 校验
python src/ioc_validate.py data/processed/iocs.json

# 生成变更报告
python src/ioc_publish.py --version v1.2.0-20260401 --message "新增 4 月 IOC"

# 提交推送
bash sync.sh "release: v1.2.0-20260401 - 新增 IOC"
```

### 3.3 日常检测

```bash
# 检测域名
python src/ioc_checker.py --domain evil.com

# 检测 IP
python src/ioc_checker.py --ip 1.2.3.4

# 检测文件 hash
python src/ioc_checker.py --hash abc123...

# 检测文件本身
python src/ioc_checker.py --file suspicious.exe
```

## 四、监控接口

### 4.1 对外消费者监控方式

| 监控对象 | 检测方式 | 变更信号 |
|---------|---------|---------|
| `index.json` | 比较 `sha256` 字段值 | 值变化 = 数据更新 |
| `index.json` | 比较 `last_updated` | 时间变化 = 有发布 |
| `index.json` | 比较 `total_count` | 数量变化 = IOC 增减 |
| `data/processed/iocs.json` | 比较文件 SHA256 | 与 `index.json.sha256` 一致 |
| `RELEASES.md` | Git diff HEAD~1 | 新版本记录追加 |
| `CHANGELOG-*.json` | 文件出现 | 新变更报告 |

### 4.2 变更摘要文件

每次发布自动生成 `CHANGELOG-v1.2.0-20260401.json`：

```json
{
  "version": "v1.2.0-20260401",
  "date": "2026-04-01",
  "previous_version": "v1.1.0-20260325",
  "summary": {
    "total_before": 1855,
    "total_after": 2100,
    "added": 250,
    "removed": 5,
    "modified": 0
  },
  "by_type": {
    "域名": { "added": 120, "removed": 2 },
    "IP":   { "added": 80,  "removed": 1 },
    "Hash": { "added": 50,  "removed": 2 }
  },
  "source_files": ["IOC情报协作_IOC_IOC-4.01.csv"],
  "sha256": "..."
}
```

### 4.3 Git 标签

```bash
# 每次发布打标签
git tag v1.2.0-20260401
git push origin v1.2.0-20260401
git push gitee v1.2.0-20260401
```

## 五、数据质量门槛

新 IOC 入库前必须通过以下校验：

| 校验项 | 规则 | 失败处理 |
|-------|------|---------|
| 非空检查 | ioc 字段不为空 | 跳过 |
| 类型合法 | type ∈ {域名, IP, Hash, URL} | 警告 |
| 域名格式 | 含点号、不含协议头 | 警告 |
| IP 格式 | x.x.x.x 每段 0-255 | 跳过 |
| Hash 格式 | 32/64 位十六进制 | 跳过 |
| 白名单过滤 | 不在 whitelist.txt 中 | 跳过 |
| 去重 | 不重复 (ioc+type) | 跳过 |

## 六、发布前检查清单

- [ ] `python src/ioc_validate.py` 全部通过
- [ ] `RELEASES.md` 已更新新版本
- [ ] `CHANGELOG-*.json` 已生成
- [ ] `index.json` SHA256 一致
- [ ] Git tag 已创建
- [ ] GitHub 推送成功
- [ ] Gitee 推送成功
