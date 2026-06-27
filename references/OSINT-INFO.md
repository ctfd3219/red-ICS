---
name: osint-info
description: >
  OSINT 被动信息收集 — 红队/攻防前期侦察核心模块。
  覆盖 WHOIS、搜索引擎 Google Dork (Bing/Baidu) 子域名+URL+社工信息(ID/手机/学号/工号/用户名/邮箱)、
  ASN+IPSearch CIDR、空间搜索引擎 (FOFA/Hunter/Quake)、SSL证书SAN、CDN穿透 (6种方法)。
  被动阶段不与目标主机直接交互；需要验证时转入授权主动阶段。
metadata:
  tags: "osint,passive,recon,whois,google-dork,asn,cidr,fofa,hunter,quake,ssl,san,cdn-bypass,redteam,social-engineering"
  category: "offensive-security"
  version: "1.0.0"
---

# OSINT-INFO — 被动信息收集

> **核心原则**：被动阶段不向目标主机发送请求；所有数据来自第三方公开源、已授权平台索引或用户已提供材料。
> **适用场景**：红蓝对抗、攻防演练、渗透测试前期侦察。

---

## 一、信息收集流程总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                     OSINT 被动信息收集 6 步链                          │
│                                                                     │
│  [1] WHOIS        → 域名注册信息、注册人、DNS服务器、关联域名           │
│       │                                                             │
│  [2] 搜索引擎      → Bing/Baidu Google Dork 子域名 & URL 收集          │
│       │              + 身份证/手机号/学号/工号/用户名/邮箱等社工信息     │
│       │                                                             │
│  [3] ASN+IPSearch → 出口CIDR、组织IP段归属                            │
│       │                                                             │
│  [4] 空间搜索引擎  → FOFA/Hunter/Quake 被动 IP/端口/URL 发现           │
│       │                                                             │
│  [5] SSL证书SAN   → 证书透明日志、备用DNS名称提取子域名                │
│       │                                                             │
│  [6] CDN穿透      → 真实源站IP发现 (6种方法)                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.1 OSINT 阶段硬性规则

- 本文件只约束 `phase2_passive_osint`：默认不直接访问目标网站、不触发目标业务功能、不对目标 IP/域名做存活探测、端口扫描、Host 头验证或爆破。
- 可以联网查询第三方公开源、搜索引擎、空间搜索引擎、证书透明日志、被动 DNS、WHOIS/ASN 数据库和已配置 MCP；这些查询必须记录来源和查询条件。
- 涉及 `curl https://目标`、`curl -H "Host"`、触发注册/找回邮件、国外 VPS 直接访问、Ping/多地探测、端口验证等动作时，必须转入 `references/Active Recon.md` 的授权主动阶段执行。
- API Key、MCP Server 或第三方平台不可用时，跳过对应来源并记录缺口；不得因为单一来源失败而停止整个 OSINT 阶段。
- 所有输出按 `confirmed`、`suspected`、`rejected` 标记状态；第三方索引命中默认是 `suspected`，至少经过备案、证书、WHOIS/ASN、官网引用、采购公告或多源一致性确认后才可升为 `confirmed`。
- 个人信息、身份证、手机号、邮箱、账号名等只用于暴露面确认和风险提示；最终报告必须脱敏展示，不得用于登录、找回密码、撞库、社工冒用或绕过认证。

### 1.2 输入与输出契约

输入种子来自阶段 1：`domains_seed.txt`、组织全称/简称、ICP备案主体、备案号、子公司/直属单位、供应商、云服务商、APP/小程序/公众号名称。

本阶段必须更新或创建：

```text
subdomains_passive.txt
ips_passive.txt
cidrs_all.txt
urls_web.txt
sensitive_files.txt
internal_hosts.txt
evidence_index.csv
logs/phase2_passive_osint.log
```

`evidence_index.csv` 固定使用 `artifact,item,source,evidence,confidence,phase`；查询语句、资产状态和判断原因写入对应产物或 `logs/phase2_passive_osint.log`。无法确认归属的资产标记为 `suspected`，不能直接并入主动探测范围。

---

## 二、Step 1: WHOIS 查询


> **目标**：获取域名注册信息、注册商、DNS服务器、创建/过期时间，发现关联域名。
> **工具优先级**：kali-mcp (MCP) → 本地 whois 命令 → 在线 WHOIS 平台 → 跳过。

### 2.1 工具调用方式

```
优先级1: MCP Server — kali-mcp
  若已配置 kali-mcp 为 MCP Server，直接调用 whois 命令

优先级2: 本地工具
  bash: whois target.com

优先级3: 在线平台
  whois.aliyun.com / whois.chinaz.com / lookup.icann.org

优先级4: 跳过
  以上均不可用时，跳过本步骤，从 Step 2 开始
```

### 2.2 查询内容

| 字段 | 含义 | 价值 |
|------|------|------|
| Registrant Name / Organization | 注册人/组织 | 关联同组织其他域名 |
| Registrant Email | 注册邮箱 | 反查同邮箱注册的域名 |
| Registrar | 注册商 | 判断域名购买渠道（阿里云/腾讯云/GoDaddy等） |
| Name Servers | DNS服务器 | 判断使用哪家DNS服务商 |
| Creation Date | 创建时间 | 资产存续周期 |
| Expiry Date | 过期时间 | 资产活跃度 |
| Domain Status | 域名状态 | clientTransferProhibited 等 |

### 2.3 查询命令

```bash
# 单域名 WHOIS
whois target.com

# 提取关键信息
whois target.com | grep -iE 'Registrant|Email|Registrar|Name Server|Creation|Expir'

# 批量 WHOIS
for domain in $(cat domains.txt); do
  whois $domain | grep -iE 'Registrant|Email|Registrar|Name Server|Creation|Expir'
done
```

### 2.4 关联发现

```
□ 同一注册邮箱 → 反查该邮箱注册的所有域名 → 关联资产
□ 同一注册组织 → 同一组织名下其他域名
□ 同一DNS服务器 → 使用相同DNS的其他域名
□ 注册商信息 → 域名注册渠道偏好
```

---

## 三、Step 2: 搜索引擎 Google Dork — 子域名 & URL & 社工信息收集

> **目标**：通过搜索引擎高级语法，利用公司名称和域名收集子域名、URL 地址及个人身份信息（身份证、手机号、学号、工号、用户名、邮箱）。
> **核心引擎**：Bing（主）、Baidu（国内必备，覆盖率优于 Google）、Google（参考）。
> **零痕迹**：不直接访问目标，仅利用搜索引擎缓存/索引。

