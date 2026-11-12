---
name: video-to-post
description: 把 B 站视频链接变成一篇有判断主线的文章，并发布到 GitHub Pages 的 skills 栏目。当用户发来视频链接并说「解析一下」「写成文章」「发到博客」时使用。内置两路转录、术语反幻觉核验、六次验收、写作框架与发布清单。
---

# 视频 → 文章 → 发布 · 在线流程指令

本文件给 AI Agent 读。资源均可通过 HTTPS 获取，不需要 Key。本机需要 `yt-dlp`、`ffmpeg`、Python 3 与 `faster-whisper`（可选，可用任意 ASR 替代）。

## 资源地址

| 用途 | 地址 |
|---|---|
| 本指令 | `https://shawn2016.github.io/skills/video-to-post/SKILL.md` |
| 转录脚本（本地 Whisper） | `https://shawn2016.github.io/skills/video-to-post/transcribe.py` |
| 首个案例：两路转录与核验表 | `https://shawn2016.github.io/skills/video-to-post/transcript.md` |
| 六次验收流程图 | `https://shawn2016.github.io/attachments/video-to-post-flow.png` |
| 写作框架（六维检查 + 判据库） | `https://shawn2016.github.io/posts/skills/采集类文章写作框架/` |
| 配套文章 | `https://shawn2016.github.io/posts/skills/video-to-post/` |
| 目标仓库 | `https://github.com/shawn2016/shawn2016.github.io` |

## 何时用

用户发来视频链接，要求解析、总结、写成文章、发到博客。只回答「视频讲了什么」不用走全流程；一旦要落成文章，按下面七步走。

## 七步流程

### 1. 元信息与查重

```bash
yt-dlp --cookies-from-browser chrome --no-playlist --dump-json "<视频URL>" > meta.json
```

B 站 API 直连常被 412 拦，`--cookies-from-browser chrome` 是必需项。记下 `title` / `uploader` / `duration` / `timestamp` / `thumbnail` / `description`。`subtitle.list` 为空表示没有官方字幕。用作者自己写的 `description` 当权威基线，它比机器转录可靠。

查重：在目标仓库 `src/content/posts/skills/` 搜 BV 号，命中就走增量（只更新，不重写）。

### 2. 复述：两路转录

```bash
yt-dlp --cookies-from-browser chrome -f 30280 --no-playlist -o "<BV>.m4a" "<视频URL>"
python3 transcribe.py <BV>.m4a transcript_local.json
```

音频流 `30280` 直接给 m4a，比下视频再提音频快。再用第二路 ASR（云端或另一个模型）转一遍，两路互校。一路 200 段、一路 5 段不是问题，错法不同才有价值。

### 3. 纠偏：术语核验表

扫出所有疑似英文专名、人名、产品名，逐个做四列对照：`本地转录 | 第二路 | 正确写法 | 依据`。依据只能是作者原文、官方文档或实搜结果。搜不到就标「存疑」，不猜。

高频音译错对照（来自 `transcript.md`）：`Grock Bolt`→Grok Bot、`A 陣`→Agent、`Carser`→Cursor、`cloudcode`→Claude Code（存疑）、`SQL`→Skill、`妥妥姐老人谈`→Lauren Tan (@poteto)。

### 4. 记忆：写 SKILL.md

把本次跑通的命令、路径、踩坑写进流程文件。本机一份（可含绝对路径），线上一份（只含 HTTPS 资源与相对命令）。

### 5. 分工：按写作框架成文

**成文原则：文章的主角是视频观点经过提炼后长出来的判断，工具链只是幕后的证据纪律。** 转录、核验这些过程一笔带过（或放证据稿链接），不进正文主线。

三步提炼法：

1. **重建结构**。作者给的是并列清单还是流程？清单背后有没有时间线、层级或循环？案例：5 个并列 tips → 读成一条「入职时间线」。
2. **对照自己**。拿自己跑过的实践逐条验证或反驳视频观点。验证过的是「我的」，没验证过的只是「我赞同的」。
3. **找缺口**。作者没讲什么、哪里会失效？缺口里长出自己的判断。

