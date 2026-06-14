---
name: red-ICS
description: >
  企业资产侦察技能包。从公司名出发，全自动完成 OSINT 被动收集 → 组织侦察
  → 主动探测 → 资产报告生成的资产侦察流水线。覆盖股权穿透、ICP备案、
  空间搜索引擎、子域名枚举、端口扫描、CDN穿透、APP反编译、Host碰撞等。
metadata:
  tags: "recon,osint,asset-discovery,subdomain,port-scan,org-recon,ICP,FOFA,WHOIS"
  category: "offensive-security"
---

# red-ICS — 企业资产侦察技能包

> **一句话描述**：从公司名出发，全自动完成 OSINT 被动收集 → 组织侦察 → 主动探测 → 资产报告生成的资产侦察流水线。
> **核心理念**：**消灭信息收集中的机械重复操作** — 你只需输入一个公司名，其余自动完成,减少信息收集机械式的重复劳动，提升效率和覆盖率。

---

## 一、这个技能做什么

| 阶段 | 内容 | 参考文档 |
|------|------|---------|
| ① 组织侦察 | 股权穿透、ICP备案、采购招标、品牌/产品名、SSL证书、云服务识别 | `ORG-RECON.md` / `ORG-RECON-GOV.md` |
| ② OSINT 被动收集 | WHOIS、搜索引擎 Dork、ASN/CIDR、空间搜索引擎、SSL证书SAN、CDN穿透 | `OSINT-INFO.md` |
| ③ 扩展资产 | 小程序/公众号/APP 发现与反编译、硬编码凭据提取 | `EXTENDED-ASSETS.md` |
| ④ 主动探测 | DNS爆破、端口扫描、CDN穿透、Host碰撞、对象存储枚举 | `Active Recon.md` |
| ⑤ 报告输出 | 汇总全部数据，生成结构化侦察报告 | `Report.md` |

**核心价值**：原本需要手动操作 10+ 个平台、执行 50+ 条命令、人工整理数小时的机械工作，由技能自动编排完成。

```
可以通过以下方式变相实现批量：
并行 Task Agent — 同时启动多个 red-ICS，每个处理一个目标
串行执行 — 依次提供多个目标名，逐个完成侦察
手动分组 — 将股权穿透出的子公司作为独立目标继续跑
如果你想批量跑多个目标，告诉我目标列表，我可以并行调度多个 agent 同时进行。
```

---

## 二、怎么用

### 2.1 前置条件

使用前请确认以下 MCP Server 已安装并配置（详见第三章）：

- `kali-mcp`（WHOIS 查询，可选，配合使用最佳）
- `IPSearch-MCP`（IP 归属反查，必需）
- `FOFA-MCP`（空间搜索引擎，需账号 Key）

### 2.2 使用方式

在对话中直接输入目标，例如：

```
帮我收集 XXX科技有限公司 的资产信息
```

```
对 example.com 做一次完整的资产侦察
```

```
对 XXX市XXX局 做红队前期侦察（政府单位）
```

```
经过授权，对 XXX市XXX局 做一次完整的信息收集
```

技能会根据目标性质自动判断使用企业版或政府版流程。

### 2.3 执行流程

```
用户输入目标（公司名/域名）
    │
    ├── [Step 1] 组织侦察 (ORG-RECON)
    │     ├── 股权穿透 → 控股子公司 / 参股公司 / 同一法人关联
    │     ├── ICP 备案 → 主域名 + 所有备案域名
    │     ├── 品牌/产品名收集 → 关联域名推测
    │     ├── 采购招标挖掘 → 内部系统名 / 供应商
    │     └── SSL 证书 / 云服务识别
    │
    ├── [Step 2] OSINT 被动收集 (OSINT-INFO)
    │     ├── WHOIS → 注册信息 + 关联域名
    │     ├── 搜索引擎 Dork → 子域名 + URL + 敏感文件 + 社工信息
    │     ├── ASN + IPSearch → CIDR 段
    │     ├── 空间搜索引擎 (FOFA/Hunter/Quake) → IP/端口/URL
    │     ├── SSL 证书 SAN → 子域名发现
    │     └── CDN 穿透 → 真实源站 IP
    │
    ├── [Step 3] 扩展资产 (EXTENDED-ASSETS)
    │     ├── 小程序 / 公众号收集
    │     └── APP 反编译 → API 端点 + 硬编码凭据
    │
    ├── [Step 4] 主动探测 (Active Recon)
    │     ├── DNS 爆破 → 子域名枚举
    │     ├── 端口扫描 → 开放端口 + 服务指纹
    │     ├── Host 碰撞 → 隐藏站点发现
    │     └── Bucket 枚举 → 对象存储公开探测
    │
    └── [Output] 报告输出 (Report.md)
          └── 填入所有收集数据 → 写入 /output/ 目录
```

