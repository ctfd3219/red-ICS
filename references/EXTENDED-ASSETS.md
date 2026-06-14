---
name: extended-assets
description: >
  扩展资产侦察 — 小程序、公众号、APP 全方位收集与深度分析。
  覆盖微信/支付宝/百度/抖音多平台小程序发现与反编译、公众号矩阵收集、
  Android/iOS APP 反编译与硬编码凭据提取、API端点获取。
metadata:
  tags: "miniprogram,app,official-account,apk,ipa,reverse-engineering,recon"
  category: "offensive-security"
  version: "1.0.0"
---

# EXTENDED-ASSETS — 小程序 / 公众号 / APP 收集

> **目标**：发现目标组织的小程序、公众号和移动APP，通过反编译提取API端点、硬编码凭据、内部域名等。
> **关键**：小程序和APP往往包含与Web端不同的API后门地址、测试环境、硬编码密钥。

---

## 一、小程序发现

### 1.1 多平台搜索

```
微信小程序:
  □ 微信App内搜索: 公司名 / 品牌名 / 产品名
  □ 微信 → 发现 → 小程序 → 顶部搜索框
  □ 来源: 公司官网二维码 / 公众号关联小程序 / 推文内链接
  □ 第三方平台: 阿拉丁指数 (aldwx.com) / 知晓程序

支付宝小程序:
  □ 支付宝App内搜索: 公司名 / 品牌名
  □ 支付宝开放平台 → 小程序搜索

百度小程序:
  □ 百度App内搜索: 公司名 / 品牌名

抖音/头条小程序:
  □ 抖音App内搜索
  □ 头条App内搜索

枚举关键词策略:
  □ 公司全称、简称、英文名
  □ 品牌名、产品名、服务名
  □ 行业通用关键词: {行业}+服务 / {行业}+助手 / {行业}+平台
  □ 竞争对手小程序 → 推测目标可能的小程序命名模式
```

### 1.2 iOS 微信小程序缓存位置

```
iOS 微信小程序缓存路径 (需越狱):
  /var/mobile/Containers/Data/Application/{微信UUID}/Library/WechatPrivate/
  或通过 iTunes 备份 → 提取 Applet 目录
```

---

## 二、公众号发现

### 2.1 微信搜索

```
微信内搜索:
  □ 微信 → 通讯录 → 公众号 → 顶部搜索
  □ 搜索词: 公司全称 / 简称 / 品牌名 / 产品名

搜索策略:
  □ 公司全称精确搜索
  □ 公司简称模糊搜索
  □ 品牌名/产品名搜索
  □ 子公司/关联公司名搜索（可能有独立公众号）
  □ 地区+公司名（如 "上海XX科技"）

识别要点:
  □ 公众号名称 → 关联域名推测
  □ 公众号简介 → 业务描述、官网链接
  □ 公众号菜单 → 跳转的URL/H5页面 → API端点
  □ 公众号认证主体 → 确认归属组织
  □ 关联小程序 → 从公众号资料页查看
```

### 2.2 公众号菜单提取

```
关注公众号后:
  □ 逐个点击底部菜单按钮
  □ 观察跳转的URL/H5页面地址
  □ 抓包分析菜单请求的API
  □ 提取服务器地址 → 可能为后端服务地址

关键信息:
  □ 菜单跳转URL → 域名 + 路径 → 新的攻击面
  □ 网页授权域名 → 公众号设置中的JS安全域名
  □ 业务域名 → 公众号设置中的业务域名
```

---

## 三、小程序反编译与深度分析

### 3.1 微信小程序PC端缓存位置

```
Windows:
  C:\Users\{用户名}\Documents\WeChat Files\{微信ID}\Applet\

Mac:
  ~/Library/Application Support/微信/Applet/

缓存目录结构:
  Applet/
  ├── {小程序AppID}/
  │   └── {版本号}/
  │       └── __APP__.wxapkg          → 主包
  │       └── __APP__#.wxapkg         → 分包
  └── ...
```

### 3.2 小程序反编译

