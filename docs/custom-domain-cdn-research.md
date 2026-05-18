# 自定义域名 & CDN 加速方案调研文档

> **调研范围**: E03（自定义域名配置）+ E04（CDN加速配置）
> **项目**: 机械师大百科
> **当前部署**: GitHub Pages — `https://windwu333.github.io/jixie-baike/`
> **日期**: 2026-05-18

---

## 目录

1. [当前状态分析](#1-当前状态分析)
2. [自定义域名可用性检查](#2-自定义域名可用性检查)
3. [方案 A: 腾讯云 CDN + 自定义域名（国内访问优化）](#3-方案-a-腾讯云-cdn--自定义域名国内访问优化)
4. [方案 B: Cloudflare CDN + 自定义域名（免备案方案）](#4-方案-b-cloudflare-cdn--自定义域名免备案方案)
5. [方案对比](#5-方案对比)
6. [百度站长平台 & 百度统计接入](#6-百度站长平台--百度统计接入)
7. [推荐建议](#7-推荐建议)
8. [附录: 名词解释](#8-附录-名词解释)

---

## 1. 当前状态分析

### 1.1 当前架构

```
用户 → GitHub Pages (windwu333.github.io/jixie-baike/)
        ├── 无自定义域名
        ├── 无 CDN 加速
        ├── 无 TLS 证书管理（由 GitHub Pages 自动提供 *.github.io 证书）
        └── 国内访问速度: 不稳定（GitHub 国内节点时快时慢）
```

### 1.2 项目关键配置

| 项目 | 当前值 |
|------|--------|
| baseURL | `https://windwu333.github.io/jixie-baike/` |
| 站点名 | 机械师大百科 |
| Hugo 版本 | 0.161.1 |
| 主题 | PaperMod |
| 部署方式 | GitHub Actions → GitHub Pages |
| sitemap | 已生成（17,240+ 条 URL） |
| robots.txt | 已配置（Allow: /） |

### 1.3 内容规模

- 站点地图包含 **17,240+ 条 URL**（大量百科词条页面）
- 意味着启用 CDN 后单次预热（或回源）流量较大

---

## 2. 自定义域名可用性检查

### 2.1 已购域名搜索

> **⚠️ 未发现任何域名购买记录**

在本机文件系统、SSH 配置、下载目录、文档目录中均未找到：
- 域名注册/续费凭证（如 `.com` / `.cn` / `.top` 等注册确认邮件）
- Whois 查询记录
- DNS 配置文件
- 现有 CNAME 记录

### 2.2 域名是否需要购买

**结论：用户（windwu）尚未购买域名。**

如需使用自定义域名，需要先完成以下步骤（由用户在域名注册商完成）：

| 步骤 | 说明 | 参考价格（年） |
|------|------|---------------|
| 1. 注册域名商账号 | 腾讯云 DNSPod / 阿里云万网 / NameSilo / GoDaddy 等 | 免费 |
| 2. 购买域名 | 建议 jixiebaike.cn（国内友好）或 jixiebaike.com（国际化） | ¥30-80 |
| 3. 实名认证 | .cn 域名需实名认证（个人身份证即可） | 免费 |
| 4. ICP 备案（若选方案 A） | 腾讯云或阿里云备案系统提交（7-20 工作日） | 免费 |

**推荐域名候选**（需确认是否被注册）：

| 域名 | 适用场景 | ICP 备案要求 |
|------|---------|-------------|
| `jixiebaike.cn` | 国内用户为主，优先推荐 | ✅ 必须备案 |
| `jixiebaike.com` | 国际化 + 国内用户 | ❌ 不备案也能用（但国内 CDN 仍需备案） |
| `jixiebaike.top` | 低成本替代方案 | ✅ 必须备案 |
| `jxbaike.cn` | 简短好记 | ✅ 必须备案 |

---

## 3. 方案 A: 腾讯云 CDN + 自定义域名（国内访问优化）

### 3.1 适用场景

- **目标用户主要在國內**（中国大陆）
- 需要**极速访问体验**（腾讯云全国 2800+ 节点）
- 接受 **ICP 备案流程**（7-20 个工作日）

### 3.2 整体架构

```
用户 → 腾讯云 CDN (国内 2800+ 节点)
        → 腾讯云 DNS (DNSPod)
            → 源站: GitHub Pages (windwu333.github.io/jixie-baike/)
        同时: 腾讯云 SSL 证书（免费或付费）
```

### 3.3 前置条件

| # | 条件 | 费用 | 时间 |
|---|------|------|------|
| 1 | 已注册域名（如 jixiebaike.cn） | ¥30-80/年 | 即时 |
| 2 | ICP 备案完成 | 免费 | 7-20 工作日 |
| 3 | 腾讯云账号 | 免费 | 即时 |
| 4 | DNSPod 域名接入 | 免费 | 即时 |

### 3.4 详细配置步骤

#### 步骤 1: 域名购买 & ICP 备案

1. 在 **腾讯云 DNSPod**（或阿里云万网）注册账号
2. 搜索并购买域名（推荐 `jixiebaike.cn`）
3. 完成域名实名认证（上传身份证，约 1-3 天审核）
4. **ICP 备案** — 进入 [腾讯云备案系统](https://beian.cloud.tencent.com/)
   - 填写主体信息（个人备案）
   - 填写网站信息（网站名称：机械师大百科）
   - 提交管局审核（各省平均 7-20 工作日）
5. 备案通过后获取 **ICP 备案号**（如：京ICP备2026XXXXXX号-1）

#### 步骤 2: DNSPod DNS 配置

1. 在 DNSPod 添加域名
2. 将域名的 NS 记录指向 DNSPod 的 DNS 服务器：
   ```
   f1g1ns1.dnspod.net
   f1g1ns2.dnspod.net
   ```
3. 添加 DNS 记录：

| 记录类型 | 主机记录 | 记录值 | 说明 |
|---------|---------|-------|------|
| CNAME | `@` | `windwu333.github.io` | 根域名指向 GitHub |
| CNAME | `www` | `windwu333.github.io` | www 子域名指向 GitHub |
| TXT | `@` | `_github-pages-challenge-windwu333.jixiebaike.cn` | 可选: 验证所有权 |

#### 步骤 3: GitHub Pages 自定义域名配置

1. 打开 GitHub 仓库 `windwu333/jixie-baike` → Settings → Pages
2. 在 "Custom domain" 输入 `jixiebaike.cn`（或 `www.jixiebaike.cn`）
3. 点击 Save — GitHub 会自动创建 `/jixie-baike/CNAME` 文件
4. 勾选 "Enforce HTTPS"（GitHub 会自动申请 Let's Encrypt 证书）
5. 更新 `hugo.toml` 中的 `baseURL`:
   ```toml
   baseURL = "https://jixiebaike.cn/"
   ```

#### 步骤 4: 腾讯云 CDN 配置

1. 进入 **腾讯云 CDN 控制台** → 域名管理 → 添加域名
2. 配置基本信息：

| 参数 | 值 |
|------|-----|
| 加速域名 | `jixiebaike.cn` 和/或 `www.jixiebaike.cn` |
| 加速区域 | **中国境内**（如果已备案） |
| 业务类型 | **静态加速**（静态网页站点） |
| 源站配置 | 源站地址: `windwu333.github.io` |
| | 回源协议: **HTTPS**（GitHub Pages 强制 HTTPS） |
| | 回源 HOST: 不填写（或填 `windwu333.github.io`） |

3. 高级配置（推荐）：

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 缓存过期规则 | `.html` → 10分钟/1小时 | HTML 需频繁更新 |
| 缓存过期规则 | `.css, .js` → 7天 | 静态资源长期缓存 |
| 缓存过期规则 | `.png, .jpg, .webp` → 30天 | 图片资源 |
| 缓存过期规则 | `.xml, .json` → 1小时 | sitemap、搜索索引 |
| 智能压缩 | 开启 | 减少传输体积 |
| HSTS 配置 | 开启 | 强制 HTTPS |

4. **等待 DNSPod 的 CNAME 生效**后，CDN 即可接管流量

#### 步骤 5: SSL 证书配置

1. 在腾讯云 **SSL 证书控制台** 申请免费证书（TrustAsia DV）
2. 证书绑定到 CDN 加速域名 `jixiebaike.cn`
3. CDN 控制台启用 HTTPS，选择该证书
4. 开启 **HTTP 自动跳转 HTTPS**

#### 步骤 6: Hugo 配置更新

修改 `hugo.toml`:

```toml
baseURL = "https://jixiebaike.cn/"
canonifyURLs = true   # 确保所有 URL 都使用新域名
```

并确保在 public/ 目录下有一个 `CNAME` 文件（内容为 `jixiebaike.cn`），或者在 Hugo 的 `/static/CNAME` 中放置。

#### 步骤 7: 验证

1. 访问 `https://jixiebaike.cn/` 确认正常
2. 检查网络请求的 CDN 加速效果（响应头中应有 `X-Cache-Lookup` 等信息）
3. 检查 HTTPS 证书是否正确（绿锁标志）
4. GitHub Actions 重新部署后确认自动发布

### 3.5 费用估算

| 项目 | 费用 | 说明 |
|------|------|------|
| 域名注册（.cn） | ¥30-80/年 | 首年优惠价 |
| ICP 备案 | 免费 | 但需要时间 |
| 腾讯云 CDN 外网流量 | ~¥0.18/GB | 静态加速，按量计费 |
| SSL 证书 | 免费 | TrustAsia DV |
| DNSPod DNS | 免费 | 基础版 |
| **合计（预估）** | **¥30-200/年** | 流量不高的情况下 |

**流量估算**: 假设每日 1000 PV，每页平均 500KB，月流量约 15GB，月费约 ¥2.7。

---

## 4. 方案 B: Cloudflare CDN + 自定义域名（免备案方案）

### 4.1 适用场景

- **不想等待 ICP 备案**（7-20 天太长）
- **海外用户较多**或不在意国内访问速度
- **零成本起步**（Cloudflare Free Plan 提供大量免费服务）
- 想要**一站式解决方案**（DNS + CDN + SSL + DDoS 防护）

### 4.2 整体架构

```
用户 → Cloudflare CDN (全球 330+ 城市节点)
        → Cloudflare DNS
            → 源站: GitHub Pages (windwu333.github.io/jixie-baike/)
        同时: Cloudflare SSL（自动免费证书）
              Cloudflare DDoS 防护（免费）
```

### 4.3 前置条件

| # | 条件 | 费用 | 时间 |
|---|------|------|------|
| 1 | 已注册域名（任意后缀） | ¥30-80/年 | 即时 |
| 2 | Cloudflare 账号 | 免费 | 5 分钟 |
| 3 | 域名注册商处可修改 NS 记录 | 免费 | 即时 |

**无需 ICP 备案** — Cloudflare 回源到海外 GitHub Pages，CDN 节点在海外及国内边缘（Cloudflare 在国内有少量合作节点，但不保证稳定性）。

### 4.4 详细配置步骤

#### 步骤 1: 域名购买

1. 在域名注册商（GoDaddy / NameSilo / 腾讯云 / 阿里云）购买域名
2. 推荐 `jixiebaike.com`（不需备案，国际上无障碍）
3. 完成域名实名认证

#### 步骤 2: 注册 Cloudflare 并添加域名

1. 访问 [cloudflare.com](https://cloudflare.com) 注册账号
2. 点击 **"Add a Site"**
3. 输入域名（如 `jixiebaike.com`）
4. 选择 **Free Plan**（免费计划）

#### 步骤 3: 配置 DNS 记录

Cloudflare 会自动扫描现有 DNS 记录。手动配置以下记录：

| 记录类型 | 名称 | 目标 | Proxy 状态 |
|---------|------|------|-----------|
| CNAME | `@` | `windwu333.github.io` | ⚡ Proxy (橙色云朵) |
| CNAME | `www` | `windwu333.github.io` | ⚡ Proxy (橙色云朵) |

> **注意**: Proxy 状态必须为橙色云朵（Proxied），这样才能启用 Cloudflare CDN 和 SSL。

#### 步骤 4: 更换域名 NS 服务器

1. Cloudflare 会提供两个 NS 地址（如 `dara.ns.cloudflare.com`）
2. 回到**域名注册商**的控制台
3. 将域名的 NS 记录更换为 Cloudflare 提供的 NS 地址
4. 等待 DNS 传播（通常 5-30 分钟，最长 48 小时）

#### 步骤 5: 配置 SSL/TLS

1. 进入 Cloudflare Dashboard → SSL/TLS
2. 选择 **"Full (strict)"** 模式（需要源站也有证书）
3. GitHub Pages 自动提供 `*.github.io` 的证书，Full(strict) 模式可正常工作
4. 开启：
   - ✅ Always Use HTTPS
   - ✅ HSTS（可选，建议开启）

#### 步骤 6: GitHub Pages 自定义域名配置

1. GitHub 仓库 Settings → Pages
2. 自定义域名输入 `jixiebaike.com`
3. Save — GitHub 自动创建 CNAME 文件
4. 勾选 "Enforce HTTPS"

#### 步骤 7: 配置页面规则（可选优化）

在 Cloudflare → Rules → Page Rules 中：

| 规则 | 设置 | 说明 |
|------|------|------|
| `jixiebaike.com/*.html` | Cache Level: Standard | HTML 可缓存 |
| `jixiebaike.com/*.css` | Cache Level: Cache Everything | CSS 缓存 |
| `jixiebaike.com/*.js` | Cache Level: Cache Everything | JS 缓存 |
| `jixiebaike.com/*.png` | Cache Level: Cache Everything | 图片缓存 |
| `jixiebaike.com/*` | Edge Cache TTL: 1 hour | 整体缓存 1 小时 |
| `jixiebaike.com/sitemap.xml` | Edge Cache TTL: 30 min | sitemap 短缓存 |

或者使用 **Cache Rules**（新界面）：

```yaml
Rule 1: *.html ⇒ Browser Cache TTL 10 min, Edge Cache TTL 10 min
Rule 2: *.css *.js ⇒ Browser Cache TTL 7 days, Edge Cache TTL 7 days
Rule 3: *.png *.jpg *.webp *.svg ⇒ Browser Cache TTL 30 days, Edge Cache TTL 30 days
```

#### 步骤 8: Hugo 配置更新

```toml
baseURL = "https://jixiebaike.com/"
```

并在 `static/CNAME` 中添加 `jixiebaike.com`。

#### 步骤 9: 验证

1. `dig jixiebaike.com` 返回 Cloudflare IP 地址
2. 直接访问 `https://jixiebaike.com/`
3. 确认浏览器绿锁 HTTPS
4. 检查 HTTP 响应头中的 `CF-Ray` 和 `Server: cloudflare`
5. 检查 GitHub Actions 重新部署后是否自动同步

### 4.5 费用估算

| 项目 | 费用 | 说明 |
|------|------|------|
| 域名注册（.com） | ¥30-80/年 | 首年优惠价 |
| Cloudflare Free Plan | 免费 | DNS + CDN + SSL + WAF 基础 |
| SSL 证书 | 免费 | 自动签发 |
| **合计** | **¥30-80/年** | 几乎零成本 |

---

## 5. 方案对比

| 对比项 | 方案 A: 腾讯云 CDN | 方案 B: Cloudflare CDN |
|--------|-------------------|----------------------|
| **国内访问速度** | ⭐⭐⭐⭐⭐ 极快（2800+ 国内节点） | ⭐⭐ 较慢（海外节点/国内合作节点有限） |
| **海外访问速度** | ⭐⭐⭐ 一般 | ⭐⭐⭐⭐⭐ 极快（全球节点） |
| **ICP 备案** | ✅ **必须**（7-20 个工作日） | ❌ **不需要** |
| **HTTPS** | ✅ 免费证书（TrustAsia） | ✅ 自动免费证书 |
| **DDoS 防护** | ⭐⭐⭐ 基础（有流量计费风险） | ⭐⭐⭐⭐⭐ 企业级免费防护 |
| **WAF (Web 防火墙)** | ⭐⭐⭐ 付费功能 | ⭐⭐⭐⭐ 免费基础规则 |
| **设置难度** | ⭐⭐⭐ 中等（备案流程繁琐） | ⭐⭐⭐⭐ 简单（20 分钟搞定） |
| **缓存配置** | 自助配置面板 | Page Rules / Cache Rules |
| **域名费用** | ¥30-80/年 + CDN 流量费 | ¥30-80/年 + 无额外费用 |
| **GitHub Pages 兼容性** | ✅ 良好（回源 HTTPS） | ✅ 优秀（Full strict 模式） |
| **DNS 管理** | DNSPod（免费） | Cloudflare DNS（免费） |
| **百度统计/站长兼容性** | ✅ 完美兼容 | ✅ 兼容 |
| **Go 索引兼容性 (baidu)** | ✅ 完美 | ✅ 可能需额外配置 |
| **月均总费用（1000PV/日）** | ~¥5-15/月 | ¥0/月 |
| **上线时间** | 7-20 天（备案审核） | 30 分钟（NS 生效后） |

### 关键决策因素

**选择腾讯云方案 A 的场景：**
- ✅ 目标用户 90% 在中国大陆
- ✅ 可以接受 7-20 天备案周期
- ✅ 愿意承担少量 CDN 流量费用
- ✅ 需要国内极速加载体验
- ✅ 百度收录优先级高（国内 IP 更友好）

**选择 Cloudflare 方案 B 的场景：**
- ✅ 希望立即上线自定义域名（零等待）
- ✅ 不想走备案流程
- ✅ 零成本启动
- ✅ 同时有海外用户
- ✅ 看重 DDoS 免费防护

---

## 6. 百度站长平台 & 百度统计接入

### 6.1 百度站长平台（Baidu Webmaster Tools）

#### 作用
- 提交站点地图（sitemap）给百度收录
- 查看百度搜索流量和关键词排名
- 提交页面进行索引请求
- 查看抓取错误

#### 配置步骤

1. **注册/登录** [百度资源搜索平台](https://ziyuan.baidu.com/)
2. **添加站点** — 输入域名（无论是自定义域名还是 GitHub Pages 域名）
3. **验证站点所有权**（三种方式任选一种）：

   | 验证方式 | 操作 | 适合场景 |
   |---------|------|---------|
   | **文件验证** | 下载 `baidu_verify_xxxxx.html` 放入 Hugo 的 `static/` 目录 | 最简单，推荐 |
   | **CNAME 验证** | 添加 TXT 记录 | DNS 级别验证 |
   | **HTML 标签验证** | 在 `<head>` 中添加 meta 标签 | Hugo 模板修改 |

   **推荐使用文件验证：**
   ```bash
   # 将百度提供的验证文件放入 static 目录
   cp ~/Downloads/baidu_verify_xxxxx.html /Users/windwu/Desktop/机械师大百科项目/static/
   ```

4. **提交 sitemap**：
   - 在百度站长平台 → 资源提交 → sitemap
   - 提交地址：`https://jixiebaike.com/sitemap.xml`（或 GitHub Pages 地址）
   - 百度会定期抓取此文件发现新页面

#### Hugo robots.txt 配置

当前 `robots.txt` 已配置：
```
User-agent: *
Allow: /
Sitemap: https://windwu333.github.io/jixie-baike/sitemap.xml
```

使用自定义域名后，`sitemap` URL 需要更新。可以设置 Hugo 自动生成：

```toml
# hugo.toml 中
enableRobotsTXT = true
```

然后在 `layouts/robots.txt` 模板中：
```txt
User-agent: *
Allow: /
Sitemap: {{ .Site.BaseURL }}sitemap.xml
```

**但当前已关闭 `enableRobotsTXT`（= false）**，且有一个静态的 `public/robots.txt`。需要手动更新或开启自动生成。

### 6.2 百度统计（Baidu Analytics）

#### 当前状态

在 `hugo.toml` 中已有占位配置但未启用：
```toml
[services]
  [services.baiduAnalytics]
    id = "UA-XXXXXXXX-X"  # 这是 Google Analytics 格式，不是百度统计！
```

> ⚠️ 当前配置可能有误：
> - `UA-XXXXXXXX-X` 是 **Google Analytics** 格式，不是百度统计
> - PaperMod 主题的 `baiduAnalytics` 期望的是百度统计 ID（格式：`xxxxxxx`，纯数字）

#### 正确的百度统计配置步骤

1. **注册** [百度统计](https://tongji.baidu.com/)
2. **添加站点** — 输入网站域名
3. **获取统计 ID** — 格式为 8 位数字（如 `12345678`）
4. **配置 Hugo**：

   ```toml
   [services]
     [services.baiduAnalytics]
       id = "12345678"  # 替换为你的百度统计 ID
   ```

   PaperMod 主题会自动在页面底部注入百度统计代码。

5. **手动验证**：
   - 部署后查看页面源代码，确认存在以下代码：
   ```html
   <script>
   var _hmt = _hmt || [];
   (function() {
     var hm = document.createElement("script");
     hm.src = "https://hm.baidu.com/hm.js?12345678";
     var s = document.getElementsByTagName("script")[0];
     s.parentNode.insertBefore(hm, s);
   })();
   </script>
   ```

#### 集成后的数据流

```
百度搜索用户
  ↓ (搜索点击)
百度站长平台 (提交 sitemap → 百度收录)
  ↓
网站 (CDN)
  ↓ (页面嵌入百度统计代码)
百度统计 (实时访问数据、来源分析)
```

### 6.3 百度收录与 CDN 的注意事项

| 场景 | 注意事项 |
|------|---------|
| **使用腾讯云 CDN** | 国内 IP + 已备案 = 百度收录无额外障碍 |
| **使用 Cloudflare CDN** | Cloudflare 节点 IP 对百度爬虫兼容性一般；建议开启 Cloudflare 的 "Baidu SEO" 功能（部分付费）或添加百度爬虫 IP 白名单 |
| **自定义域名 vs GitHub Pages** | 自定义域名（尤其是 .cn）对百度 SEO 更有优势 |

**Cloudflare 额外配置（方案 B 优化百度收录）：**

在 Cloudflare 中针对百度蜘蛛绕过缓存直接回源：
```
Firewall Rules → Create Rule:
  Field: User Agent
  Operator: contains
  Value: Baiduspider
  Action: Bypass Cache
```

---

## 7. 推荐建议

### 短期快速上线方案（1 周内）: 方案 B — Cloudflare

```
购买域名 (30分钟) → 注册 Cloudflare (10分钟) → 配置 DNS + SSL (10分钟) 
→ GitHub Pages 配置 (5分钟) → 部署验证 (10分钟)
→ 共计: ~1 小时可上线
```

### 长期国内优化方案（1 个月）: 方案 A — 腾讯云 CDN

```
购买域名 (即时) → 提交 ICP 备案 (7-20天) 
→ 备案通过后配置腾讯云 CDN (1小时)
→ 配置百度站长平台 + 百度统计 (30分钟)
→ 共计: 7-20 天可上线
```

### 分阶段执行建议

| 阶段 | 时间 | 动作 |
|------|------|------|
| **阶段 1** | 第 1 天 | 购买域名，先采用 Cloudflare 方案 B 快速上线 |
| **阶段 2** | 第 1 天 | 同步开始 ICP 备案流程（即使先用 Cloudflare） |
| **阶段 3** | 备案通过后 | 切换到腾讯云 CDN 方案 A（只需改 DNS，不影响 SEO） |
| **阶段 4** | 长期 | 配置百度站长平台，持续提交 sitemap |

### 域名注册商建议

| 注册商 | 优点 | 缺点 |
|--------|------|------|
| **腾讯云 DNSPod** | 与 CDN 无缝集成，.cn 域名备案流程快 | 价格中等 |
| **阿里云万网** | .cn 域名管理成熟，备案流程完善 | 价格中等 |
| **NameSilo** | 无隐藏费用，Whois 隐私免费 | 不支持 ICP 备案 |
| **GoDaddy** | 国际域名多，优惠活动多 | 续费价格高 |

---

## 8. 附录: 名词解释

| 术语 | 说明 |
|------|------|
| **CDN** | Content Delivery Network，内容分发网络。在全球部署节点缓存静态资源，加速用户访问 |
| **ICP 备案** | 中国大陆要求所有提供互联网信息服务的网站必须进行工信部备案 |
| **CNAME** | 域名解析记录，将一个域名指向另一个域名 |
| **回源** | CDN 节点没有缓存时，向源站（GitHub Pages）请求数据 |
| **SSL/TLS** | HTTPS 加密通信协议 |
| **HSTS** | HTTP Strict Transport Security，强制浏览器使用 HTTPS 访问 |
| **NS 记录** | Name Server 记录，指定域名的 DNS 服务器 |
| **sitemap** | 站点地图 XML 文件，列出网站所有 URL 供搜索引擎爬取 |
| **百度站长平台** | 百度提供的网站收录管理和数据分析工具 |
| **百度统计** | 百度提供的网站访问统计分析工具 |

---

> **下一步**: 用户确认域名选择和方案后，可进入实际配置执行阶段。
> **待决策**: 
> 1. 是否已购买域名？如果没有，选择哪个域名？（推荐 `jixiebaike.cn` 或 `jixiebaike.com`）
> 2. 选择方案 A（腾讯云，需备案）还是方案 B（Cloudflare，免备案）？
> 3. 是否立即开始 ICP 备案流程？
