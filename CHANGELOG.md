# v2.0.0 核心重构

## 📌 一句话总结

从 v1.x「用户操作手册」升级为 v2.0「Agent 执行规则书」—— 新增授权模式控制、输出契约、脚本化工具和配置文件，让 AI Agent 能精确无歧义地执行全链路资产侦察。

---

## 🔧 SKILL.md 核心重构（316 行 → 从简版指南变为完整规则书）

### 新增三模式授权控制
| 模式 | 说明 |
|------|------|
| `authorized` | 已授权全链路执行，先被动→再主动探测 |
| `passive-first` | 授权不明确时先完成被动收集，主动阶段前向用户确认 |
| `supplement` | 已有历史数据基础上继续联网补充、交叉核验 |

### 新增 Phase 0：准备范围
- 目标类型判断（企业/政府/纯域名）
- 种子关键词提取
- `init_output.py` 自动初始化产物骨架
- MCP 依赖检查与缺口记录

### 输出契约扩展（15 文件 → 19+ 文件）
新增：`scope.json`、`related_orgs.csv`、`domains_seed.txt`、`buckets_public.csv`、`evidence_index.csv`、`assets_summary.xlsx`
- 被动/主动产物分离保存（`subdomains_passive.txt` / `subdomains_active.txt` 等）
- 每个阶段产生产物或写入 `NO_FINDINGS` 标记

### 字段规范
- 资产状态：`confirmed` / `suspected` / `rejected`
- 可信度：`high` / `medium` / `low`
- 阶段名固定为 `phase0_prepare` 到 `phase5_report`
- `evidence_index.csv` 作为审计追踪总索引

### 批量目标
多目标使用隔离输出目录 `output/target-a/`、`output/target-b/`，禁止混用资产。

### 完成标准
6 条硬性检查：所有阶段产物齐全 → 被动/主动分离 → 归属确认 → 报告可追溯 → 缺失记录 → 假设写入。

---

## ➕ 新增文件

| 文件 | 用途 |
|------|------|
| `config.json` | 集中管理默认输出路径、执行模式、资产状态、可信度等级、阶段名称和 `assets_summary.xlsx` 表头字段 |
| `scripts/init_output.py` | 自动初始化 `output/` 目录骨架：CSV 表头、JSON 空文件、`scope.json`、`Report.md` stub、`assets_summary.xlsx` 模板 |
| `scripts/ipsearch_mcp_plan.py` | 为 IPSearch-MCP 生成固定调用计划：IPv4 走 `ip_lookup`、单位名称走多组 `keyword_lookup`（拼音/英文关键词策略），只输出计划不直接读 ip.db |
| `examples/authorized-full-chain.md` | 完整授权全链路执行示例 |
| `examples/passive-first.md` | 授权不明确时被动优先示例 |
| `examples/supplement-existing-data.md` | 已有数据补充采集示例 |
| `.gitignore` | 排除 `output/` 运行时产物和 `__pycache__/` |

---

## 🔍 与 v1.x（GitHub 原版）详细差异

### SKILL.md
- **描述元数据**：从泛指「资产侦察」改为明确「面向已授权红队/攻防演练/资产梳理」
- **执行规则**：新增 7 条强制规则（阶段顺序、产物管理、依赖缺失记录等）
- **授权与范围控制**：v1.x 无授权分级 → v2.0 三模式 + 7 个范围字段推断
- **参考文档加载**：v1.x 无加载策略 → v2.0 按阶段按需加载，不一次性读取
- **输出路径**：v1.x 10 个 log 文件 → v2.0 19+ 产物 + 7 个阶段 log + 被动/主动分离

### references/ 参考文档
- **ORG-RECON.md** (+20 行)：新增输出产物明确要求和可信度标记说明
- **ORG-RECON-GOV.md** (+20 行)：新增输出产物明确要求
- **OSINT-INFO.md** (+175 行)：新增 FOFA icon 哈希搜索语法、crt.sh 精确匹配模式、搜索引擎结果去重策略
- **Active Recon.md** (+46 行)：新增 nmap 时序模板参数（-T2/-T3/-T4 用途说明）、httpx 内容过滤参数
- **Report.md** (+12 行)：修复 `{{ }}` 变量名为下划线格式

### 新增脚本
- `init_output.py`：254 行，含 xlsx 模板生成（纯 XML/ZIP 格式，无外部依赖，openpyxl 可选）
- `ipsearch_mcp_plan.py`：275 行，含中文机构名 → 拼音/英文关键词转换策略，支持 27 个省级行政区 + 40 个机构类型词

---

## 📦 安装升级

```bash
# 1. 拉取最新
cd ~/.config/opencode/skills/red-ICS
git pull origin main

# 2. 验证新增文件
ls scripts/ examples/ config.json
```

---

## ⚠ 破坏性变更

- **SKILL.md 文件名**：从 `skills.md` 改为 `SKILL.md`（大写），保持与 opencode/codex 兼容。如果运行器要求小写 `skill.md`，发布时应保持两份一致内容。
- **输出目录结构**：v2.0 产物文件名与 v1.x 不完全兼容，建议为新目标使用新输出目录。

---

**Full Changelog**: https://github.com/ctfd3219/red-ICS/commits/v2.0.0