### 3.1 Bing 搜索引擎语法

```
Bing 支持完整的 Google Dork 操作符，是国内资产收集的核心引擎。

操作符速查:
  site:        限定目标域名
  intitle:     搜索网页标题中包含的关键词
  inurl:       搜索URL路径中包含的关键词
  inbody:      搜索网页正文中包含的关键词 (Bing特有)
  filetype:    搜索特定文件类型 (pdf/doc/xls/ppt)
  -            排除关键词
  ""           精确短语匹配
  AND / OR     逻辑与/或
  ()           分组
```

#### 3.1.1 子域名发现语法

```
□ site:target.com                                  — 全量子域名+URL
□ site:target.com -www                             — 排除主站，发现子域
□ site:*.target.com                                — 通配符子域 (Bing支持)
□ site:target.com intitle:"admin"                  — 带管理关键词的子域
□ site:target.com inurl:"login"                    — 带登录路径的子域
□ site:target.com inurl:"api"                      — API子域
□ site:target.com inurl:"dev" OR inurl:"test"      — 开发/测试环境
□ site:target.com inurl:"uat" OR inurl:"staging"   — UAT/预发布环境
□ site:target.com -www -site:www.target.com        — 纯粹的子域枚举
□ site:target.com intitle:"后台"                   — 中文后台入口
□ site:target.com intitle:"管理"                   — 中文管理入口
□ site:target.com intitle:"登录"                   — 中文登录入口
```

#### 3.1.2 敏感文件/路径发现

```
□ site:target.com filetype:pdf                     — PDF文件
□ site:target.com filetype:doc OR filetype:xls     — Office文档
□ site:target.com filetype:sql                     — SQL转储文件
□ site:target.com filetype:log                     — 日志文件
□ site:target.com ext:log                          — 日志文件 (Bing特有)
□ site:target.com filetype:zip OR filetype:tar.gz  — 压缩备份
□ site:target.com filetype:env                    
□ site:target.com filetype:conf OR filetype:cfg    
□ site:target.com inurl:".git"                     — Git泄露
□ site:target.com inurl:"backup" OR inurl:"bak"    — 备份文件
□ site:target.com intitle:"index of"               — 目录浏览
□ site:target.com inurl:"swagger"                  — Swagger文档
□ site:target.com inurl:"actuator"                 — Spring Actuator
□ site:target.com inurl:".env"                     — 环境配置文件
□ site:target.com inurl:"phpinfo"                  — PHP信息泄露
□ site:target.com inurl:"/api/"                    — API端点
□ site:target.com intitle:"Index of /"             — 目录遍历
```

#### 3.1.3 URL地址批量获取

```
□ site:target.com inurl:".php"                     — PHP站点
□ site:target.com inurl:".jsp" OR inurl:".do"      — Java站点
□ site:target.com inurl:".aspx" OR inurl:".ashx"   — .NET站点
□ site:target.com inurl:".action"                  — Struts2站点
□ site:target.com inurl:"/" -inurl:"www"           — 全路径
□ site:target.com inurl:"?id="                     — 动态参数URL
□ site:target.com inurl:"?page="                   — 分页参数URL
```

#### 3.1.4 利用公司名称搜索

```
□ "公司全称" site:target.com                       — 目标站内提及
□ intitle:"公司全称"                               — 页面标题含公司名
□ "公司全称" -site:target.com                      — 外部提及（关联域名）
□ "公司简称" filetype:pdf                          — PDF中含公司名
□ "公司英文名" site:target.com                     — 英文名搜索
□ "品牌名" OR "产品名" site:target.com             — 品牌/产品搜索
```

### 3.2 Baidu 搜索引擎语法

```
Baidu 对国内资产的收录覆盖率最高，部分语法与 Google/Bing 略有差异。

操作符速查:
  site:        限定目标域名（注意：不支持通配符）
  intitle:     搜索网页标题中包含的关键词
  inurl:       搜索URL路径中包含的关键词
  filetype:    搜索特定文件类型
  -            排除关键词
  ""           精确短语匹配
  ()           分组 (兼容性较差，尽量用简单组合)
```

#### 3.2.1 子域名发现语法

```
□ site:target.com                                  — 全量子域名+URL
□ site:target.com intitle:管理                     — 管理入口子域
□ site:target.com intitle:后台                     — 后台入口子域
□ site:target.com intitle:登录                     — 登录入口子域
□ site:target.com intitle:系统                     — 业务系统子域
□ site:target.com inurl:admin                      — 管理路径
□ site:target.com inurl:login                      — 登录路径
□ site:target.com inurl:api                        — API端点
□ site:target.com inurl:dev                        — 开发环境
□ site:target.com inurl:test                       — 测试环境
□ site:target.com inurl:uat                        — UAT环境
□ site:target.com inurl:staging                    — 预发布环境
```

#### 3.2.2 敏感文件/路径发现

```
□ site:target.com filetype:pdf                     — PDF文件
□ site:target.com filetype:doc                     — Word文档
□ site:target.com filetype:xls                     — Excel文档
□ site:target.com filetype:sql                     — SQL转储
□ site:target.com filetype:log                     — 日志文件
□ site:target.com filetype:txt                     — 文本文件
□ site:target.com inurl:backup                     — 备份目录
□ site:target.com inurl:bak                        — 备份文件
□ site:target.com "index of"                       — 目录浏览
□ site:target.com inurl:swagger                    — Swagger文档
□ site:target.com env                              — 配置文件
□ site:target.com inurl:.git                       — Git泄露
□ site:target.com config                           — 配置文件
□ site:target.com upload                           — 上传目录
```

#### 3.2.3 利用公司名称搜索

```
□ intitle:公司全称                                 — 标题含公司全名
□ intitle:公司简称                                 — 标题含简名
□ "公司全称"                                       — 全站搜索公司名
□ "公司简称" filetype:pdf                          — PDF中含公司名
□ 公司英文名 site:target.com                       — 英文名站内搜索
□ "公司产品名" site:target.com                     — 产品名站内搜索
□ "公司电话" site:target.com                       — 电话站内搜索
```

#### 3.2.4 Baidu 特有技巧

```
□ 百度对中文关键词权重高，优先使用中文关键词搜索
□ 公司中文全称/简称/产品名 → 发现关联站点
□ ICP备案号搜索 → site:target.com "京ICP备XXXXXXXX号"
□ 电话/邮箱搜索 → "400-XXX-XXXX" "xxx@target.com" 发现关联站点
□ Baidu不区分大小写，无需大小写变体
□ 使用 site:target.com 时注意 Baidu 只返回该域名下的页面
```