---

## 三、MCP Server 安装与配置

> **安装目录**：所有 MCP Server 安装在 opencode skills 目录下：
> `~/.config/opencode/skills/`

### 3.1 IPSearch-MCP（必需）

**作用**：通过 `ip.db` 反查组织名对应的 IP 段 (CIDR)。

**Release 地址**：`https://github.com/SleepingBag945/IPSearch-MCP/releases/tag/1`

> Release 提供了打包好的各平台可执行文件和 ip.db 压缩包（`IP.zip`），无需 git clone 和 pip install。

**Release 文件清单**：

| 平台 | 可执行文件 | 下载地址 |
|------|-----------|---------|
| Windows x64 | `IPSearch-windows-amd64.exe` | `https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-windows-amd64.exe` |
| macOS Intel | `IPSearch-darwin-amd64` | `https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-darwin-amd64` |
| macOS Apple Silicon | `IPSearch-darwin-arm64` | `https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-darwin-arm64` |
| Linux x86_64 | `IPSearch-linux-amd64` | `https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-linux-amd64` |
| Linux ARM64 | `IPSearch-linux-arm64` | `https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-linux-arm64` |
| ip.db 压缩包 (通用) | `IP.zip` | `https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IP.zip` |

**自动安装**（技能启动时自动检测并执行）：

技能启动时自动检测 `~/.config/opencode/skills/ipsearch-mcp/` 目录下是否存在对应平台的可执行文件和 `ip.db`。若缺失，则按以下步骤自动下载：

```bash
# === Step 0: 检测操作系统与架构 ===
# 自动获取 OS 类型和 CPU 架构，匹配对应的可执行文件名

# === Step 1: 创建安装目录 ===
# Windows:
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills\ipsearch-mcp"
# macOS/Linux:
mkdir -p ~/.config/opencode/skills/ipsearch-mcp

# === Step 2: 下载对应平台的可执行文件 ===

# —— Windows x64 ——
Invoke-WebRequest `
  -Uri "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-windows-amd64.exe" `
  -OutFile "$env:USERPROFILE\.config\opencode\skills\ipsearch-mcp\IPSearch-windows-amd64.exe"

# —— macOS Intel (darwin-amd64) ——
curl -L -o ~/.config/opencode/skills/ipsearch-mcp/IPSearch-darwin-amd64 \
  "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-darwin-amd64"
chmod +x ~/.config/opencode/skills/ipsearch-mcp/IPSearch-darwin-amd64

# —— macOS Apple Silicon (darwin-arm64) ——
curl -L -o ~/.config/opencode/skills/ipsearch-mcp/IPSearch-darwin-arm64 \
  "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-darwin-arm64"
chmod +x ~/.config/opencode/skills/ipsearch-mcp/IPSearch-darwin-arm64

# —— Linux x86_64 ——
curl -L -o ~/.config/opencode/skills/ipsearch-mcp/IPSearch-linux-amd64 \
  "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-linux-amd64"
chmod +x ~/.config/opencode/skills/ipsearch-mcp/IPSearch-linux-amd64

# —— Linux ARM64 ——
curl -L -o ~/.config/opencode/skills/ipsearch-mcp/IPSearch-linux-arm64 \
  "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IPSearch-linux-arm64"
chmod +x ~/.config/opencode/skills/ipsearch-mcp/IPSearch-linux-arm64

# === Step 3: 下载 ip.db 压缩包 (IP.zip, ~81MB) ===

# Windows:
Invoke-WebRequest `
  -Uri "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IP.zip" `
  -OutFile "$env:USERPROFILE\.config\opencode\skills\ipsearch-mcp\IP.zip"

# macOS/Linux:
curl -L -o ~/.config/opencode/skills/ipsearch-mcp/IP.zip \
  "https://github.com/SleepingBag945/IPSearch-MCP/releases/download/1/IP.zip"

# === Step 4: 解压 IP.zip → 释放 ip.db 到同目录 ===

# Windows:
Expand-Archive -LiteralPath "$env:USERPROFILE\.config\opencode\skills\red-ICS\ipsearch-mcp\IP.zip" `
  -DestinationPath "$env:USERPROFILE\.config\opencode\skills\red-ICS\ipsearch-mcp"

