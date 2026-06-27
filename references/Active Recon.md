---
name: active-recon
description: >
  主动信息收集 — 红队/攻防主动探测核心模块。
  覆盖主动探测前置检查、DNS爆破 (OneForAll/Subfinder)、端口扫描 (Nmap/Masscan)、
  CDN穿透 (6种方法获取真实IP)、端口服务指纹识别、HTTP Host碰撞、对象存储主动枚举。
  需完整授权，严格控制速率。
metadata:
  tags: "active,recon,redteam,dns-brute,port-scan,nmap,masscan,cdn-bypass,host-collision,bucket-enum"
  category: "offensive-security"
  version: "1.0.0"
---

# Active Recon — 主动信息收集

> **核心原则**：在完整授权范围内，通过主动探测获取目标实时资产信息。
> **适用场景**：红蓝对抗、攻防演练、渗透测试 — 已完成被动收集后的主动补充。
> **⚠ 重要警告**：主动探测会向目标发送请求，必须在获得完整书面授权后进行。

---

## 一、主动探测前置检查

```
执行前必须全部确认:
  □ 授权函已签署且明确包含主动探测范围
  □ 已配置代理/IP白名单（避免被封）
  □ 速率限制参数已设置 (延迟 ≥ 500ms, 并发 ≤ 100)
  □ 紧急停止方案已确认
  □ 已通知甲方探测时间段
  □ 日志记录已启用
  □ 操作IP已加入甲方白名单
```

---

## 二、DNS 爆破 — 子域名主动枚举

> **工具选型**：OneForAll（国内首选，模块最全）→ Subfinder（海外目标/补充）。

### 2.1 OneForAll 深度子域名收集 (首选)

```bash
# 项目地址: https://github.com/shmilylty/OneForAll
# OneForAll 是国内环境子域名收集的首选工具，模块覆盖最全

# #### 安装 ####
git clone https://github.com/shmilylty/OneForAll.git
cd OneForAll
pip install -r requirements.txt

# #### 基础用法 ####
python oneforall.py --target target.com run

# #### 参数说明 ####
# --target:  目标主域名
# --alive:   仅输出存活子域名 (DNS解析验证)
# --dns:     启用DNS数据集查询
# --brute:   启用字典爆破模式
# --req:     指定请求延迟 (默认1s)
# --takeover 检测子域名接管漏洞

# #### 运行流程 (按顺序执行模块) ####
# 1. cert_spotter / crtsh → 证书透明度日志
# 2. 搜索引擎模块: 百度/Google/Bing/搜狗/360
# 3. dns_dataset → SecurityTrails/Robtex/DNSDumpster
# 4. dns_brute → 内置多级字典爆破
# 5. alt_dns → 通过置换发现新子域名
# 6. ssl_cert → SSL证书提取
# 7. cdn → CDN检测
# 8. alive → 存活验证

# #### 配置文件优化 ####
# 编辑 config/default.py 或 api.json 配置 API Key (提升覆盖率):
#   - SecurityTrails API Key
#   - Censys API ID/Secret
#   - BinaryEdge API Key
#   - VirusTotal API Key
#   - Fofa Email/Key
#   - Shodan API Key

# #### 输出文件 ####
# results/target.com.csv   → 完整结果 (含子域名/IP/CNAME/CDN等)
# results/target.com.json  → JSON格式
# results/target.com.txt   → 纯子域名列表

# #### 组合流程 ####
# 1. 先跑 oneforall
python oneforall.py --target target.com run

# 2. 提取存活子域名
python oneforall.py --target target.com --alive True run

# 3. 结果与其他工具合并去重
cat results/target.com.txt subfinder_out.txt | sort -u > all_subdomains.txt
```

### 2.2 Subfinder 补充收集

```bash
# 项目地址: https://github.com/projectdiscovery/subfinder
# 多源被动+轻量主动，速度快

# #### 安装 ####
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# #### 基础用法 ####
subfinder -d target.com -all -o subfinder_out.txt

# #### 配置API Key ####
# 编辑 ~/.config/subfinder/provider-config.yaml
# 配置后可大幅提升收集覆盖率

# #### 组合使用 ####
subfinder -d target.com -all -o subfinder_raw.txt

# 配合 puredns 高精度解析
puredns resolve subfinder_raw.txt --resolvers resolvers.txt --write subfinder_alive.txt
```