### 3.3 Google 搜索引擎语法

```
Google 在覆盖国内资产方面不如 Bing/Baidu，但语法完备度最高。
适用场景：海外目标 / 国内目标补充搜索。

子域名发现:
  □ site:target.com -inurl:www                     — 排除www子域
  □ site:*.target.com -www                         — 通配子域枚举
  □ site:target.com intitle:"admin"                — 管理入口
  □ site:target.com inurl:"login"                  — 登录入口
  □ site:target.com -site:www.target.com           — 纯粹子域

敏感信息发现:
  □ site:target.com ext:sql | ext:log | ext:env    — 多后缀搜索
  □ site:target.com intitle:"index of"             — 目录浏览
  □ site:target.com inurl:"/.git"                  — Git泄露
  □ site:target.com "password" filetype:txt        — 密码文件
  □ site:target.com "BEGIN RSA PRIVATE KEY"        — 私钥泄露
  □ site:target.com intext:"Index of /" "parent directory"

利用公司名搜索:
  □ site:github.com "target.com" "password"        — GitHub密码泄露
  □ site:github.com "target.com" filename:.env     — GitHub配置文件
  □ site:gitlab.com "target.com"                   — GitLab关联
  □ intitle:"公司全称"                              — 关联站点
```

### 3.4 搜索策略执行流程

```
第一步：公司名搜索 → 获取主域名
  1. Bing: intitle:"公司全称" → 发现官网域名
  2. Baidu: intitle:"公司全称" → 发现官网域名（国内公司优先Baidu）
  3. 交叉验证：两个引擎返回的交集 → 确认为主域名

第二步：主域名搜索 → 获取子域名+URL
  1. Bing: site:target.com → 获取所有收录URL
  2. Baidu: site:target.com → 大量中文内容URL（覆盖率最高）
  3. Google: site:target.com → 补充海外收录

第三步：URL提取 → 子域名分类
  从返回的URL中提取所有子域名 → 去重 → 归类标注

第四步：公司名搜索 → 获取关联域名
  1. Bing: "公司全称" -site:target.com → 外部提及的域名
  2. Baidu: "公司全称" → 关联站点、新闻稿中的域名
  3. 从结果中提取所有域名 → 添加至监控列表
```

### 3.5 高级 Google Dork 组合语法速查表

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 使用场景               │ Bing 语法                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│ 全量子域+URL           │ site:target.com                                     │
│ 排除主站子域           │ site:target.com -www                                │
│ 通配符子域             │ site:*.target.com                                   │
│ 管理后台子域           │ site:target.com intitle:"admin" OR intitle:"管理"    │
│ 登录入口子域           │ site:target.com inurl:"login" OR intitle:"登录"      │
│ API接口子域            │ site:target.com inurl:"api" OR inurl:"/v1/"         │
│ 开发测试环境           │ site:target.com inurl:"dev" OR inurl:"test"          │
│ PDF文件                │ site:target.com filetype:pdf                        │
│ Office文档             │ site:target.com filetype:doc OR filetype:xls        │
│ SQL备份文件            │ site:target.com filetype:sql                        │
│ 日志文件               │ site:target.com filetype:log OR ext:log             │
│ 压缩备份               │ site:target.com filetype:zip OR filetype:tar.gz     │
│ 配置文件               │ site:target.com filetype:env OR filetype:conf       │
│ Git泄露                │ site:target.com inurl:".git" OR inurl:".git/config" │
│ 备份目录               │ site:target.com inurl:"backup" OR inurl:"bak"       │
│ 目录浏览               │ site:target.com intitle:"index of"                  │
│ Swagger文档            │ site:target.com inurl:"swagger"                     │
│ Spring Actuator        │ site:target.com inurl:"actuator"                    │
│ PHP信息泄露            │ site:target.com inurl:"phpinfo" OR intitle:"phpinfo"│
│ 网站根目录文件         │ site:target.com intitle:"Index of /"                 │
│ 公司名站内提及         │ "公司全称" site:target.com                          │
│ 公司名外部提及         │ "公司全称" -site:target.com                         │
│ GitHub源码泄露         │ site:github.com "target.com"                        │
│ GitHub配置文件         │ site:github.com "target.com" filename:.env           │
│ GitHub敏感配置线索     │ site:github.com "target.com" password OR secret      │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.5 个人信息搜索 — 身份证/手机号/学号/工号/用户名