```bash
# #### 反编译工具 ####
# wxappUnpacker: https://github.com/qwerty472123/wxappUnpacker

# 安装
git clone https://github.com/qwerty472123/wxappUnpacker.git
cd wxappUnpacker
npm install

# 解包主包
node wuWxapkg.js __APP__.wxapkg

# 解包分包（如果有）
node wuWxapkg.js __APP__#1.wxapkg
node wuWxapkg.js __APP__#2.wxapkg

# #### 其他反编译工具 ####
# 1. unveilr (Go语言)
#    https://github.com/nicoxiang/unveilr
#    unveilr wxapp ./__APP__.wxapkg

# 2. wxappUnpacker (Python版)
#    https://github.com/leo9960/wechat-app-unpack
```

### 3.3 从小程序代码提取关键信息

```bash
# #### 提取所有URL ####
grep -r -oP 'https?://[a-zA-Z0-9./_?=&%-]+' unpacked/ | sort -u > miniapp_urls.txt

# #### 提取API端点 ####
grep -r -oP '["\x27]\/api\/[^"\x27]+' unpacked/ | sort -u
grep -r -oP '["\x27]/v[0-9]+/[^"\x27]+' unpacked/ | sort -u

# #### 提取域名列表 ####
grep -r -oP '[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' unpacked/ | sort -u > miniapp_domains.txt

# #### 提取 AppID / Secret ####
grep -r -iE '(appid|app_id|appsecret|app_secret)\s*[=:]\s*["\x27][^"\x27]+["\x27]' unpacked/

# #### 提取硬编码凭据 ####
grep -r -iE '(api[_-]?key|api[_-]?secret|access[_-]?key|secret[_-]?key|token|sign[_-]?key|encrypt[_-]?key|password)\s*[=:]\s*["\x27][^"\x27]+["\x27]' unpacked/

# #### 提取阿里云AK ####
grep -r -oP 'LTAI[0-9A-Za-z]{16,20}' unpacked/

# #### 提取腾讯云AK ####
grep -r -oP 'AKID[0-9A-Za-z]{32}' unpacked/

# #### 提取AWS AK ####
grep -r -oP 'AKIA[0-9A-Z]{16}' unpacked/

# #### 提取内部IP ####
grep -r -oP '\b(10|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9.]+\b' unpacked/

# #### 提取内部域名 ####
grep -r -oP '[a-zA-Z0-9.-]+\.(internal|local|lan|dev|test|staging|uat)\.[a-zA-Z]+' unpacked/

# #### 提取微信支付MCHID ####
grep -r -oP '(mch_id|mchid|MCH_ID)\s*[=:]\s*["\x27]?[0-9]{10}["\x27]?' unpacked/

# #### 提取WebSocket ####
grep -r -oP '(ws|wss)://[a-zA-Z0-9./_?=%-]+' unpacked/
```

### 3.4 小程序关键文件分析

```
□ project.config.json → appid、projectname、云开发环境ID
□ app.json → 页面路由、权限配置、tabBar、subPackages
□ app.js → 全局变量、初始化逻辑、登录流程
□ 各页面js → 业务逻辑、API请求、数据处理
□ utils/ → 工具函数(加密/签名/请求封装)
□ config/ → 环境配置(dev/test/prod)
□ request.js / api.js → 统一的API请求封装(完整API清单)
□ cloudfunctions/ → 微信云函数(可能有隐藏API)

第三方SDK识别:
  □ wx.request → 网络请求
  □ wx.login → 登录认证
  □ wx.requestPayment → 微信支付
  □ wx.getLocation → 地图定位 (可能含高德/腾讯地图Key)
  □ wx.cloud → 微信云开发
  □ 第三方推送 (极光/个推)
```

---

## 四、APP 发现

### 4.1 Android APP 发现

```
应用商店搜索:
  □ 华为应用市场 (appgallery.huawei.com)
  □ 小米应用商店 (app.mi.com)
  □ OPPO软件商店
  □ vivo应用商店
  □ 应用宝 (sj.qq.com)
  □ 豌豆荚 (wandoujia.com)
  □ 酷安 (coolapk.com)
  □ Google Play (play.google.com)

第三方APK下载:
  □ APKPure (apkpure.net) → 含历史版本
  □ APKMirror (apkmirror.com)
  □ APKCombo (apkcombo.com)
  □ APKMonk
```

### 4.2 iOS APP 发现