### 2.3 泛解析处理 (Wildcard DNS)

```bash
# 检测是否存在泛解析
dig RANDOMSTRING12345.target.com
# 如果有A记录返回 → 存在泛解析 → 需过滤假阳性

# puredns 自带泛解析过滤
puredns resolve subdomains_merged.txt \
  --resolvers resolvers.txt \
  --wildcard-threshold 5 \
  --write resolved_filtered.txt

# 手动过滤泛解析
# 1. 先解析一个确定不存在的子域名，获取泛解析IP
RAND_IP=$(dig +short randomstring12345.target.com | head -1)
# 2. 排除该IP的解析结果
grep -v "$RAND_IP" resolved_all.txt > resolved_no_wildcard.txt
```

### 2.4 字典生成策略

```python
# 基于公司信息的字典生成
company_name = "example"

variations = [
    # 基础变形
    company_name,
    company_name.replace('e', ''),

    # 环境前缀
    f"dev-{company_name}", f"test-{company_name}",
    f"uat-{company_name}", f"staging-{company_name}",
    f"api-{company_name}", f"admin-{company_name}",

    # 环境后缀
    f"{company_name}-dev", f"{company_name}-test",
    f"{company_name}-uat", f"{company_name}-staging",

    # 常见子域名前缀
    *[f"{p}" for p in [
        'www', 'mail', 'ftp', 'admin', 'api', 'dev', 'test',
        'staging', 'uat', 'beta', 'sandbox', 'portal', 'sso',
        'vpn', 'git', 'jenkins', 'jira', 'wiki', 'confluence',
        'oa', 'erp', 'crm', 'hr', 'finance', 'monitor', 'grafana',
        'kibana', 'k8s', 'docker', 'registry', 'nexus', 'harbor',
        'm', 'mobile', 'h5', 'app', 'pay', 'open', 'cloud',
        'static', 'img', 'cdn', 'log', 'data', 'file', 'upload',
    ]],
]

with open('custom_dict.txt', 'w') as f:
    for v in variations:
        f.write(v + '\n')
```

---

## 三、端口扫描

> **工具选型**：Nmap（准确，服务识别）→ Masscan（快速，C段全端口）。
> **扫描端口清单**：20, 21, 22, 23, 80, 443, 445, 873, 1433, 1521, 2181, 2375, 3306, 3389, 5000, 5432, 5601, 6379, 7001, 7002, 8080, 8161, 8443, 8848, 9043, 9200, 9300, 11211, 27017

### 3.1 Nmap 端口扫描 (选)

```bash
# #### 存活探测 (优先) ####
ping {{IP}}

# #### 综合端口+服务版本扫描 (推荐) ####
nmap -sS -sV -T4 -Pn \
  -p 20,21,22,23,80,443,445,873,1433,1521,2181,2375,3306,3389,5000,5432,5601,6379,7001,7002,8080,8161,8443,8848,9043,9200,9300,11211,27017 \
  -iL live_hosts.txt --open \
  -oA nmap_scan

# #### 全端口扫描 (谨慎使用) ####
nmap -sS -T3 -p- -iL live_hosts.txt --open -oA nmap_fullport

# #### Web端口专项扫描 ####
nmap -sS -T4 -p 80,443,8080,8443,7001,7002,8000-9000,3000,5000,5601 \
  --open -iL live_hosts.txt -oG nmap_web.txt

# #### 提取Nmap结果为IP:Port列表 ####
grep -oP 'Host: \S+.*Ports:' nmap_scan.gnmap | \
  awk '{for(i=1;i<=NF;i++){if($i~/Ports:/){p=i+1; while(p<=NF && $p!~/Ignored/){split($p,a,"/"); if(a[2]=="open") print $2":"a[1]; p++}}}}' | \
  sort -u > nmap_ports.txt
```

### 3.2 Masscan 快速C段扫描 (备选)

```bash
# #### 仅存活探测 ####
masscan {C_SEGMENT}/24 -p0 --rate 10000 -oG masscan_ping.txt

# #### 指定端口快速扫描 ####
masscan {C_SEGMENT}/24 \
  -p20,21,22,23,80,443,445,873,1433,1521,2181,2375,3306,3389,5000,5432,5601,6379,7001,7002,8080,8161,8443,8848,9043,9200,9300,11211,27017 \
  --rate 5000 -oG masscan_ports.txt

# #### 全端口快速扫描 ####
masscan {IP} -p1-65535 --rate 3000 -oG masscan_full.txt
# 注意: 全端口扫描速率要降低，避免被IDS拦截

# #### 提取Masscan结果为IP:Port列表 ####
grep -oP '\d+\.\d+\.\d+\.\d+:\d+' masscan_ports.txt | sort -u > masscan_port_list.txt
```

