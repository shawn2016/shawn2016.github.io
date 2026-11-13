---
name: github-io-post
description: 把任意信源（GitHub 仓库、网页链接、一个主题或一段素材）写成一篇符合「采集类文章写作框架」的收藏/技能文章，落地到本地数字花园 /Users/shawn/Desktop/shawn2016，并发布到 shawn2016.github.io。当用户发来仓库或网页链接说「调研一下并写篇文章」「发到 github.io」「写到博客」「收录一下」，或只给一个主题要写成收藏文章时使用。串联信源核验（README/源码/Release 实证）、WHY→HOW→WHAT 成文、实操步骤与同类方案对比、判据库追加、GitHub 发布与逐 URL 验证。
version: 1.0.0
---

# 信源 → 好文章 → shawn2016 / GitHub Pages

覆盖「非视频」的采集类文章。视频转文章走 `bilibili-to-post`，成文原则与发布链路相同，只是少了转录环节。

## 三段职责，别混在一起

| 段 | 交出什么 | 依据 |
|---|---|---|
| 调研 | 可引用的证据（数字、事实、源码位置） | README / 源码 / Release notes / 仓库 API |
| 成文 | 一条可迁移的判断 + 实操 + 对比 | `collections/采集类文章写作框架.md`（六维检查） |
| 发布 | 本地笔记 + 站点文章 + 判据库条目 | 仓库 `AGENTS.md` / `src/content.config.ts` |

## 执行步骤

### 1. 信源核验（不可省）

- 仓库类：`gh api repos/<owner>/<repo>` 拿 stars/forks/created/语言分布/协议；`gh api repos/<o>/<r>/releases` 拿版本节奏；`gh api .../commits` 拿提交量与贡献者。
- 读 README 全文，再读关键源码定位证据。**交互细节（怎么配对、按钮叫什么、错误提示文案）从源码 i18n 文案或组件里核实，不靠猜。** 例：`gh api repos/<o>/<r>/contents/apps/x/src/i18n/messages/en.ts --jq '.content' | base64 -d | grep -i pairing`
- 大仓库不要 `git clone`：本机会被内存限制 kill（Exit 137）。全部走 `gh api contents` / `git trees`。

### 2. 成文（六维检查）

读 `/Users/shawn/Desktop/shawn2016/collections/采集类文章写作框架.md`。硬约束：

- WHY（具体痛点）→ HOW（反直觉判断 + 成立条件）→ WHAT（按方法论顺序展开工具）
- 段落 1–3 句；禁用词零命中：赋能、闭环、天花板、绝绝子、yyds、首先其次最后、值得注意的是、总的来说
- 数字 / 事实 / 亲手试过的路径至少占其二；写失效场景与代价
- 换掉工具名文章仍成立（否则是说明书，重写）

**工具类文章两条硬要求（2026-11-13 用户追加）**：

1. **实操方案**：按使用顺序给步骤（安装 → 组网 → 配对 → 日常 → 进阶），每步都能照着做，不给抽象描述。
2. **同类方案对比**：对比表用判据维度（如「中心在哪 / 信任从哪来 / 能力覆盖 / 平台 / 成本」），不用功能打分；表后给「按成立条件的选型清单」，最后诚实写目标方案的风险。

### 3. 落地两处

| 位置 | 文件 | frontmatter |
|---|---|---|
| 本地数字花园 | `~/Desktop/shawn2016/collections/<slug>.md` | `title / description / date / tags / status: 🌿 / publish: true / link`，正文以 `# 标题` 开头 |
| 站点文章 | 仓库 `src/content/posts/collections/<slug>.md` | `title / published / draft: false / description / tags / category: 收藏 / sourceLink` |

站点 schema 只有 `title`、`published` 必填，其余有默认值；`published` 不是 `date`。正文由前端渲染，curl 抓不到正文是正常现象。

### 4. 判据库追加

写完在 `collections/采集类文章写作框架.md` 的「判据库」末尾追加一条（线上副本 `src/content/posts/skills/采集类文章写作框架.md` 同步改）：

`- YYYY-MM-DD 主题：一条可迁移的判断`

### 5. 发布

单文件用 Contents API（快、稳）：

```bash
cd /tmp && sha=$(gh api repos/shawn2016/shawn2016.github.io/contents/<path> --jq '.sha' 2>/dev/null)
B64=$(base64 -i article.md)
jq -n --arg c "$B64" --arg s "$sha" '{message:"feat: ...", content:$c, branch:"main"} + (if $s=="" then {} else {sha:$s} end)' > payload.json
gh api -X PUT repos/shawn2016/shawn2016.github.io/contents/<path> --input payload.json --jq '{commit:.commit.sha}'
```

多文件走 `scripts/publish.py --dir <目录> --repo shawn2016/shawn2016.github.io --message "..." [--dry-run]`（Git Data API：blobs → tree → commit → PATCH `refs/heads/main`，注意 `refs` 是复数）。

### 6. 验证

```bash
gh run list -R shawn2016/shawn2016.github.io --limit 2          # Pages 必须 success
curl -s "https://shawn2016.github.io/sitemap-0.xml" | grep -c <slug>
curl -s "https://shawn2016.github.io/posts/collections/<slug>/" | grep -o '<title>[^<]*</title>'
```

标题正确 + sitemap 收录 + workflow success，三条齐了才算发布完成。

## 踩坑清单

- `git clone` 大仓库被 kill（Exit 137）→ 全程用 `gh api`。
- Contents API 的 sha 拿不到就是新建文件（404 正常），别当失败。
- Pages 部署约 1–1.5 分钟，`gh run watch <id>` 等完再验证。
- sitemap 有缓存，刚部署完可能还没更新，等 workflow success 后再查。
- 文章标题带中文书名号无妨，slug 由文件名决定，文件名用英文短词。

## 案例

- 2026-11-13 `oinkvm/oink`（Rust + Tauri 软件 KVM）→《共用键鼠：把「谁是主机」换成「谁在场」》→ `https://shawn2016.github.io/posts/collections/oink/`。首版只有原理，用户反馈「知道原理有啥用」后补实操六步与六方案对比表，这条反馈成为本 skill 的硬要求。
