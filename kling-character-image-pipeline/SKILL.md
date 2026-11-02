---
name: kling-character-image-pipeline
description: 用可灵 API 生成角色标准照（正面+侧面+全身）→ AI MultiShot 补全多角度 → 创建 Element 的完整流水线。也适用于场景/道具标准照生成。已有完整代码在 kling.py。
---

# Kling 角色标准照生成流水线（文生图 → AI MultiShot → Element）

## 适用场景

需要为短剧角色生成**标准人物主套照片**（正面半身 + 侧面 + 全身），并创建可灵 Element 用于跨镜角色一致性。

**也适用于**：场景参考照、道具标准照的生成。

## 已有代码位置

核心流水线在 `app/services/kling.py`，函数位置：

| 函数 | 功能 | 认证方式 |
|------|------|---------|
| `_call_kling_image(prompt, model_name, aspect_ratio)` | 文生图 | `_kling_auth_header()` 自动选择新旧Key |
| `_call_ai_multi_shot(frontal_image_url, auth_header)` | 提交MultiShot任务 | 新API Key `Bearer`（旧JWT不兼容） |
| `_poll_ai_multi_shot(task_id, auth_header)` | 轮询MultiShot结果 | 同提交时的Auth |
| `generate_character_images(name, prompt, output_dir, ws, proj)` | **三步合一** | 需先调 `set_kling_auth_mode(True)` |
| `_download_image(url, path)` | 下载图片到本地 | — |

## 认证模式切换（关键踩坑 🔴）

可灵有两套认证方式：

| 认证方式 | 适用场景 | 设置方式 |
|----------|---------|---------|
| **旧 JWT**（AK/SK） | `/v1/images/generations` 文生图、Element 创建 | 默认，无需设置 |
| **新 API Key Bearer** | **AI MultiShot**、新模型（`kling-image-o1` 等） | 调用前必须执行 `set_kling_auth_mode(True)` |

**⚠️ 致命陷阱：所有调 `generate_character_images` 的入口都必须在调用前设新Key！**

代码中两个入口：
- **`l02.py`**（角色仓库页面的接口）→ 已正确调 `set_kling_auth_mode(True)` ✅
- **`api_endpoints.py`**（旧API端点）→ 曾经漏调，导致 MultiShot 走旧 JWT 失败 ❌

**修复方法：** 在 `api_endpoints.py` 中 `from app.services.kling import generate_character_images, set_kling_auth_mode` 然后在调用前加 `set_kling_auth_mode(True)`。

## 完整流程

### 角色（三步）

```
Step 1: _call_kling_image(prompt, "kling-v3", "1:1")
        → 正面半身照 URL（存 frontal.jpg）

Step 2: _call_ai_multi_shot(frontal_url) → task_id
        _poll_ai_multi_shot(task_id) → {element_images[]}
        → 多角度图（每套3张，可能多套），自动下载为 side1/2、full_body、angle_4~9

Step 3: 多图 Base64 → POST /v1/general/advanced-custom-elements
        → element_id（用于 L05/L06 视频生成的角色一致性）
```

### 场景/道具（单步）

场景和道具**不需要 MultiShot**，直接文生图 + 创建 Element 即可，走旧 JWT。

## AI MultiShot API 文档（2026-06-26 实测）

**端点：** `POST /v1/general/ai-multi-shot`
**认证：** 新 API Key `Bearer`（必须 `set_kling_auth_mode(True)`）
**计费：** 20 积分/次（Image 资源包）

### 请求参数

```json
{
  "element_frontal_image": "https://...正面照URL",
  "callback_url": "",  // 可选
  "external_task_id": ""  // 可选
}
```

### ⚠️ 响应格式陷阱（重要！）

官方文档说返回 `element_images[]`，但**实际返回格式不同**：

```json
{
  "task_result": {
    "images": [
      {
        "url_1": "正面/主体角度URL",    // ⭐ 主角度
        "url_2": "左侧面45度URL",       // ⭐ 侧角度1
        "url_3": "右侧面45度URL",       // ⭐ 侧角度2
        "index": 0                      // 第几组
      },
      { "url_1": "...", "url_2": "...", "url_3": "...", "index": 1 }  // 第二组
    ]
  }
}
```

**代码必须平坦化处理：** 把每组 `url_1/url_2/url_3` 展平为 `[{image_url: ...}]` 数组。

```python
raw_images = result.get("images", [])
flat = []
for img_set in raw_images:
    for key in ("url_1", "url_2", "url_3"):
        if img_set.get(key):
            flat.append({"image_url": img_set[key]})
```

### 返回数量

- 通常返回 **2~3 组**（每组3个角度），即 **6~9 张**多角度图
- 首次调用可能只返回1组（3张），是因为图片还没完全处理完

## prompt 建议

调用 `_call_kling_image` 时传入的 prompt 决定了正面照质量。建议包含：

```
中国{角色名}，{年龄+性别描述}，正面半身肖像照，柔和自然光，高清写实
```