### 3.3 端口分类与优先级

```
第一优先级 (直接RCE/数据泄露):
  □ 6379  Redis          → 未授权访问
  □ 27017 MongoDB        → 未授权访问
  □ 2375  Docker API     → 未授权访问
  □ 873   Rsync          → 未授权访问
  □ 2181  ZooKeeper      → 未授权访问
  □ 11211 Memcached      → 未授权访问
  □ 8848  http(Nacos)    → 未授权访问

第二优先级 (登录暴露面记录，不做口令尝试):
  □ 22    SSH            → 远程登录暴露面
  □ 3389  RDP            → 远程桌面暴露面
  □ 3306  MySQL          → 数据库暴露面
  □ 1433  MSSQL          → 数据库暴露面
  □ 5432  PostgreSQL     → 数据库暴露面
  □ 21    FTP            → 匿名访问暴露面
  □ 23    Telnet         → 明文协议

第三优先级 (Web中间件/运维):
  □ 80/443   标准Web     → 存活确认+指纹识别
  □ 8080/8443 Tomcat     → 管理入口/版本风险线索
  □ 7001/7002 WebLogic   → 历史高危版本风险线索
  □ 8161     ActiveMQ    → 管理入口暴露面
  □ 9043     WebSphere   → 历史高危版本风险线索
  □ 9200/9300 ES         → 未授权访问
  □ 5601     Kibana      → 未授权访问
  □ 5000     Docker Reg  → 镜像仓库暴露面
  □ 1521     Oracle      → 数据库暴露面
  □ 445      SMB         → SMB 暴露面/历史漏洞风险线索
```

---

## 四、CDN 穿透 — 获取真实源IP

> **前置判断**：先确认目标是否使用了CDN，再执行穿透方法。

### 4.0 CDN 快速判断

```bash
# 方法1: ping.chinaz.com → 多地Ping → 不同地区返回不同IP → 确认CDN
# 方法2: nslookup target.com → 返回多个不同网段IP → 确认CDN
# 方法3: dig target.com → ANSWER SECTION中IP数量≥2 → 确认CDN

# ===== 确认使用CDN后，以下6种方法尝试获取真实源IP =====
```

---

### 4.1 方法一：子域名/分站IP (首选，成功率最高)

```bash
# 原理: 很多子域名不会配置CDN，解析得到的IP大概率是源站IP
# 步骤:
#   1. 收集所有子域名
#   2. 逐个DNS解析
#   3. 多地Ping验证 → 筛选出未挂CDN的子域名
#   4. 未挂CDN的子域名IP → 可能是主站真实IP

# 常见未挂CDN的子域名类型:
# dev.target.com / staging.target.com / admin.target.com
# mail.target.com / ftp.target.com / cpanel.target.com
# internal.target.com / vpn.target.com
# api.target.com / m.target.com / h5.target.com

# 脚本: 批量解析+存活验证
for sub in $(cat all_subdomains.txt); do
  ip=$(dig +short A $sub | head -1)
  if [ -n "$ip" ]; then
    echo "$sub → $ip"
  fi
done | sort -u -t'→' -k2

# 对每个IP做whois/ASN查询，筛选非CDN节点的IP
# 交叉验证: curl -k https://{IP} -H "Host: target.com"
```

---

### 4.2 方法二：历史DNS解析记录 (信息密度最高)

```bash
# SecurityTrails (需API Key)
curl -s "https://api.securitytrails.com/v1/history/${TARGET}/dns/a" \
  -H "apikey: $ST_API_KEY" | jq -r '.records[].values[].ip'

# VirusTotal (需API Key)
curl -s "https://www.virustotal.com/api/v3/domains/${TARGET}/resolutions?limit=40" \
  -H "x-apikey: $VT_API_KEY" | jq -r '.data[].attributes.ip_address'

# 微步在线 (x.threatbook.com) → 域名分析 → 历史解析
# DNSdumpster → 查看历史DNS数据

# 注意: 历史IP可能已失效，需逐IP扫描验证存活状态
```

