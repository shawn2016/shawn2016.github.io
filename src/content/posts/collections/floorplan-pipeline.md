---
title: 户型改造全链路：用单一数据源驱动彩平图、CAD 与 3D 网页
published: 2026-11-13
draft: false
description: 给 AI 一张户型图加几句改造想法，它常被困在「照原图出图」或只能出效果图。本文把流程倒过来：先落成一份结构化 JSON（project.json），彩平 HTML、CAD 矢量、SketchUp 3D 都是它的投影。附按使用顺序的六步实操与同类方案对比。
tags: [方法, 装修, 户型图, CAD, 3D, 自动化]
category: 收藏
sourceLink: https://github.com/ZWD11/house-plan-designer
---

# 户型改造全链路：用单一数据源驱动彩平图、CAD 与 3D 网页

## 痛点：给 AI 一张户型图，它卡在哪

一个真实场景。用户拿着自建房首层平面图说：「按我的需求改完之后，出一张彩色的平面设计图，不要效果图。」

多数工具到这一步就拐弯了。它们要么照原图描一遍（改造意图被丢），要么直接渲染一张室内效果图（用户根本没要）。我们第一次跑出来的图，主卧门被墙吞了、该拆的神位隔断还在、书架挡住了套卫的门——根因不是画功差，是**没有结构化中间层**：从「图」直接到「图」，任何改动都要回到像素里手动修，三套交付物各画各的，数据永远对不齐。

这条链路的效率瓶颈，不在「画得好不好」，在「改得起改不起」。

## 判断：把单一数据源当中心，下游全是投影

反直觉的地方在这：不要在彩平工具、CAD、3D 软件里各建模一遍，而是先落成一份结构化 JSON——`project.json`——把墙体、门窗、房间、家具、改造日志全部写进去。之后三套交付物都是这份 JSON 的投影：

- 彩平 HTML = `project.json` → HouseSpec → 注入设计器模板
- CAD DXF = `project.json` → 矢量生成脚本
- 3D SKP = `project.json` → SketchUp 建模脚本

**把工具名全换成别的，流程依然成立**。这是方法论，不是某个软件的使用说明。HouseSpec、DXF、SketchUp 只是「投影方式」的可替换实现。

这个判断有成立条件：**户型必须有明确的改造意图**（拆哪面墙、哪个房间改功能）。如果只是「把这张原图还原成可看的网页」，直接走 house-plan-designer 原图路线就够了，不必上这套重量级管线。

第二层判断更关键：改造意图必须结构化进 `project.json` 的 `change_log`，而不是写在聊天里。否则「改完的图」没有任何下游能正确消费——你以为改了，机器以为没改。

## 四段流水线（按方法论顺序展开）

![改造后彩色平面布置图](/attachments/floorplan-pipeline/designer-2d.png)

1. **需求采集**：原始户型图 + 改造想法 + 现场硬事实（层高、承重墙、厨房/卫生间位置、朝向）。图上看不出的事实，必须用户确认，不能在图里猜。
2. **建单一数据源**：把上面一切落成 `project.json`（schema 见下）。这是全链路的唯一真相源。
3. **JSON → 彩平 HTML**：`project_to_housespec.py` 把 project.json 翻译成 house-plan-designer 的 HouseSpec，再注入它的单文件模板 `assets/template.html`（three.js 已内联），产出可双击离线打开的设计器网页。
4. **JSON → CAD DXF**：`plan_b_to_dxf.py` 生成分层矢量图（WALL / WINDOW / DOOR / STAIR / DIM / TEXT / FURN + CHANGE 红标），含原生 DIMENSION。
5. **JSON → 3D SKP**：`build_3d.py` 经 SketchUp MCP 桥，把墙体、楼板、门窗拉伸成概念模型。

![3D 概念模型俯视](/attachments/floorplan-pipeline/model-3d.png)

![CAD 矢量线稿](/attachments/floorplan-pipeline/cad-line.png)

![project.json 数据叠加核对](/attachments/floorplan-pipeline/overlay.png)

## 实操：按使用顺序的六步

下面每一步都是「输入 → 命令 → 输出 → 验证点」。agent 照着做即可复现整条链路。

### 步骤 0：准备设计器模板

```bash
git clone https://github.com/ZWD11/house-plan-designer ~/.workbuddy/tools/house-plan-designer
```

验证：`~/.workbuddy/tools/house-plan-designer/assets/template.html` 存在（约 1MB，three.js 内联）。**不要改这个模板**，它只负责渲染，数据来自 `window.__PRESET__`。

