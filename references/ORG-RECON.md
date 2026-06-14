---
name: org-recon
description: >
  组织侦察 — 企业股权穿透、ICP备案、采购招标、品牌产品名收集、SSL证书分析、云服务商识别。
  从公司名出发，构建完整商业关系图谱与数字资产清单。
metadata:
  tags: "org-recon,equity,icp,bidding,ssl,cloud,recon"
  category: "offensive-security"
  version: "1.0.0"
---

# ORG-RECON — 组织侦察（企业通用版）

> **目标**：从单一公司名称出发，构建目标组织的完整商业关系图谱，挖掘所有关联实体及其数字资产。
> **适用场景**：红蓝对抗、攻防演练、渗透测试 — 企业目标的组织级侦察。
>
> **💡 若目标为政府/事业单位**：请使用ORG-RECON.md+专项版 `ORG-RECON-GOV.md`（行政架构穿透 → gov.cn 域名体系 → 政府采购 → 政务云）。

---

## 一、股权穿透分析

### 1.1 数据源

| 平台 | 数据范围 | 查询方式 |
|------|---------|---------|
| 国家企业信用信息公示系统 (gsxt.gov.cn) | 全国工商登记信息 | 免费，按企业名称查询 |
| 天眼查 (tianyancha.com) | 工商+司法+知识产权 | 免费基础版/付费VIP |
| 企查查 (qcc.com) | 工商+司法+舆情 | 免费基础版/付费VIP |
| 启信宝 (qixin.com) | 工商+招投标+新闻 | 免费基础版/付费VIP |
| 爱企查 (aiqicha.baidu.com) | 工商+司法+ICP备案 | 免费 |
| 巨潮资讯网 (cninfo.com.cn) | 上市公司公告/年报 | 免费 |

### 1.2 股权穿透层级

```
第1层: 目标公司本身
  → 工商全称、曾用名、简称、英文名
  → 统一社会信用代码
  → 注册地址、经营地址
  → 经营范围（获取业务关键词）

第2层: 股东/投资方
  → 控股股东（>50%）→ 其控制的其他公司
  → 机构股东 → 其投资组合中的同行业公司
  → 自然人股东 → 其担任法人/股东的其他公司

第3层: 对外投资（核心提取层）
  → 全资子公司（100%）
  → 控股子公司（持股 >50%）★重点标记
  → 参股公司（持股 <50%）

第4层: 分支机构
  → 分公司
  → 办事处
  → 研发中心/实验室

第5层: 关联关系
  → 同一法人代表的公司
  → 同一董监高的公司
  → 同一注册地址/办公地址的公司
  → 历史股东/历史法人
```

### 1.3 控股子公司提取规则（≥50%）

```
筛选标准: 持股比例 ≥ 50%
提取字段:
  □ 企业全称（含曾用名）       → 用于后续所有侦察步骤
  □ 统一社会信用代码           → 数据库唯一标识
  □ 法定代表人                 → 反查其名下其他公司
  □ 注册资本 / 实缴资本        → 规模评估
  □ 成立日期                   → 资产存续周期
  □ 注册地址                   → 地理分布
  □ 经营范围关键词             → 业务方向判断
  □ 官网/域名                  → 直接攻击面
  □ 联系电话 / 邮箱            → 社工人点 + 反查关联
  □ 软件著作权 / 专利           → 产品名、技术栈
  □ 招投标信息                 → 内部系统名称、供应商
  □ 持股比例                   → 控制力判断
```

### 1.4 股权穿透输出格式

```markdown
## 股权穿透图谱 — XX公司

### 控股子公司 (≥50%)
| 公司名 | 关系 | 持股比例 | 法人 | 域名 | 电话 | 邮箱 |
|--------|------|---------|------|------|------|------|
| 上海XX信息技术有限公司 | 全资子公司 | 100% | 李四 | sh-xx.com | 021-xxxx | hr@sh-xx.com |
| 杭州XX网络科技有限公司 | 控股子公司 | 67% | 王五 | hz-xx.com | 0571-xxxx | - |
| 北京XX数据服务有限公司 | 控股子公司 | 51% | 赵六 | bj-xx.com | 010-xxxx | info@bj-xx.com |

### 参股公司 (<50%)
| 公司名 | 关系 | 持股比例 | 法人 | 域名 |
|--------|------|---------|------|------|
| 深圳XX智能有限公司 | 参股公司 | 30% | 孙七 | sz-xx.com |

### 同一法人关联
| 公司名 | 法人 | 域名 | 与目标关系 |
|--------|------|------|-----------|
| XX云计算有限公司 | 张三 | xx-cloud.com | 同一法人 |
```