---

### 4.3 方法三：SSL证书关联域名反查 (两步法)

```bash
# 原理: 同一SSL证书可能关联多个域名，通过证书反查关联域名→解析获取IP
# 步骤: 证书→关联域名→解析域名(两步，证书本身不包含IP)

# Step 1: 获取证书哈希
CERT_SHA256=$(curl -s "https://crt.sh/?q=%25.${TARGET}&output=json" | \
  jq -r '.[].sha256' | sort -u | head -1)

# Step 2: 用证书哈希反查所有使用同一证书的域名
curl -s "https://crt.sh/?q=${CERT_SHA256}&output=json" | \
  jq -r '.[].name_value' | sort -u | tee san_domains.txt

# Step 3: 解析这些关联域名 → 若某个域名未挂CDN → 该IP即为真实IP
for domain in $(cat san_domains.txt); do
  ip=$(dig +short A $domain | head -1)
  echo "$domain → $ip"
done

# Step 4: 对解析出的IP批量验证
# → 对非CDN节点的HTTPS端口提取证书 → 匹配目标域名 → 确认真实IP
```

---

### 4.4 方法四：邮件头分析

```
原理: 目标网站若有邮件发送功能（注册验证/密码重置/通知），
      发送的邮件源码中可能暴露源站IP。
      发件服务器IP通常不在CDN后面。

步骤一: 触发邮件发送
  □ 注册账号 → 验证邮件
  □ 密码找回 → 重置邮件
  □ 订阅通知 → 通知邮件
  □ 联系表单 → 自动回复

步骤二: 查看邮件源码
  □ QQ邮箱: 邮件 → 更多 → 查看邮件源码
  □ 163邮箱: 邮件 → 更多 → 查看原文
  □ Gmail: 邮件 → 显示原始邮件

步骤三: 搜索 "Received: from" → 追踪邮件传输路径
  □ 最底部的 "Received: from" 通常是发件服务器IP
  □ 排除知名邮件服务商IP (QQ/163/Gmail等)
  □ 剩余IP → 可能是源站IP或企业邮件服务器IP

步骤四: 提取IP
  grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' email_header.txt | sort -u
```

---

### 4.5 方法五：SPF记录 — 发件服务器IP

```bash
# SPF记录中的发件服务器IP通常不挂CDN

# 查询SPF记录
dig TXT target.com | grep "v=spf1"
dig TXT target.com +short | grep -oE 'ip4:[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}[^ ]*'

# SPF记录解读:
#   ip4:123.123.123.123        → 发件服务器真实IP
#   ip4:123.123.123.0/24       → 整个C段可能都属于目标
#   include:spf.mail.qq.com    → 使用腾讯企业邮箱
#   include:spf.qiye.aliyun.com → 使用阿里企业邮箱
#   a:mail.target.com          → mail.target.com的解析IP
#   mx                         → MX记录指向的邮件服务器IP
```

---

### 4.6 方法六：CDN未覆盖区域访问

```bash
# 原理: 国内CDN在海外无节点，使用国外DNS/服务器访问时直接回源

# 使用国外DNS服务器解析
nslookup ${TARGET} 8.8.8.8            (Google DNS)
nslookup ${TARGET} 1.1.1.1            (Cloudflare DNS)
nslookup ${TARGET} 208.67.222.222     (OpenDNS)
nslookup ${TARGET} 9.9.9.9            (Quad9)
nslookup ${TARGET} 77.88.8.8          (Yandex DNS - 俄罗斯)

# 在线全球DNS查询
# dnschecker.org → 全球多节点DNS解析
# whatsmydns.net → 全球DNS查询

# 从国外VPS直接访问
curl -sI https://${TARGET}
# 对比国内解析结果 → IP不同且为单一IP → 很可能是源站

# 适用场景:
#   仅面向国内用户的网站
#   使用国内CDN (阿里云CDN/腾讯云CDN/网宿/蓝汛/白山云)
```

---

### 4.7 CDN 穿透策略优先级

