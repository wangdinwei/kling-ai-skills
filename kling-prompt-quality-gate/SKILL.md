---
name: kling-prompt-quality-gate
description: Kling AI 视频提示词质量门禁 — 8要素检查清单 + 6风格模板 + 自动验证函数
---

# Kling Prompt 质量门禁

## 8秒 Kling 视频提示词铁律

### 公式
```
[Anime/Style declaration FIRST] + [Subject with full appearance] + [Specific verb] + [Scene details] + [ONE camera movement] + [Lighting 1-2 items] + [Atmosphere] + Negative: [3-5 items]
```

### 图生视频：首句不写风格，改写「守住参考图风格」

上面那条公式是**文生视频**的。一旦用了首帧图（image2video），风格已经被首帧锁死，再在首句写 `Anime style, ...` 会和参考图抢方向盘，导致画风漂移。

图生视频的首句固定成这句，其余要素不变：

```
Maintain the bold-outlined American cartoon illustration style of the reference image exactly.
```

也就是把 `[Anime/Style declaration FIRST]` 换成 `[Maintain the <具体画风> style of the reference image exactly.]`，后面只写**动作 + 场景 + 一种运镜 + 光线 + 氛围**，不再重复描述画风细节（描边粗细、平涂、笔触这类已经在首帧里了）。

图生视频的三个附带约束：

1. **角色外观只写「与参考图一致」级别的确认，不要重写全量外观串** —— 重写反而可能把首帧里没有的特征加进去（换衣服、换发色）
2. **首帧里已有的构图不要重描述**。写「wide shot from behind」会跟首帧的景别打架；用「the camera holds static / tracks sideways」这类只描述变化的说法
3. **负面词里写死首帧已经正确的东西**，防它改（例：首帧是关着嘴的，就加 `open mouth, teeth showing`）
4. **提示词只能描述首帧里真实存在的东西**（最贵的一条）。上游出图模型常把你写的夸张指令“降级”成它肯画的东西——写完提示词必须**看图逐条核对**，再按图改提示词，不能拿着原始意图去喂图生视频。
   - 实测三种降级：想让它“把身体压成二维纸片贴玻璃”→ 画成“**他的大海报贴在玻璃上**”；“上半身还在床上、下半身已走到门口”→ 画成“**并置两个人**”；“身体像漏气球瘪下去”→ 只画成“**疲惫地坐着**”。
   - 处理顺序：① 看图 → ② 能用的直接**改提示词去描述图**（海报就写海报、并置就写分裂构图）→ ③ 完全不能用才重出图。
   - 不要在被降级的图上**加更多形容词**（`must be a flat two-dimensional sheet`），模型只会再次降级，白花一次视频钱。
5. **人物用短指代，不要贴全量外观串** —— 图生视频的一致性由首帧负责，提示词只需指认「the man in the navy polo and glasses」。实测把两个角色的完整外观串（各 25–35 词）贴进每条 prompt，词数会被顶到 165–178、越过 80–150 甜区，得逐条返工；换成短指代后同一条落在 84–148 词，动作描写的空间反而更大。
   - 词数超了，先砍「重复描述首帧已有内容」的句子（外观、景别、背景陈设），**不要砍动作和运镜**——那才是 8 秒里唯一在变的东西。
6. **首帧图的 prompt 不能从视频 prompt 程序化剥出来**。视频 prompt 里的连续动作（「他举起图纸戳向对方」）和运镜句（`The camera pushes in`）一旦进了图片 prompt，出图模型会去画「手拿物体的那一下」——这是六指/手指粘连的头号来源，镜头的静态瞬间也丢了。正确做法：**逐条手写静态瞬间**（此刻脸朝哪、嘴闭、手在画面外或平放不抓东西），动作和运镜只留在视频 prompt 里。程序化剥离只能当草稿，必须人工过一遍。

### ⭐ 图生视频的核心：只写「他做了什么」，禁止写构图

这是 I2V 质量差异最大的一个变量，比调任何参数都有效。**写画面长什么样，输出就是一张会呼吸的静止图；写身体在做什么，才有运动。**

| 写法 | 例 | 实际结果 |
|---|---|---|
| ❌ 构图式 | `Over-the-shoulder framing: blurred worker shoulders in the foreground, the foreman in three-quarter profile facing frame left, a crane behind` | 构图对了，但**人物几乎不动、背景完全静止** |
| ✅ 动作式 | `The foreman TURNS his head toward the man beside him, RAISES his free hand and jabs a finger in the air, his torso twisting with the gesture; the other man shifts his weight and turns his shoulder` | 抬手、转身、扭转、尘埃飘动 |