---

## 二、品牌与产品名收集

### 2.1 信息来源

```
收集来源:
  □ 公司官网 → "产品中心""解决方案"
  □ 招聘网站（Boss直聘/拉勾/猎聘）→ JD中提到的系统/框架
  □ 公司年报 → 业务板块描述
  □ 新闻稿/媒体报道 → 产品发布
  □ 应用商店 → APP名称（App Store / 华为应用市场 / 小米应用商店）
  □ 微信公众号/小程序名称（微信搜索公司名/品牌名）
  □ 商标/专利数据库 → 产品商标名
  □ 域名WHOIS → 注册组织名
```

### 2.2 收集内容

```
□ 品牌名称          → 可能的子域名（brand.company.com）
□ 产品名称          → 可能的独立域名（product.com）
□ 内部系统代号       → 可能的内部域名
□ 技术栈关键词       → 用于后续指纹识别
□ 供应链关系         → 上下游公司的攻击面
□ APP名称+BundleID  → APK反编译入口
□ 小程序名称+AppID   → 代码提取
```

### 2.3 收集命令

```bash
# 从官网提取产品名
curl -s https://target.com | grep -oP '(产品|解决方案|平台|系统)[^<]{0,50}' | sort -u

# 从招聘JD提取技术栈（搜索引擎）
# site:zhaopin.com "公司名"
# site:lagou.com "公司名"
```

---

## 三、ICP 备案查询（主域名查询）

### 3.1 查询渠道（按优先级）

```
第一优先级: 官方渠道
  □ ICP/IP地址/域名信息备案管理系统
    https://beian.miit.gov.cn
    查询路径: 公共查询 → 备案信息查询 → 输入主办单位名称

第二优先级: 爱企查
  □ https://aiqicha.baidu.com
    浏览器搜索公司名 → 选择第一个公司 → 鼠标滑到知识产权位置 → 查看"网站备案"栏目 → 所有主域名信息显示
    优势: 自动关联公司名下所有备案域名，无需手动逐域名查询

第三优先级: 第三方平台
  □ 站长之家 ICP查询: https://icp.chinaz.com
    → 按主办单位名称 / 域名 / 备案号查询
  □ 备案查询网: https://beianx.cn
    → 支持按主体名批量查询
  □ ICP备案批量查询: https://icp.aizhan.com
    → 输入公司名批量获取备案域名列表
```

### 3.2 查询策略

```
策略一: 公司全称精确查询
  1. 用目标公司全称逐一在上述平台查询
  2. 获取所有已备案域名
  3. 记录备案号、审核时间、备案状态

策略二: 公司简称/曾用名模糊查询
  1. 用简称、曾用名补充查询
  2. 可能发现未及时变更备案名称的遗留域名

策略三: 子公司/关联公司查询
  1. 对每个持股 ≥50% 的子公司逐一查询
  2. 汇总完整的备案域名清单

策略四: 备案号反查
  1. 发现备案号后 → 用备案号反查
  2. 同一备案号下的其他域名 → 同一主办单位

策略五: 域名反查
  1. 用已知域名反查备案主体
  2. 确认域名是否真的属于目标公司
  3. 发现挂在该主体名下但"看起来不像"的域名

策略六: 邮箱/电话反查
  1. 部分平台支持按备案邮箱/电话反查
  2. 发现同一联系人备案的其他公司/域名
```

### 3.3 提取字段

```
□ 备案号（如 京ICP备XXXXXXXX号）
□ 主办单位名称
□ 主办单位性质（企业 / 个人 / 政府机关）
□ 网站名称
□ 网站首页地址（域名）
□ 审核通过时间
□ 备案状态（正常 / 已注销）
□ 备案邮箱 / 电话（如平台支持）
```

---

## 四、采购招标信息挖掘

### 4.1 数据源