```
执行优先级 (从高到低):

① 子域名/分站IP (mail/api/dev等)
   → 最可靠，部分业务无法走CDN
   → 成功率: ★★★★★

② DNS历史记录 (SecurityTrails/VirusTotal)
   → 零痕迹，历史数据不受当前CDN影响
   → 成功率: ★★★★☆

③ SPF记录
   → 邮件服务器IP稳定，一般不频繁变更
   → 成功率: ★★★★☆

④ SSL证书关联域名反查
   → 通过关联域名间接获取
   → 成功率: ★★★☆☆

⑤ 邮件头分析
   → 需要目标有邮件发送功能
   → 成功率: ★★★☆☆

⑥ CDN未覆盖区域 (国外DNS)
   → 简单直接，适用国内CDN
   → 成功率: ★★★☆☆

每获取一个疑似真实IP → 立即验证:
  curl -sI -k https://{IP} -H "Host: target.com" | head -20
  → 若返回目标网站内容 → 确认为真实IP
  → 若返回错误/默认页面/CDN拦截 → 排除
```

---

## 五、端口服务识别

### 5.1 HTTP/HTTPS 服务 — 网站指纹识别

> **参考**：详见 `fingerprint.md` 完整指纹识别方法论。
> **核心目标**：识别 CMS、中间件、开发语言/框架、WAF、CDN、第三方服务。

```bash
# #### httpx 批量指纹采集 ####
httpx -l targets.txt \
  -title -tech-detect -status-code -content-length \
  -follow-redirects -follow-host-redirects \
  -server -websocket -ip -cname -cdn \
  -o httpx_fingerprint.json -json

# #### WhatWeb 指纹识别 ####
whatweb -i targets.txt --log-json whatweb_out.json
whatweb --aggression 3 https://target.com

# #### Wappalyzer CLI ####
wappalyzer https://target.com

# #### 手动关键Header提取 ####
curl -sI https://target.com | grep -iE 'Server:|X-Powered-By:|Set-Cookie:|Via:|X-Cache:|X-Generator:'

# #### CMS特征提取 ####
curl -s https://target.com | grep -iE 'generator|wp-content|wp-includes|dedecms|discuz|phpcms'

# #### WAF检测 ####
wafw00f -l targets.txt -o waf_detection.txt

# #### nuclei 技术识别模板 ####
nuclei -l targets.txt -t ~/nuclei-templates/technologies/ -o nuclei_tech.json -json
```

### 5.2 非HTTP服务 — Nmap 服务版本识别

```bash
# Nmap -sV 结果直接给出服务名和版本
# 提取关键服务的版本信息

# #### 数据库服务版本 ####
grep -E 'mysql|mssql|postgresql|oracle|redis|mongodb' nmap_scan.nmap

# #### Web中间件版本 (非HTTP端口也有) ####
grep -E 'tomcat|weblogic|jetty|jboss|websphere|nginx|apache|iis' nmap_scan.nmap

# #### 运维服务版本 ####
grep -E 'docker|zookeeper|rsync|kubernetes|etcd' nmap_scan.nmap
```

### 5.3 特殊服务快速检测

```bash
# #### Redis (6379) — 未授权检测 ####
echo -e "INFO\r\n" | nc -w 3 {IP} 6379

# #### MongoDB (27017) — 未授权检测 ####
echo '{"isMaster": 1}' | nc -w 3 {IP} 27017

# #### Memcached (11211) — 未授权检测 ####
echo "stats" | nc -w 3 {IP} 11211

# #### Elasticsearch (9200) — 未授权检测 ####
curl -s http://{IP}:9200/_cat/indices

# #### Docker API (2375) — 未授权检测 ####
curl -s http://{IP}:2375/version

# #### Rsync (873) — 未授权检测 ####
rsync rsync://{IP}:873/

# #### ZooKeeper (2181) — 未授权检测 ####
echo "envi" | nc -w 3 {IP} 2181

# #### Etcd (2379) — 未授权检测 ####
curl -s http://{IP}:2379/v2/keys/

# #### Kubelet (10250) — 未授权检测 ####
curl -s https://{IP}:10250/pods/ -k
```

---

## 六、端口扫描报告格式

### 6.1 标准报告模板