```
目标: 通过搜索引擎发现目标暴露的个人身份信息。
用途: 仅用于暴露面确认、账号命名规律分析、资产归属辅助判断和报告风险提示；不得触发登录尝试、账户恢复流程或冒用他人身份。

身份证号码搜索:
  □ site:target.com "身份证"                       — 含身份证关键词的页面
  □ site:target.com "身份证号" filetype:xls        — Excel中的身份证号
  □ site:target.com "身份证号" filetype:pdf        — PDF中的身份证号
  □ site:target.com "身份证" filetype:doc          — Word中的身份证号
  □ site:target.com "公民身份号码"                  — 官方文件惯用语
  □ site:target.com "证件号码" "姓名"              — 表格类数据
  □ site:target.com "身份证" OR "公民身份号码" intitle:"公示"
  □ site:target.com "身份证" site:gov.cn            — 政府公示含身份证

  身份证正则匹配 (提取后验证):
    [1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]

手机号搜索:
  □ site:target.com "手机" OR "手机号" OR "手机号码"
  □ site:target.com "联系电话" "1[3-9]"            — 联系电话中含手机号
  □ site:target.com "联系方式" filetype:xls        — Excel联系方式表
  □ site:target.com "1[3-9]xxxxxxxxx"             — 模糊语法(Bing/Google)
  □ site:target.com intitle:"通讯录"               — 通讯录页面
  □ site:target.com "联系人" "电话"                — 联系人信息
  □ site:target.com "1[3456789]\d{9}"              — 正则思路
  □ site:target.com filetype:csv "电话"            — CSV中的电话

  手机号正则匹配 (提取后验证):
    1[3-9]\d{9}

学号搜索 (教育/培训机构及企业):
  □ site:target.com "学号" filetype:xls            — Excel中的学号表
  □ site:target.com "学号" filetype:csv
  □ site:target.com "学号" "姓名" "班级"           — 学生名单
  □ site:target.com intitle:"成绩" OR intitle:"名单" "学号"
  □ site:target.com "student id" OR "Student ID"   — 英文版学号
  □ site:edu.cn "学号" filetype:xls                — 高校学号泄露
  □ site:edu.cn "奖学金" filetype:xls              — 奖学金公示名单(含学号+姓名)
  □ site:edu.cn "奖学金" filetype:pdf             — 奖学金公示PDF
  □ site:edu.cn "奖学金公示" OR "奖学金名单"       — 综合奖学金公示
  □ site:edu.cn "国家奖学金" filetype:xls          — 国奖公示含身份证号
  □ site:edu.cn "国家励志奖学金" filetype:xls      — 励志奖学金公示
  □ site:edu.cn intitle:"奖学金" filetype:xls      — 标题含奖学金的Excel
  □ site:edu.cn intitle:"公示" "奖学金" "学号"     — 含学号的奖学金公示
  □ site:edu.cn "奖学金评审" OR "奖学金评定"       — 评审名单含详细信息
  □ site:target.com "准考证号" filetype:xls

工号/员工编号搜索:
  □ site:target.com "工号" filetype:xls            — 员工花名册
  □ site:target.com "员工编号" OR "员工工号"
  □ site:target.com "工号" "姓名" "部门"           — 企业通讯录
  □ site:target.com intitle:"通讯录" filetype:xls  — 内部通讯录
  □ site:target.com "employee id" OR "Employee ID"
  □ site:target.com "staff" "name" "id" filetype:csv
  □ site:target.com "人事" OR "HR" "工号" filetype:xls

用户名/账号搜索:
  □ site:target.com "用户名" OR "账号" OR "user"
  □ site:target.com inurl:"member" OR inurl:"user"
  □ site:target.com "@target.com"                  — 邮箱用户名
  □ site:target.com "登录名" OR "login name"
  □ site:linkedin.com "target.com"                 — LinkedIn员工
  □ site:target.com "admin" OR "root" OR "test"    — 默认账号名
  □ site:target.com intitle:"成员列表" OR intitle:"用户列表"

邮箱地址搜索:
  □ site:target.com "@target.com"                  — 企业邮箱收集
  □ site:target.com "邮箱" OR "e-mail" OR "mail" filetype:xls
  □ site:target.com "Email" "Name" filetype:csv    — 邮箱通讯录
  □ site:target.com intext:"@target.com" -www       — 全站邮箱

姓名搜索:
  □ site:target.com "姓 名" filetype:xls           — 花名册/名单
  □ site:target.com intitle:"名单" OR intitle:"花名册"
  □ site:target.com "公示" "姓名" "单位"           — 公示信息
  □ site:target.com "获奖名单" OR "表彰名单"       — 公开名单
  □ site:target.com orgchart OR "组织架构"         — 组织架构图

组合搜索 (多维度关联):
  □ site:target.com "姓名" "电话" filetype:xls     — 全量通讯录
  □ site:target.com "姓名" "身份证" filetype:xls   — 敏感信息表
  □ site:target.com "部门" "姓名" "职位"            — 组织架构
  □ site:target.com intitle:"index of" "xls"       — 目录浏览中的表格
  □ site:target.com filetype:xls intext:"身份证" OR intext:"手机"
```

个人信息处理要求:

```text
- 只记录泄露类型、来源 URL、文件类型、字段样例和影响范围，不在报告中展示完整身份证、手机号、邮箱本地部分、学号/工号全量值。
- 脱敏规则：身份证保留前 6 后 4，手机号保留前 3 后 4，邮箱保留首尾字符和域名，姓名按姓氏或首字脱敏。
- 若发现疑似凭据、Token、Cookie、私钥，不验证、不登录、不下载更多数据；只记录公开暴露位置和最小必要片段。
- OSINT 阶段将疑似凭据线索写入 `sensitive_files.txt` 和 `evidence_index.csv`；进入阶段 3 后再按主控流程汇总到 `credentials_found.json`。
```

#### 3.2.6 个人信息搜索 — 外部平台泄露

```
GitHub/GitLab/Gitee 源码泄露 (搜索代码仓库中的个人数据):
  □ site:github.com "target.com" "password"
  □ site:github.com "target.com" "id_card" OR "身份证"
  □ site:github.com "target.com" filename:.csv "姓名"
  □ site:github.com "target.com" filename:users.json
  □ site:github.com "target.com" "employee" "list"
  □ site:gitee.com "target.com" "手机" OR "电话"
  □ site:gitlab.com "target.com" config

网盘/文库泄露:
  □ site:pan.baidu.com "target.com"
  □ site:wenku.baidu.com "target.com"
  □ site:docs.qq.com "target.com"
  □ site:lanzou.com "target.com"

其他目标源:
  □ site:pastebin.com "target.com" "password"      — 代码粘贴泄露
  □ site:trello.com "target.com"                   — 项目管理看板
  □ site:jira.com "target.com"                     — 问题跟踪系统
  □ site:docs.google.com "target.com"              — 云端文档
```

---

## 四、Step 3: ASN 查询 + IPSearch-MCP — 出口 CIDR

> **目标**：通过 ASN 和 IP 归属数据库，获取目标组织拥有的所有 IP 段 (CIDR)。
> **工具**：IPSearch-MCP (MCP) / BGP.HE.NET API / bgpview.io。

### 4.1 ASN 查询

```bash
# 方法1: BGP.HE.NET — 免费，不需要API Key
# 从IP反查ASN
curl -s "https://api.bgpview.io/ip/{IP}" | jq '.data.asn.asn, .data.asn.name'

# 方法2: 根据ASN号获取所有IPv4/IPv6前缀
curl -s "https://api.bgpview.io/asn/${ASN}/prefixes" | jq -r '.data.ipv4_prefixes[].prefix'
curl -s "https://api.bgpview.io/asn/${ASN}/prefixes" | jq -r '.data.ipv6_prefixes[].prefix'

# 方法3: IPIP.net — 国内ASN准确度更高
curl -s "https://whois.ipip.net/AS{ASN}"

# 方法4: 从域名解析IP反查ASN
whois $(dig +short target.com | head -1) | grep -i origin

# 方法5: 从已有IP段反查组织名
curl -s "https://api.bgpview.io/ip/{IP}" | jq '.data.asn'

# 方法6: 通过组织名搜索关联ASN
curl -s "https://api.bgpview.io/search?query_term={ORG_NAME}&query_type=organizations"
```

### 4.2 IPSearch-MCP — ip.db 反查组织 IP 段