实测同一张首帧、同一个模型，仅这条差异：5/10 → **9/10**。

三条硬规则：

1. **每条至少 3 个明确的身体动作动词**（turns / raises / shifts / leans / twists / swallows / exhales / tightens）。`look / hold / sit / stand` 这类静态动词不算。
2. **背景也必须给动作** —— `the crane swings across the sky` / `dust blows across the court` / `neon slides across his face`。人动了背景还是死的，一眼假。
3. **构图和人物长相一个字都不要写** —— 首帧已经把它们定死了。写进去只会挤掉动作词的预算，并把模型往「复刻这张照片」的方向推。

**自检一句话**：把这条提示词里的构图词全部删掉，剩下的句子还在描述「人在干什么」吗？不是就重写。

### 第二个旋钮：动作幅度参数（提示词写对了也可能不动）

提示词写成动作式只是第一步。**多数 i2v 模型另有一个“运动幅度/引导强度”参数，它压得低会把动作限回静止图**，而且不报错、不警告，只给你一张会呼吸的照片。

实测同一张首帧 + 同一段动作式提示词，仅改这个参数：

| 幅度参数 | 结果 | 评分 |
|---|---|---|
| 0.3（低） | 人物几乎不动，背景完全静止 | 5/10 |
| 0.7（高） | 抬手、转身、躯干扭转、尘埃飘动 | **9/10** |

**排查顺序**：输出“像照片在抖”→ ① 先查提示词是不是写成了构图式（见上）→ ② 再查幅度参数是不是保守默认值 → ③ 最后才怀疑模型不行。参数偏保守时先把幅度上调一档重出同一镜对比，比换模型快得多。

### 首帧提示词的专用坑

首帧图按图片生成规则写，但有两个只在首帧里出现的陷阱：

| 想表达 | ❌ 别写 | ✅ 写 |
|---|---|---|
| 这个角色不戴帽子 | `bare-headed` | `short black hair visible, no hard hat` |

`bare-headed` 会被图片模型理解成**光头**，摘帽连头发一起摘了。凡是“某人没有拿某件道具”的设定，都要**正面写出那个部位本来的样子**（有头发、双手空着），而不是写“没有 X”——否定式写法模型看不见。

### 模型能力边界：不再是"只能 8 秒"

可灵 4.0 起单次可生成 **最长 30 秒**，可用 **最多 10 张关键帧**引导画面变化、组合 **最多 15 项参考素材**，并补强了大福度动作与复杂运镜。这直接改三条分镜策略：

- 副歌/高潮段可以拍成 **10–15 秒长镜头**，不用切碎成 2 秒一片（但一条长镜仍需“仅一种运镜”）；
- “身体逐日变垮”“物体渐变”这种连续变化，用 **关键帧序列**喂，不要一帧帧猜提示词；
- 多角色/多道具镜头可多样参考素材同时锁，不得只靠文字描述。

### 四层结构（比 8 要素更适合多镜头的片子）

写单镜用上面的 8 要素公式；写一整套镜头时按四层搭：

| 层 | 写什么 |
|---|---|
| 角色设定层 | 身份、年龄、服装、面部特征、**当下情绪** |
| 分镜结构层 | 景别 + 机位（平视/俯拍/过肩）+ **动作节奏**（缓转/突回），短剧靠“三秒一个信息点” |
| 风格锚点层 | 参考导演 + 色调 + 质感三件套，全片统一 |
| 技术参数层 | 比例、单镜时长、运动方式、帧率 |

### 光影：全片只收成“一个具体光源”

每镜各写一套灯，影子方向对不上，剪起来就是拼凑感。**先定一个具体光源（窗／门口／一盏台灯），之后每镜只写它此刻照到哪。** 光线定方向，色调定冷暖，氛围由墙上影子带出来。

### 跨镜人物一致性：先出“角度集合图”

不要指望每镜独立写提示词能保持同一张脸。标准做法：

1. 先出一张**正面定妆图**，再用 Edit 类模型衍生 **侧脸 60°／背身／三种表情**，组一套参考图
2. 每镜首句固定 `Maintain the character's face, hairstyle and body type of the reference image exactly.`
3. 首帧图里已有的构图不重描述，只写变化（`the camera holds static` / `tracks sideways`）