```
App Store 搜索:
  □ 公司名 / 品牌名 / 开发者名
  □ 查看同一开发者账号下的所有APP
  □ TestFlight (如有邀请链接)

发现策略:
  □ 公司全称/简称/英文名
  □ 品牌名/产品名
  □ 同一开发者账号下的APP (查看开发者页面)
  □ 公司软著/专利中提到的APP名称
  □ 招聘JD中提到的APP项目
```

---

## 五、APK 反编译与深度分析

### 5.1 反编译工具链

```bash
# #### 1. apktool — 反编译资源+smali ####
apktool d target.apk -o apk_output/
# 输出: apk_output/AndroidManifest.xml (明文)
#       apk_output/res/ (资源文件)
#       apk_output/smali/ (smali字节码)

# #### 2. jadx — 反编译为Java源码 (推荐) ####
jadx -d jadx_output/ target.apk
jadx-gui target.apk  # GUI模式，支持交叉引用、全文搜索

# #### 3. GDA (GJoy Dex Analyzer) — 国产反编译利器 ####
# 支持: 直接查看dex、字符串搜索、交叉引用、脱壳

# #### 4. apkleaks — 自动扫描硬编码凭据 ####
# https://github.com/dwisiswant0/apkleaks
apkleaks -f target.apk -o apkleaks_result.json

# #### 5. MobSF — 移动安全自动化分析平台 ####
# https://github.com/MobSF/Mobile-Security-Framework-MobSF
# Docker 一键启动:
docker run -it -p 8000:8000 opensecurity/mobile-security-framework-mobsf
```

### 5.2 AndroidManifest.xml 分析

```bash
# 提取权限列表
cat apk_output/AndroidManifest.xml | grep -oP 'android\.permission\.[A-Z_]+' | sort -u

# 提取Activity (所有页面入口)
grep -oP '<activity[^>]*android:name="([^"]+)"' apk_output/AndroidManifest.xml | sort -u

# 提取Service (后台服务)
grep -oP '<service[^>]*android:name="([^"]+)"' apk_output/AndroidManifest.xml | sort -u

# 提取Receiver (广播接收器)
grep -oP '<receiver[^>]*android:name="([^"]+)"' apk_output/AndroidManifest.xml | sort -u

# 提取Provider (内容提供者)
grep -oP '<provider[^>]*android:name="([^"]+)"' apk_output/AndroidManifest.xml | sort -u

# 提取Intent-Filter中的scheme/host
grep -oP 'android:(scheme|host)="([^"]+)"' apk_output/AndroidManifest.xml | sort -u

# 查看debuggable标志
grep -i 'debuggable' apk_output/AndroidManifest.xml

# 查看allowBackup标志
grep -i 'allowBackup' apk_output/AndroidManifest.xml
```

### 5.3 从 APK 提取关键信息

