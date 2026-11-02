---
name: kling-cli-install-china
description: 在墙内 Linux 服务器上安装可灵官方 CLI（@klingai/cli-cn），通过境外 VPS 中转下载 tarball，利用服务器虚拟桌面完成 OAuth 授权。
---

# Kling CLI 安装与授权（中国服务器版）

## 安装

### npm 直装（墙外/有翻墙环境）
```bash
npm i -g @klingai/cli-cn --registry=https://registry.npmjs.org
```

### 墙内无翻墙（本文场景）
npm registry 被墙，mihomo 代理 TLS 握手也经常断开。通过境外 VPS 中转下载：

```bash
# 1. 在境外 VPS 上下载 tarball
curl -sL 'https://registry.npmjs.org/@klingai/cli-cn/-/cli-cn-0.1.1.tgz' -o /tmp/kling-cli.tgz

# 2. scp 回本地服务器
sshpass -p 'VPS密码' scp root@VPS_IP:/tmp/kling-cli.tgz /tmp/kling-cli.tgz

# 3. 从本地 tarball 安装
npm i -g /tmp/kling-cli.tgz
```

### 添加到 PATH
```bash
echo 'export PATH="/root/.npm-global/bin:$PATH"' >> ~/.bashrc
```

## OAuth 授权

### 问题
`kling login` 启动本地 HTTP 服务器在 `127.0.0.1:8787` 监听回调，浏览器授权成功后重定向到此地址。如果用户在自己电脑上打开授权链接，回调会到用户电脑 `127.0.0.1`，不是服务器。

### 正确做法：用 Hermes 内置浏览器（推荐）
Hermes 的 `browser_navigate` 运行在服务器本机，回调地址 `127.0.0.1:8787` 也是本机，完美匹配。

**必须的启动顺序：**
1. 先 `kling login`（启动端口 8787 等待回调）
2. 再 `browser_navigate` 到输出的授权 URL

每刷新一次页面就会生成新的 `auth_request_id`，但只要 `kling login` 进程没死、`state` 参数匹配，回调仍然有效。

### ⚠️ 已知障碍：headless 浏览器会话不稳定

可灵的 OAuth 授权页面在 headless 浏览器中极不稳定：
- `browser_snapshot()` 频繁返回空页面（哪怕页面实际已加载）
- 每次 `browser_navigate()` 刷新页面都会生成新的 `auth_request_id`
- 新的 `auth_request_id` 与旧的 `kling login` 进程的 `state` 参数不匹配
- `kling login` 默认超时 300s，多次导航后容易超时退出
- **解决方案**：每次重新导航后，必须重启 `kling login` 拿全新的 URL

**真实教训**：在 headless 浏览器里做可灵 OAuth 授权非常脆。如果一次搞不定，建议：
1. 让用户在 VNC/ToDesk 桌面里用 Chromium 操作（noVNC 看屏幕 + 用户口述验证码）
2. 或者给用户 URL 让他们在自己手机上打开，回调的问题后面再解决
3. **终极方案**：用户用 ToDesk 远程到服务器桌面，直接在服务器浏览器上完成授权，回调完美匹配 `127.0.0.1:8787`

### 🔴 授权交互铁律：一步一停，绝不多做

用户明确要求「不要着急，一个信息一个信息慢慢交付」。每操作一步必须等用户明确指令，不要连续点击或预判下一步。

### 授权步骤 ⚠️ 关键规则：按用户节奏，一步一停

```bash
# 1. 启动 kling login（后台）
export PATH="/root/.npm-global/bin:$PATH"
kling login > /tmp/kling_login.txt 2>&1 &
# 拿到授权 URL

# 2. 浏览器打开授权 URL
browser_navigate("https://klingai.com/auth/authorize?...")

# 3. 登录流程（🔴 铁律：每步等用户指令，绝不提前操作）
# 页面布局（无 UI 变化时不要刷新页面，刷新会导致新的 auth_request_id）：
#   - 顶部：用户名密码标签行（含两个可点击选项 @e7 @e8）
#   - 手机号输入框 @e3（带 +86 前缀）
#   - 验证码输入框 @e4
#   - 「获取验证码」按钮 @e5（输入手机号后高亮可用）
#   - 「立即创作」提交按钮 @e6（输入验证码后高亮可用）

# ① 用户说「下一步」→ 输入手机号到 @e3
# ② 用户说「下一步」→ 点「获取验证码」@e5（发短信）
# ③ 用户告知验证码 → 但可能选择语音验证码通道
#   如果用户要求「点语音」→ 查看页面是否有语音验证码切换选项
#   （通常在发送短信后会出现语音验证码备选入口）
# ④ 用户告知语音验证码 → 填入验证码 @e4
# ⑤ 自动跳转回调到 127.0.0.1:8787，登录完成

# 常见问题处理：
# - snapshot 返回空页面 → 重新 browser_navigate（但 auth_request_id 会变）
# - 多次刷新导致之前 kling login 超时 → 重新启动 kling login 拿新 URL
# - 用户说「不要着急」→ 绝对不要连续操作，等明确指令
```

### 备选：用 VNC 桌面浏览器
```bash
# 在 VNC 桌面里打开 Chromium（需有 noVNC 访问）
XAUTHORITY=/root/.Xauthority DISPLAY=:1 chromium-browser --no-sandbox "授权URL"
```
连接 noVNC: `http://服务器IP:6080/vnc.html`，密码 `mal-ai`。

**⚠️ Chromium 启动常见问题**：如果 `DISPLAY=:1` 报 `Missing X server`，需要同时设置 `XAUTHORITY=/root/.Xauthority`。

