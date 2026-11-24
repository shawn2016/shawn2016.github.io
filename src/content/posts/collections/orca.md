---
title: 多 Agent 并行：先问隔离由谁提供，再问谁更聪明
published: 2026-11-24
draft: false
description: 一个 agent 跑测试时你不敢在同一目录开第二个。拆开 Orca 看它怎么用 git worktree 把并行变成仓库自身的能力，附从零跑通的详细步骤、手机与远程配置、bot 常驻方案，以及按判据维度做的同类方案对比
tags: [开源, 工具, AI, agent, 方法论]
category: 收藏
sourceLink: https://github.com/stablyai/orca
---

先说一个场景。

你让一个 agent 在仓库里跑测试、改重构，它跑到一半。这时你想顺手修另一个 bug，却不敢在同一个目录再开一个终端——两个进程同时改同一批文件，谁把谁覆盖了你说了不算。于是你只能等，等它跑完再开下一个。

多数人这时会去挑更聪明的模型，或者加订阅、加并发额度。但卡住你的不是智力，是目录。两个 agent 共用一个工作区的时候，再强的模型也得排队。

这篇想把判断往前挪一步：**多 Agent 并行，第一问不是选谁干活，是隔离单元由谁提供**。隔离落在仓库本身，删掉目录就能还原；隔离落在某个工具里，你换工具时得连会话一起搬家。第二问才是执行机在哪，因为 agent 跑在你合上盖就休眠的笔记本上，和跑在一台常开的机器上，是两种东西。

