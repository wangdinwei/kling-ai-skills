# Kling Production Notes · 可灵视频生产实战

> 用可灵（Kling）API 搭一条能批量出片的流水线：角色一致性、口型对齐、提示词质量门禁、时长取整的坑。

不是 API 文档的复述。这里写的是**文档里没写、只有真跑过才知道**的部分。

---

## 这个仓库解决什么问题

接入可灵 API 本身不难，难的是把它做进生产：

- **JWT 必须带 `nbf`**，不带直接拒；签名是 HS256，不是 Bearer Token
- **时长会被取整**，按时长算成本的报价会亏
- 角色一致性不能靠提示词描述，要靠先出多角度参考图、注册成可复用元素
- 长镜头口型越跑越歪，单镜必须控制时长
- 提示词质量直接决定废片率，需要一套可执行的检查清单，而不是「多写点形容词」

---

## 内容索引

| 条目 | 解决什么 |
|---|---|
| [kling-character-image-workflow](kling-character-image-workflow) | 用 AI MultiShot 出多角度角色参考图，再注册为可复用的 Kling 元素 —— 一致性的根 |
| [kling-character-image-pipeline](kling-character-image-pipeline) | 角色形象生成的端到端管线（多角色、批量、失败重试） |
| [kling-prompt-quality-gate](kling-prompt-quality-gate) | 提示词的 8 项质量检查 + 风格模板 + 自动校验，降低废片率 |
| [kling-prompt-post-enhance](kling-prompt-post-enhance) | 提示词二次增强 / 改写策略 |
| [kling-cross-shot-consistency-prompt](kling-cross-shot-consistency-prompt) | 跨镜头保持角色与场景一致（点名谁拿什么、避免否定式描述） |
| [kling-duration-rounding](kling-duration-rounding) | 时长取整的真实规则与按秒报价的偏差 |
| [kling-lipsync-mv-assembly](kling-lipsync-mv-assembly) | 口型 MV 装配：先量脸占比 → 分段对口型 → 拼接 → 烧字幕 |
| [kling-turbo-trial-video-pipeline](kling-turbo-trial-video-pipeline) | 低成本试片管线：先用便宜档位验镜头可行性 |
| [kling-api-balance-query](kling-api-balance-query) | 余额 / 配额查询，出片前先看够不够 |
| [kling-cli-install-china](kling-cli-install-china) | 国内网络环境下安装 CLI 的可行路径 |

---

## 鉴权：JWT（HS256）

可灵用签名 JWT，不是普通 Bearer Token：

```python
import json, base64, hmac, hashlib, time
ak = "YOUR_KLING_ACCESS_KEY"      # from env, never hardcode
sk = "YOUR_KLING_SECRET_KEY"
now = int(time.time())
header = {"alg": "HS256", "typ": "JWT"}
payload = {"iss": ak, "exp": now + 1800, "nbf": now - 5}
b64 = lambda d: base64.urlsafe_b64encode(d).decode().rstrip("=")
hb = b64(json.dumps(header, separators=(",", ":")).encode())
pb = b64(json.dumps(payload, separators=(",", ":")).encode())
sig = hmac.new(sk.encode(), f"{hb}.{pb}".encode(), hashlib.sha256).digest()
token = f"{hb}.{pb}.{b64(sig)}"   # valid ~30 min
```

- Base URL：`https://api-beijing.klingai.com`
- 覆盖的端点：`POST /v1/images/generations`、`POST /v1/general/ai-multi-shot`、
  `POST /v1/general/advanced-custom-elements`、`GET /v1/general/ai-multi-shot/{task_id}`、
  视频生成、余额查询

> `nbf` 必须带，且要比当前时间略早；缺失或被判为未来时间都会被拒。

---

## 怎么读

每个目录是一份独立操作手册（`SKILL.md`，原本是给 AI 助手的执行指令，格式对人同样可读）：

```
目录名/
├── SKILL.md          # 症状 / 目标 → 参数与步骤 → 验收标准
└── references/       # 可选：参数表、实测数据
```

## 关于

作者：[Dingwei Wang (@wangdinwei)](https://github.com/wangdinwei)

实际做过：用可灵做完整的 MV 与短剧镜头生产 —— 角色一致性、逐段口型对齐、字幕卡点、失败重做。

可承接：AI 视频生产流水线搭建、模型接入与调优、批量出片系统。**远程 / 项目制**。

## License

MIT — see [LICENSE](LICENSE).

> 本仓库已脱敏：**不含任何 API Key、个人信息或客户数据。** 用自己的 `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` 通过环境变量注入。
