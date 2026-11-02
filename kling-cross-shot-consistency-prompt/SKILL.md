---
name: kling-cross-shot-consistency-prompt
category: mlops
description: Prevent visual drift in Kling AI multi-shot video — 4 prompt pillars (scene anchor locking, era anchoring, building style locking, character description freezing) based on community research and real project experience.
---

# Kling AI 跨镜一致性提示词工程

防止 AI 视频在不同镜头之间出现视觉漂移（角色变脸、场景跳跃、时代混搭等）。

## 核心原理

Kling AI 对每个镜头独立生成，**不记忆前后镜头内容**。每个镜头完全靠 prompt 文字描述来还原。所以跨镜一致性 = **跨镜prompt描述词的一致性**。

社区共识：*"Character consistency in Kling is entirely a prompting discipline problem."* —— 你只要留一点模糊描述，AI 每次都会填不一样的东西。

参考来源：
- Kling 官方博客 (kling.ai)
- Reddit r/KlingAI_Videos 社区
- AtlasCloud 社区指南
- Neolemon 一致性指南

## 四大支柱

### 支柱1：场景锚定词锁定（防场景漂移）
同 scene_group 内所有镜头，prompt_en 的**开头场景锚定词必须一字不差**：
```prompt
✅ 正确：每镜都以完全相同的开头
"In a modern high-tech city with gleaming glass skyscrapers, ..."
"In a modern high-tech city with gleaming glass skyscrapers, ..."
"In a modern high-tech city with gleaming glass skyscrapers, ..."

❌ 错误：开头词变了
"In a modern high-tech city..." → "In the city..."
⬆️ AI 会认为这是不同的场景
```

- **判定方法**：取同 scene_group 第一镜的前5个单词作为黄金锚定，后续每镜对比
- 覆盖范围：介词（In/the/at/outside）、冠词（a/an/the）、所有形容词

### 支柱2：年代锚定（防时代跳跃）
每个场景描述**必须**包含明确时代词：
| 时代 | 关键词 |
|------|--------|
| 现代 | modern / contemporary / 2020s / present-day |
| 古装 | ancient / medieval / traditional / Ming dynasty era |
| 未来 | futuristic / sci-fi / year 2147 |

同 scene_group 内的时代词必须完全一致。如果一半写 modern、一半写 traditional，Kling 会生成截然不同的画面。

### 支柱3：建筑/环境风格锁定（防风格混搭）
每个场景锚定必须写明建筑类型和风格：
```
glass skyscrapers            ← 现代示例项目
traditional brick courtyard  ← 古装/传统
low-rise concrete apartment  ← 普通居民区
```

同 scene_group 内，建筑材质和风格描述必须一致。
❌ 镜#1「glass skyscraper」→ 镜#2「low old building with wooden door」

### 支柱4：角色描述冻结（防角色变化）
- **主角（有参考图锁定）**：prompt_en 中只写角色英文名 + 动作，不重复外貌
  ✅ "Qin Lie walks into the room"
  ❌ "A tall young man in blue suit walks into the room"
- **配角/龙套**：首次出场给 10-20 词完整外貌/服装/身份，后续镜头一字不差
- **空镜**（纯环境）：scene_description 注明"无角色"

## 常见问题及根因

| 用户发现的漂移 | 行业叫法 | 根因分析 |
|--------------|---------|---------|
| 高楼大厦→矮楼 | 场景漂移 | 场景锚定词不一致 |
| 现代→八九十年代木门 | 场景漂移 | prompt 没有年代标签 |
| 主角变样 | 角色漂移 | 角色描述词在不同镜头有差异 |
| 画面色调跳来跳去 | 色调漂移 | 光线/光源描述不一致 |

## Prompt 模板片段

```
## ⚡ 跨镜一致性铁律（最高优先级）

Kling AI 对每个镜头独立生成镜头，不记忆前后镜头内容。

### 铁律1：场景锚定词锁定
- 同一 scene_group 内的所有镜头，prompt_en 的开头场景锚定词必须一字不差
- ✅ 正确：每镜都以完全相同的 "In a modern high-tech city..." 开头
- ❌ 错误：镜#1 写 "In a modern high-tech city" → 镜#2 写 "In the city"

### 铁律2：年代锚定
- 每个场景描述必须包含明确的时代词
- 现代剧用：modern / contemporary / 2020s / present-day
- 古装剧用：ancient / medieval / traditional / Ming dynasty era
- 未来剧用：futuristic / sci-fi / year 2147
- 同 scene_group 内的时代词必须完全一致

### 铁律3：建筑/环境风格锁定
- 每个场景锚定必须写明建筑类型和风格
- 同 scene_group 内，建筑材质和风格描述必须一致

### 铁律4：角色描述冻结
- 主角只写英文名 + 动作，不重复外貌
- 配角首次出场给 10-20 词完整描述，后续镜头一字不差
```

## 审计方法

用以下维度检查生成的 storyboard.json：

1. **年代一致性** — 每个镜头是否包含时代词
2. **场景锚定一致性** — 同 scene_group 的前5个词是否一致
3. **建筑风格一致性** — 同 scene_group 内是否冲突
4. **角色描述一致性** — 同角色在不同镜头的描述词是否一致
5. **Prompt 长度** — 是否 ≤ 2500 字符（Kling 硬性上限）
6. **景别/运镜交替** — 相邻镜头是否重复
7. **scene_group 完整性** — 是否缺少 scene_group 字段

## 参考资料
- https://kling.ai/blog/fix-ai-video-drift-consistency-guide
- https://www.atlascloud.ai/blog/guides/how-to-use-kling-3.0-for-character-consistency
- https://www.neolemon.com/blog/kling-ai-grok-ai-character-consistency-tips
- https://www.reddit.com/r/KlingAI_Videos/