### 备选2：用 ToDesk 远程桌面
服务器已预装 ToDesk（`/usr/local/bin/todesk`），systemd 服务 `todeskd.service` 开机自启。用户可以在自己电脑上打开 ToDesk，找到服务器设备（设备名 `Linux-J9H7K2`，配置文件 `/etc/todesk/reg.conf`）发起远程连接。ToDesk 替代 VNC 的优势：无需手动输入 noVNC 地址和密码。

ToDesk 连接后，用户在远程桌面看到的是服务器 VNC 显示 :1 的桌面。我（AI）可以通过终端命令在同一个桌面启动 Chromium：
```bash
XAUTHORITY=/root/.Xauthority DISPLAY=:1 chromium-browser --no-sandbox --disable-gpu --start-maximized "授权URL"
```
用户可以直接在远程桌面的 Chromium 中操作 OAuth 登录。

### 关键踩坑
1. **顺序不能错**：先 `kling login` 再打开浏览器 URL，反过来无效
2. **慢工出细活**：每步等用户反馈，不要连续操作（用户会批评「不要着急」）
3. **页面空白的坑**：headless 浏览器会话极不稳定，`browser_snapshot` 频繁返回空页面
   - 每次 `browser_navigate` 会产生新的 `auth_request_id`
   - 旧的 `kling login` 进程与之不匹配 → 超时（300s 自动退出）
   - 超时后必须重启 `kling login` 拿全新 URL 再 navigate
   - **🔴 超时后再授权无效**：`kling login` 超时（300s）后即使浏览器中用户完成授权，回调也不会被接收（进程已死）。用户看到"可灵已连接"绿色提示页时，服务端可能早已超时退出。必须重新启动 `kling login` 拿全新 URL，再让用户在浏览器打开那个新 URL。
- **建议**：如果一次授权不成功，改用 VNC/ToDesk 桌面 Chrome 操作
4. **验证码分两种**：短信验证码 + 语音验证码，用户可能要求先发短信再切语音
5. **PATH 问题**：`npm i -g` 安装到 `/root/.npm-global/bin/`，此路径默认不在 root 的 PATH 中，需手动 `export PATH="/root/.npm-global/bin:$PATH"`

## ⚠️ 2026重大变更：新API Key认证体系

2026年可灵统一了认证体系：
- **旧**：AK/SK → HMAC SHA256 → JWT token（`Authorization: Bearer <jwt>`）
- **新**：API Key 单字符串（`Authorization: Bearer <apikey>`）
- **API端点**：`api.klingai.com` → **`api-beijing.klingai.com`**
- **旧AK/SK不再支持新模型**，必须迁移

新API Key对CLI仍不兼容（CLI只走OAuth），但简化了HTTP API调用——不需要JWT签名了。

## ⚠️ 关键认知：CLI 认证 ≠ API Key 认证（额度独立）

**CLI 只支持 OAuth 认证**（token 保存在 `/root/.kling/.credentials`），不支持 Access Key + Secret Key 方式。

这意味着：
- **同一个 Kling 账号**，用 OAuth 登录 CLI 和用 API Key 调 HTTP 接口，**灵感值（积分/资源包）池是完全独立的**
- CLI 登录的账号可能 `availableRemainCredits: 0`，而 API Key 对应的账号有资源包（如视频生成5000积分）
- 你买的资源包（如「正式-视频生成-5000-20并发-6个月」）只走 API 渠道，MCP/CLI 花不了它
- 不能直接用 CLI 替换调 `kling_api.py` 的旧代码继续用同样的 API Key — CLI 换了认证方式后账号会看到 0 余额

**Access Key / Secret Key 是**可灵开发者平台（console.klingai.com）生成的，用于 HTTP API 调用。
- 可以从「资源包管理」页面查看已有资源包
- 资源包 ID（如 `897564772261601328`）≠ Access Key，别搞混

### 管线替换决策框架

| 因素 | 继续用 API Key (手搓) | 切到 CLI (OAuth) |
|------|:---:|:---:|
| 余额 | ✅ 有资源包 | ❌ 需单独充值 |
| AI MultiShot | ✅ 支持 | ❌ 不支持 |
| Element 角色创建 | ✅ 支持 | ❌ 不支持 |
| 帧参考 base64 | ✅ 支持 | ❌ 不支持 |
| 跨镜一致性增强 | ✅ 有 | ❌ 无 |
| 提示词清洗引擎 | ✅ 5轮 | ❌ 无 |
| 视频后处理(帧提取) | ✅ 支持 | ❌ 不支持 |
| 后台线程并发 | ✅ 支持 | ❌ 无 |
| `--poll` 一步出结果 | ✅ 自实现 | ✅ 原生 |
| 模型动态发现 | ❌ 硬编码 | ✅ who_am_i |

**结论**：手搓代码比官方 CLI 能力更强。只在需要 CLI 独有的功能（如 MCP 模式、自然的终端体验）时才考虑切换。切换时注意 OAuth 账号需单独充值。

## 验证安装
```bash
kling --help
kling who_am_i  # 查看用户身份+可用模型
kling account   # 查会员等级+灵感值余额（CLI OAuth 账号的余额）
```

## CLI 核心命令
| 命令 | 用途 |
|------|------|
| `kling text_to_image <prompt> --poll` | 文生图，一步出结果 |
| `kling image_to_image --image <path> <prompt> --poll` | 参考图生图 |
| `kling text_to_video <prompt> --poll` | 文生视频 |
| `kling image_to_video --image <path> <prompt> --poll` | 图生视频 |
| `kling query_tasks <id>` | 查任务状态 |
| `kling account` | 查会员+灵感值余额 |

`--poll` 参数避免手动轮询，提交后等出结果再返回。