### 步骤 1：采集需求，写成 project.json

最小可用 schema（坐标系：1:1 毫米，Y 向上，南外墙外边 y=0，西外墙外边 x=0）：

```json
{
  "schema": "floorplan-pipeline/v1",
  "units": "mm",
  "coordinate": "模型空间 1:1，Y 向上；南外墙外边 y=0，西外墙外边 x=0",
  "plan": "B",
  "plan_summary": "改造意图一句话写清：拆哪面墙、哪个房间改功能、保留什么",
  "source": {
    "base_image": "原始户型图路径",
    "calibration": { "origin_px": [198, 1073], "outer_px": [693, 857],
                     "outer_mm": [9600, 12000], "wall_240_px": "17~18" }
  },
  "building": { "outer": [9600, 12000], "wall_thickness": 240,
                "wall_height": 3000, "north": "+Y" },
  "grid": { "x": [0, 240, 3540, 3780, 6120, 6360, 9360, 9600],
            "y": [0, 240, 3840, 4080, 6030, 6270, 8220, 8460, 11760, 12000] },
  "rooms": [
    { "id": "MB", "name": "主卧", "zone": [240, 240, 3540, 3840],
      "floor": "浅柚木地板", "door": "D-MB", "private": true }
  ],
  "doors": [
    { "id": "D-MB", "axis": "v", "at": 240, "a": 240, "b": 3840, "into": [3540, 2040] }
  ],
  "windows": [],
  "furniture": [],
  "change_log": [
    { "id": "C4", "range": [4700, 1600, 6500, 3920],
      "desc": "拆除中部神位矮台隔断，开放书房岛式落公共区西南侧",
      "status": "applied" }
  ],
  "downstream": { "sketchup": { "model": "首层_B方案_3D概念模型.skp" } }
}
```

验证：JSON 能 `json.load`；`building.outer` 与实际外廓毫米数一致；`change_log` 把改造意图写进了数据，而非只写在聊天里。

### 步骤 2：project.json → HouseSpec

```bash
python3 project_to_housespec.py   # 输入 project.json，输出 spec_B方案.json
```

脚本做三件关键转换：坐标翻转（`flip(y)=DEPTH-y`，HouseSpec 的 Y 向下）、墙取中线、按房间功能规则从 321 件家具库自动选具名家具布置（床/衣柜/沙发/餐桌/书桌/书架等约 70 件）。

验证：`spec_B方案.json` 含 `walls / openings / rooms / furniture / style`；家具件数 > 0。

### 步骤 3：HouseSpec → 彩平 HTML

用 house-plan-designer 自带的 `build.py` 注入。模板里**没有可手改的占位符**——预设是打包时注入的，`build.py` 会把 spec 包成 `{'spec': spec}`、转义 `<`、并在 `<meta charset>` 之后写入 `<script id="__preset">window.__PRESET__={...}</script>`。手改会静默失败，必须走这个工具：

```bash
python3 ~/.workbuddy/tools/house-plan-designer/scripts/build.py \
  spec_B方案.json \
  -o 自建房首层_B方案_装修设计器.html \
  --template ~/.workbuddy/tools/house-plan-designer/assets/template.html
```

验证：双击 HTML 离线打开，能看到改造后的彩色平面 + 家具 + 2D/3D 切换。`build.py` 还会在 spec 旁生成 `.build_walls.json`（墙数比上次少会提醒，多半是生成脚本里的注释吞了代码）。本文配套「资源包」见下节，下载后可直接复现这个 HTML。

### 步骤 4：project.json → CAD DXF

```bash
python3 plan_b_to_dxf.py   # 输出 首层平面图_B方案_改造后.dxf
```

产出分层矢量：WALL / WINDOW / DOOR / STAIR / DIM / TEXT / FURN，外加 CHANGE 图层用红色标出所有「待确认/改造」项。含原生 DIMENSION 标注（不是手画线）。

验证：用任意 CAD 或在线 DXF 查看器打开，图层面板能看到上述分层；DIMENSION 是真实标注对象。

### 步骤 5：project.json → SketchUp 3D

先配 MCP 桥（`~/.workbuddy/mcp.json` 增 `"sketchup": {"command":"python3","args":[".../cad/sketchup_bridge.py"]}`），在 SketchUp 2027 加载 Ruby 插件后：

```bash
python3 build_3d.py   # 经 MCP 把墙/板/门窗拉伸成 SKP
```