```bash
# #### 提取所有URL (Java源码) ####
grep -r -oP 'https?://[a-zA-Z0-9./_?=&%:\-]+' jadx_output/ | sort -u > app_urls.txt

# #### 提取API端点 ####
grep -r -oP '["\x27]\/api\/[^"\x27]+' jadx_output/ | sort -u
grep -r -oP '["\x27]/v[0-9]+/[^"\x27]+' jadx_output/ | sort -u

# #### 提取域名列表 ####
grep -r -oP '[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' jadx_output/ | sort -u > app_domains.txt

# #### 提取BASE_URL / HOST / ENDPOINT ####
grep -r -iE '(base[_-]?url|host[_-]?name|server[_-]?url|endpoint|domain)\s*[=:]\s*["\x27][^"\x27]+["\x27]' jadx_output/ | sort -u

# #### 提取硬编码凭据 ####
grep -r -iE '(api[_-]?key|api[_-]?secret|app[_-]?key|app[_-]?secret|access[_-]?key|secret[_-]?key|token|sign[_-]?key|encrypt[_-]?key|password|aes[_-]?key|des[_-]?key)\s*[=:]\s*["\x27][^"\x27]+["\x27]' jadx_output/ > app_secrets.txt

# #### 提取阿里云AK ####
grep -r -oP 'LTAI[0-9A-Za-z]{16,20}' jadx_output/ | sort -u

# #### 提取腾讯云AK ####
grep -r -oP 'AKID[0-9A-Za-z]{32}' jadx_output/ | sort -u

# #### 提取AWS AK ####
grep -r -oP 'AKIA[0-9A-Z]{16}' jadx_output/ | sort -u

# #### 提取七牛AK ####
grep -r -oP '[a-zA-Z0-9\-_]{30,50}' jadx_output/ | grep -v '/' | sort -u

# #### 提取微信AppID ####
grep -r -oP 'wx[0-9a-zA-Z]{16}' jadx_output/ | sort -u

# #### 提取内部IP ####
grep -r -oP '\b(10|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9.]+\b' jadx_output/ | sort -u

# #### 提取内部域名 ####
grep -r -oP '[a-zA-Z0-9.-]+\.(internal|local|lan|dev|test|staging|uat)\.[a-zA-Z]+' jadx_output/ | sort -u

# #### 提取第三方SDK Key ####
grep -r -iE '(jpush|getui|xmpush|huawei|xiaomi|amap|lbs|baidu|tencent|bugly|umeng|share|pay|push|map|ad|crash)' jadx_output/ | grep -iE 'key|appid|id|secret|token' | sort -u

# #### 提取数据库连接串 ####
grep -r -iE '(jdbc|mysql|mssql|oracle|postgresql|mongodb|redis|sqlite)://' jadx_output/ | sort -u

# #### 提取加密/签名相关 ####
grep -r -iE '(MD5|SHA|AES|DES|RSA|HMAC|Base64|encode|decode|encrypt|decrypt|sign|verify)' jadx_output/ | grep -iE 'key|secret|iv|salt|key' | sort -u
```

### 5.4 so 库字符串提取

```bash
# 提取arm64-v8a架构so库中的字符串
strings apk_output/lib/arm64-v8a/*.so | grep -iE 'key|secret|token|http|api|url|host|password|server' | sort -u

# 提取armeabi-v7a架构
strings apk_output/lib/armeabi-v7a/*.so | grep -iE 'key|secret|token|http|api|url|host|password' | sort -u

# 提取x86架构 (模拟器)
strings apk_output/lib/x86/*.so | grep -iE 'key|secret|token|http|api' | sort -u

# 提取所有IP地址
strings apk_output/lib/arm64-v8a/*.so | grep -oP '\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b' | sort -u
```

### 5.5 assets 资源分析

```bash
# 解压APK (apk本质是zip)
unzip target.apk -d apk_assets/
# 或: cp target.apk target.zip && unzip target.zip -d apk_assets/

# 分析assets目录中的配置文件
find apk_assets/assets/ -type f | xargs file | grep -iE 'json|xml|text|config'

# 提取JSON配置文件中的URL/Key
grep -r -oP 'https?://[^\"]+' apk_assets/assets/ | sort -u

# 提取可能的配置文件
find apk_assets/ -name "*.json" -o -name "*.xml" -o -name "*.properties" -o -name "*.plist" -o -name "*.cer" -o -name "*.pem" -o -name "*.p12" -o -name "*.jks" -o -name "*.bks"
```

---

## 六、iOS APP 分析

### 6.1 IPA 基本分析

```bash
# #### 解压ipa ####
# ipa 本质是 zip 压缩包
unzip target.ipa -d ipa_output/

# 查看包内容
ls -la ipa_output/Payload/*.app/

# #### Info.plist 分析 ####
# 提取Bundle ID
plutil -p ipa_output/Payload/*.app/Info.plist | grep -i 'CFBundleIdentifier'

# 提取版本号
plutil -p ipa_output/Payload/*.app/Info.plist | grep -i 'CFBundleShortVersionString'

# 提取URL Schemes
plutil -p ipa_output/Payload/*.app/Info.plist | grep -iE 'CFBundleURLSchemes|url'

# 提取ATS配置 (App Transport Security)
plutil -p ipa_output/Payload/*.app/Info.plist | grep -iA5 'NSAppTransportSecurity'

# 提取权限声明
plutil -p ipa_output/Payload/*.app/Info.plist | grep -iE 'UsageDescription|Privacy'
```

### 6.2 二进制文件分析