更细腻的前端可基于角色设定（外貌、服装、气质）由 LLM 自动构造英文 prompt。

## 存储目录结构

```
production/{项目}/角色/
├── 人物/{角色名}/
│   ├── frontal.jpg       ← 正面半身照（1.2~1.5MB）
│   ├── image.jpg          ← 页面展示用（复制 frontal.jpg）
│   ├── side1.jpg          ← 侧面照 (MultiShot)
│   ├── side2.jpg          ← 另侧照
│   ├── full_body.jpg      ← 全身照
│   ├── angle_4~9.jpg      ← 更多角度（MultiShot 返回多组时）
│   ├── element_id.json    ← {element_id: "xxx"}
│   └── config.json        ← 角色配置（element_id + name）
├── 场景/{场景名}/
│   ├── reference.jpg      ← 标准场景照
│   └── element_id.json
└── 道具/{道具名}/
    ├── reference.jpg      ← 标准道具照
    └── element_id.json
```

## ⚡ 决策原则：什么时候用什么API（2026-06-30 定稿）

### 人物：文生图 → MultiShot → Element ✅

```
_call_kling_image("kling-v3")   → 正面半身照（1张）
_call_ai_multi_shot()           → 多角度补全（20积分/次）
advanced-custom-elements        → Element（o_102人物）
```

**这就是正确方案。** MultiShot 是可灵官方能力，一张正面照自动补侧面/全身/多角度，无需自己衍生光照变体或额外扩图。

### 场景/道具：文生图 → Element ✅

```
_call_kling_image("kling-v3")   → 场景参考图（1张）
advanced-custom-elements        → Element（o_106场景 / o_104道具）
```

**不需要MultiShot，不需要扩图（expand）API。** kling-v3 文生图直接出高质量场景图就够了。扩图API（8积分/次）存在但并非必须。

### ❌ 不要做的事

| 不要做 | 原因 |
|--------|------|
| 给同一场景生成光照变体（早晨/黄昏/夜晚多张图） | 光照变化在视频prompt里用文字描述，不是提前生成静态图 |
| 给场景走MultiShot | 场景不需要多角度补全 |
| 自己写衍生/拼接逻辑 | 可灵内生能力已经覆盖，直接调用即可 |
| 在种子脚本/剧本里写死多光照 | 种子脚本的 `LIGHTING` 数组（晨光/黄昏/月光等）是旧产物，核心管线不依赖它 |

### 核心哲学

> **「可灵是具备这种能力的，我们要借助可灵的能力」** — 用户

- 人物 → MultiShot（可灵官方角度补全）
- 场景 → 文生图（可灵kling-v3）
- 光照/氛围 → 视频生成prompt里写

不要自己建一套衍生流程，不要生成用户看不懂的变体图集。

## 注意事项

1. **MultiShot 必须用新 API Key**（旧 JWT 不支持此接口）
2. **不要通过代理调Kling API** — 走翻墙反而超时，用 `_NO_PROXY_OPENER`
3. 角色生成约需 1-3 分钟（文生图 ~30s + MultiShot ~20s + Element ~60s）
4. **Element 创建前必须先保存所有图片到本地**（Base64上传统一用本地文件）
5. 写入 `config.json` 和 `cast.json` 是调用方的职责，`generate_character_images` 只产图

## 多用户权限陷阱

**现象**：API 返回 HTTP 500，服务端日志报 `Permission denied`。

**根因**：生产目录 `/data/user-projects/` 属主 `webapp:webapp`，但测试脚本以 `root` 运行创建了 root 属主的子目录。

**排查**：
```bash
stat /data/user-projects/用户路径/production/项目名/角色/人物/ | head -4
ps aux | grep gunicorn | grep -v grep  # 看看 gunicorn 以谁的身份运行
```

**修复**：
```bash
chown -R webapp:webapp /data/user-projects/用户路径/角色/人物/
```

## 前端 loading 不关闭的兜底

**现象**：API 返回成功或错误后，`pipeline-progress-bar` 一直显示不消失。

**根因**：`app.js` 中 `generate-asset` 的 `.catch()` 可能被 `showLHToast()` 的异常打断，导致 `hideStepLoading()` 未执行。

**建议修复**：用 `.finally()` 保证无论如何都关闭 loading：
```javascript
fetch('/api/generate-asset', {...})
  .then(...)
  .catch(...)
  .finally(function() {
    if (typeof hideStepLoading === 'function') hideStepLoading();
  });
```

## 前端选中角色但生成用的名字不对

**现象**：用户在项目人物库点击了"龙白芷"，但生成的按钮传的是"未命名角色"。

**根因**：前端 `show-asset-detail`（点击角色名）和 `generate-asset`（点击生成按钮）是两个独立的事件，选中角色后 `data-asset-name` 没有更新到生成按钮上。

**排查**：检查生成按钮的 `dataset`：
```javascript
document.querySelector('[data-action="generate-asset"]').dataset.assetName
// 如果为空，说明角色选择没同步到生成按钮
```
