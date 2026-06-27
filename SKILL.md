---
name: red-ics
description: >
  面向已授权红队、攻防演练、资产梳理和安全评估场景的企业/机构全链路资产侦察技能。
  从公司名、机构名或域名出发，按阶段完成目标解析、组织侦察、被动 OSINT、扩展资产发现、
  主动探测、资产确权、去重汇总和结构化报告生成。默认先完成可公开验证的被动收集；
  当用户明确说明已授权主动探测范围、时间窗口或要求完整全链路执行时，继续执行端口扫描、
  Host 碰撞、Bucket 枚举等主动阶段，并记录范围、速率和证据。
metadata:
  tags: "recon,osint,asset-discovery,subdomain,port-scan,org-recon,ICP,FOFA,WHOIS"
  category: "offensive-security"
  short-description: "企业/机构全链路资产侦察"
---

# red-ics

执行企业/机构全链路资产侦察。目标是从一个公司名、机构名或域名开始，尽可能完整地收集组织、域名、子域名、IP、CIDR、Web、端口、供应商、云服务、APP、小程序、公众号、泄露线索和主动探测结果，并生成可复核的结构化报告。

## 执行规则

- 除非用户明确要求只做部分阶段，否则保持全链路信息收集方向。
- 按阶段顺序执行，因为后续阶段依赖前置阶段产出的种子数据。
- 启动时不要一次性读取所有参考文档；进入对应阶段时再读取相关文档。
- 所有中间产物写入 `output/`，阶段日志写入 `output/logs/`。
- 每个阶段结束后进行去重、归一化和可信度标记，再把标准化结果传递给下一阶段。
- 缺失工具、网络受限、API Key 不存在、分支被跳过时，必须写入日志和最终报告，不要静默忽略。
- 不执行漏洞利用、凭据使用、破坏性测试、权限提升、持久化、数据导出等行为；只记录暴露迹象和可复核证据。

## 授权与范围控制

根据用户输入选择最强适用模式：

1. **全链路授权模式**：用户说明已经授权、要求完整全链路收集、提供演练范围，或明确要求红队/攻防前期侦察时使用。先执行被动阶段，再在授权范围内执行主动阶段。
2. **被动优先模式**：授权或主动范围不清楚时使用。先完成组织侦察、被动 OSINT、扩展公开资产、归一化和报告草稿；进入主动探测前，向用户确认授权范围和时间窗口。
3. **补充采集模式**：用户提供已有资产清单、历史报告或阶段产物时使用。在已有数据基础上继续联网收集、交叉核验、补齐缺口，并生成更新后的报告。

进入主动探测前，确认或从用户请求中推断以下字段：

- 目标名称、域名或机构名
- 授权域名、IP 或 CIDR 范围
- 是否允许主动探测
- 探测时间窗口或速率约束
- 输出路径，默认使用 `output/`

如果用户明确要求完整全链路执行，但部分字段缺失，使用保守默认值继续推进：主动检查保持低速、限定在已识别且可归属的范围内，并将假设写入 `output/logs/scope.log`。

## 参考文档读取规则

只在对应阶段读取必要参考文档：

- 企业组织侦察：读取 `references/ORG-RECON.md`。
- 政府或事业单位组织侦察：读取 `references/ORG-RECON-GOV.md`。
- 被动 OSINT、搜索引擎、WHOIS、ASN/CIDR、FOFA/Hunter/Quake、SSL SAN、被动 CDN 源站线索：读取 `references/OSINT-INFO.md`。
- APP、小程序、公众号、安装包、公开接口、硬编码端点发现：读取 `references/EXTENDED-ASSETS.md`。
- 已授权主动 DNS 枚举、端口扫描、Host 碰撞、Bucket 枚举、服务指纹识别：读取 `references/Active Recon.md`。
- 最终报告模板和章节要求：读取 `references/Report.md`。

参考文档里的命令示例需要结合当前系统、可用工具和授权范围调整。优先使用已配置的 MCP 工具和本地已安装工具。外部账号、API Key 或工具缺失时，跳过对应分支并记录缺口。

## 目录结构

本技能按 opencode 兼容结构组织：

```text
SKILL.md / skill.md    核心规则文件，包含触发规则和调用说明
scripts/               脚本模块目录
references/            阶段参考文档，按需加载
examples/              典型调用示例，按场景参考
config.json            默认参数、阶段名、状态枚举和 Excel 模板列配置
output/                运行产物目录
```

当前仓库保留 `SKILL.md` 作为核心规则文件，以兼容 Codex 校验流程；如果 opencode 运行器严格要求小写 `skill.md`，发布时应保持两者内容一致或按运行器要求做大小写迁移，避免维护两份不同规则。

## 配置文件