```markdown
## 端口扫描报告 — 目标公司

**扫描时间**: 2026-01-15 10:00-10:30
**扫描方式**: Nmap -sS -sV -T4
**扫描端口**: 20,21,22,23,80,443,445,873,1433,1521,2181,2375,3306,3389,5000,5432,5601,6379,7001,7002,8080,8161,8443,9043,9200,9300,11211,27017

### 端口服务总览

| IP | 端口 | 服务 | 版本 | 页面标题 | 技术栈 | 归属判断 |
|----|------|------|------|---------|--------|---------|
| x.x.x.1 | 80 | HTTP | nginx/1.18.0 | "XX公司官网" | Vue.js | 是 |
| x.x.x.1 | 443 | HTTPS | nginx/1.18.0 | "XX公司官网" | Vue.js | 是 |
| x.x.x.2 | 3306 | MySQL | 5.7.38 | - | - | 是 |
| x.x.x.3 | 6379 | Redis | 5.0.7 | - | - | 疑似 |
| x.x.x.3 | 27017 | MongoDB | 4.4.6 | - | - | 疑似 |
| x.x.x.4 | 8080 | HTTP | Tomcat 9.0.65 | "Apache Tomcat" | Java | 是 |
| x.x.x.5 | 80 | HTTP | Apache/2.4.54 | "XX公司" | React | 否(旁站) |

### 高危端口清单

| IP | 端口 | 服务 | 风险类型 | 验证结果 |
|----|------|------|---------|---------|
| x.x.x.3 | 6379 | Redis | 未授权访问 | 存在未授权 |
| x.x.x.6 | 22 | SSH | 远程登录暴露面 | 待确认归属与访问策略 |

### 指纹识别详情

| URL | CMS/版本 | 中间件/版本 | 语言框架 | WAF | CDN |
|-----|---------|------------|---------|-----|-----|
| www.target.com | - | Nginx 1.18 | Vue.js/PHP | 阿里云WAF | 阿里云CDN |
| admin.target.com | 若依 4.7 | Nginx 1.18 | Java/Spring | - | - |
| api.target.com | - | Nginx 1.18 | Spring Boot 2.7 | - | - |
```

### 6.2 简化格式 (CSV)

```
IP,端口,服务,版本,标题,WAF,CDN,归属
x.x.x.1,80,HTTP,nginx/1.18,XX公司官网,阿里云WAF,阿里云CDN,是
x.x.x.1,443,HTTPS,nginx/1.18,XX公司官网,阿里云WAF,阿里云CDN,是
x.x.x.2,3306,MySQL,5.7.38,-,-,-,是
x.x.x.3,6379,Redis,5.0.7,-,-,-,疑似
x.x.x.4,8080,HTTP,Tomcat 9.0.65,Apache Tomcat,-,-,是
x.x.x.5,80,HTTP,Apache/2.4.54,XX公司,-,-,否
```

---

## 七、HTTP Host 碰撞

> **原理**：当一个IP上运行多个虚拟主机时，只能通过HTTP Host头区分不同站点。
> 通过遍历已知域名列表 + 目标IP进行Host碰撞，发现隐藏站点。

### 7.1 碰撞准备

```
数据准备:
  □ IP列表 → 来自C段扫描发现的Web端口IP
  □ 域名列表 → 来自子域名收集的所有域名
  □ 内部域名 → 从JS中提取的内部API域名
  □ 证书域名 → 从SSL证书SAN中提取的域名
```

### 7.2 执行方法

```bash
# #### 方法1: httpx Host碰撞 ####
httpx -l web_ips.txt \
  -H "Host: {subdomain}" \
  --host-collision-domain-list all_subdomains.txt \
  -title -status-code -content-length \
  -o host_collision.json -json

# #### 方法2: 手动验证脚本 ####
for ip in $(cat web_ips.txt); do
  for domain in $(cat all_subdomains_internal.txt); do
    code=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Host: $domain" --connect-to "::$ip:" "http://$domain")
    if [ "$code" != "000" ]; then
      echo "[$code] $ip → $domain"
    fi
  done
done

# #### 方法3: 强制绑定Hosts验证 ####
# 修改 /etc/hosts 后直接访问
echo "{IP} {domain}" >> /etc/hosts
curl -sI https://{domain}
# 验证完成后删除
sed -i '/{IP} {domain}/d' /etc/hosts
```

### 7.3 碰撞结果验证

```
发现不同Host头返回不同内容 → 确认存在虚拟主机
发现Host头返回内容与直接访问域名一致 → CDN穿透成功
发现Host头返回内部系统 → 高价值发现

常见碰撞目标:
  □ 已知的员工系统域名 (oa/erp/crm.internal.xxx.com)
  □ 从JS中提取的内部API域名
  □ 从证书SAN中提取的内部域名
  □ 内部DNS泄露的域名
  □ 运维管理系统 (jenkins/gitlab/nacos/grafana)
```