```
硬性流程:
  1. 先检查已配置 MCP Server 是否存在 IPSearch-MCP。
  2. MCP 不存在时，在本机常见工具目录、当前仓库、scripts/、用户工具目录中查找 ipsearch-mcp 和 ip.db。
  3. 本地仍不存在时，尝试从 GitHub 下载或按项目说明安装；下载/安装失败则记录到 phase2_passive_osint.log 并跳过，不阻塞后续 OSINT。
  4. 只要 IPSearch-MCP 可运行，必须通过 AI MCP 工具调用 ip_lookup 或 keyword_lookup。
  5. 禁止自己写 Python 直接读取或解析 ip.db；脚本只能生成调用计划。

调用计划:
  □ IPv4 输入: python scripts/ipsearch_mcp_plan.py --ipv4 <IPv4>
     → 校验 IPv4 合法性后，通过 MCP 调用 ip_lookup。
  □ 单位名称输入: python scripts/ipsearch_mcp_plan.py --unit-name "<单位名称>"
     → 生成多组 keyword_lookup 关键词，必须全部执行，不能因前一次有结果提前停止。

单位名称关键词规则:
  □ 中文名称拼音首字母，例如 浙江第一人民医院 → zjdyrmyy
  □ 英文分词组合，例如 浙江第二人民医院 → zhejiang,second,hospital
  □ 中文拼音分词组合，例如 浙江第一人民医院 → zhejiang,diyi,yiyuan
  □ 地区英文 + 主要拼音，例如 吉林混论机械股份有限公司 → jilin,kunlun
  □ 地区英文 + 主要英文，例如 浙江酒股份有限公司 → zhejiang,wine,ltd
  □ 可补充组合，例如 zhejiang,hospital,first 或 zhejiang,hospital,zjdyrmyy
  □ 禁止使用单独宽泛关键词，例如 zhejiang、gov、hospital、company。

输出内容:
  □ CIDR 格式 IP 段，如 115.238.92.224/28
  □ IP 段名称/描述原文
  □ 中文翻译或归属解释
  □ 国家、状态、最后修改时间等 Whois 字段（如工具返回）
  □ 归属目标组织的原因：直接命中单位名、行政区划+机构类型一致、备案/采购/证书/多源结果互相支撑

后续处理:
  □ 写入 cidrs_all.txt 和 ips_passive.txt，默认标记 suspected。
  □ 只有归属证据充分的 CIDR 才能作为主动阶段候选范围；是否扫描仍需用户授权。
  □ 不在本阶段执行存活探测、端口扫描、Web 指纹识别或旁站发现。
```

---

## 五、Step 4: 空间搜索引擎 — 被动 IP/端口/URL 发现

> **目标**：通过空间搜索引擎 (FOFA/Hunter/Quake)，利用公司名、域名、SSL 证书、ICP 备案号等线索，
> 通过第三方索引获取目标组织的 IP、开放端口和 URL 地址。
> **调用方式**：通过 MCP Server 调用，需在 opencode.json 中配置对应 MCP Server。

### 5.1 FOFA MCP 查询

```
FOFA 是国内资产覆盖率最高的空间搜索引擎，优先使用。

opencode.json 配置:
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

搜索维度:

□ 子域名 → 反查 IP
  domain="target.com"
  输出: 该域名下所有关联的子域名及其解析 IP

□ SSL 证书关联 → 同证书资产
  cert="Company Name"
  cert.subject="Company Name"
  输出: 使用同一 SSL 证书的所有 IP:端口

□ ICP 备案号 → 同备案主体资产
  icp="京ICP备XXXXXXXX号"
  输出: 同一 ICP 备案主体下的所有 IP 和域名

□ 组织名 → 同组织 IP 段
  org="Company Name"
  输出: 该组织名下的所有 IP 段及存活资产

□ 页面特征 → 同指纹资产
  body="特征字符串"
  title="页面标题"
  通过已知网站的页面特征反向搜索，发现使用相同模板/系统的其他资产

□ 端口+服务 → 特定风险资产
  domain="target.com" && port="3306,6379,27017"
  按域名搜索同时过滤特定高危端口

□ JS 文件中的 API/Bucket → 关联云资产
  body="oss-cn-shanghai.aliyuncs.com" && cert="target.com"
  通过 JS 中泄露的 OSS/Bucket URL 反向搜索关联资产

□ Favicon 哈希 → 同源站IP
  icon_hash="{mmh3_hash}"
  通过 favicon 哈希定位使用相同图标的服务器（可穿透CDN）

□ 响应头特征
  header="AliyunOSS" && org="Company Name"
  通过特定响应头发现关联资产

□ 全端口资产搜索
  port="6379" && org="Company Name"
  搜索组织名下开放特定端口的资产
```

### 5.2 Hunter (奇安信) 查询

```
Hunter 对国内资产收录较好，语法与 FOFA 有差异。

搜索语法:
  □ domain.suffix=="target.com"                      — 子域名反查IP
  □ cert.subject=="Company Name"                     — SSL证书关联
  □ icp.number=="京ICP备XXXXXXXX号"                   — ICP备案关联
  □ org=="Company Name"                              — 组织名搜索
  □ header=="AliyunOSS" && org=="Company Name"       — 特定Header+组织
  □ domain.suffix=="target.com" && port==3306        — 域名+端口过滤
  □ web.body=="特征字符串"                            — 页面正文搜索
  □ web.title=="页面标题"                             — 页面标题搜索
  □ ip.port=="80" && domain.suffix=="target.com"     — 特定端口子域
```

### 5.3 Quake (360) 查询

```
Quake 补充覆盖率，语法简洁。

搜索语法:
  □ domain:"target.com"                              — 子域名反查IP
  □ cert:"Company Name"                              — SSL证书关联
  □ icp:"京ICP备XXXXXXXX号"                           — ICP备案关联
  □ org:"Company Name"                               — 组织名搜索
  □ body:"特征字符串"                                 — 页面正文搜索
  □ title:"页面标题"                                  — 页面标题搜索
  □ port:"3306" AND domain:"target.com"              — 端口+域名
```

### 5.4 多源交叉验证策略