完成标志：能说出这条视频改变了你哪个判断，并在文中明写出来。

文章必须有可迁移的判断主线，不是视频摘要，也不是流水线日志。按 WHY → HOW → WHAT 组织：

1. **WHY**：具体痛点场景，不是抽象抱怨
2. **HOW**：一个「反直觉判断 + 成立条件」，工具名全部换掉后仍成立
3. **WHAT**：按方法论顺序展开工具，不按功能列表展开
4. 证据：数字、事实、亲手试过的路径，至少占其二；诚实写失效场景
5. 段落 1–3 句，禁用词零命中：赋能、闭环、天花板、绝绝子、yyds、首先其次最后、值得注意的是、总的来说
6. 结尾提炼一条判断，追加到写作框架的判据库

### 6. 陪跑：落本地 + 逐项验收

本地数字花园 `Desktop/shawn2016` 放一份（frontmatter：`title / date / tags / status / publish: true`）。站点副本放 `site-publish/`，frontmatter 对齐 `src/content.config.ts` 的 posts schema：

```yaml
---
title: 把「听懂了」变成可核对的东西
published: 2026-11-12
draft: false
description: 一句话说清读者带走什么
tags: [skills, ai, 写作, 方法论]
category: 技能
image: /attachments/xxx.jpg
---
```

验收清单：禁用词零命中、frontmatter 字段齐全、图片路径可达、判据库已追加、链接指向真实路由、slug 与附件不重名。

### 7. 自动化：发布并验证

优先用 GitHub Git Data API（`POST /git/blobs` → `POST /git/trees` 带 `base_tree` → `POST /git/commits` → `PATCH /git/refs/heads/main`）。浅克隆在本机容易被内存限制杀掉。更新分支引用必须用复数 `refs/heads/main`，查 commit 要保留完整 40 位 sha。

发布后逐项验证 200：文章页、`/skills/` 栏目、`SKILL.md`、证据稿、附件图片、`/llms.txt`，并确认新文章出现在 Recent Posts 里。同日已有多篇时排序不保证第一，收录才是硬指标。Pages workflow 必须为 success。

## 硬性规则

1. **两路转录，不可用单路稿直接成文**。机器转录里的专名错率极高，本地小模型尤其严重。
2. **作者原文优先级最高**。视频简介、UP 主置顶评论、官方字幕 > 任何一路 ASR。
3. **每个工具名、人名都要有出处**。写不出依据就标存疑，不要顺手改成一个「看起来对」的名字。
4. **官方字幕为空时不要伪造时间戳**。标注转录方式和边界，别把口播稿说成逐字稿。
5. **文章不是摘要，也不是流水线日志**。检验：把视频里的产品名换成同类产品，文章还成立吗？不成立就是说明书，重写。通篇在讲「我怎么跑通工具」的，同样重写——工具过程交给证据稿，正文只留观点的提炼与思考。
6. **frontmatter 用站点 schema 的字段名**。`published` 不是 `date`，`category` 用「技能」，`image` 用 `/attachments/` 开头的绝对路径。
7. **图片放 `public/attachments/`，在线指令放 `public/skills/<slug>/`**。文章里引用绝对路径，不要引用本地磁盘路径。
8. **发布属于外部动作**。提交前给用户看文件清单；发布后逐 URL 验证，没验证完不算完成。
9. **不急着设定时任务**。每 15 分钟一次 ≈ 一天近 100 次执行，每次都花钱。同一条流程手动跑顺几次再考虑自动化。

## 适用边界

- 口播类视频（教程、分享、访谈）→ 转录可靠，流程完整可用。
- 画面演示为主（表单操作、代码录屏、设计走查）→ 转录拿不到画面信息，文章要明确说明「只覆盖口播」，或补截图。
- 已有官方字幕或作者长文 → 跳过第 2 步，核验和成文仍要做。
- 非 B 站来源 → 第 1、2 步换成对应平台的下载方式，第 3 步以后不变。