[Orca](https://github.com/stablyai/orca) 是这个判断下的一个样本。它 2026 年 3 月 17 日建库，到 11 月 24 日有 134,695 star、8,607 fork、约 472 位贡献者，最近一版是 11 月 23 日的 v1.4.272，安卓端当天还发了 v0.0.70。规模不是重点，重点是它把上面两问的答案都写进了架构里：隔离用 git worktree，执行机由你自己指定。

## 一、隔离单元决定并行是否成立

Orca 的做法不是开多个窗口、给每个窗口配一个 agent，而是让每个任务拿到一份独立的磁盘目录。官方文档的原话是 worktree-native：每个任务通过 `git worktree` 得到仓库的一份独立 on-disk 副本，agent 因此永远不会踩到彼此的文件。

具体机制是这样。每个仓库有一个 base ref（通常是 `origin/main`），每个 worktree 有一个 start-from ref，以及自己的分支、自己的文件、自己的 agent 终端。你可以在创建时把 start-from 改成另一个本地分支、某个具体 commit SHA，或者远端分支——比如把工作叠在正在审查的 PR 上。

这里有个容易被忽略的细节：它生成的是**标准 git worktree**。你可以在里面开终端跑 `git status`、`git rebase`、`git cherry-pick`，Orca 下一次渲染就能看到变化。反过来，你自己用 `git worktree add` 建的目录也能在侧栏的 Non-Orca worktrees 里显示出来。隔离放在 Git 这一层，意味着退出成本几乎为零——不支持这个工具了，目录和分支还在原地。

代价也在同一处。全新 worktree 是干净检出，被 gitignore 的依赖、缓存、本地密钥全都不在。Orca 给了三种补法，各有边界：

| 方式 | 作用 | 边界 |
|---|---|---|
| Settings → Repository 里的 Worktree Shared Paths | 从主检出物化到新 worktree，macOS 上尽量用 APFS clone-copy，否则符号链接 | 按用户、按仓库配置 |
| `orca.yaml` 的 `worktree.sharedDirectories` | 共享 gitignore 的大目录，适合 `node_modules`、`.cache` | 必须在主检出里已存在且被 gitignore；被跟踪或缺失的路径直接跳过 |
| 仓库根目录的 `.worktreeinclude` | 把 `.env`、`.vscode/settings.json` 这类文件**复制**一份进去，各 worktree 各自持有 | 只认字面路径，glob 和取反会被警告跳过 |

这组配置值得在第一次用之前就写好。否则每开一个 worktree 就重装一遍依赖，并行的收益会被启动成本吃掉。

## 二、从零跑通：一次三 agent 竞速

官方文档给的第一个练习是五分钟内让三个 agent 并行做同一道题。这个顺序本身比功能列表更有用，照着走一遍就能建立心智模型。

**第一步，装桌面端。** macOS 用 Homebrew 时要写全名，`brew install --cask stablyai/orca/orca`；bare `orca` 是另一个无关的 Plotly cask，README 专门提醒过。Arch 用 `yay -S stably-orca-bin`，其他平台去 orca.dev/download 取安装包。Windows 的签名由 SignPath.io 提供。

**第二步，加仓库。** 侧栏点 Add Repo，指向本地检出。Orca 读 Git 状态，把默认分支认作 base ref，之后可以在仓库设置里改。

**第三步，建 worktree。** 点仓库名旁边的 `+`，输入任务名，比如 `fix-login-race`；留空它会用海洋生物命名。创建对话框里有 Project 和 Run on 两个输入框，输入即过滤，回车确认。Agent 选择器可以 Set as default。想手动指定分支名，展开 Advanced 填 Branch name；从 GitHub PR 或 Linear issue 创建时这个字段会隐藏，因为分支名直接取自工单。

提交之后对话框立刻关闭，`git fetch` 和 `git worktree add` 在后台跑，侧栏出现进度行。这点在超大仓库里很关键——你不用盯着它，也可以切到别的 worktree 继续工作，失败会在面板里给出 Retry。

**第四步，让三个 agent 各做一版。** 把步骤重复三次，得到 `fix-login-race`、`fix-login-race-2`、`fix-login-race-3`，分别挂 Claude Code、Codex、Cursor CLI，然后给三个终端贴同一段提示词。三条分支、三份 diff、同一个题目。把标签页拖到窗格边缘可以分屏，三个 agent 同屏跑。

**第五步，挑一份发货。** 逐个打开 diff 视图，用 Annotate AI Diff 在具体改动行上留言，把意见送回最接近的那一个 agent。commit、push、开 PR、等检查都在应用内完成。另外两份一键删除，分支跟着一起走。

这套流程的关键不是"能同时跑三个"，而是**比较成本被压低了**。三份结果并排摆着，你选的是改动本身，不是听信某个 agent 的自述。

## 三、把执行机挪走：本地、SSH、常开服务器、云 VM

隔离解决之后，第二个问题是任务跑在哪。Orca 列了四条路，共同点是都不卖托管 VPS——机器和云账号都是你自己的。

**本地桌面**：默认路径，UI、终端、agent、浏览器在同一台机器上，适合短任务快速迭代。

**SSH 目标**：在 Settings → SSH 添加主机，测试连接（仓库 worktree 要求远端有 git），创建 worktree 时在 Run on 里选它。agent 和 git worktree 在远端跑，编辑器和 diff 留在笔记本。第一次连接时 Orca 会在主机上装自己的受管 server，所以远端 Node 版本不对也不会挡住连接。适合你已经有一台 Mac mini、GPU 机器或 VPS 的情况。

**Remote Orca Server**：和 SSH 的区别是——会话状态归服务器所有，笔记本合盖后 agent 继续跑，手机、浏览器、CLI 和自动化都能连到同一套会话。最省事的配法是两台机器都装 Orca 和 Tailscale，在服务端走 Settings → Remote Orca Servers → Advertise this app as a server → New Link，选 Tailscale 地址生成链接，客户端 Add Server 粘贴。无界面的 Linux 机器用 `orca serve --pairing-address <你可达的 Tailscale 地址>`。

**Cloud VM / 每工作区环境**：在 Settings → Experimental 打开 Cloud VM，让 agent 按提示词装技能并生成 `orca.yaml` 配方：

```
Use the orca-per-workspace-env skill to set up a per-workspace environment for this repo.
```

配方定义创建、挂起、恢复、销毁的动作，供应方可以是 Vercel Sandbox、Fly、Modal、SSH 主机或本地 Docker，账单走你自己的云账号。配方要出现在创建对话框里，前提是 `orca.yaml` 的 `environmentRecipes` 写仓库的主检出上，只写在功能分支里不算。

选择依据可以压缩成一句话：机器够快就留本地；已有 VPS 用 SSH；想要一个常开的会话中心用 Remote Server；每个任务都要干净沙箱才用 Cloud VM。四种模式可以在同一个安装里混用。

## 四、手机端：它是遥控器，不是编辑器

移动端目前是 beta，App Store 和 Google Play 都能装，安卓有 APK。它能做的事有边界：看所有主机的 worktree 状态（working / done / waiting on input）、读终端回卷、在 Chat UI 或原始终端里回复、审 diff 并提交、切账号看额度、从手机上创建 worktree、给 agent 发 Quick Commands。官方文档自己写明它不是完整编辑器，是桌上那台机器的遥控器——会话仍归桌面所有。

配对步骤：

1. 桌面上从账号/状态菜单打开配对流程，得到一次性配对码；不用的一段时间后二维码 10 分钟过期，重新生成即可。
2. 手机打开 App 选 Pair，粘贴配对码；也可以直接点桌面给出的深链进配对页。
3. 能连 Relay 时优先用，只有 Relay 需要登录；局域网地址选择器是可选的，纯 LAN 配对则必须给地址。
4. 配对建立的是这台手机的设备令牌。桌面退出后直连/LAN 会话会断，重开即恢复。

连不上有几种典型原因：桌面和手机不在同一网络路径上（LAN、Tailscale 或配对时用的通道）；协议版本不匹配时 App 会拦下这台主机并提示更新；桌面清过配对设备时先试横幅上的 Retry，不行再从桌面 Re-pair。手机改地址不需要重新配对——主机卡片的 ⋯ 菜单里改 Address 就行，端口缺省是 `6768`，这条路在你家 LAN 和 Tailscale 之间切换时很省心。

agent 等你拍板时，Needs you 会在手机上收工具授权和访问请求；桌面不可达时消息会排队，恢复连接后按顺序发出。

## 五、让 bot 常驻：从「我发指令」到「它自己触发」

如果你想要的是"早上看一眼有什么要我审的"，而不是每次自己开终端，就轮到 Bots。bot 有名字、职责、记忆和自动化，住在某台电脑的一个文件夹里，用你自己的 Claude Code 或 Codex 跑——**它干活的消耗算在你的订阅上**。

建一个 bot：侧栏 Bots 区点 `+` → New bot → Start from scratch，也可以从 24 个模板里挑。填名字和头像，用一句话写清它负责什么，确认它跑在哪台机器、用哪个 agent，然后 Create。bot 一旦选定机器就不会搬走。

接着给它第一份真任务，比如"每天早上总结 acme/web 改了什么、什么要我审"。它会立刻做其中一小块并显示结果，然后写下自己的职责，后续对话都从这里起步。涉及代码改动时，它把活交给 worker——一个在独立 worktree 里的 Claude Code 或 Codex 会话，所以不会动你的检出；PR 会回到 bot 这里。

触发方式有三类：在 bot 的 Connectors 页加 Slack（每个 bot 是独立 Slack app，需要在 Slack 工作区做一次 App Configuration Token）、GitHub（在 issue 或 PR 里 mention）、Linear（`@Orca scout` 或 `bot:scout` 标签）；在聊天里直接说"每个工作日 9 点"或"acme/web 的 PR 打开时"，它会建好自动化；以及 webhook。调度粒度支持小时、每天、工作日、每周、cron 和 RRULE。

**电脑必须醒着。** 这是这类方案最容易被忽略的代价：bot 只在它所在机器醒着且在线时工作。Orca 有 Keep computer awake 设置防休眠，但 Mac 合盖照样睡。Slack、GitHub、Linear 的请求最多等一天。要真正做到常驻，把 bot 放到一台已配对的常开服务器上。

权限也要想清楚。默认只有你能问；加进 Who can ask 的人，是用**你的权限、在你的机器上**跑请求，只该加你愿意把键盘交出去的人。bot 的记忆是纯 Markdown 的 `SOUL.md` 和 `MEMORY.md`，可以直接读写。它还会自己干两件小事：每天几次只读地看看 Slack、Linear、GitHub 和项目里有什么等你处理（Suggestions，默认工作日 8 点到 20 点每 4 小时）；以及有对话的第二天凌晨 3 点后整理记忆，可在设置里改成每周或关掉。

## 六、CLI：让 agent 反过来驱动 Orca

桌面端自带 CLI，在 Settings → General → Orca CLI 里注册。它管的是正在运行的那个编辑器，Orca 会让自己版本的 `orca` 优先于 shell 启动文件里可能存在的旧全局安装。

```
command -v orca
orca status --json

orca worktree ps --json
orca worktree create --repo id:<repoId> --name my-task --issue 123 --json
orca terminal send --text "continue" --enter --json
orca terminal wait --for tui-idle --timeout-ms 30000 --json

orca goto --url https://example.com --json
orca snapshot --json
orca click --element @e3 --json
orca fill --element @e1 --value "user@example.com" --json
```

浏览器那组是 snapshot → interact → re-snapshot 的循环，`snapshot` 返回 `@e1` 这样的引用，后续 click/fill 按引用操作。换设备画像用 `orca set device --name "iPhone 12" --json`。想让 agent 自己会用这些命令，可以给它装配套技能：`npx skills add https://github.com/stablyai/orca --skill orca-cli`，无界面场景用 `orca skills install --skill orca-cli`。

## 七、同类方案对比

这张表不按功能打分，按判据看：隔离由谁提供、会话归谁所有、执行机在哪、成本从哪来、退出代价多大。

| 方案 | 隔离由谁提供 | 会话归谁所有 | 执行机在哪 | 成本从哪来 | 退出代价 |
|---|---|---|---|---|---|
| 一个终端 + 手动 `git worktree` | Git 本身，你自己敲命令 | 你自己的终端 | 你的机器 | 免费 | 零，全是标准 Git 对象 |
| 多窗格终端复用器 + 手动 worktree | Git 本身，终端只负责显示 | 你的 tmux / 终端会话 | 你的机器或 SSH 主机 | 免费 | 低，但要自己维护布局与状态 |
| IDE 内置 agent 并排开 | 编辑器自己的工作区或进程隔离 | 编辑器 | 本地 IDE + 厂商云 | 订阅或额度 | 中，会话和插件生态绑在编辑器里 |
| 托管 agent 平台 | 平台分配的云端沙箱 | 平台 | 厂商云 | 按任务/席位计费 | 高，代码靠 PR 导出，会话留在平台 |
| Orca | Git worktree，工具负责自动化 | 你指定的本地机 / SSH / 自己的服务器 | 你控制的机器 | 工具免费，消耗走你已有的 agent 订阅 | 低，worktree 和记忆都是仓库/文件 |

按成立条件给一份选型清单：

- 你已经重度使用命令行 agent，且同时有两件以上互不相关的改动 → 值得引入 worktree 层；只有一件任务时，直接单 agent 更快。
- 你已经有常开机器 → 优先把会话放上去，本地机器只当 UI；没有的话，先别为"合盖继续跑"专门买机器。
- 你需要别人从 Slack 或 GitHub 触发 → 选能把触发入口接到你现有协作工具上的方案，同时按"愿意借出多少权限"来决定开给谁。
- 你的隔离需求必须可审计、可迁移 → 坚持隔离落在 Git 层，别把 worktree 当某工具的私有状态。

## 八、它的代价

第一，迭代太快。v1.4 已经发到 272 版，README 自己说"每天发布，这份功能列表永远追不上"。这既是活力也是风险：今天的操作路径下个月可能改名字，重要流程以文档和 changelog 为准。

第二，移动端还是 beta，且手机只是遥控器。桌面一关，直连会话就断；想真正无人值守，得有一台常开的服务器。

第三，bot 的账单在你头上。它用你的 Claude Code 或 Codex 订阅跑，包括那些每 4 小时的只读巡视和凌晨的记忆整理——想省额度就去设置里关。

第四，规模数字要看两面。134,695 star 对应的是 9,458 个 open issue 和 8,607 个 fork。热闹意味着生态和迭代，也意味着你大概率会在 issue 区找到自己那一个问题。

## 收尾

回到开头那句话。多 Agent 并行能不能成立，先看隔离单元由谁提供——落在仓库层，你就随时能退出；落在工具层，你换工具就得连会话一起搬。第二个问题是执行机归谁，它决定任务是陪你合盖睡觉，还是在一台常开的机器上继续走。

Orca 把这两个答案分别放进了 git worktree 和你自选的运行时里，所以它值得被当成一个样本来拆，而不只是一个可以点的下载按钮。工具名换成别的，这套判断依然能用——这才是它值得记下来的部分。

相关链接：

- 仓库：https://github.com/stablyai/orca
- 官网与下载：https://orca.dev
- 第一个三 agent 会话教程：https://orca.dev/docs/first-session
- Worktree 文档：https://orca.dev/docs/model/worktrees
- 运行方式：https://orca.dev/docs/ways-to-run
- Bot 快速上手：https://orca.dev/docs/bots
- CLI 概览：https://orca.dev/docs/cli/overview