```bash
# #### 提取二进制中的字符串 ####
BINARY="ipa_output/Payload/*.app/$(basename ipa_output/Payload/*.app .app)"

# 提取URL
strings "$BINARY" | grep -oP 'https?://[a-zA-Z0-9./_?=&%:\-]+' | sort -u

# 提取硬编码凭据
strings "$BINARY" | grep -iE '(api[_-]?key|secret|token|password|credential)'

# 提取内部IP
strings "$BINARY" | grep -oP '\b(10|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9.]+\b'

# 提取所有可读字符串 (关注长度>10的)
strings -n 10 "$BINARY" > ios_strings.txt
```

### 6.3 资源文件分析

```bash
# #### 分析数据库文件 ####
find ipa_output/ -name "*.sqlite" -o -name "*.db" -o -name "*.realm"
# 用 sqlite3 打开:
sqlite3 path/to/file.sqlite ".tables"
sqlite3 path/to/file.sqlite "SELECT * FROM sqlite_master WHERE type='table';"

# #### 分析plist文件 ####
find ipa_output/ -name "*.plist" | while read f; do
  echo "=== $f ==="
  plutil -p "$f" 2>/dev/null
done

# #### 分析json配置文件 ####
find ipa_output/ -name "*.json" | xargs grep -l -iE 'url|host|key|secret|token' 2>/dev/null

# #### 查找证书文件 ####
find ipa_output/ -name "*.p12" -o -name "*.pem" -o -name "*.crt" -o -name "*.cer" -o -name "*.der"
```

---

## 七、APP 动态抓包分析

### 7.1 代理配置

```
代理工具:
  □ Burp Suite (推荐)
  □ Fiddler
  □ Charles
  □ mitmproxy

Android 配置:
  1. WiFi设置 → 代理 → 手动 → 填写代理IP:Port
  2. 浏览器访问 http://burp 下载CA证书
  3. 安装证书: 设置 → 安全 → 从SD卡安装
  4. Android 7+ 需root或修改APP (系统证书不信任用户证书)

iOS 配置:
  1. WiFi设置 → HTTP代理 → 手动 → 代理IP:Port
  2. Safari访问 http://burp 下载CA证书
  3. 设置 → 通用 → 关于 → 证书信任设置 → 开启
```

### 7.2 SSL Pinning 绕过

```
常见绕过方法:
  □ Frida + objection: 动态HOOK绕过证书校验
    objection -g com.xxx.xxx explore
    android sslpinning disable
    ios sslpinning disable

  □ Xposed + JustTrustMe (Android)
    安装JustTrustMe模块 → 自动信任所有证书

  □ Frida脚本 (通用):
    frida -U -f com.xxx.xxx -l ssl_bypass.js --no-pause

  □ 修改APK:
    apktool d → 修改network_security_config.xml → 重新打包

  □ VirtualXposed / 太极 (免root)
```

### 7.3 抓包目标

```
抓包分析重点:
  □ 完整API请求 + 响应 (URL/Method/Headers/Body)
  □ 请求签名算法 (Header中的sign/token生成逻辑)
  □ 加密字段识别 (请求/响应体的base64/加密值)
  □ 认证流程 (登录/Token获取/Token刷新)
  □ WebSocket通信
  □ 第三方SDK上报

API文档推断:
  □ 从抓包中汇总所有API端点
  □ 记录每个端点: URL + Method + Content-Type + 参数名 + Auth要求
  □ 识别参数命名规范 (驼峰/下划线/拼音)
```

---

## 八、输出格式

