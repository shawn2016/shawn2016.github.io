---
name: bilibili-to-post
description: 把 B 站视频链接解析成一篇符合「采集类文章写作框架」的 skills 栏目文章，落到本地数字花园 /Users/shawn/Desktop/shawn2016，并发布到 shawn2016.github.io。当用户发来 B 站链接说「解析」「写成文章」「发到 github.io / shawn2016」时使用。串联 yt-dlp 下音频、两路 ASR 转录、术语反幻觉核验、WHY→HOW→WHAT 成文、判据库追加、GitHub Git Data API 发布与逐 URL 验证。
version: 1.1.0
---

# B 站视频 → 好文章 → shawn2016 / GitHub Pages

从 hermes 的 `~/.hermes/skills/media/bilibili-transcribe`（只到结构化笔记）扩展而来，补上「好文章的写法」和「发布链路」。在线版给外部模型读：`https://shawn2016.github.io/skills/video-to-post/SKILL.md`。

**1.1.0 修订（2026-11-12）**：首篇成文把流水线当成了文章主角，用户指出「要的是视频观点变成自己的东西，不是跑通工具链」。成文原则升级为「提炼 + 对照 + 找缺口」，见第 4 步。

## 三段职责，别混在一起

| 段 | 交出什么 | 依据 |
|---|---|---|
| 转录 | 两路转录稿 + 术语核验表 | hermes `bilibili-transcribe` 的 Step 0/2/3 与反幻觉核验 SOP |
| 成文 | 视频观点的提炼 + 自己的思考 + 判据一条 | `shawn2016/skills/采集类文章写作框架.md`（六维检查） |
| 发布 | 本地笔记 + 站点文章 + 在线 SKILL.md + 附件 | 仓库 `AGENTS.md` / `src/content.config.ts` |

## 环境（本机已验证 2026-11-12）

- `yt-dlp`：`/Users/shawn/.local/bin/yt-dlp`（必须 `--cookies-from-browser chrome`，否则 B 站 412）
- 音频流：`-f 30280` 直接下 m4a；`ffmpeg` 在 `/opt/homebrew/bin/ffmpeg`
- 本地 Whisper：`/usr/bin/python3` 自带 `faster_whisper 1.2.1`（`/opt/homebrew/bin/python3` 没有，别用）
  - tiny 模型：`/Users/shawn/.cache/huggingface/hub/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356`
  - 脚本：`scripts/transcribe.py <audio> <out.json>`，同时产出同名 `.txt`
- 云端 ASR：`AudioTranscribe` 工具（中文口播准确率明显高于 tiny），文件路径传本地绝对路径
- 发布：`gh` 已登录 `shawn2016`（`gh auth token` 可用），`scripts/publish.py` 走 Git Data API
- 视频元信息：`curl` 直连 `api.bilibili.com/x/web-interface/view` 会 412；用 `yt-dlp --dump-json` 或 WebFetch 拿

## 执行步骤

### 1. 元信息与查重

```bash
cd <工作目录>
yt-dlp --cookies-from-browser chrome --no-playlist --dump-json "<视频URL>" > meta.json
```

记 `title / uploader / duration / timestamp / description / thumbnail / cid`。作者 `description` 是权威基线。查重：`gh api repos/shawn2016/shawn2016.github.io/contents/src/content/posts/skills --jq '.[].name'`，正文里搜 BV 号，命中走增量。

### 2. 下音频 + 两路转录

```bash
yt-dlp --cookies-from-browser chrome -f 30280 --no-playlist -o "<BV>.m4a" "<视频URL>"
/usr/bin/python3 ~/.workbuddy/skills/bilibili-to-post/scripts/transcribe.py <BV>.m4a transcript_local.json
```

第二路用 `AudioTranscribe(filePath=<绝对路径.m4a>)`。两路都保留，写进证据稿 `transcript.md`。

### 3. 术语反幻觉核验（不可省）

四列表：`本地 tiny | 云端 ASR | 正确写法 | 依据`。依据只能是作者原文 / 官方仓库 / 实搜。英文专名默认全查；人名必查。实测 tiny 在 4 分钟视频里错 6 个（`Grock Bolt`→Grok Bot、`A 陣`→Agent、`Carser`→Cursor、`SQL`→Skill、`妥妥姐老人谈`→Lauren Tan @poteto）。查不到标「存疑 ⚠️」，不猜。

### 4. 成文：提炼 + 对照 + 找缺口（不是复述，也不是流水线日志）

**成文原则：文章的主角是视频的观点经过提炼后长出来的判断，工具链只是幕后的证据纪律。** 转录、核验、SKILL.md 这些过程一笔带过（或放证据稿链接），不进正文主线。读者要带走的是「视频观点 → 我的思考」，不是「我怎么跑通工具」。

三步提炼法：