| 平台 | 信息类型 | 查询方式 |
|------|---------|---------|
| 中国政府采购网 (ccgp.gov.cn) | 采购公告/中标/合同 | 搜采购单位名称 |
| 各省政府采购网 | 地方采购信息 | 搜单位名称 |
| 公共资源交易平台 | 招标/中标/流标 | 搜招标人/采购人 |
| 中国招标投标公共服务平台 | 全国招标信息 | 搜公司名 |
| 千里马招标网 (qianlima.com) | 企业招标 | 搜公司名 |
| 剑鱼标讯 (jianyu360.com) | 企业采购 | 搜公司名 |

### 4.2 从采购公告可提取的信息

```
采购公告中可能暴露:
  □ 单位内部系统名称       → "XX公司ERP系统升级项目"
  □ 现有系统架构           → "基于XX平台/XX数据库/XX中间件"
  □ 信息化承建方           → "由XX公司承建" / "中标供应商: XX科技"
  □ 预算金额               → 系统规模评估
  □ 联系人 + 电话          → 社工入口
  □ 技术要求文档           → 详细技术栈
  □ 供应商联系方式         → 供应链攻击面

提取关键词:
  □ 系统名称: 管理系统 / 平台 / 大数据 / 云平台 / 数据中心 / ERP / OA / CRM
  □ 技术栈: Java / .NET / Oracle / MySQL / Hadoop / Spring / Vue / React
  □ 供应商: 中标方 / 承建方 / 运维方
```

### 4.3 招标信息关联链

```
链条:
  采购公告 → 中标方 → 该供应商中标的其他项目 → 其他公司
  → 同一供应商服务多家公司 → 相同的技术栈/系统架构
  → 该供应商的源码仓库/知识库 → 可能含所有客户的配置

操作:
  1. 搜索目标公司所有采购公告（近3年）
  2. 提取每个项目的中标方 → 供应商清单
  3. 搜索每个供应商中标的其他项目 → 关联公司
  4. 搜索供应商公开的源码仓库（GitHub/Gitee）→ 配置泄露风险
```

---

## 五、SSL 证书分析

### 5.1 证书字段价值

```
证书字段提取与价值:
  □ Subject → Common Name（CN）→ 主域名
  □ Subject Alternative Names（SAN）→ 所有关联域名（核心字段）
  □ Issuer → 证书颁发机构（Let's Encrypt / DigiCert / 阿里云SSL等）
  □ Organization（O）→ 组织名（可与企业信息交叉验证）
  □ Organizational Unit（OU）→ 部门/团队信息
  □ not_before / not_after → 证书有效期 → 资产活跃度
  □ Serial Number → 证书序列号（可用于反向关联）
```

### 5.2 SSL 证书查询命令

```bash
# 获取目标域名的SSL证书
echo | openssl s_client -connect ${TARGET}:443 -servername ${TARGET} 2>/dev/null | \
  openssl x509 -noout -text

# 提取关键字段
echo | openssl s_client -connect ${TARGET}:443 -servername ${TARGET} 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName

# crt.sh 查询（证书透明度日志）
curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | \
  jq -r '.[] | "\(.common_name) | \(.name_value) | \(.issuer_name) | \(.not_before) | \(.not_after)"'
```

### 5.3 证书关联分析

```
关联维度:
  □ 同一证书 → 同一服务器 → 可能共用IP
  □ 同一 Organization → 同一组织 → 兄弟域名
  □ 同一 Issuer → 同一签发批次 → 关联域名组
  □ 证书有效期 → 定期更新的资产 vs 遗忘的资产

证书发现:
  □ SAN字段中的非目标域名 → 关联公司域名
  □ 证书序列号反查 → 同一证书的其他关联域名
  □ 通配符证书（*.target.com）→ 子域名范围
```

---

## 六、云服务商识别

### 6.1 DNS 记录分析

```bash
# 查看DNS记录类型识别云服务
dig A ${domain}          # IP归属 → ASN → 云服务商
dig CNAME ${domain}      # CDN/WAF/云存储识别
dig MX ${domain}         # 邮件服务商
dig TXT ${domain}        # SPF/DKIM记录 → 邮件/验证服务
dig NS ${domain}         # DNS托管商

# 批量查询
for domain in $(cat domains.txt); do
  echo "=== $domain ==="
  dig +short ANY $domain | grep -iE 'aliyun|tencent|qiniu|aws|azure|cloudflare|huawei'
done
```

