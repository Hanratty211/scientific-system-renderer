# `scientific-system-renderer` 技能

[English](README_EN.md)

这是一个由 Codex、Claude Code 或其他编程 Agent 调用的科研系统渲染技能，用证据、接口和物理约束驱动 Blender/SVG 架构图、实物连接图与元器件图的生成和审查。

## 适合用它做什么

- 绘制系统架构、真实设备连接、实验装置、元器件设备和机制子图。
- 把产品照片、数据手册、CAD、草图和技术约束转成可复现的 Blender 场景。
- 组合高清无文字 3D 渲染与可编辑 SVG 标注。
- 检查光路、线缆、流路、热路、无线场、机械接触、运动范围和支架是否可信。
- 修复穿模、悬空、端口错误、方向错误、尺度误导、时序状态误画成多套硬件等问题。

## 典型请求

- “根据这些实物照片和手册，画一张真实设备连接图，输出 `.blend`、透明 PNG 和标注 SVG。”
- “把这个跨电子、流体和机械的系统整理成架构图与实物图两个 panel。”
- “审查现有 Blender 场景，找出不可能的路径、悬空支架和错误接口并修复。”
- “给这个器件制作正交元器件图，标出有效面、端口和安装位置。”

## 你需要提供

- 想表达的系统结论和目标受众。
- 可用的照片、手册、数据表、CAD、草图、尺寸或接口说明。
- 哪些细节必须真实，哪些可以明确标为 schematic。
- 输出尺寸、背景、视角、文件格式和是否需要可编辑标注。

## 产出

- 可复现的 Blender 建模脚本和 `.blend` 工程。
- 高清无文字透明 PNG 与白底检查图。
- 可编辑 SVG 标注版及其 PNG 预览。
- `scene_manifest.json`、来源台账、QA 日志和再生成命令。
- 对已有图稿的物理、视觉和交付风险清单。

## Agent 接入

请保留整个技能目录，不要只复制 `SKILL.md`，因为工作流依赖 `manifest.yaml`、`static/`、`references/`、`scripts/` 和 `assets/`。

Codex 可将稳定 checkout 链接到技能目录：

```bash
ln -s /absolute/path/scientific-system-renderer \
  ~/.codex/skills/scientific-system-renderer
```

重新打开 Codex 会话后，自然描述任务或明确说“使用 `$scientific-system-renderer`”。

Claude Code 建议保留稳定 checkout，再在 `~/.claude/agents/scientific-system-renderer.md` 建一个薄 wrapper：

```markdown
---
name: scientific-system-renderer
description: Build and audit evidence-grounded scientific system renders.
---
Read `/absolute/path/scientific-system-renderer/SKILL.md` first and follow it.
Load supporting files from that skill directory only when needed.
Do not replace its truth-model and visual-QA workflow with a generic response.
```

其他 Agent 只需支持读取本地文件和执行工具，即可用自定义 prompt、subagent 或命令 wrapper 指向真实的 `SKILL.md`。

## 边界

- 该技能不会把生成图或相似产品照片当作真实硬件证据。
- 合成回归测试只验证规则，不证明具体项目的设计正确。
- 任何事实性不确定项都不得由 Agent 自行猜测：先向用户提问；用户无法确认时再查厂商资料、论文、标准或专利；仍无法确认则省略，或明确标为 `unresolved` 的示意占位。
- 涉及安全、医疗、法规或制造验收时，输出不能替代领域专家审查。

## 开源与数据边界

仓库只包含技能说明、原创代码、通用模板和原创合成测试，不包含论文 PDF、论文图片、逐篇论文摘要、DOI/题录语料、厂商图片、用户项目素材或私有路径。用户为具体项目引入的参考资料不应提交到本仓库，除非其许可证明确允许再分发。

代码和文档采用 Apache-2.0 许可证。第三方输入材料仍受各自许可证和使用条款约束。
