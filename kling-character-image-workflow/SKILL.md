---
name: kling-character-image-workflow
description: Complete workflow for generating multi-angle character reference images and registering them as Kling AI elements for consistent video generation.
---

# Kling AI 角色图生成全流程

## Trigger

用户问「怎么生成角色图」「一整套正脸侧脸」「角色注册怎么搞」「主体生成怎么用」「智能补全主体图」「L02添加角色」时加载此技能。

完整实操文档见 feishu_17 OB: `/path/to/project

后端实现（2026-06-08 已上线）：
- AI MultiShot 提交: `app/services/kling.py` → `_call_ai_multi_shot(frontal_url, token)` 返回 task_id
- AI MultiShot 轮询: `app/services/kling.py` → `_poll_ai_multi_shot(task_id, token, timeout_minutes=5)` 返回 `{frontal_image, element_images: [{image_url}]}`
- 三步合一（文生图→MultiShot→创建Element→下载保存）: `app/services/kling.py` → `generate_character_images(character_name, prompt, output_dir, workspace, project)` 返回 `{element_id, local_paths}`
- API 接口: `POST /api/character/generate`（在 `app/routes/main.py` → `api_character_generate_impl()`，通过 `app/routes/pipeline.py` 注册）
- 前端入口: L02 角色仓库（`static/js/steps/step-L02.js`），未配 L01 角色旁有「✨ XXX → 添加角色」按钮，调 `/api/character/generate`

## ⚠️ 关键认知：AI MultiShot 不是文生图

用户经常误解的一点：以为要手动一张张文生图生成侧脸、全身。实际上可灵有专门API「智能补全主体图」(AI MultiShot) — **给一张正面照，AI自动补全其他角度**，一步到位。

## Auth：JWT 不是简单 Bearer Token

可灵API用 JWT (HS256) 认证，需要生成 token：

```python
import json, base64, hmac, hashlib, time
ak = "KLING_ACCESS_KEY"  # 你的ACCESS_KEY
sk = "KLING_SECRET_KEY"  # 你的SECRET_KEY
now = int(time.time())
header = {"alg": "HS256", "typ": "JWT"}
payload = {"iss": ak, "exp": now + 1800, "nbf": now - 5}
hb = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).decode().rstrip("=")
pb = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
sig = hmac.new(sk.encode(), f"{hb}.{pb}".encode(), hashlib.sha256).digest()
sb = base64.urlsafe_b64encode(sig).decode().rstrip("=")
token = f"{hb}.{pb}.{sb}"  # 有效期30分钟
```

Base URL: `https://api-beijing.klingai.com`

视频生成用 KEY-185（`_kling_jwt_185()`），文生图/主体/AI MultiShot 用普通 KEY（`_kling_jwt()`）。**注意**：示例短视频项目 `_create_kling_element()` 在 `app/_core.py:365~429` 之前误用了 `_kling_jwt_185()`（2026-06-08 已修复为 `_kling_jwt()`）——如果你的主体注册用的是普通KEY，需改成 `_kling_jwt()`，否则401。

## Two-API Workflow

1. **AI MultiShot** (`POST /v1/general/ai-multi-shot`) — 1张正面照 → 多角度图
2. **Create Element** (`POST /v1/general/advanced-custom-elements`) — 多图注册为可复用主体

### Step 1: Generate a front-facing portrait

用 Kling 文生图 API (`POST /v1/images/generations`)，选 `kling-v2-1` 模型效果最好。

### Step 2: AI MultiShot - generate multi-angle views

只传一个参数：`element_frontal_image`（正面照URL）。

异步任务，轮询 `GET /v1/general/ai-multi-shot/{task_id}` 直到 succeed。

成功响应格式：
```json
{
  "code": 0,
  "data": {
    "task_status": "succeed",
    "task_result": {
      "element_frontal_image": "https://...正面照.jpg",
      "element_images": [
        {"image_url": "https://...侧脸1.jpg"},
        {"image_url": "https://...侧脸2.jpg"},
        {"image_url": "https://...全身.jpg"}
      ]
    }
  }
}
```

### Step 3: Register as an Element

```json
{
  "element_name": "角色名",      // ≤20字符
  "element_description": "描述", // ≤100字符
  "reference_type": "image_refer",
  "element_image_list": {
    "frontal_image": "正面照URL",
    "refer_images": [
      {"image_url": "侧脸图URL"},   // 注意是 [{"image_url": "..."}] 格式！
      {"image_url": "全身图URL"}
    ]
  },
  "tag_list": [{"tag_id": "o_102"}]
}
```

> ⚠️ **`refer_images` 格式坑：** 现有代码 `app/_core.py:385` 写成了 `[{"image_url": img_b64}]` 只传了一张。正确格式是 `[{"image_url": "侧脸.jpg"}, {"image_url": "全身.jpg"}]`（数组内每项一个对象）。

### Step 4: Use in Video Generation

```
<<<element_1>>>在街道上漫步，阳光明媚，电影级画质
```

## ⚠️ 关键踩坑点

1. **图片URL有时效性** — 可灵返回的所有图片URL（文生图/AI MultiShot）都有过期时间。必须在轮询回调中**立即下载**：
   ```python
   import urllib.request
   urllib.request.urlretrieve(image_url, "本地路径/角色_角度.jpg")
   ```