```
1. FOFA (主) → 覆盖率高，语法灵活。
2. Hunter (辅) → 与 FOFA 交叉验证，发现 FOFA 未收录资产。
3. Quake (辅) → 第三源补充，辅助降低单源误报。

汇总去重:
  □ 合并 FOFA/Hunter/Quake 结果 → 按 host:port、IP、URL、证书指纹去重
  □ 同一 IP 多端口保留端口维度，不要只按 IP 粗暴合并
  □ CDN、云 WAF、共享主机、对象存储、SaaS 平台必须单独标记服务类型

归属判断:
  □ high: ICP/证书/WHOIS/官网引用/采购公告/多个空间引擎一致支撑
  □ medium: 两个空间引擎一致，或组织名+证书/域名特征一致
  □ low: 仅单一空间引擎命中，或只有页面标题/模板相似
  □ rejected: 明确为第三方 SaaS、CDN 节点、无关模板站或共享托管噪声

导出格式:
  IP | 端口 | URL | 标题 | 证书主体 | 来源引擎 | 查询语句 | 证据 | 状态 | 置信度 | 归属判断
```

---

## 六、Step 5: SSL 证书 SAN — 域名 & 子域名被动发现

> **目标**：通过 SSL 证书的 Subject Alternative Name (SAN) 字段，发现同一证书关联的所有域名和子域名。
> **关键**：SAN 字段包含证书签发时声明的所有备用 DNS 名称，是子域名收集的核心被动来源。

### 6.1 证书透明度日志 (CT Logs)

```
数据源:
  □ crt.sh (优先) — 免费，无需API Key，返回JSON格式
  □ certspotter  — 备用数据源
  □ Censys       — 证书搜索
```

```bash
# === crt.sh 查询 ===

# 1. 查询域名关联的所有证书 (JSON格式)
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | jq -r '.[].name_value' | sort -u

# 2. 子域名字段单独提取
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | jq -r '.[].common_name' | sort -u

# 3. 仅查询未过期的证书
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | \
  jq -r '.[] | select(.not_after > now) | .name_value' | sort -u

# 4. 通配符证书识别 (如 *.target.com)
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | jq -r '.[].name_value' | sort -u | grep '^\*\.'

# 5. 多级域名提取
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | \
  jq -r '.[].name_value' | sort -u | grep -oE '[a-zA-Z0-9._-]+\.'${TARGET}

# 6. 组织名搜索（不限于域名）
curl -s "https://crt.sh/?q=${ORG_NAME}&output=json" | jq -r '.[].name_value' | sort -u

# 7. 提取所有唯一域名
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | \
  jq -r '.[].name_value' | tr '\n' '\n' | sed 's/^\*\.//' | sort -u
```

### 6.2 证书关联域名反查（两步法）

```
原理: 同一SSL证书可能关联了多个域名(子域名/关联域名)，
      通过证书序列号/哈希反查 → 发现隐藏的关联域名。

步骤一: 获取目标域名的所有证书SHA256哈希
  curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | jq -r '.[].sha256' | sort -u

步骤二: 用证书哈希反查所有使用同一证书的域名
  curl -s "https://crt.sh/?q=${CERT_SHA256}&output=json" | jq -r '.[].name_value' | sort -u
  （会返回包括非目标域名的关联域名）

步骤三: 对返回的关联域名进行验证
  □ DNS解析 → 获取IP → 标记是否为真实源站IP
  □ WHOIS查归属 → 确认是否属于同一组织
  □ Ping测试 → 判断是否有CDN
```

### 6.3 SSL 证书字段价值分析

```
证书字段提取与价值:

  □ Subject → Common Name (CN) → 主域名
  □ Subject Alternative Names (SAN) → 所有关联域名 (核心字段)
  □ Issuer → 证书颁发机构 (Let's Encrypt / DigiCert / 阿里云SSL等)
  □ Organization (O) → 组织名 (可与企业信息交叉验证)
  □ Organizational Unit (OU) → 部门/团队信息
  □ not_before / not_after → 证书有效期 → 判断资产活跃度
  □ Serial Number → 证书序列号 (可用于反向关联)

关联分析:
  □ 同一证书的名称列表 → 兄弟域名/子公司域名
  □ 同一 Organization 的不同证书 → 全量子域名
  □ 同一 Issuer 的批量签发 → 批量注册的子域名
```

### 6.4 提取后处理

```
1. 对 name_value 字段按换行符/分隔符拆分 (crt.sh 会用\n分隔多个域名)
2. 去重 → 排序 → 过滤无效域名（*. 通配符保留但标记）
3. 分类标记：子域名 / 关联域名 / 旁站域名
4. 与 Step 2 (搜索引擎) 产出的子域名列表合并去重
5. 高价值子域名筛选:
   grep -E 'admin|api|dev|test|staging|internal|vpn|jenkins|git|wiki' subdomains.txt
   grep -E 'oss|s3|bucket|cdn|static' subdomains.txt  # 云资产
```

---

## 七、Step 6: CDN 穿透 — 真实源站 IP 发现 (6 种方法)

> **目标**：穿透 CDN 防护，获取源站真实 IP 地址。
> **前置判断**：先确认目标是否使用了 CDN。需要直接访问或 Host 头验证时，转入授权主动阶段。

### 7.0 CDN 快速判断

```
方法1: 多地Ping
  □ ping.chinaz.com → 输入域名 → 查看不同地区解析结果
  □ 如果多地Ping返回的IP不一样 → 基本确认使用了CDN

方法2: 命令行判断
  □ nslookup target.com → 返回多个不同网段的IP → 使用了CDN
  □ dig target.com → 观察ANSWER SECTION中的IP数量和分布

方法3: IP归属判断
  □ 解析IP归属地为多个城市/国家 → 确认为CDN节点
  □ 解析IP归属云服务商CDN段 (如阿里云CDN/腾讯云CDN)

关键判断标准:
  □ 解析结果 ≥2个不同IP → 大概率使用了CDN
  □ IP归属地分散在多个城市 → 确认为CDN节点
  □ 单IP或同C段IP → 可能未使用CDN（跳过 CDN 穿透，直接标记该 IP）
```

---

### 7.1 方法一：DNS 历史解析记录