### 6.2 CNAME 特征库

| CNAME后缀 | 服务商 | 服务类型 |
|-----------|--------|---------|
| `*.aliyuncs.com` | 阿里云 | OSS / CDN |
| `*.kunlun*.com` | 阿里云 | WAF |
| `*.alicdn.com` | 阿里云 | CDN |
| `*.dcdn*.com` | 阿里云 | DCDN |
| `*.myqcloud.com` | 腾讯云 | COS / CDN |
| `*.cdn.myqcloud.com` | 腾讯云 | CDN |
| `*.qiniudns.com` / `*.qiniucdn.com` | 七牛云 | CDN / 存储 |
| `*.cloudfront.net` | AWS | CDN |
| `*.s3.*.amazonaws.com` | AWS | S3 |
| `*.azureedge.net` | Azure | CDN |
| `*.blob.core.windows.net` | Azure | Blob |
| `*.myhuaweicloud.com` | 华为云 | OBS |
| `*.huaweicloudwaf.com` | 华为云 | WAF |
| `*.bdydns.com` | 百度云 | CDN |
| `*.volccdn.com` | 火山引擎 | CDN |
| `*.ksyuncdn.com` | 金山云 | CDN |
| `*cloudflare*` | Cloudflare | CDN/WAF |

### 6.3 HTTP 响应头特征

```bash
# 页面底部云服务商声明
curl -s https://${target} | grep -iE '阿里云|腾讯云|华为云|百度智能云|AWS|Azure|Google Cloud'

# HTTP响应头
curl -sI https://${target} | grep -iE 'Server:|X-Powered-By:|Via:|X-Cache:'

# Server头特征:
# AliyunOSS               → 阿里云OSS
# Tengine / ATS           → 阿里云CDN
# tencent-cos             → 腾讯云COS
# NWS_VCLOUD              → 华为云
# CloudFront              → AWS CloudFront
# Azure                    → Microsoft Azure
```

### 6.4 邮件服务识别

```bash
# MX记录分析
dig MX target.com

# SPF记录
dig TXT target.com | grep "v=spf1"

# 常见邮件服务:
# include:spf.mail.qq.com          → 腾讯企业邮箱
# include:spf.qiye.aliyun.com      → 阿里企业邮箱
# include:_netblocks.google.com    → Google Workspace
# include:spf.protection.outlook.com → Microsoft 365
# include:spf.mailcloud.163.com    → 网易企业邮
```

### 6.5 云服务商输出格式

```markdown
## 云服务商识别结果

| 服务商 | 服务类型 | 关联域名 | 确认方式 |
|--------|---------|---------|---------|
| 阿里云 | ECS | www.xxx.com → 47.xx.xx.xx (AS45102) | IP归属 |
| 阿里云 | CDN | cdn.xxx.com → *.kunlun*.com | CNAME |
| 阿里云 | OSS | static.xxx.com → *.aliyuncs.com | CNAME |
| 阿里云 | 企业邮箱 | MX → *.mx.mail.aliyun.com | MX记录 |
| 腾讯云 | COS | img.xxx.com → *.myqcloud.com | CNAME |
| Cloudflare | CDN/WAF | www.xxx.com → NS: *.ns.cloudflare.com | NS记录 |

### 后续行动
- 阿里云: 枚举 OSS Bucket，检查 RAM 权限
- 腾讯云: 枚举 COS Bucket
- Cloudflare: CDN 回源 IP 探测
```

---

## 七、组织侦察产出格式