2. **AI MultiShot 输入要求** — 必须清晰、无遮挡的正脸照，否则补全效果差
3. **创建主体也支持Base64** — 如果图片已下载到本地，可以转Base64传给 `frontal_image` / `refer_images`
4. **tag_list 必填** — 人物用 `o_102`，道具 `o_104`，场景 `o_106`
5. **图片规格** — jpg/jpeg/png，≤10MB，≥300px，宽高比 1:2.5~2.5:1
6. **每个任务都是异步的** — 提交后轮询直到 `task_status = "succeed"`

## 现有代码对照（示例短视频项目 — 2026-06-08 已实现）

| 功能 | 状态 | 位置 |
|------|------|------|
| 文生图 | ✅ 已有 | `app/services/kling.py` → `_call_kling_image()` |
| AI MultiShot | ✅ 已实现 | `app/services/kling.py` → `_call_ai_multi_shot()` + `_poll_ai_multi_shot()` |
| 三步合一全流程 | ✅ 已实现 | `app/services/kling.py` → `generate_character_images()` |
| 创建主体 | ✅ 已有（JWT key 已修复） | `app/_core.py` → `_create_kling_element()` |
| 视频引用 | ✅ 已有 | `app/services/kling.py` → `_call_kling_video_omni()` |
| API 接口 | ✅ 已实现 | `POST /api/character/generate`（在 `app/routes/main.py` + `pipeline.py`） |

## 已修复的 Bug（2026-06-08）
- `_create_kling_element()` 的 JWT key: `_kling_jwt_185()` → `_kling_jwt()` — KEY-185 是视频专用，文生图/主体用普通 KEY
- AI MultiShot 新增：`_call_ai_multi_shot(frontal_url)` 提交 + `_poll_ai_multi_shot(task_id)` 轮询
- `generate_character_images()` 将三步整合为一个调用：文生图▶AI MultiShot▶创建 Element▶下载到本地
- 所有多角度图下载到 `{workspace}/production/{project}/角色/{character_name}/` 下（frontal.jpg, side1.jpg, side2.jpg, full_body.jpg）
- 轮询 Element 任务时也统一用 `_kling_jwt()` 而非 `_kling_jwt_185()`

### 前端入口
- L02 角色仓库（`templates/step_L02/_warehouse.html` + `static/js/steps/step-L02.js`）
- 未配声线的 L01 角色旁有两个按钮：
  - 「✨ XXX → 添加角色」（黄色）— 弹窗确认 → 调 `/api/character/generate` → 滚动到配置区
  - 「🎙️ XXX → 新增声线」（蓝色）— 弹窗确认 → 弹窗选声线 → 滚动到配置区

## Image Specs

| Item | Requirement |
|------|-------------|
| Format | jpg / jpeg / png |
| Max size | ≤10MB |
| Min resolution | ≥300px |
| Aspect ratio | 1:2.5 ~ 2.5:1 |
| Frontal image | Clear, unobstructed, facing camera |

## 完整curl测试脚本（可直接在服务器跑）

```bash
# 0. 配置
AK="你的ACCESS_KEY"
SK="你的SECRET_KEY"
BASE="https://api-beijing.klingai.com"

# 1. 生成JWT Token
TOKEN=$(python3 -c "
import json, base64, hmac, hashlib, time
ak='$AK'; sk='$SK'
now=int(time.time())
hb=base64.urlsafe_b64encode(json.dumps({'alg':'HS256','typ':'JWT'}, separators=(',',':')).encode()).decode().rstrip('=')
pb=base64.urlsafe_b64encode(json.dumps({'iss':ak,'exp':now+1800,'nbf':now-5}, separators=(',',':')).encode()).decode().rstrip('=')
sig=base64.urlsafe_b64encode(hmac.new(sk.encode(), f'{hb}.{pb}'.encode(), hashlib.sha256).digest()).decode().rstrip('=')
print(f'{hb}.{pb}.{sig}')
")

# 2. 文生图
RESP=$(curl -s -X POST $BASE/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model_name":"kling-v2-1","prompt":"年轻男性，短发，正面半身肖像照","n":1}')
TASK_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['task_id'])")
# ...轮询拿到正面照URL...

# 3. AI MultiShot
RESP3=$(curl -s -X POST $BASE/v1/general/ai-multi-shot \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"element_frontal_image\": \"$FRONTAL_URL\"}")
# ...轮询拿到多角度图...

# 4. 创建主体
curl -s -X POST $BASE/v1/general/advanced-custom-elements \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"element_name":"角色名","reference_type":"image_refer","element_image_list":{"frontal_image":"正面照URL","refer_images":[{"image_url":"侧脸URL"}]},"tag_list":[{"tag_id":"o_102"}]}'
```

## Tag IDs Reference

| tag_id | Type | Description |
|--------|------|-------------|
| o_102 | 人物 | Character（最常用） |
| o_103 | 动物 | Animal |
| o_104 | 道具 | Props/Vehicle |
| o_105 | 服饰 | Clothing |
| o_106 | 场景 | Scene |
| o_107 | 特效 | Effects |

## Official Docs

- [主体管理](https://klingai.com/document-api/apiReference/model/element)
- [智能补全主体图](https://klingai.com/document-api/apiReference/model/aiMultiShot)
- [图像生成](https://klingai.com/document-api/apiReference/model/imageGeneration)