```markdown
## 扩展资产报告 — XX公司

### 一、小程序清单
| 名称 | 平台 | AppID | 主体 | 功能 | API域名 |
|------|------|-------|------|------|---------|
| XX助手 | 微信 | wx1234567890 | XX科技 | 用户服务 | api.xx.com |
| XX商城 | 微信 | wx0987654321 | 上海XX信息技术 | 电商 | shop.xx.com |
| XX服务+ | 支付宝 | 20240xxxxx | XX科技 | 便民服务 | ali.xx.com |

### 二、公众号清单
| 名称 | 类型 | 微信号 | 认证主体 | 关联小程序 | 菜单URL |
|------|------|--------|---------|-----------|---------|
| XX科技 | 服务号 | xx-tech | XX科技有限公司 | XX助手 | https://m.xx.com |
| XX招聘 | 订阅号 | xx-hr | XX科技有限公司 | - | - |

### 三、APP清单
| 名称 | 平台 | 包名/BundleID | 版本 | 下载渠道 | 开发者 |
|------|------|-------------|------|---------|--------|
| XX助手 | Android | com.xx.assistant | 3.2.1 | 应用宝 | XX科技 |
| XX服务 | iOS | com.xx.service | 2.8.0 | App Store | XX科技 |

### 四、API端点提取 (来自APP/小程序)
| 端点 | HTTP方法 | Auth | 来源 |
|------|---------|------|------|
| https://api.xx.com/v1/user/login | POST | 否 | LoginActivity |
| https://api.xx.com/v1/user/info | GET | Bearer | UserInfoActivity |
| https://api.xx.com/v1/order/list | GET | Sign | OrderListActivity |
| https://api.xx.com/upload/file | POST | Token | FileUpload |

### 五、硬编码凭据
| 类型 | 值 | 位置 | 风险等级 |
|------|-----|------|---------|
| 阿里云OSS AK | LTAI5txxxx | com/xx/utils/OSSManager.java | 高-云资源访问 |
| 微信AppID | wx1234567890 | AndroidManifest.xml | 中-身份标识 |
| AES Encryption Key | abc123def456... | com/xx/utils/EncryptUtil.java | 高-通信解密 |
| 内部API地址 | http://192.168.1.100:8080 | com/xx/config/ApiConfig.java | 高-内网探测 |
| 高德地图Key | b2c3d4e5f6... | AndroidManifest.xml | 低-公开Key |

### 六、内部域名/IP
| 地址 | 类型 | 来源 | 推测用途 |
|------|------|------|---------|
| 192.168.1.100:8080 | 内网IP | APK硬编码 | 内部API服务 |
| api-dev.xx.com | 内部域名 | APK硬编码 | 开发环境API |
| 10.0.1.50 | 内网IP | JS文件 | 测试服务器 |

### 七、第三方SDK
| SDK | 平台 | 用途 | 提取到的Key |
|-----|------|------|------------|
| 极光推送 | Android/iOS | 消息推送 | AppKey=xxx |
| 高德地图 | Android/iOS | 定位/地图 | Key=xxx |
| 微信支付 | Android/iOS | 支付 | MCHID=xxx |
| Bugly | Android | 崩溃统计 | AppID=xxx |
| 友盟+ | Android/iOS | 统计分析 | AppKey=xxx |
```

---

## 九、工具链速查

```
┌──────────────────────────────────────────────────────────────────────┐
│ 类型        │ 工具               │ 用途                  │ 平台      │
├──────────────────────────────────────────────────────────────────────┤
│ 小程序发现  │ 微信/支付宝/百度App │ 搜索+使用小程序        │ All       │
│ 小程序反编译│ wxappUnpacker       │ 解包wxapkg            │ Node.js   │
│ 小程序反编译│ unveilr             │ 解包wxapkg (Go版)     │ Go        │
│ APK发现     │ 华为/小米/应用宝等   │ 应用商店搜索           │ Web       │
│ APK下载     │ APKPure/APKMirror   │ 含历史版本            │ Web       │
│ APK反编译   │ apktool             │ 资源+smali反编译      │ Java      │
│ APK反编译   │ jadx                │ dex→Java源码 (推荐)   │ Java      │
│ APK反编译   │ GDA                 │ 国产反编译利器         │ Windows   │
│ APK扫描     │ apkleaks            │ 自动扫描硬编码凭据     │ Python    │
│ APK扫描     │ MobSF               │ 自动化安全分析平台     │ Docker    │
│ IPA分析     │ class-dump / Hopper │ Mach-O反编译          │ macOS     │
│ 动态调试    │ Frida / objection   │ SSL Pinning绕过       │ All       │
│ 动态调试    │ Xposed + JustTrustMe│ Android证书信任       │ Android   │
│ 抓包        │ Burp Suite / Charles│ HTTP/HTTPS中间人代理  │ All       │
└──────────────────────────────────────────────────────────────────────┘
```