```markdown
## 组织侦察报告 — XX科技有限公司

### 一、基本信息
| 字段 | 值 |
|------|-----|
| 企业全称 | XX科技有限公司 |
| 曾用名 | XX信息技术有限公司 |
| 统一社会信用代码 | 91110108XXXXXXXXXX |
| 法定代表人 | 张三 |
| 注册资本 | 5000万人民币 |
| 成立日期 | 2015-03-15 |
| 注册地址 | 北京市海淀区XX路XX号 |
| 官网 | www.xxx.com |
| 联系电话 | 010-XXXXXXXX |
| 邮箱 | hr@xxx.com |

### 二、股权穿透
| 公司名 | 关系 | 持股比例 | 法人 | 域名 | 电话 |
|--------|------|---------|------|------|------|
| 上海XX信息技术 | 全资子公司 | 100% | 李四 | sh-xx.com | 021-xxxx |
| 杭州XX网络科技 | 控股子公司 | 67% | 王五 | hz-xx.com | 0571-xxxx |

### 三、品牌与产品
| 品牌/产品名 | 类型 | 关联域名/APP | 来源 |
|------------|------|------------|------|
| XX云平台 | SaaS产品 | cloud.xx.com | 官网 |
| XX助手 | APP | App Store/华为应用市场 | 应用商店 |
| XX小程序 | 微信小程序 | wxid: xxx | 微信搜索 |

### 四、ICP备案域名
| 域名 | 备案号 | 主办单位 | 审核时间 | 状态 |
|------|--------|---------|---------|------|
| www.xxx.com | 京ICP备2020XXXXXX号 | XX科技有限公司 | 2020-06-01 | 正常 |
| admin.xxx.com | 京ICP备2020XXXXXX号 | XX科技有限公司 | 2020-06-01 | 正常 |
| xx-cloud.com | 京ICP备2021XXXXXX号 | XX科技有限公司 | 2021-03-15 | 正常 |
| old.xxx.com | 京ICP备2018XXXXXX号 | XX信息技术有限公司(曾用名) | 2018-01-10 | 已注销 |

### 五、采购招标线索
| 项目名称 | 中标方 | 涉及系统 | 预算(万) |
|---------|--------|---------|---------|
| XX公司ERP系统升级 | XX软件科技 | SAP ERP | 300 |
| 数据中台建设项目 | 杭州XX数据 | 大数据平台(基于Hadoop) | 800 |

### 六、供应商清单
| 供应商 | 服务内容 | 关系 | 备注 |
|--------|---------|------|------|
| XX软件科技 | ERP实施 | 长期合作 | 可能有VPN/堡垒机权限 |
| 杭州XX数据 | 数据中台 | 项目合作 | 可能有数据访问接口 |

### 七、云服务商识别
| 服务商 | 服务 | 关联域名 | 确认方式 |
|--------|------|---------|---------|
| 阿里云 | ECS+OSS+CDN | www/static/cdn.xxx.com | IP归属+CNAME |
| 腾讯云 | 企业邮箱 | MX → mail.qq.com | MX记录 |

### 八、SSL证书
| 域名 | CN | SAN域名数 | 颁发者 | 有效期 |
|------|-----|----------|--------|--------|
| www.xxx.com | *.xxx.com | 5 | TrustAsia | 2025.01-2026.01 |
```

---

## 八、工具链速查

```
┌──────────────────────────────────────────────────────────────────────┐
│ 步骤        │ 工具/平台             │ 用途              │ 付费      │
├──────────────────────────────────────────────────────────────────────┤
│ 股权穿透    │ 天眼查/企查查/爱企查    │ 股东/子公司/关联   │ 免费基础   │
│ 股权穿透    │ gsxt.gov.cn           │ 工商登记官方数据   │ 免费      │
│ 品牌收集    │ 官网/招聘/应用商店      │ 产品名/APP        │ 免费      │
│ ICP备案     │ beian.miit.gov.cn     │ 官方备案查询       │ 免费      │
│ ICP备案     │ aiqicha.baidu.com     │ 爱企查关联备案     │ 免费      │
│ ICP备案     │ icp.chinaz.com        │ 站长之家ICP        │ 免费      │
│ ICP备案     │ beianx.cn             │ 备案查询网         │ 免费      │
│ ICP备案     │ icp.aizhan.com        │ ICP批量查询        │ 免费      │
│ 采购招标    │ ccgp.gov.cn           │ 政府采购           │ 免费      │
│ 采购招标    │ 各省公共资源交易平台    │ 招标公告           │ 免费      │
│ SSL证书     │ crt.sh / openssl      │ 证书透明+字段提取  │ 免费      │
│ 云服务商    │ dig / curl / nslookup  │ DNS+Header分析     │ 免费      │
└──────────────────────────────────────────────────────────────────────┘
```