---

## 八、对象存储主动枚举

### 8.1 Bucket 爆破

```bash
# #### s3scanner (AWS S3) ####
s3scanner scan --buckets-file bucket_names.txt

# #### Cloud Enum (多云平台) ####
# 支持 AWS / Azure / GCP
cloud_enum -k company_name -k product_name

# #### 自定义Bucket枚举 (阿里云OSS) ####
for bucket in $(cat bucket_names.txt); do
  for region in $(cat oss_regions.txt); do
    url="https://${bucket}.${region}.aliyuncs.com"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url")
    if [ "$code" = "200" ]; then
      echo "[PUBLIC] $url"
    elif [ "$code" = "403" ]; then
      echo "[EXISTS] $url"
    fi
  done
done

# #### 自定义Bucket枚举 (腾讯云COS) ####
for bucket in $(cat bucket_names.txt); do
  for region in $(cat cos_regions.txt); do
    url="https://${bucket}.cos.${region}.myqcloud.com"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url")
    if [ "$code" = "200" ]; then
      echo "[PUBLIC] $url"
    elif [ "$code" = "403" ]; then
      echo "[EXISTS] $url"
    fi
  done
done
```

### 8.2 Bucket 命名字典

```
云服务商Bucket命名规律:
  阿里云 OSS:  {name}-{env}.oss-{region}.aliyuncs.com
  腾讯云 COS:  {name}-{env}.cos.{region}.myqcloud.com
  AWS S3:      {name}-{env}.s3.amazonaws.com
  华为云 OBS:  {name}-{env}.obs.{region}.myhuaweicloud.com
  七牛 Kodo:   {name}.qiniucdn.com

命名字典生成维度:
  前缀: 公司名/简称/英文名/缩写/拼音/品牌/产品/APP名
  环境: prod, dev, test, staging, uat, pre, sandbox, gray, canary
  功能: static, img, image, video, media, upload, download, file
         backup, log, archive, data, sql, dump
         source, src, wwwroot, htdocs, web, frontend
         config, conf, env, settings, properties, secrets
  地域: shanghai, beijing, hangzhou, shenzhen, guangzhou
         hongkong, singapore, tokyo, frankfurt, chengdu

组合规则:
  {name}-{env}        → aliyun-prod
  {name}{env}         → aliyunprod
  {env}-{name}        → prod-aliyun
  {env}.{name}        → prod.aliyun
  {name}              → aliyun
```

### 8.3 公开Bucket内容探测

```bash
# #### 阿里云OSS List ####
curl -s "https://{bucket}.oss-{region}.aliyuncs.com/?prefix&max-keys=1000" | \
  grep -oP '<Key>[^<]+</Key>' | sed 's/<[^>]*>//g'

# #### AWS S3 List (需要List权限) ####
aws s3 ls s3://{bucket}/ --no-sign-request 2>/dev/null

# #### 手动遍历敏感路径 ####
PATHS=(
  "backup/" "database/" "db_backup/" "sql/" "dump/"
  "config/" "conf/" "env/" "settings/" "properties/"
  "logs/" "log/" "access_log/" "error_log/"
  "source/" "src/" "wwwroot/" "htdocs/" "web/"
  ".git/" ".svn/" ".env" "wp-config.php" "web.config"
  "upload/" "files/" "data/" "assets/"
)

for path in "${PATHS[@]}"; do
  curl -s -o /dev/null -w "$path → %{http_code}\n" \
    "https://{bucket}.oss-{region}.aliyuncs.com/$path"
done

# #### 优先搜索后缀 ####
# .sql, .sql.gz, .tar.gz, .zip, .7z, .rar    → 数据库/源码备份
# .env, .properties, .yml, .yaml, .json       → 配置文件
# .pem, .key, .crt, .cer, .p12, .pfx          → 证书密钥
# .log, .txt, .csv, .xlsx                     → 日志/数据
```

---

## 九、主动探测安全控制

### 9.1 速率控制

