---
name: kling-prompt-post-enhance
description: 在不修改现有AI视频生成核心逻辑的前提下，通过后处理方式增强可灵（Kling AI）提示词，提升画质和流畅感。核心原则：只加不删，只补不改，安全可回滚。
version: 1.0.0
author: 小马（飞书1号）
---

# 可灵提示词后处理增强法

## 适用场景

现有项目中已经有一套完整的 prompt 生成逻辑（如 DeepSeek 生成分镜→可灵出图），但生成效果不够理想。**直接改核心生成逻辑风险大、牵一发动全身**，需要用轻量的后处理来"锦上添花"。

## 核心原则

| 原则 | 说明 |
|------|------|
| **只加不删** | 不修改原有 prompt 的任何内容，只在末尾追加引导词 |
| **只补不改** | 缺什么补什么，不改变原意 |
| **安全回滚** | 所有改动集中在新增函数+几行调用，删掉即可回滚 |
| **给范例好过加规则** | 告诉AI"写成什么样"比告诉AI"不要写成什么样"有效得多。3个高质量示例让评分+2分 |

## 效果量化（基于示例公司项目实测）

### 评分体系

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| 指令清晰度 | 20% | AI是否明确知道自己要做什么 |
| 规则覆盖度 | 20% | 是否覆盖了光线、材质、动词、negative等关键维度 |
| 示例质量 | 20% | 正反例是否到位，数量是否足够 |
| 约束合理性 | 20% | 规则的松紧是否合适，字数限制是否合理 |
| 可灵适配度 | 20% | 是否针对可灵的特性做了优化 |

### 实测提分路径（示例公司项目：75→86）

| 阶段 | 分数 | 做了什么 |
|------|------|---------|
| 原始 | 75 | 架构扎实但"负面驱动"过多，AI保守 |
| 第一轮 | 80 | BANNED_KEYWORDS放词+字数放宽+加光线要求 |
| 第二轮 | 86 | 加3个高质量范例+材质要求+negative_prompt+动词要求 |

## 步骤

### 第一步：审计现有 prompt 生成链路

找到 prompt 的完整生命周期：
```
文本生成 → 分镜生成(含prompt_en) → 清洗过滤(BANNED_KEYWORDS) → 提交API
```

关键问题：**BANNED_KEYWORDS 是否误删了有用词？**
常见误删：`cinematic`（可灵官方推荐）、`film grain`、`anamorphic lens flare`

检查方法：
```python
# 搜索项目中的 BANNED_KEYWORDS
grep -n "BANNED_KEYWORDS" app.py
```

### 第二步：调研目标API的最佳实践

收集官方和社区的 prompt 指南，关注：
- 推荐的 prompt 结构公式
- 对哪些词/描述敏感（可灵对光线、运镜特别敏感）
- 常见踩坑

### 第三步：确定后处理增强点

在提交可灵前、生成逻辑后，新增一个增强函数：

```python
def _enhance_kling_prompt(prompt_en, prev_prompt_en=None, shot_num=0):
    """具体增强逻辑"""
```

检查维度：
1. **光线描述** — prompt里有没有light/shadow/sun等词，没有则补默认光线
2. **景深** — 特写镜头缺浅景深则补
3. **连贯性** — 同一场景的连续镜头加动作延续引导
4. **氛围** — 如果有情绪标注，补对应的氛围词

### 第四步：调用增强

在提交API前加上几行调用：

```python
enhanced = _enhance_kling_prompt(prompt_en, prev_prompt_en, shot_num)
if enhanced != prompt_en:
    print(f"prompt已增强 +{len(enhanced)-len(prompt_en)} chars")
prompt_en = enhanced
```

### ⑤ 加高质量prompt示例

这是投入最小、效果最明显的改动。在system prompt中输出格式之前加入3-5个不同场景的完整prompt_en示例。

**为什么有效：** AI看一个"满分答案"比读十条规则理解得更快。规则告诉AI"不要做什么"，示例告诉AI"要写成什么样"。