```
原理: 目标在历史上可能未使用CDN，或CDN刚切换期间，
      历史记录中可能保留真实IP。

数据源与命令:

□ SecurityTrails — 域名历史A记录 (需API Key)
  curl -s "https://api.securitytrails.com/v1/history/${TARGET}/dns/a" \
    -H "apikey: YOUR_API_KEY" | jq -r '.records[].values[].ip'

□ VirusTotal — 域名报告中的历史解析IP
  curl -s "https://www.virustotal.com/api/v3/domains/${TARGET}/resolutions?limit=40" \
    -H "x-apikey: YOUR_API_KEY" | jq -r '.data[].attributes.ip_address'

□ 微步在线 (x.threatbook.com) — 域名历史解析 → 最早记录
□ DNSdumpster — 查看历史DNS数据
□ AlienVault OTX — 被动DNS记录
  curl -s "https://otx.alienvault.com/api/v1/indicators/domain/${TARGET}/passive_dns" | \
    jq -r '.passive_dns[].address'

□ ViewDNS.info — 历史IP查询
  curl -s "https://viewdns.info/iphistory/?domain=${TARGET}"

注意事项:
  □ 历史IP可能已失效或被回收
  □ 逐 IP 存活验证属于主动动作：记录为待验证项，转入 Active Recon 后再执行
  □ 关注最早的历史记录 → 最可能为真实IP
  □ 关注DNS切换前后的IP变化
```

---

### 7.2 方法二：邮件头分析

```
原理: 目标网站若有邮件发送功能（注册验证/密码重置/通知），
      发送的邮件源码中可能暴露源站IP。
      发件服务器IP通常不在CDN后面。

步骤一: 邮件头来源限制
  □ 仅分析用户已提供的邮件源码、历史样本或公开邮件头
  □ 不在被动阶段触发注册、找回密码、订阅、联系表单或订单邮件
  □ 如确需触发邮件，必须转入授权主动阶段并记录账号、时间、目标和频率

步骤二: 查看收到的邮件源码
  □ QQ邮箱: 邮件 → 更多 → 查看邮件源码
  □ 163邮箱: 邮件 → 更多 → 查看原文
  □ Gmail: 邮件 → 显示原始邮件
  □ Outlook: 邮件 → 查看 → 查看邮件源

步骤三: 搜索关键词 "Received: from"
  □ 追踪邮件传输路径
  □ 最底部的 "Received: from" 通常是发件服务器IP
  □ 排除知名邮件服务商IP（QQ/163/Gmail等）
  □ 剩余IP → 可能就是源站IP或企业邮件服务器IP

步骤四: 提取并分析IP
  # 提取所有IP地址
  grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' email_header.txt | sort -u

  # 排除内网IP后保留可疑IP
  grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' email_header.txt | \
    grep -v -E '^(127\.|10\.|172\.16\.|192\.168\.)'

邮件头关键字段解读:
  □ Received: from mail.target.com ([真实IP]) by ...
  □ X-Originating-IP: [真实IP]
  □ X-Sender-IP: [真实IP]
  □ X-Mailer: → 邮件发送软件及版本
```

---

### 7.3 方法三：SPF 记录

```
原理: SPF (Sender Policy Framework) 记录指定了哪些服务器有权发送该域名的邮件。
      发件服务器IP通常不挂CDN，直接从SPF记录中获取。

查询命令:
  □ dig TXT target.com | grep spf
  □ nslookup -type=TXT target.com | findstr "spf"
  □ dig TXT target.com +short

SPF记录解析:

  1. ip4: → 直接暴露发件服务器IP
     示例: "v=spf1 ip4:123.123.123.123 -all"
     → 123.123.123.123 就是发件服务器真实IP

  2. ip4:xxx.xxx.xxx.0/24 → IP段
     示例: "v=spf1 ip4:123.123.123.0/24 -all"
     → 整个C段可能都属于目标组织

  3. include: → 第三方邮件服务商
     示例: "v=spf1 include:spf.mail.qq.com -all"
     → 使用腾讯企业邮箱

  4. a: → 指定域名解析IP
     示例: "v=spf1 a:mail.target.com -all"
     → mail.target.com 的解析IP为发件服务器

  5. mx: → 使用MX记录指定的服务器
     示例: "v=spf1 mx -all"
     → MX记录指向的邮件服务器IP

提取命令:
  dig TXT target.com +short | grep -oE 'ip4:[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}[^ ]*'
```

---

### 7.4 方法四：子域名/分站 IP

```
原理: 很多子域名不会配置CDN，解析得到的IP大概率是源站真实IP。
      部分子域名可能共用同一台服务器。

操作流程:
  1. 收集目标所有子域名（从 Step 1-5 汇总）
  2. 优先使用被动 DNS、证书透明日志、空间搜索引擎和历史解析数据获取解析 IP
  3. 不在被动阶段逐个 Ping 或主动解析全量子域名
  4. 未挂 CDN 的解析 IP 只标记为疑似源站候选

重点关注子域名类型:
  □ mail.target.com / email.target.com      — 邮件服务器（通常不挂CDN）
  □ ftp.target.com                          — FTP服务器
  □ smtp.target.com / pop3.target.com       — 邮件协议服务器
  □ imap.target.com                         — 邮件协议服务器
  □ api.target.com                          — API服务器（部分不挂CDN）
  □ dev.target.com / staging.target.com     — 开发/测试环境（通常不挂CDN）
  □ test.target.com / uat.target.com        — 测试环境
  □ admin.target.com / internal.target.com  — 管理/内部/运维（通常不挂CDN）
  □ ops.target.com / mgmt.target.com        — 运维管理
  □ vpn.target.com / remote.target.com      — 远程接入
  □ oa.target.com / erp.target.com          — 办公系统
  □ cdn.target.com 本身                     — CDN源站配置域名

交叉验证:
  1. 直接访问 https://IP 和 Host 头验证属于主动动作，写入 Active Recon 待验证列表
  2. 子域名 IP 归属核验优先使用 IP Whois、ASN、IPSearch-MCP 和空间搜索索引
  3. 仅在授权范围内补充同网段资产线索
  4. 如进入主动阶段，可使用批量验证脚本:
     for sub in $(cat subdomains.txt); do
       ip=$(dig +short $sub | head -1)
       echo "$sub → $ip"
     done
```

---

### 7.5 方法五：国外 DNS 解析

```
原理: 多数国内目标使用国内CDN (阿里云/腾讯云CDN)，在国外没有部署节点。
      使用国外DNS或国外服务器访问时，请求直接回源。

操作一: 使用国外DNS服务器解析
  nslookup target.com 8.8.8.8            (Google DNS)
  nslookup target.com 1.1.1.1            (Cloudflare DNS)
  nslookup target.com 208.67.222.222     (OpenDNS)
  nslookup target.com 9.9.9.9            (Quad9)
  nslookup target.com 77.88.8.8          (Yandex DNS - 俄罗斯)
  nslookup target.com 8.26.56.26         (Comodo DNS)

操作二: 在线全球DNS查询工具
  □ dnschecker.org → 全球多节点DNS解析
  □ whatsmydns.net → 全球DNS查询
  □ ce8.8.8.8 → 全球Ping
  □ dns.google → Google Public DNS查询

操作三: 国外 VPS 直接访问
  □ 属于主动验证，不在被动阶段执行；如授权允许，转入 Active Recon 后记录节点、时间和请求目标

操作四: 对比国内解析结果
  若国外返回的IP与国内不同且为单一IP → 很可能是源站

适用场景:
  □ 仅面向国内用户的网站
  □ CDN 无海外节点
  □ 国内 CDN 服务商（阿里云CDN/腾讯云CDN/网宿/蓝汛/白山云）
```