```bash
# 所有主动探测工具必须设置延迟参数
# 通用规则: 每个目标至少100ms延迟

# masscan: --rate 限制每秒发包数
masscan {target} -p1-65535 --rate 1000  # 不要超过5000

# nmap: -T 控制速度等级 (0-5, 默认T3)
nmap -T3 {target}         # 推荐T3, 平衡速度和稳定性
nmap -T2 {target}         # 慢速, 降低对目标影响

# httpx: -rl 限制每秒请求数
httpx -rl 50 {targets}     # 每秒50个请求

# nuclei: -rl 限制 + -bs 限制并发
nuclei -rl 30 -bs 30 {targets}

# 自定义curl间隔
sleep 0.5  # 每次请求间隔500ms
```

### 9.2 代理配置

```bash
# HTTP代理 (使用授权测试出口或隔离网络)
export HTTP_PROXY="http://proxy_ip:port"
export HTTPS_PROXY="http://proxy_ip:port"

# 工具级代理
nmap --proxies http://proxy:8080
httpx -proxy http://proxy:8080

# SOCKS5代理
# proxychains 包装
proxychains4 nmap -sT -p- {target}
```

### 9.3 操作日志模板

```markdown
## 主动探测日志 — 目标公司

**探测时间段**: 2026-01-15 10:00-12:00
**甲方确认人**: XXX
**操作IP**: x.x.x.x (已加入白名单)

| 时间 | 操作 | 目标 | 工具 | 命令 | 结果 | 备注 |
|------|------|------|------|------|------|------|
| 10:00 | 子域名爆破 | target.com | oneforall | oneforall --target ... | 发现87个存活子域 | - |
| 10:15 | 端口扫描 | x.x.x.0/24 | nmap | nmap -sS -sV ... | 发现12个Web端口 | - |
| 10:30 | CDN穿透 | target.com | dig+curl | 子域名解析 | 获取真实IP: x.x.x.x | - |
| 10:45 | 指纹识别 | Web列表 | httpx | httpx -tech-detect | 识别到Spring Boot等 | - |
| 11:00 | Host碰撞 | Web IPs | curl | Host碰撞脚本 | 发现内部oa系统 | - |
| 11:30 | Bucket枚举 | target | 自定义脚本 | OSS枚举 | 发现公开Bucket: xxx | - |

### 异常记录
- 10:18 WAF返回429限流 → 已降低httpx速率到30req/s
- 10:25 某IP无响应 → 已标记为无效，跳过后续扫描
- 无其他异常
```

---

## 十、完整工具链速查

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 阶段        │ 工具               │ 用途               │ 速率要求             │
├──────────────────────────────────────────────────────────────────────────────┤
│ DNS爆破     │ OneForAll          │ 子域名深度枚举     │ 内置延迟1s           │
│ DNS爆破     │ Subfinder          │ 多源子域名收集     │ 适量                │
│ DNS解析     │ puredns            │ 高精度解析+泛解析  │ 可控                │
│ 端口扫描    │ Nmap               │ 端口+服务版本      │ -T3 (-T2更低影响)   │
│ 端口扫描    │ Masscan            │ 快速C段端口扫描    │ --rate ≤ 5000       │
│ Web存活     │ httpx              │ Web存活+指纹       │ -rl 50              │
│ 指纹识别    │ WhatWeb / Wappalyzer│ CMS识别            │ 适量                │
│ WAF检测     │ wafw00f            │ WAF类型识别        │ 适量                │
│ 模板识别    │ nuclei             │ 技术栈/暴露面识别  │ -rl 30              │
│ Bucket枚举  │ s3scanner/cloud_enum│ 对象存储发现       │ 适量                │
│ 代理控制    │ proxychains        │ SOCKS5代理包装     │ -                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 十一、安全守则

```
1. 授权确认: 每次主动探测前确认授权范围，超出范围立即停止
2. 速率控制: 所有主动探测添加延迟参数，避免对目标服务造成明显压力
3. 出口隔离: 主动探测使用授权测试出口或隔离网络，与日常办公网络隔离
4. 日志记录: 所有探测操作记录时间戳、目标、方法、结果
5. 数据隔离: 产出物加密存储，演练结束后按甲方要求处置
6. 禁止利用: 发现漏洞立即记录，不得在未授权情况下深入利用
7. 范围优先: 甲方给定的演练范围优先于侦察发现的所有资产
8. 紧急停止: 接到甲方通知或发现异常立即停止所有操作
9. 被动优先: 始终先完成全部被动收集，再用主动探测补充
10. 资产确权: 所有发现资产必须通过多维度交叉确认归属
```