# macOS/Linux:
unzip -o ~/.config/opencode/skills/red-ICS/ipsearch-mcp/IP.zip -d ~/.config/opencode/skills/red-ICS/ipsearch-mcp/

# === Step 5: 清理压缩包 ===
# Windows:
Remove-Item -LiteralPath "$env:USERPROFILE\.config\opencode\skills\red-ICS\ipsearch-mcp\IP.zip"
# macOS/Linux:
rm -f ~/.config/opencode/skills/red-ICS/ipsearch-mcp/IP.zip
```

**安装后目录结构**：

```
~/.config/opencode/red-ICS/skills/ipsearch-mcp/
├── IPSearch-windows-amd64.exe    ← Windows 可执行文件
├── IPSearch-darwin-amd64         ← macOS Intel 可执行文件
├── IPSearch-darwin-arm64         ← macOS Apple Silicon 可执行文件
├── IPSearch-linux-amd64          ← Linux x86_64 可执行文件
├── IPSearch-linux-arm64          ← Linux ARM64 可执行文件
└── ip.db                         ← IP 归属数据库 (解压自 IP.zip)
```

> 实际目录中只会有**当前操作系统对应**的一个可执行文件 + `ip.db`。

**缺失时的处理**：

> 若 `ip.db` 下载失败或未找到，技能会提示并跳过该步骤：
> ```
> [WARNING] ip.db 未找到或下载失败。
>   请确保 ip.db 在以下路径中:
>   ~/.config/opencode/skills/red-ICS/ipsearch-mcp/ip.db
> 跳过 Step 2.3 ASN/IPSearch 步骤，继续后续流程。
> ```

### 3.2 FOFA-MCP（需配置账号）

**作用**：通过 FOFA 空间搜索引擎获取 IP、端口、URL 等资产。

**安装方式**：通过 `npx -y fofa-mcp-server` 自动拉取（首次运行自动下载到 npm 缓存），无需手动安装。

**账号配置**：

使用前必须在 opencode 的 MCP 配置中设置 FOFA 账号信息。编辑 `~/.config/opencode/opencode.json`：

```json
{
  "mcp": {
    "fofa": {
      "type": "local",
      "command": ["npx", "-y", "fofa-mcp-server"],
      "enabled": true,
      "env": {
        "FOFA_EMAIL": "your@email.com",
        "FOFA_KEY": "your-api-key"
      }
    }
  }
}
```

> **FOFA Key 获取**：登录 https://fofa.info → 个人中心 → API 管理 → 复制 Email 和 API Key。

**未配置时的处理**：

> 若 `FOFA_EMAIL` 或 `FOFA_KEY` 为空，技能会停止并提示先配置：
> ```
> [STOP] FOFA 未配置账号信息，空间搜索引擎步骤需要 FOFA API。
> 请在 opencode.json 的 mcp.fofa.env 中配置:
>   FOFA_EMAIL  → FOFA 注册邮箱
>   FOFA_KEY    → FOFA API Key (个人中心获取)
> 配置完成后重新执行。
> ```
>
> 没有 FOFA 账号时，Step 2.4 空间搜索引擎步骤跳过，其余流程继续。

### 3.3 kali-mcp（可选）

**作用**：提供 `whois` 命令用于域名 WHOIS 查询。

若不可用，回退使用在线 WHOIS 平台或跳过 WHOIS 步骤。

---

## 四、输出路径

```
项目目录/
├── output/                          ← 所有产出物输出到此目录
│   ├── Report.md                    ← 最终侦察报告（模板→填入数据）
│   ├── company_info.json            ← 公司基础信息 + 股权穿透
│   ├── domains_all.txt              ← 全部域名（去重）
│   ├── subdomains_all.txt           ← 全部子域名（去重）
│   ├── ips_all.txt                  ← 全部 IP（去重）
│   ├── cidrs_all.txt                ← 全部 CIDR 段（去重）
│   ├── urls_web.txt                 ← 全部 Web URL
│   ├── ports_open.csv               ← 开放端口清单 (IP,Port,Service,Version)
│   ├── host_collision.csv           ← Host 碰撞命中结果
│   ├── sensitive_files.txt          ← 发现的敏感文件 URL
│   ├── credentials_found.json       ← 硬编码凭据清单
│   ├── internal_hosts.txt           ← 内部域名/IP 泄露
│   ├── vendors_partners.csv         ← 供应商/合作商清单
│   ├── cloud_services.csv           ← 云服务识别结果
│   └── logs/                        ← 各步骤执行日志
│       ├── step1_org_recon.log
│       ├── step2_osint.log
│       ├── step3_extended_assets.log
│       └── step4_active_recon.log
│
├── references/                      ← 参考流程文档（只读）
│   ├── Report.md
│   ├── OSINT-INFO.md
│   ├── ORG-RECON.md
│   ├── ORG-RECON-GOV.md
│   ├── EXTENDED-ASSETS.md
│   └── Active Recon.md
│
└── skills.md                        ← 本文件
```

---

## 五、注意事项

### 5.1 安全合规

| 规则 | 说明 |
|------|------|
| **授权优先** | 仅在已获完整书面授权范围内执行信息收集 |
| **被动优先** | OSINT 阶段全程零痕迹，不向目标发任何请求 |
| **主动需确认** | 进入主动探测前，须二次确认授权范围和探测时间窗口 |
| **速率控制** | 所有主动探测工具必须设置延迟（≥ 500ms），避免 DDoS 效果 |
| **IP 白名单** | 主动探测前操作 IP 需加入甲方白名单 |
| **数据隔离** | 不同目标的资产数据严格隔离，禁止交叉使用 |
| **日志完整** | 所有操作记录时间戳、目标、方法、结果 |
| **禁止利用** | 发现漏洞立即记录，不得在未授权情况下深入利用 |

### 5.2 环境依赖

| 工具 | 用途 | Windows | macOS | Linux |
|------|------|---------|-------|-------|
| Node.js 18+ | MCP Server (npx) 运行 | 系统安装 | 系统安装 | 系统安装 |
| PowerShell / curl | 下载 Release 文件 | 系统自带 | 系统自带 | 系统自带 |
| unzip | 解压 IP.zip | Expand-Archive (自带) | 系统自带 | 系统自带 (`apt install unzip`) |
| IPSearch-MCP + ip.db | IP 归属反查 | 自动从 Release 下载 (~89MB) |
| FOFA-MCP + Key | 空间搜索 | npx 自动拉取 + 手动配置 Key |

### 5.3 常见问题

| 问题 | 处理方式 |
|------|---------|
| FOFA 未配置 Key | 空间搜索步骤跳过，其余流程继续 |
| ip.db 未找到 | ASN/IP 归属步骤跳过，提示手动放置 |
| 目标无 ICP 备案 | 跳过备案查询，使用搜索引擎获取域名 |
| 目标使用 CDN | 自动触发 6 种 CDN 穿透方法 |
| 主动探测被 WAF 拦截 | 自动降低速率，切换代理 |
| 无公开采购招标记录 | 跳过招标分析，不影响后续流程 |

### 5.4 目标类型自动判断

| 输入特征 | 判断类型 | 使用流程 |
|---------|---------|---------|
| `.gov.cn` / 政府/局/委/厅/办 | 政府/事业单位 | ORG-RECON-GOV |
| 有限公司/科技/股份 + `.com/.cn` | 企业 | ORG-RECON |
| 只有域名，无公司名 | 通用 | 跳过组织侦察，直接从 OSINT 开始 |

---

## 六、快速参考

```
输入: "帮我收集 XX科技有限公司 的资产信息"

技能自动执行:
  ① 判断目标类型 → 企业
  ② 检查 MCP 依赖 → 自动安装缺失项
  ③ 组织侦察 → 股权/ICP/招标/云服务
  ④ OSINT 被动收集 → WHOIS/搜索引擎/ASN/FOFA/SSL/CDN穿透
  ⑤ 扩展资产 → 小程序/公众号/APP
  ⑥ 主动探测 → DNS爆破/端口扫描/Host碰撞/Bucket枚举
  ⑦ 去重合并 → 写入 Report.md → 产出到 /output/

耗时估算: OSINT 阶段 5-15 分钟 / 主动探测视目标规模 10-60 分钟
```
