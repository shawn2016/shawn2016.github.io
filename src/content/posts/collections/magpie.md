---
title: 从 CC Switch 到 magpie：把「改配置」换成「接管出口」
published: 2026-11-23
draft: false
description: 两个工具都帮你切 API provider，差别在关掉它们之后。拆开配置改写与本地网关两条路线，给出从 CC Switch 迁到 magpie 的实操步骤、按判据维度的对比表和选型清单，以及网关常驻的真实代价
tags: [开源, 工具, AI, 方法论]
category: 收藏
sourceLink: https://github.com/yetone/magpie
---

先说一个场景。

你机器上装着 Claude Code 和 Codex，手里有四个 API key：一个官方 Claude、一个 DeepSeek、一个公司内部中转、一个 Kimi。你想让 Claude Code 跑 DeepSeek，Codex 跑 Kimi，月底再看谁把额度先用光。

两个工具都说能干这件事。CC Switch 有 90 多个 preset、支持十二个 agent；magpie 的 README 开头就写着「Claude Code on Kimi, Codex on DeepSeek」。菜单长得差不多，都能一键切。

差别藏在关掉它们之后。关掉 CC Switch，agent 还在直连原来的 provider，配置文件里写好的 endpoint 和 key 照常工作。关掉 magpie，所有指向它的 agent 一起断——除非你在关之前执行过还原。

这篇想论证一件事：**挑这类工具，第一问不是支持多少 provider，而是请求从谁手里出去**。出口留在 agent 手里，工具只是个编辑器；出口收到工具手里，工具就成了调度层。这个位置决定故障半径、接管成本，以及你能不能跨 agent 共享一份订阅。

## 两条路，分岔在「谁持有出口」

CC Switch 的默认动作是改配置。它读每个 agent 自己的配置文件——Claude Code 是 `~/.claude/settings.json`，Codex 是 `~/.codex/config.toml`——只替换连接字段：endpoint、key、模型名、API 协议。插件、hooks、权限、你自己加的环境变量和注释都留着。它的 README 写得很直白：「Switching replaces only the connection details」。

这意味着默认情况下，Claude Code 拿着 key 直连 provider。CC Switch 退出时把直连配置写回，下次启动再接管。它另有「Routing」模式，会把请求转发到本机做协议转换，但那是你主动打开的可选项，不是默认状态。

magpie 反过来。装好之后，agent 的 base URL 一律指向 `http://127.0.0.1:3425`，key 填 `magpie`。agent 不再持有任何厂商的 key 和 URL，所有请求先到本地网关，由网关决定转发给谁、转成什么协议、额度不够时换哪个账号。

一句可迁移的判断：**配置改写型把控制权留在被管理的对象手里，网关型把控制权收拢到自己手里**。前者退出无痕，代价是每个 agent 仍是孤岛；后者能做跨 agent 的调度，代价是它必须在。

成立条件说清楚：如果你只有一个 agent、一个官方订阅、够用，这套判断不成立，随便挑一个就行。它只在「多 agent × 多 provider × 多账号」时才开始起作用。

## 实操：从 CC Switch 迁到 magpie

下面是我在这台 Mac 上真实走过的路径。magpie 版本 0.1.4710，macOS arm64。

### 第一步：先看清楚当前谁在接管

别急着装。先读一眼你现在的配置指向哪：

```bash
grep -iE "BASE_URL|ANTHROPIC_MODEL" ~/.claude/settings.json
grep -iE "base_url|model_provider" ~/.codex/config.toml
```

我这一步查出来 Claude Code 指向 `http://127.0.0.1:4000`，模型是 `deepseek-v4-flash`，而 CC Switch 数据库里记录的当前 provider 是 MiniMax。两者对不上——说明这份配置后来被另一个工具改过，CC Switch 当时并不是实际生效的那个。

