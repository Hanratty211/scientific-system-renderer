# Scientific System Renderer

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Skill version](https://img.shields.io/badge/skill-v1.5.0-0b7285.svg)](manifest.yaml)
[English](README_EN.md)

面向 Codex、Claude Code 等 Agent 的科研系统渲染 Skill。它把实物照片、
说明书、论文方法、CAD、用户标注和物理约束整理成可验证的 truth model，
再生成或审查 Blender/SVG 架构图、实物连接图、元器件图和机制图。

它不是“一键美化器”。核心目标是让图中的器件、端口、连接、支架、尺度、
时序和信号路径都能追溯到证据，并用自动检查和高清局部 QA 阻止“画得像，
但接错了”的结果进入最终稿。

## 适用场景

- 光学、电子、RF、流体、热学、真空、机械、机器人、生物医学和工业系统；
- 论文或汇报中的 3D 实验平台、系统架构、器件视图和机制 inset；
- 高分辨率透明无文字底图与可编辑 SVG 标注；
- 修复光路/线缆穿模、器件悬空、端口接错、比例失真和时序误画；
- 对已有 Blender 工程做物理、接口、构图和交付审计。

## v1.5.0 实物识别与视觉验收

新增 [形态、尺度与连接可读性规则](references/identity-scale-and-route-clarity.md)：
保留手持、佩戴、叠放与机械耦合关系；区分电路板、封装、接头和软材料的材质；
按证据区分仪器外形；真实尺寸与局部放大分开表达；实体线与说明箭头分层。
拓扑自动检查不再被当成形态、比例或画面可读性的验收依据。
共性问题先做代表性返工样张，并逐项保留未返工状态，不能宣称更新 Skill 即修好所有图。

## v1.4.1 范围防降级

整体架构请求不能用器件特写、器件拼盘或互不相连的模型替代。建模前锁定
系统边界、输入/激励、核心装置、必要控制支路与输出；用独立交付合同保留
这些要求。证据只支持器件时，应更换验证案例或提问，不能缩小任务范围。

```bash
python3 scripts/validate_delivery_scope.py delivery_contract.json scene_manifest.json
python3 scripts/test_delivery_scope.py
```

该检查核对声明的视图、必要节点、关系类型和完整路径，不证明实际画面
可见、端口正确或科学依据充分。器件模型可作为素材，但不计为整体架构验收。
所有请求视图均须交付；电源与控制等并行支路逐条匹配，不能共用一条连接
抵数。当前范围回归 20 项通过，另有 22 个独立构造的输入探针通过修复后重测。

## v1.4 新增检查

- 输出 PASS / FAIL / UNVERIFIED 及覆盖率，未检查的场景不能冒充通过。
- 对实际几何执行有限宽度采样检查，包含连接两端的器件；只允许接口局部接触。
- 增加镜面方向、斜入射光斑和路径对支架的投影歧义检查。
- QA 绑定场景/图片 SHA256；用户验收与 Agent 自检分开记录。
- 无标注交付不生成标注文件；只记录真实发生的检查和返工。
- 新增 Blender 场景回归与安装路径检查，见 [几何验证](references/geometry-validation.md)。

几何采样不是连续体积碰撞证明，投影包围盒只产生待核对候选；仍需逐图目检。
自动路径碰撞检查仅覆盖受支持的单条、等半径圆截面曲线。NURBS、修改器、
多段样条、变半径、网格代理和实例化几何不会被误算为已完成检查。
仓库包含 21 个原创 Blender 回归场景；它们验证工具行为，不代表论文案例已验收。

## 核心约束

### 1. 器件存在性单独取证

“这种系统通常有该器件”不等于“这套设备里确实有”。每个最终出现的器件
必须是用户确认、来源可见、权威资料支持，或明确标成 schematic placeholder。

### 2. 逐端口身份图

端口数量正确还不够。每个端口都要记录稳定 ID、所在面与行列位置、方向、
介质、身份依据和置信度。宽幅总览只用于场景关系，端口顺序优先服从近景证据。

### 3. 不允许“静默空端口”

每个端口必须声明为：

- `connected`：必须存在连接；
- `intentionally-open`：必须写明原因和证据；
- `outside-figure`：必须说明连接延伸到图外并给出证据。

### 4. 世界坐标与最终相机双重检查

连接既要在 3D 中不穿模，也要在最终画面中不形成无意义的 X 交叉、离框后
重新进入、假接到邻近端口等歧义。端点必须落在显式 port anchor 上。

### 5. 用户纠正会使旧验收失效

只要用户更正器件、端口、连接或工作状态，受影响的 manifest、模型、路径、
标注、caption、局部 crop 和 QA 都必须重做，不能只修画面上的一个症状。

## 从真实绘图返工中提炼的问题

本 Skill 的强化来自一次真实仪器平台图的多轮纠错，已完全匿名化，未收录任何
项目素材。主要教训是：

| 失败模式 | 原因 | 新的防线 |
|---|---|---|
| 整体架构变成单一器件图 | 先挑容易建模的局部照片，遗漏系统范围 | 独立请求合同 + system scope gate |
| 凭总览补出并不存在的机箱 | 把“合理”当成“存在” | component existence gate |
| 端口数量对但身份和上下顺序错 | 没有逐面 port map | schema 1.3 port evidence |
| 漏掉短跳线，端口空着也通过 | 未连接仅是 warning | `connection_expectation` 硬错误 |
| 不确定器件类型时先猜后问 | 缺少不确定性阻断 | 先问用户，再查权威来源 |
| 光纤/线缆离框、回穿、端点悬空 | 按外观拉曲线 | route corridor + endpoint anchors |
| 3D 不相交但画面出现 X 交叉 | 只查世界坐标 | camera-space crossing audit |
| 整图看不出小接头错误 | 缺少局部证据 | deterministic detail crops |
| 用户改正后旧 caption/QA 仍保留 | 修改未向下游传播 | correction invalidation protocol |
| 透明 PNG 在某些背景难判断 | 只看单一预览 | white/dark/checkerboard QA |
| 标注过早加入，线和字反复打架 | 底图未锁定 | no-text master first |

## 工作流

```text
证据清单
  -> 器件存在性锁定
  -> 逐面端口图与 port-to-port 表
  -> scene_manifest.json
  -> 2D storyboard / gray box
  -> 脚本化 Blender 建模
  -> 端点、碰撞、支架、投影审计
  -> 透明无文字高清渲染
  -> 全图 + 接头/支架/分支局部 QA
  -> 可编辑 SVG 标注
  -> 交付与公开发布审计
```

Agent 会从 [SKILL.md](SKILL.md) 进入，根据 [manifest.yaml](manifest.yaml)
加载最小必要规则。物理连接任务会额外加载
[interface-and-route-qa.md](references/interface-and-route-qa.md)。

## 安装

### Codex

```bash
git clone https://github.com/Hanratty211/scientific-system-renderer.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$(pwd)/scientific-system-renderer" \
  "${CODEX_HOME:-$HOME/.codex}/skills/scientific-system-renderer"
```

重新打开任务后，直接描述科研绘图需求；也可明确调用
`$scientific-system-renderer`。

### Claude Code 或其他 Agent

让 Agent 先读取仓库根目录的 `SKILL.md`，并按需读取 `manifest.yaml`、
`static/`、`references/`、`scripts/` 和 `assets/`。不要只复制 `SKILL.md`，
否则会丢失验证器、模板和领域规则。

## 快速开始

安装 Python 图像依赖：

```bash
python3 -m pip install -r requirements.txt
```

初始化一个渲染包：

```bash
python3 scripts/init_render_project.py render-package \
  --title "Example system" --domain general \
  --views architecture,physical-setup,component-sheet
```

编辑 `render-package/scene_manifest.json`，替换 starter evidence 并解决所有
`open_questions`，然后运行：

```bash
python3 scripts/validate_scene_manifest.py \
  render-package/scene_manifest.json \
  --report render-package/qa/manifest_validation.md
```

Blender 场景审计：

```bash
blender --background render-package/final/system.blend \
  --python scripts/audit_blender_scene.py -- \
  --output render-package/qa/blender_scene_audit.json \
  --strict-endpoints
```

渲染与局部 QA：

```bash
python3 scripts/render_qa.py render-package/final/system_no_text.png \
  --require-alpha --min-width 3000 \
  --contact-sheet render-package/qa/background_contact_sheet.png \
  --report render-package/qa/render_qa.md

python3 scripts/generate_detail_crops.py \
  render-package/final/system_no_text.png \
  render-package/qa/qa_regions.json \
  render-package/qa/crops \
  --contact-sheet render-package/qa/detail_contact_sheet.png \
  --report render-package/qa/detail_crops.md
```

## 自测与发布检查

```bash
python3 scripts/run_synthetic_benchmark.py \
  --report /tmp/ssr_synthetic_benchmark.md
python3 scripts/audit_public_release.py .
python3 -m py_compile scripts/*.py assets/build_scene.template.py
```

合成 benchmark 覆盖光学、数字计算、可穿戴、生物医学、机器人、热流体、
软体系统、机械结构和微流控等原创测试场景。它只验证规则，不证明具体项目的
设备和拓扑正确。

## 仓库结构

```text
SKILL.md                       Agent 入口与完成门
manifest.yaml                 路由与按需加载规则
static/core/                  始终生效的 truth contract
references/                   物理、接口、Blender、视觉与证据规范
scripts/                      manifest、Blender、渲染、crop、发布审计
assets/                       原创通用模板与合成 benchmark
evals/                        Agent 行为评测样例
agents/                       Agent 接入元数据
```

## 开源与隐私边界

本仓库只包含原创通用说明、代码、模板和合成测试，不包含：

- 用户照片、视频、论文 PDF、论文图片或厂商宣传图；
- 用户项目生成图、`.blend` 工程或本地实验日志；
- 私有绝对路径、账号标识、凭据或访问令牌；
- 可识别具体未公开实验平台的端口图和接线表。

项目素材应保留在项目自己的 `references/` 或私有目录，不得提交到本仓库，
除非许可证明确允许再分发。提交前运行 `audit_public_release.py`。

## 局限

- 自动 AABB、端点和二维交叉检查是保守候选检测，不能替代人工视觉审查；
- 通用规则不能证明特定设备的安全性、法规符合性或制造可行性；
- 缺少证据时，Skill 会阻断、询问、检索或省略，而不是自动补全硬件事实。

## License

[Apache License 2.0](LICENSE)。用户输入和第三方资料仍受其原始许可证约束。