### 运镜写自然英文 + 速度

`a slow push-in toward his face over 4 seconds` 比 `zoom in` 稳得多。速度/时长参数能直接控制画面节奏，避免模型自己决定快慢。

### 硬性标准

| # | 规则 | 验证方法 | 原因 |
|---|------|---------|------|
| 1 | **80-150词** | `word_count = len(text.split())` | 80-150词甜区72%成功率，短prompt仅55% |
| 2 | **首句锤定风格**（文生写画风名，图生写 `Maintain ... of the reference image exactly`） | `text.lower().startswith(('anime','cinematic','sci-fi','maintain','keep','preserve'))` | Kling 优先读开头锚定风格 |
| 3 | **仅一种运镜** | count_camera_movements(text) == 1 | 8秒只能展示一种镜头运动 |
| 4 | **动词具体** | check no vague words (run/look/walk/sit/hold) | 具体动词让AI生成更准确的动作 |
| 5 | **角色描述分模式**：T2V 写完整外观+服装；I2V 用短指代（`the man in the navy polo`）| 每个角色可辨识 | T2V 不记忆上文，不写等于不存在；I2V 外观由首帧锁死，重写反而打架并顶破词数 |
| 6 | **负面词必填** | `"Negative:" in text` | 可灵无独立负面词框 |
| 7 | **无模糊词** | `not any(w in text for w in ['beautiful','nice','good','amazing'])` | 模糊词等于没写 |
| 8 | **单一焦点** | describes ONE subject doing ONE action | 8秒多焦点会崩 |

### DO/DON'T 动词表

| ❌ 笼统 | ✅ 具体 |
|---------|---------|
| walks | strolls slowly / strides purposefully / shuffles |
| runs | dashes / sprints / jogs |
| looks | gazes / stares / glances / peers |
| sits | lounges / perches / sinks into |
| holds | clutches / grips / cradles |
| smiles | grins / beams / smirks |
| jumps | leaps / lunges / springs |

## 自动验证函数

```python
def validate_kling_prompt(text):
    """验证可灵提示词质量，返回 pass/fail + 具体问题"""
    text = text or ""
    words = text.strip().split()
    word_count = len(words)
    has_negative = "Negative:" in text
    has_camera = any(w in text.lower() for w in
        ['tracking', 'camera', 'push in', 'pan', 'crane', 'low angle',
         'dolly', 'zoom', 'static shot', 'aerial', 'handheld'])
    has_style_anchor = text.lower().startswith((
        'anime', 'cinematic', 'sci-fi',
        'maintain',            # 图生视频：守住参考图风格
        'keep', 'preserve',
    ))
    no_vague = not any(w in text.lower() for w in ['beautiful', 'nice', 'good', 'amazing'])

    issues = []
    if word_count < 80:   issues.append(f"词数不足: {word_count}/80")
    if word_count > 150:  issues.append(f"词数过多: {word_count}/150")
    if not has_negative:  issues.append("缺少 Negative 负面词")
    if not has_camera:    issues.append("缺少运镜词（tracking/pan/push/crane等）")
    if not has_style_anchor: issues.append("首句未声明风格（Anime/Cinematic）")

    return {
        "pass": len(issues) == 0,
        "word_count": word_count,
        "has_negative": has_negative,
        "has_camera": has_camera,
        "has_style_anchor": has_style_anchor,
        "no_vague": no_vague,
        "issues": issues
    }
```

### 自动审计的两个系统误判（否则一半“问题”是假的）

拿脚本批量审 15 条提示词，实测报出 12 条“问题”，逐条看只有 4 条是真的。两类误判必须先在审计器里排掉：

| 误判 | 现象 | 修法 |
|---|---|---|
| **子串命中** | `pan` 命中 `pantry`、`panels`；`static` 与 `holds static` 重复计数成“两种运镜” | 运镜词用**锚定正则**（`pan(?:s)? (?:left|right|across)`），不要裸 `in` 匹配 |
| **摄像机短语当成演员动词** | `the camera holds static` 被计成弱动词 `holds`；`the muscle at his temple jumps` 被计成弱动词 `jumps` | 查弱动词前先剔除摄像机/解剖短语，或只对“主语是人”的从句查 |

运镜词表也要补全，否则会漏报成“运镜 0 种”：`pushes in` / `pulls back` / `tracks sideways,along` / `glides along` / `tilts up` / `arcs around` / `dollies in` / `holds static`。