- `config.json` 保存默认输出目录、执行模式、资产状态、可信度、阶段名和 `assets_summary.xlsx` 表头。
- 初始化脚本默认读取 `config.json`；需要指定其他配置时使用 `python scripts/init_output.py --config <配置文件>`。
- 修改 Excel 汇总列名时，优先改 `config.json` 的 `xlsx_template.columns`，不要直接改脚本常量。

## 示例文件

按需要读取 `examples/`：

- 用户明确授权并要求完整执行时，参考 `examples/authorized-full-chain.md`。
- 用户要求先收集或不扫描时，参考 `examples/passive-first.md`。
- 用户提供已有数据并需要补充采集、核验和报告时，参考 `examples/supplement-existing-data.md`。

## 输出契约

创建或更新以下目录结构：

```text
output/
  Report.md
  scope.json
  company_info.json
  related_orgs.csv
  domains_seed.txt
  domains_all.txt
  subdomains_passive.txt
  subdomains_active.txt
  subdomains_all.txt
  ips_passive.txt
  ips_active.txt
  ips_all.txt
  cidrs_all.txt
  urls_web.txt
  ports_open.csv
  host_collision.csv
  buckets_public.csv
  sensitive_files.txt
  credentials_found.json
  internal_hosts.txt
  vendors_partners.csv
  cloud_services.csv
  evidence_index.csv
  assets_summary.xlsx
  logs/
    scope.log
    phase0_prepare.log
    phase1_org_recon.log
    phase2_passive_osint.log
    phase3_extended_assets.log
    phase4_active_recon.log
    phase5_report.log
```

如果某个阶段没有发现结果，也要创建对应文件，并写入空表头或 `NO_FINDINGS` 标记，避免后续阶段无法判断是“无结果”还是“未执行”。

## 字段规范

- 资产状态使用 `confirmed`、`suspected`、`rejected` 三类；默认新发现资产为 `suspected`，完成确权后再改为 `confirmed`。
- 可信度使用 `high`、`medium`、`low` 三档；不要混用百分比、中文描述或自由文本。
- 阶段名固定为 `phase0_prepare`、`phase1_org_recon`、`phase2_passive_osint`、`phase3_extended_assets`、`phase4_active_recon`、`phase5_report`。
- `evidence_index.csv` 作为证据总索引，字段固定为 `artifact,item,source,evidence,confidence,phase`。
- `assets_summary.xlsx` 作为人工汇总模板，首行字段固定为：组织、域名、子域名、IP、CIDR、Web、端口、供应商、云服务、APP、小程序、公众号、泄露线索、主动探测。
- 任何进入最终报告的关键资产，都要能在 `evidence_index.csv` 中找到来源或说明缺口。

## 辅助脚本

- `scripts/init_output.py`：用于初始化 `output/` 目录、标准产物文件、CSV 表头、空 JSON 文件、`assets_summary.xlsx` 汇总模板和阶段日志。
- `scripts/ipsearch_mcp_plan.py`：用于为 IPSearch-MCP 生成固定调用计划；IPv4 走 `ip_lookup`，单位名称走多组 `keyword_lookup`，只输出计划，不读取 `ip.db`，不替代 MCP 查询。
- 默认运行方式：`python scripts/init_output.py --config config.json --output output --target "<目标>" --mode <authorized|passive-first|supplement|unknown>`。
- 脚本默认不覆盖已有文件；只有明确需要重建空产物时才使用 `--force`。
- 验证脚本计划但不落盘时，使用 `--dry-run`。
- 如果脚本不可用，按“输出契约”手动创建同样的目录和文件。

## 执行流程

### 阶段 0：准备范围

输入：用户请求、目标名称或域名、授权描述、本地环境。

动作：

- 判断目标类型：企业、政府/事业单位、纯域名目标或混合目标。
- 提取已知域名、公司别名、机构名称、地区、品牌、产品和种子关键词。
- 如果 Python 可用，优先运行 `python scripts/init_output.py --output output --target "<目标>" --mode <模式>` 初始化产物骨架。
- 如果无法运行脚本，则手动创建 `output/`、`output/logs/`、`scope.json` 和 `logs/scope.log`。
- 检查可用 MCP Server、本地工具、环境变量和 API Key。
- 记录不可用依赖和替代路径。

产物：

- `scope.json`
- `domains_seed.txt`
- `logs/scope.log`
- `logs/phase0_prepare.log`

### 阶段 1：组织侦察

输入：公司名、机构名、别名、目标类型。

动作：

- 企业目标读取 `references/ORG-RECON.md`。
- 政府或事业单位目标读取 `references/ORG-RECON-GOV.md`。
- 收集工商/机构基础信息、股权或行政关系、ICP备案、品牌产品名、采购招标线索、供应商、云服务商和关联域名。
- 为每个关联实体和域名标记可信度。

产物：

- `company_info.json`
- `related_orgs.csv`
- `vendors_partners.csv`
- `cloud_services.csv`
- 更新后的 `domains_seed.txt`
- `logs/phase1_org_recon.log`