这一眼很重要。迁移的目标不是「把 CC Switch 的配置复制过去」，而是「把现在真正生效的连接方式迁过去」。

### 第二步：安装

官方给的是一行命令：

```bash
curl -fsSL https://usemagpie.ai/install.sh | sh
```

脚本会校验 SHA-256，把 `magpie.app` 放进 `/Applications`，把命令软链到 `~/.local/bin/magpie`。我这边下载时遇到 502，回退下载被中断，于是走了手动等价路径：

```bash
# 从官方 feed 拿当前版本的下载地址与校验和
curl -fsSL https://usemagpie.ai/api/latest | python3 -m json.tool | less

# 下载后先校验，再解压安装
shasum -a 256 magpie-darwin-arm64.zip
ditto -x -k magpie-darwin-arm64.zip /tmp/magpie-x
mv /tmp/magpie-x/magpie.app /Applications/
ln -sf /Applications/magpie.app/Contents/MacOS/magpie ~/.local/bin/magpie
magpie --version
```

无论走哪条路，最后都要能跑出版本号。别跳过这步。

### 第三步：把 provider 迁进去

magpie 的 README 写着「Import brings in the providers from CC Switch, Claude Code, Codex and Alma」。这个一键导入在图形界面里，CLI 没有对应命令。

如果你用 CLI，就得自己搬。CC Switch 的 provider 存在 `~/.cc-switch/cc-switch.db` 的 `providers` 表里，`settings_config` 是 JSON，key 以明文放在 `env` 字段。写个脚本读出来，逐个调 `magpie provider add`：

```bash
magpie provider add "DeepSeek Official" \
  anthropic=https://api.deepseek.com/v1 \
  key=sk-... \
  id=cc-deepseek-official \
  models=deepseek-v4-pro
```

字段含义：`anthropic=` 是 Anthropic 兼容的 base URL，`url=` 是 OpenAI 兼容的，`key=` 是密钥，`models=` 指定暴露哪些模型，`id=` 自己起一个稳定标识。

这里有个坑我踩到了：两个 qwen provider 和 Unitoken DeepSeek 共用同一个 key 和 base URL，magpie 直接拒收，报「already added with that key」。这是它的去重逻辑。共用一份凭据的不同模型，在 magpie 里属于同一个 provider，用 `magpie provider models <id> +<model>` 增补模型即可，不必重复建条目。

迁移完验证：

```bash
magpie providers
magpie models
```

前者列出 provider 和猜出来的 host，后者列出 agent 能选的全部模型，格式是 `provider/model`。Codex 的 ChatGPT 订阅不用搬，magpie 会从本地登录态自动发现。

### 第四步：让 agent 接入网关

到这一步 magpie 有 provider 了，但 agent 还没指向它。逐个切：

```bash
magpie claude cc-deepseek-official/deepseek-v4-pro
magpie codex codex/gpt-6-luna
```

执行后 magpie 会改写 agent 的配置，把 base URL 指向自己的网关，并记住接管前的原配置。后悔了就还原：

```bash
magpie claude default
magpie codex default
```

这条还原命令是网关型工具必须存在的东西。它把「接管」变成可逆动作，也是我敢把 CC Switch 卸掉的前提。

### 第五步：日常与进阶

日常切换在菜单栏做，或者用 CLI 直接指定模型。查额度用 `magpie accounts`。想让多个订阅按策略轮转，建一个 routing group：

```bash
magpie group add "daily-coding" \
  models=claude/claude-opus-5-5,copilot/claude-opus-5.5 \
  routing=smart
magpie claude group/daily-coding
```

`routing` 可选 `smart`、`order`、`rotate`、`usage`、`pace` 等模式，分别对应按剩余额度、按序、轮询、按用量、按周配额节奏来选账号。

再往下一层是隐私遮蔽。打开后，key、邮箱这类值在请求离开本机前被替换成占位符，回复里再还原。默认关闭，在 Settings → Privacy 里开。要注意模型看到的是占位符，如果任务本身就是分析某个密钥，得把它加进 Never mask。