**最后一条最实用**：审计器只证明“格式合规”，**不证明画面成立**。必须再抽 3–5 张 make-or-break 的首帧图单张看——拼成联络图一起问视觉模型，它会一律回“无问题”（实测 19 张拼图零问题，单张抽查发现 3 个夸张意象根本没画出来）。

## 6个风格差异化模板

### 1. 二次元（Anime Fantasy）
```
Anime style, [Japanese animation aesthetic], magical/fantasy scene. 
[Subject with full appearance] [specific verb] in/at [scene].
[Scene details with magical elements]. 
[Camera: dynamic tracking / slow push in / dramatic low angle].
[Lighting: moonlight glow / magical aura / warm sunset].
[Atmosphere: dreamy / epic / vibrant].
Anime art style with detailed character design and vibrant colors.
Negative: photorealistic, 3D render, western cartoon, deformed hands, blurry face
```

### 2. 搞笑（Comedy）
```
Anime comedy, [exaggerated expressions style]. 
[Subject] [specific verb] in [chaotic scene].
[Comedic action details with exaggerated reactions]. 
[Camera: static mid-shot / quick pan / handheld].
[Lighting: bright indoor / warm kitchen / daylight].
[Exaggerated facial expressions, motion lines].
Negative: horror, slow motion, sad mood, dark lighting, photorealistic
```

### 3. 赛博朋克（Sci-fi Cyberpunk）— 注意这里不是anime
```
Cinematic sci-fi, [photorealistic cyberpunk aesthetic]. 
[Camera: slow crane / tracking / aerial] [subject] [verb] through [futuristic scene]. 
[Scene details with neon/holographic elements]. 
[Lighting: neon ambient / volumetric / high contrast / blue hour].
[Film-like quality, detailed textures].
Negative: cartoon, 2D animation, bright daylight, overexposed, plastic textures
```

### 4. 悬疑反转（Mystery Suspense）
```
Anime mystery, [film noir aesthetic], suspenseful atmosphere. 
[Subject] [specific verb] in [dark moody scene]. 
[Scene details with suspense elements]. 
[Camera: slow push in / dolly zoom / static wide / slow track].
[Lighting: low-key / chiaroscuro / flickering single source / deep shadows].
[Muted color palette, eerie tone].
Negative: bright daylight, comedy, cartoonish, colorful palette, cheerful mood
```

### 5. 热血战斗（Action Battle）
```
Anime battle shonen, [epic action style]. 
[Subject] [specific verb] in [battle scene]. 
[Dynamic action description]. 
[Camera: dramatic low angle / whip pan / dynamic tracking].
[Lighting: golden aura / explosion light / dramatic backlight / rim light].
[Bold impact frames, speed lines, glowing effects].
Negative: slow motion, static camera, dull colors, peaceful atmosphere, blurry
```

### 6. 治愈甜宠（Romance Healing）
```
Anime romance, [Makoto Shinkai-inspired aesthetic]. 
[Subject] [specific verb] in [warm gentle scene]. 
[Romantic/gentle action details]. 
[Camera: static shot / slow pan / gentle push in].
[Lighting: soft golden hour / warm window light / sunset glow].
[Soft pastel colors, heartwarming atmosphere].
Negative: horror, intense action, dark lighting, aggressive movement, cold tones
```

## 示例（已验证的高质量prompt，约135词）

### 二次元魔法少女变身
```
Anime style, magical girl transformation scene. A teenage girl with long black hair stands on a rooftop at night, wearing a white dress that flutters in the wind. Silver moonlight descends from above, enveloping her body in a glowing aura. Pink cherry blossom petals swirl around her as she raises both hands together. The camera slowly zooms in on her face as her eyes open, revealing golden irises. Starlight streams from her fingertips, forming a circular magic array in the air with glowing pink and blue lines. She wears a pink pleated skirt, white knee-high boots, and a golden tiara on her head. The city skyline glows with warm orange lights in the background. Cinematic lighting, high contrast between cool moonlight and warm city glow, anime art style with detailed character design and vibrant colors. Negative: photorealistic, 3D render, western cartoon, deformed hands, blurry face.
```

## 参考文档

- OB: `示例公司项目/40-技术文档/可灵Kling_深度调研与完整指南_2026-06-25.md`
- OB: `示例公司项目/60-功能设计/预制种子AI生成提示词方案.md`