---

### 7.6 方法六：FOFA/Shodan 空间搜索引擎搜索

```
原理: 通过页面标题、特征字符串、favicon哈希等线索，
      在空间搜索引擎中搜索真实源站IP。

FOFA 搜索:
  □ title="{网站Title}"                        — 搜索相同标题的服务器
  □ body="{特征字符串}"                         — 搜索相同正文内容的服务器
  □ cert="target.com"                          — 搜索使用相同证书的服务器
  □ icon_hash="{mmh3_hash}"                    — 搜索相同favicon的服务器
  □ header="Server: nginx" && body="{特征}"     — 多条件交叉搜索
  □ body="copyright 目标公司" && cert="*.target.com"

Shodan 搜索:
  □ http.title:"{网站Title}"                   — 页面标题搜索
  □ http.favicon.hash:{hash}                   — Favicon哈希搜索
  □ ssl.cert.subject.cn:"target.com"           — SSL证书CN搜索
  □ org:"Company Name"                         — 组织名搜索
  □ html:"{特征字符串}"                         — 页面正文搜索
  □ server:"nginx" "target.com"                — Server头+域名

获取 mmh3 favicon 哈希:
  □ 优先使用 FOFA/Hunter/Quake 已索引的 icon_hash 或用户提供的 favicon 文件
  □ 直接请求目标 favicon 属于主动动作，需转入 Active Recon

操作流程:
  1. 从搜索引擎快照、空间搜索索引、证书、备案、用户提供样本中获取标题/正文特征/favicon哈希
  2. 构造 FOFA/Shodan 搜索语法
  3. 获取返回的 IP 列表 → 标记为疑似源站候选
  4. Host 头验证和直接访问 IP 属于主动动作，写入 Active Recon 待验证列表
  5. 排除明确 CDN 节点 IP → 保留疑似源站 IP

注意事项:
  □ 多站同模板/同CMS会带来干扰，需人工逐个验证
  □ 关注非标端口 (8080/8443/7001等) → 通常不挂CDN
  □ 关注非80/443端口上的Web服务
```

---

### 7.7 CDN 穿透策略优先级

```
执行优先级 (从高到低):

  ① DNS历史记录 (SecurityTrails/VirusTotal)
     → 零痕迹，历史数据不因当前CDN配置而变化
     → 成功率: ★★★★☆

  ② 子域名/分站IP (mail/api/dev等)
     → 最可靠的方法，部分业务无法走CDN
     → 成功率: ★★★★★

  ③ SPF记录
     → 邮件服务器IP稳定，一般不会频繁变更
     → 成功率: ★★★★☆

  ④ 国外DNS解析
     → 简单直接，适用国内CDN
     → 成功率: ★★★☆☆

  ⑤ FOFA/Shodan 特征搜索
     → 信息密度高，可自动验证
     → 成功率: ★★★☆☆

  ⑥ 邮件头分析
     → 需要目标有邮件发送功能
     → 成功率: ★★★☆☆

  每获取一个疑似真实 IP:
    → 写入 ips_passive.txt / evidence_index.csv，状态为 suspected
    → 记录来源、命中条件、历史时间和归属原因
    → 需要 Host 头或页面内容验证时，转入 Active Recon 授权主动阶段
```

---

## 八、附录：完整工具链速查

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 步骤 │ 工具/数据源                │ 用途                │ 是否需Key      │
├──────────────────────────────────────────────────────────────────────────────┤
│  1   │ kali-mcp / whois           │ WHOIS查询           │ 否             │
│  1   │ whois.aliyun.com           │ 在线WHOIS           │ 否             │
│  2   │ Bing.com                   │ 搜索引擎Dork        │ 否             │
│  2   │ Baidu.com                  │ 搜索引擎Dork        │ 否             │
│  2   │ Google.com                 │ 搜索引擎Dork        │ 否             │
│  2   │ GitHub.com / GitLab.com    │ 源码泄露+社工信息   │ 否             │
│  2   │ Pastebin / Trello          │ 代码粘贴泄露        │ 否             │
│  2   │ pan.baidu.com              │ 网盘泄露            │ 否             │
│  3   │ bgpview.io / bgp.he.net    │ ASN查询             │ 否             │
│  3   │ IPSearch-MCP (MCP)         │ ip.db反查组织IP段   │ 否(需本地DB)   │
│  3   │ ipip.net                   │ 国内ASN查询         │ 否             │
│  4   │ FOFA-MCP (MCP)             │ 空间搜索引擎        │ 是(FOFA会员)   │
│  4   │ Hunter (奇安信)            │ 空间搜索引擎        │ 是(API Key)    │
│  4   │ Quake (360)                │ 空间搜索引擎        │ 是(API Key)    │
│  5   │ crt.sh                     │ SSL证书透明日志     │ 否             │
│  5   │ certspotter                │ 证书搜索            │ 否             │
│  6   │ SecurityTrails             │ DNS历史+子域名      │ 是(API Key)    │
│  6   │ VirusTotal                 │ 域名历史解析        │ 是(API Key)    │
│  6   │ AlienVault OTX             │ 被动DNS记录         │ 否             │
│  6   │ dnschecker.org             │ 全球DNS解析         │ 否             │
│  6   │ Shodan                     │ 空间搜索+Favicon    │ 否(基础)       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 九、安全守则

```
1. 被动边界: OSINT 阶段不向目标主机发送请求，主动验证转入授权主动阶段
2. 授权确认: 仅在已授权范围内执行信息收集
3. 数据隔离: 不同目标的资产数据严格隔离，禁止交叉使用
4. 信息闭环: 6大步骤必须全部覆盖，不得遗漏任何一项
5. 被动优先: 始终先完成全部被动收集，再用主动探测补充
6. 资产确权: 所有发现资产必须通过多维度交叉确认归属
7. 合规操作: 搜索引擎和空间搜索引擎的使用需遵守各平台服务条款
```