### 阶段 2：被动 OSINT

输入：`domains_seed.txt`、组织名称、别名、ICP备案、供应商名称。

动作：

- 读取 `references/OSINT-INFO.md`。
- 收集 WHOIS、搜索引擎、ASN/CIDR、空间搜索引擎、SSL 证书 SAN、历史 DNS、公开 URL、被动 CDN 源站线索。
- 仅在已配置且凭据可用时使用 FOFA/Hunter/Quake。
- 搜索引擎和第三方索引结果视为被动数据；被动模式下不要直接探测目标主机。
- 区分已确认资产和疑似资产。

产物：

- `domains_all.txt`
- `subdomains_passive.txt`
- `ips_passive.txt`
- `cidrs_all.txt`
- `urls_web.txt`
- `sensitive_files.txt`
- `internal_hosts.txt`
- 更新后的 `evidence_index.csv`
- `logs/phase2_passive_osint.log`

### 阶段 3：扩展资产

输入：组织名称、品牌、产品、公众号、小程序、APP 名称、前序阶段发现的域名。

动作：

- 读取 `references/EXTENDED-ASSETS.md`。
- 发现小程序、公众号、移动 APP、包名、应用商店元数据、公开 API 端点、内嵌域名和公开配置线索。
- 不绕过认证、不解密受保护数据、不使用发现的凭据。
- 只记录与资产归属判断有关的端点、包名、域名和配置证据。

产物：

- `credentials_found.json`
- 更新后的 `urls_web.txt`
- 更新后的 `domains_all.txt`
- 更新后的 `internal_hosts.txt`
- 更新后的 `evidence_index.csv`
- `logs/phase3_extended_assets.log`

### 阶段 4：已授权主动侦察

输入：主动授权范围、`subdomains_passive.txt`、`ips_passive.txt`、`cidrs_all.txt`、`domains_all.txt`。

进入条件：

- 仅在全链路授权模式下，或用户明确确认后进入本阶段。
- 主动探测必须限制在授权域名、IP 或 CIDR 范围内。
- 设置速率限制，并记录命令、时间戳、目标和结果。

动作：

- 读取 `references/Active Recon.md`。
- 执行范围内 DNS 枚举、存活检查、端口/服务发现、Web 指纹识别、CDN 源站验证、Host 碰撞检查和对象存储暴露检查。
- 优先选择低影响的发现和指纹识别方法。
- 如果出现错误、限速、WAF 拦截、响应不稳定或范围不明确，降低速率、缩小范围或停止对应分支，并记录原因。

产物：

- `subdomains_active.txt`
- `ips_active.txt`
- `ports_open.csv`
- `host_collision.csv`
- `buckets_public.csv`
- 更新后的 `subdomains_all.txt`
- 更新后的 `ips_all.txt`
- 更新后的 `urls_web.txt`
- 更新后的 `evidence_index.csv`
- `logs/phase4_active_recon.log`

### 阶段 5：归一化、确权与报告

输入：所有阶段产物。

动作：

- 合并被动和主动资产。
- 对域名、子域名、IP、URL、CIDR、供应商和证据记录去重。
- 至少通过一个可靠信号确认资产归属，例如 ICP、证书 SAN、WHOIS 组织、官网引用、采购记录、ASN 归属、APP 元数据或一致的品牌特征。
- 无法确认归属的记录标记为 `suspected`，不要标记为 `confirmed`。
- 读取 `references/Report.md` 并生成 `output/Report.md`。
- 在报告中写入跳过分支、缺失依赖、执行假设和不确定性。

产物：

- `domains_all.txt`
- `subdomains_all.txt`
- `ips_all.txt`
- `evidence_index.csv`
- `Report.md`
- `logs/phase5_report.log`

## 失败处理

- MCP Server 缺失：优先尝试本地工具，其次使用公开来源或人工检索方式，仍不可用则跳过并记录。
- API Key 缺失：跳过对应数据源，继续使用其他来源。
- 网络受限：记录受限命令或来源，继续使用本地或已收集产物。
- 无结果：创建对应产物并写入 `NO_FINDINGS`。
- 主动探测前范围不清：完成被动阶段后，向用户确认主动范围。
- 主动探测异常：降低速率、缩小范围或停止对应分支，并记录原因。

## 批量目标

多个目标必须使用隔离输出目录：

```text
output/
  target-a/
  target-b/
```

不要混用不同目标的资产。只有在关系被明确确认后，才允许生成跨目标关联汇总。

## 完成标准

满足以下条件才算执行完成：

- 所有适用阶段都已经产生产物，或写明跳过原因。
- 被动发现和主动发现先分离保存，再合并为最终标准化文件。
- 无法确认归属的资产已明确标记。
- `output/Report.md` 已生成，并能追溯到支撑产物。
- 缺失工具、API Key、网络阻断和执行假设都已写入报告。