1. **重建结构**。作者给的是并列清单还是流程？清单背后有没有时间线、层级或循环？案例：5 个并列 tips → 读成一条「入职时间线」，核心判断浮出来。
2. **对照自己**。拿自己跑过的实践逐条验证或反驳视频观点。验证过的是「我的」，没验证过的只是「我赞同的」。
3. **找缺口**。作者没讲什么、哪里会失效？缺口里长出自己的判断。案例：视频没讲「入职是单向的」「记忆会过期」「小事背后是管理」。

完成标志：**能说出这条视频改变了你哪个判断**，并在文中明写出来。说不出来就重写。

读 `/Users/shawn/Desktop/shawn2016/skills/采集类文章写作框架.md`。硬约束：

- WHY（具体痛点）→ HOW（反直觉判断 + 成立条件）→ WHAT（按方法论顺序展开工具）
- 数字 / 事实 / 亲手试过的路径至少占其二；写失效场景
- 段落 1–3 句；禁用词零命中：赋能、闭环、天花板、绝绝子、yyds、首先其次最后、值得注意的是、总的来说
- 换掉工具名文章仍成立（否则是说明书，重写）
- 结尾一条判断，追加到框架文的判据库（本地 + 线上副本都改）

站点 frontmatter 对齐 `src/content.config.ts`：`title / published / draft / description / tags / category: 技能 / image: /attachments/xxx.jpg`。`published` 不是 `date`。

### 5. 落地三处

| 位置 | 文件 |
|---|---|
| 本地数字花园 | `~/Desktop/shawn2016/notes/ai/<标题>.md`（`title/date/tags/status/publish: true`）+ 判据库追加 |
| 站点发布副本 | `site-publish/src/content/posts/skills/<slug>.md`、`site-publish/public/skills/<slug>/SKILL.md` + `transcript.md`、`site-publish/public/attachments/` 图片 |
| 本机 skill | 本文件 + `scripts/` |

`src/pages/skills/index.astro` 只收 `entry.id.startsWith("skills/")` 的文章，所以文件必须放 `posts/skills/`。`src/pages/llms.txt.ts` 自动收最近 20 篇。

### 6. 发布（外部动作，先给用户看清单）

```bash
python3 ~/.workbuddy/skills/bilibili-to-post/scripts/publish.py \
  --dir <site-publish 绝对路径> --repo shawn2016/shawn2016.github.io \
  --message "feat: 新增视频转文章流程与文章" --dry-run   # 先预览
# 去掉 --dry-run 真正提交
```

浅克隆会被本机内存限制 kill（Exit 137），所以走 Git Data API：blobs → tree（带 `base_tree`）→ commit → `PATCH /git/refs/heads/main`（复数 `refs`，单数只有 GET 可用）；查 commit 用完整 40 位 sha。

### 7. 验证

```bash
gh api repos/shawn2016/shawn2016.github.io/actions/runs --jq '.workflow_runs[0] | [.status,.conclusion]'
for u in /posts/skills/<slug>/ /skills/ /skills/<slug>/SKILL.md /skills/<slug>/transcript.md /attachments/<img> /llms.txt; do
  curl -s -o /dev/null -w "%{http_code} $u\n" "https://shawn2016.github.io$u"
done
```

`llms.txt` 的 Recent Posts 里要出现新文章（同日多篇时排序不保证第一，收录才是硬指标）。Pages workflow 必须 success，全部 200 才算完成。

## 踩坑清单

- B 站 API 直连 412 → 用 `yt-dlp --cookies-from-browser chrome --dump-json`；本机代理 `127.0.0.1:7897` 对 B 站不通，别浪费时间。
- 刚发布的视频 `subtitle.list` 常为空，官方字幕等几小时才有；不要伪造时间戳。
- `faster-whisper` 在 `/tmp/whisper_venv` 跨 session 常损坏（hermes skill 有完整修复 SOP）；本机直接用 `/usr/bin/python3` 最省事。
- 云端 ASR 会把连读产品名粘成一个词（`grokbotmuse`），本地 tiny 会把英文专名听成中文音；两路互校 + 作者原文才能定稿。
- 发布用 API 而非 clone；分支引用 PATCH 用复数路径；Contents API 偶发 404 抖动，用 commit 文件清单复核更可靠。
- 不要给这条链路加定时任务：每 15 分钟一次 ≈ 一天近 100 次执行，每次都花钱。手动跑顺几次再说。

## 案例

- 2026-11-12 `BV18JW96aEog`《别一上来就让 AI 干活》→ 文章《别学那 5 个技巧，学那条入职时间线》→ `https://shawn2016.github.io/posts/skills/video-to-post/`，证据稿 `https://shawn2016.github.io/skills/video-to-post/transcript.md`。v1.0.0 首篇《把「听懂了」变成可核对的东西》以流水线为主线，被用户判为不合格后按 1.1.0 成文原则重写。