## 对比：按判据看，不按功能打分

| 判据 | CC Switch（配置改写型） | magpie（网关常驻型） |
|---|---|---|
| 出口在哪 | agent 直连 provider；路由是可选开关，退出时写回直连配置 | 常驻 `127.0.0.1:3425`，agent 一律指向网关 |
| 信任从哪来 | 信任 agent 自己的配置文件，工具只改连接字段 | 信任本地网关，agent 不持有厂商 key 与 URL |
| 能力覆盖 | 12 个 agent，90+ preset；直连／路由／聚合三态；MCP、Skills、Prompts、会话浏览 | 网关说四种协议（OpenAI Chat／Responses／Anthropic Messages／Gemini），菜单栏／TUI／Web／CLI／Docker；订阅共享、路由组、隐私遮蔽 |
| 故障半径 | 工具不在，agent 照常直连 | 网关不在，所有接入的 agent 一起断 |
| 接管成本 | 切换即写配置；官方 provider 不进本地路由 | 需执行 `magpie <agent> default` 才还原 |
| 体量与节奏 | 156k stars，2025-08 起，Rust／Tauri，约日更 | 40k stars，2026-09 起，Go，一天发四到五个版本，仍是 0.1.x |

按成立条件的选型清单：

- 只有一个 agent、一个官方订阅、够用 → 两个都不用装。
- 多个 agent 多 provider，只想快速切 key，不想要常驻进程 → 配置改写型。
- 想把一份订阅给多个 agent 用，或要跨账号故障转移、统一用量、隐私遮蔽 → 网关型。
- 一台机器要给团队或远端设备共享 provider → 网关型，它支持 gateway key 和远程 magpie。
- 环境不允许后台常驻服务，或要求工具关闭后零残留 → 配置改写型。

## magpie 的代价，说在最后

网关是单点。它不跑，所有指向它的 agent 都断。这不是 bug，是架构的必然结果——你既然把出口收拢到一个点，这个点就成了必经之路。卸载前一定先逐个 `magpie <agent> default`，不能直接删应用。

协议转换引入新变量。thinking signature、图片能力、流式事件都要过一层翻译，上游行为不一致时容易出问题。CC Switch 在 README 里专门写了一个叫 Rectifier 的机制来修这类请求，说明这不是假想的风险，网关型方案同样要面对。

订阅跨客户端使用要看厂商条款。CC Switch 在自己的 FAQ 里明确写了「使用订阅在非官方客户端可能违反厂商服务条款，风险自担」。订阅共享是 magpie 的主打能力之一，这条风险不会因为它实现得优雅就消失。

迭代快也是成本。我写这篇时版本是 0.1.4710，当天它发了五个版本。命令和设置项还在变，照着教程做之前先跑一次 `magpie --help` 对一下当前版本。

还有一处容易漏：API key 现在存在 magpie 自己的 `~/.config/magpie/providers.json` 里。你多了一个要备份的地方。`magpie backup` 可以把它和用量、profile、agent 模型一起打包，用口令封起来。

## 收尾

从 CC Switch 换到 magpie，表面是换了个应用，实际是把「谁持有出口」这个问题的答案改了。

配置改写型让你随时能退回直连，代价是能力止步于单 agent；网关型把调度能力打开，代价是它必须常驻、必须被正确还原。判断的依据不是哪个 star 多、哪个 preset 全，而是你能不能接受「关掉它之后，我的 agent 还能不能干活」这个问题的答案变成「不能」。

我自己这台机器上的迁移已经做完：CC Switch 连同 `~/.cc-switch` 一起移进了废纸篓，magpie 接管了五个 provider。Claude Code 目前还指向另一个本地中转，没切到 magpie——这是下一步的事，也正好说明「装好工具」和「让工具接管」是两件事。
