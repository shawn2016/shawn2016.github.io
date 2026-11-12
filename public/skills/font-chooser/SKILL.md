---
name: font-chooser
description: 为设计稿、海报、网页排版选择并接入开源中文字体。当用户要求做设计、指定字体名、问「用什么字体好」，或需要看字体样子来挑字体时使用。内置 230 款可商用开源字体的检索、130 款中文字体的真实渲染样张，以及可直接粘贴的 CSS 引用代码。无需 API Key。
---

# 字体选择与使用 · 网页版指令

本文件给 AI Agent 读。所有资源均可通过 HTTPS 直接获取，不需要注册、不需要 Key、不需要安装任何工具。

## 资源地址

| 用途 | 地址 |
|---|---|
| 本指令 | `https://shawn2016.github.io/skills/font-chooser/SKILL.md` |
| 230 款结构化数据（JSON） | `https://shawn2016.github.io/skills/font-chooser/font_catalog.json` |
| 样张图册索引（含风格速查、逐页清单） | `https://shawn2016.github.io/skills/font-chooser/index.md` |
| 样张图片 01–15 | `https://shawn2016.github.io/attachments/font-atlas-01.png` … `font-atlas-15.png` |
| 四款对照图（黑体/宋体/倾斜/圆体） | `https://shawn2016.github.io/attachments/font-compare-4.png` |
| 交互预览页（输入任意文字） | `https://shawn2016.github.io/skills/font-chooser/gallery.html` |
| 配套文章 | `https://shawn2016.github.io/posts/skills/font-chooser/` |

`font_catalog.json` 的每条记录含：`id`、`family`、`familyEn`、`aliases`、`style`、`styleCn`、`summary`、`useCases`、`avoid`、`tags`、`license`、`note`、`cssFamily`、`supportsChinese`、`srcMB`、`weights[{weight, css, link, slices}]`。其中 `weights[].css` 是现成的绝对 CSS 地址，`weights[].link` 是可直接粘贴的 `<link>` 标签。

## 何时用

用户要做设计稿 / 海报 / 网页排版，报了字体名，问「用什么字体好」，或希望看着字体样子来选。选完字体必须给出可运行的引用代码，不要只给一个名字。

## 三种方式

**A. 用户给了字体名**
在 `font_catalog.json` 里按 `family` / `familyEn` / `aliases` / `id` 匹配。别名覆盖 230/230，中文名、英文名、别名、id 都能解析。例如「思源黑体」「Source Han Sans」「noto-sans-sc」是同一条。

**B. 用户没指定，按文字条件自己选**
读 `useCases`、`styleCn`、`summary` 挑 2–3 个候选，再看 `avoid` 排除误用。中文场景先筛 `supportsChinese: true`。

**C. 看图选（多模态 / 视觉判断优先）**
1. 读 `index.md` 的「风格速查」，按 7 类定位页码。
2. 打开对应的 `font-atlas-NN.png`，逐卡片看大字「字体样张」与小字「春风又绿江南岸 · 2026 · ¥1,234.56」（后者用来验收数字和标点风格）。
3. 选中后按「第 N 页 #M」在 `index.md` 查到 `id`。每页编号从 #1 重新计数，页码和编号必须同时给出。
4. 用该 id 按 A 的方式取引用代码。

## 落地引用

```html
<link rel="stylesheet" href="https://duadu.cc/web/FontChan/api/font/<id>/<weight>/result.css">
<style>
  .title { font-family: "<cssFamily>", system-ui, sans-serif; font-weight: <weight>; }
</style>
```

`<id>`、`<weight>`、`<cssFamily>` 一律由 `font_catalog.json` 给出，不要手写猜测。也可以直接用 `weights[].link` 和 `weights[].rule` 字段。

字体不需要下载。分片 CSS 用 `unicode-range` 覆盖全字集，浏览器运行时按页面文字自动取需要的几片，动态数字、用户昵称、随机标题都能正常显示，不用提前知道字符集。

## 硬性规则

1. **中文设计先筛 `supportsChinese: true`**。230 款里只有 130 款含中文字形，其余是纯拉丁字体。拿 `Anton`、`Bebas Neue` 排中文会静默 fallback 到系统字体，等于没选。
2. **一个字重一条 `<link>`**，CSS 里的 `font-weight` 必须和 link 的字重一致，否则浏览器合成假粗体。多字重就贴多条。
3. **展示体不排正文**。查 `avoid`，例如得意黑「倾斜且粗，正文完全不能用」。
4. **中英混排**：`font-family` 写一串字体名即可，中文落到中文字体、英文落到英文字体，不用写判断。
5. **场景数据有脏标签**：`useCases` 有批量打标签痕迹（「寒蝉正楷」被标成「英文长文」），只作参考，判断以 `styleCn`、`summary` 和样张图为准。
6. **风格速查只是导航**：索引把 115 种细碎 `styleCn` 归并成 7 类，具体字形一律以图片为准。
7. **授权**：全部 OFL-1.1 / Apache / MIT，可商用可再分发，保留原作者版权声明；`note` 里有额外限制的（如站酷庆科黄油体不得改名、不得售卖字体本身）必须遵守。
8. **清单之外的字体**（如「阿里巴巴普惠体」）不在这套 link 体系里。不要编造一个不存在的 CSS 地址；请用户提供字体文件，或明确说明无法接入。
9. **引用必须对齐**：报出「第 N 页 #M」时要同时给出 `id`，避免跨页编号混淆。

## 适用边界

- **产出 HTML / CSS / SVG 设计稿代码** → 精确生效，字体真会渲染出来。
- **AI 直接生成图片** → 字形由模型画出，不由 CSS 控制。样张只能当风格提示词或参考图；要精确字形，改为生成代码再截图。
- **样张图片只覆盖固定样张文字**。换自己的文案时，需要重新生成图册，或用远程分片实时预览。
- **下载字体文件本体**需要字体酱的 API Key（邀请码），贴 `<link>` 不需要。字体都是开源的，也可从 Google Fonts / GitHub 上游获取。

## 数据来源

字体清单来自字体酱公开接口 `https://duadu.cc/web/FontChan/api/fonts`（免登录）。样张由 Chrome 用其公开 woff2 分片真实渲染，与最终设计稿字形一致。文章：https://shawn2016.github.io/posts/skills/font-chooser/