**示例应该覆盖的场景类型：**

| 场景类型 | 示例要点 |
|---------|---------|
| 对话场景 | 火光/灯光+材质+慢节奏+静态镜头 |
| 动作场景 | 城市夜景+霓虹灯+跟拍+手持感 |
| 场景交代 | 自然光+摇镜+环境细节 |

**标记"不要照抄"** — 告诉AI这是风格参考，不是模板填充。

### 第六步：验证回滚

不满意直接删新增函数和调用行，零影响。

## 常见增强词（可灵专用）

| 缺失类型 | 补什么 |
|---------|--------|
| 缺光线 | `natural balanced lighting` |
| 特写缺景深 | `shallow depth of field` |
| 同一场景连续镜头 | `motion flows naturally from previous shot` |

## 配套的 L05 System Prompt 调优（源头改善）

除了后处理，还可以从源头（生成prompt的system prompt）做4个小改动，跟后处理互补：

### ① 放宽字数限制
- 原：30-55词 → 改：60-90词
- 可灵API限制512字符(~100词)，55词是自我设限
- **研究数据**（基于2000+次生成，来源videoai.me）：80-150词首次成功率达72%，30-60词仅55%

### ③ 加光线硬要求 + 材质要求 + 动词要求
在【画面质量要求】节中新增：
```
⚠️ 每个镜头必须写光线！可灵对光线描述极度敏感——
❌ 差: "A man sitting in a room"
✅ 好: "A man sitting in a leather armchair, warm lamplight casting soft shadows across his face, the rest of the room in deep shadow"
```
```
动词要具体（"strolls slowly" 好于 "walks"，"dashes" 好于 "runs"）
```
```
材质纹理要写具体（"weathered oak desk"好于"desk"，"cracked leather"好于"chair"）
```

### ③ 加动词具体化要求
```
动词要具体（"strolls slowly" 好于 "walks"，"dashes" 好于 "runs"）
```

动词具体化对照表：

| 笼统 | 具体 |
|------|------|
| walks | strolls / strides / shuffles |
| runs | dashes / sprints / jogs |
| looks | gazes / stares / glances |
| sits | lounges / perches / sinks into |
| holds | clutches / grips / cradles |

### ④ 输出格式加 negative_prompt
在 shot JSON 结构中新增字段：
```json
"negative_prompt": "deformed hands, twisted fingers, extra limbs, blurry face, low quality, watermark"
```

同时需要在L06提交代码中应用：
```python
neg = shot.get('negative_prompt', '') or ''
if neg:
    prompt_en = prompt_en.rstrip('. ') + '. Negative: ' + neg
```

可灵常见伪影及对应负面词：

| 伪影 | 负面词 |
|------|--------|
| 手变形、手指数量不对 | deformed hands, twisted fingers, extra limbs |
| 脸模糊、五官漂移 | blurry face, distorted face |
| 画面水印感 | watermark, logo |
| 动作僵硬 | frozen motion, stiff movement |

## BANNED_KEYWORDS 注意事项

搜索项目中的 BANNED_KEYWORDS 配置：
```bash
grep -n "BANNED_KEYWORDS" app.py
```

可灵官方推荐使用 `cinematic`、`film grain`、`anamorphic lens flare` 等电影质感词。**不要放在禁用列表里。**

```python
# ❌ 错误：删了可灵的好词
BANNED_KEYWORDS = {'cinematic', 'film grain', 'anamorphic lens flare', ...}

# ✅ 正确：只删最虚的词
BANNED_KEYWORDS = {'masterpiece', 'best quality', '4k quality', 'high production value'}
```

## 注意事项

1. 不要在增强函数里修改原有prompt的文字，只追加
2. 每个补充词都要有条件判断（不要无脑加）
3. 增强词必须是可灵能理解的技术词，不要加抽象描述
4. 改之前先备份
5. 建议先跑一集对比效果再决定是否保留
6. system prompt改动和后处理增强相互独立，可各自单独回滚