建模按 `f.normal.z` 符号定 pushpull 方向，防墙挤入地下；层高用 `building.wall_height`。

验证：SketchUp 打开 SKP，实体数 > 0，墙体立在 0 以上；概念模型即可，细节待现场复核。

## 资源包：新 agent 直接照跑

本文配套资源包已发布，含本链路在 B 方案上的完整可运行实现。新 agent 下载后**无需重写脚本**即可复现「这个」HTML（而非另起一份）：

- `project.json` —— B 方案单一数据源（21K 真实几何，不是最小示例）
- `spec_B方案.json` —— 由 `project_to_housespec.py` 生成
- `project_to_housespec.py` —— project.json → HouseSpec 转换器
- `plan_b_to_dxf.py` —— project.json → CAD DXF
- `build_3d.py` + `sketchup_bridge.py` —— project.json → SketchUp 3D

下载根目录：`https://shawn2016.github.io/attachments/floorplan-pipeline/kit/`

最省路径：把 kit 下到本地，先 `python3 project_to_housespec.py` 得 spec，再用上面步骤 3 的 `build.py` 命令注入模板，即得与本文一致的改造后彩平 HTML。要换成你自己的户型，改 `project.json` 重跑即可——单一数据源一改，下游三套交付物全跟着变。

## 同类方案对比（按判据维度，不按功能打分）

| 方案 | 中心在哪 | 数据同源 | 改造支持 | 交付形态 | CAD 可用 | 3D 可用 | 本地可控 | 成本 |
|---|---|---|---|---|---|---|---|---|
| 纯 interior-plan-studio（原图→效果图） | 聊天上下文 | 否 | 弱 | 图片 | 否 | 否 | 视实现 | 低 |
| 纯 house-plan-designer（原图→设计器） | 单 HTML 模板 | 是（单形态） | 需手写 spec | 网页 | 导出 | 是 | 是 | 免费 MIT |
| 酷家乐 / 三维家等 SaaS | 厂商云端 | 是（闭源） | 强 | 网页/云 | 是 | 是 | 否（数据在厂商） | 订阅 |
| **本 pipeline（project.json 单一源）** | **结构化 JSON** | **是（三形态共享）** | **强（change_log 驱动）** | **HTML+DXF+SKP** | **是** | **是** | **是** | 免费 MIT |

按成立条件选：

- 只想「把原图变成能看的网页」→ 直接用 house-plan-designer，别上重武器。
- 要商用、要厂商兜底、不在乎数据出本地 → SaaS。
- 要「按我的改造想法改完再出图」，且要同一份数据同时给彩平 / CAD / 3D 三种交付 → 本 pipeline。
- 只想要一张效果图发朋友圈 → interior-plan-studio 或任何出图工具即可。

## 风险与代价（诚实列）

- **现场事实是假设，不是测量**。层高按 3000 假定、厨房南墙靠推断、承重墙未判——这些在 CAD 里标红（CHANGE 图层），交付前必须用户现场复核。不复核就施工，拆错承重墙是结构事故。
- **SketchUp 2027 兼容坑**：官方插件 `UI.start_timer` 在该版本不触发，需改成同步执行 `dispatch_request`；Ruby 控制台热重载会重置模块变量导致服务退出，干净重启才恢复。
- **自检脚本环境故障**：`check.mjs` 用的 puppeteer-core 与系统 Chrome 的 CDP 协议偶发不匹配会卡死。我们用 2D 截图核验成品（含开放书房/客厅/餐厅/主卧/次卧/楼梯/家具全要素），替代自动验收。
- **模板不要改**：`assets/template.html` 是设计器打包产物，改了就失去升级通道。
- **几何为概念模型**：墙体厚度、家具尺寸来自推断，非竣工尺寸，正式施工图需另行深化。

## 收尾：给第二读者 / 新 agent 的判断

挑户型改造工具链，第一问不该是「出图好不好看」，而是**「数据是不是单一源、下游是不是投影」**。数据源一分散，三次改动就要手动对齐三套图，返工从这里开始。

要把这套固化成可复用 skill：把步骤 1–5 的四个脚本（`project_to_housespec.py` / `plan_b_to_dxf.py` / `build_3d.py` / `sketchup_bridge.py`）连同 `project.json` schema 收进一个 skill 目录，入口命令读一张图 + 一段改造想法，自动跑完五步产出三套交付物。本仓库 `cad/` 下已有完整可运行版本，是这套流程的参考实现。
