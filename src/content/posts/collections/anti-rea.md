---
title: 防 AI 逆向：把「藏住秘密」换成「打断默认扫描」
published: 2026-11-23
draft: false
description: AI 逆向代理能按格式把发布产物拆开。拆开源工具 BLA，给出一条判据：有效的反逆向不是把文件撑大，而是让默认扫描退出、让等价可验证、让发布可回滚。附实操步骤、同类方案对比和它自己承认的代价
tags: [开源, 工具, 安全, 方法论]
category: 收藏
sourceLink: https://github.com/qybaihe/bla
---

先说一个场景。

你发布了一个 Electron 应用：`dist/` 里有 JS chunk、一张 SourceMap、一个 `.asar`，附带一个 SQLite 缓存和一个小 WASM 模块。你没写错任何代码，但 AI 逆向代理只需要按格式读：解包 asar、还原 `sourcesContent`、把 IPC 通道配对、打开 sqlite 和 wasm 的导出表。README 给的价格是几十秒、约 0.20 美元。你的业务逻辑被复刻，不是因为密码学输了，是因为产物天生带着结构化入口。

传统答案有两条，都不太让人满意。变量改名和压缩把可读性拿掉，LLM 读一遍就能总结；VM 壳把执行包起来，代价是跨平台构建和性能，还有一整条新的调试链路。

这篇想换一个问法：**评估反逆向工具，第一问不是「藏得多深」，而是「它改变了攻击者默认路径的哪个退出条件」**。有效防御要同时做到三件事：默认扫描失败、运行时等价可验证、发布后可回滚。缺一件，你付的钱就变成了别人的重试成本。

成立条件也要先说清：这套判据针对自动化代理的第一次默认扫描。对手换成有无限时间的真人、或者愿意把每个预算参数调到上限，它买的是时间，不是秘密。

## 默认扫描为什么会退出

[BLA](https://github.com/qybaihe/bla) 是这条判据的一个极端样本。它是给软件发布产物做防御的开源 CLI 加 MCP 服务，MIT 协议，npm 包叫 `bla-agents`，当前 3.5.7。仓库 2026 年 10 月 25 日建库，到 11 月 23 日约 6440 star、797 fork；最近 100 次提交里，qybaihe 512 次、DeryFerd 126 次，两个人占了绝大多数。11 月 18 日到 21 日发了 3.5.0 到 3.5.7 至少八版。项目很新，迭代很快，这两件事要一起看。

它不试图让逆向不可能，而是往分析器的默认约束上放东西。README 把做法写成四层，翻译成判据就是三类退出条件。

第一类是让分析器读到假答案。honey SourceMap、canary 元数据、模拟的 SGX/TPM2 委托清单、看起来合理的影子状态机。分析器拿到多条互相冲突的线索，要花上下文去分辨哪条是真的。

第二类是让默认预算先耗尽。14 类格式的实测里：Electron asar 从 607 B 变成 16.9 MiB，撞上 16 MiB 的 `DEFAULT_ASAR_MAX_HEADER_BYTES`；Erlang BEAM 从 84 B 变成 241 KiB，超过 64 个 chunk；Safetensors 和 GGUF 都撞在 32 层嵌套；PCAP 经 tshark 展开到 12.7 MiB，超过固定的 8 MiB 输出上限。REA 在 2026-11-17 的 `05be423` 版本上，这些路径按默认参数都退出了。

第三类是让剥离单点失效。self-seal 用 SHA-256 把 JS、WASM、原生附属文件绑在一起；sidecar entangle 把校验写到多处调用点。攻击者拿掉一个诱饵或 nop 掉一处检查，产物自己会失败。这两项默认关闭，后面会说代价。

关键的一句在 README 自己写的说明里：**这些预算大多是可以被调用方调高的**。asar 上限可以调到 256 MiB，WASM 接口上限到 512 MiB，BEAM 的 `max_chunks` 也能改。只有 PCAP 的 tshark 输出、Safetensors/GGUF 的 32 层、Electron fuse 的 32 个哨兵是固定值。所以「实测通过」准确的读法是「按默认参数，分析器停在这里」，不是「分析器永远进不来」。

## 从零跑一遍：六步，每步都能验证

我把一个 165 字节的 ESM 文件放进 `dist/`，里面只有一个求和函数和一个 API 地址，用 3.5.7 在本机 Node v24.22.1 跑了一遍。命令来自官方安装文档，输出是我自己看到的。

**第一步，确认 Node 版本。** 需要 `^22.23.4 || >=24.0.0`。不想安装就直接用 npx，想进 CI 就装成开发依赖：

```bash
node -v
npm install --save-dev bla-agents
# 或 pnpm add -D bla-agents
```

**第二步，正常构建，然后先看计划。** `harden` 只找构建产物（`dist/`、`build/`、`out/`、`release/`、根目录二进制和模型），不碰 vite 配置、测试和构建脚本。`--dry-run` 一个字节都不写：

```bash
npm run build
npx bla-agents harden . --dry-run
```

我这一步的输出是 `discovered=1 hardened=0 failed=0`，并列出 `dist/app.js` 将写到 `.bla-hardened/dist/app.js`。

**第三步，生成加固镜像。** 不加 `--apply` 时，原产物不动，`harden` 只写一目录部分镜像：

```bash
npx bla-agents harden .
```

我的样例从 165 B 涨到 163 KB，报告写 `score=92`，tokens 放大 5810.3 倍。这个倍数是工具内部模型算出来的，不是实测账单，别当成省钱或费钱的凭据。

**第四步，亲手验一次等价。** 这一步不能省。工具自己的 `verify` 输出写得很清楚：`Runtime equivalence: NOT VERIFIED (no original-versus-protected execution test was run)`，它的 PASS 只覆盖 Counter-REA 结构检查。我用 Node 直接加载两个模块对比：

```bash
node --input-type=module -e "
const a = await import('./dist/app.js');
const b = await import('./.bla-hardened/dist/app.js');
const xs = [{price:3,qty:4},{price:1.5,qty:2}];
console.log(a.total(xs), b.total(xs), a.endpoint === b.endpoint);
"
# 我这边输出：15 15 true
```

**第五步，发布与回滚。** 确认测试通过后再 `--apply`，它只覆盖构建产物，原件放在项目外的状态目录（`BLA_STATE_DIR` 可改），`--restore` 原样放回：

```bash
npx bla-agents harden . --apply
npm test
npx bla-agents harden . --restore   # 出问题时
```

`verify` 的两个参数顺序是「加固文件在前，原文件在后」：`npx bla-agents verify ./dist/app.bla.js ./dist/app.js`。顺序写反，结构检查就失去了对照。

**第六步，再按场景加东西。** 让 Agent 接手就跑 `npx bla-agents setup`，它会注册 31 个 MCP 工具和 `blind-llm-agents` 技能，之后在 Claude Code、Cursor、Codex 这类客户端里说一句「加固当前项目」即可；Agent 在覆盖构建产物前会先问你。前端项目可以改成构建期插件，`intensity` 支持 `stealth / balanced / maximum / bankrupt`：

```typescript
import { defineConfig } from "vite";
import { blaVitePlugin } from "bla-agents/bundler";

export default defineConfig({
  plugins: [blaVitePlugin({ intensity: "bankrupt", enableHoneySourceMaps: true })],
});
```

原生项目用 `npx bla-agents emit-headers` 生成 C/C++/Rust/Go 头文件，在 `main()` 里调一次锚点函数，把计数器编进 `.rodata`。SQLite 的 `--sqlite-eval-trap` 要单独开，开了之后蜜表生成列会调用一个普通连接没有的函数，这同时会让应用自己的 `PRAGMA integrity_check` 和 `VACUUM` 失败，除非你注册同名函数。

## 同类方案怎么选

对比按前面那三条判据来：默认扫描是否退出、等价是否可验证、发布是否可回滚。

| 方案 | 防御落点 | 默认扫描影响 | 等价验证 | 回滚代价 | 主要代价 |
|---|---|---|---|---|---|
| 压缩与改名混淆 | 源码可读性 | 弱，LLM 能总结重命名 | 靠自己测试 | 低 | 保护的是人眼，不是结构化解析 |
| VM 壳 / 强加壳 | 执行过程 | 中，分析器要穿壳 | 难，行为差异常见 | 中到高 | 跨平台、体积、启动性能、调试链路 |
| 客户端加密 + 服务端授权 | 关键逻辑所在 | 强，本地拿不到逻辑 | 明确，接口即边界 | 低 | 离线不可用；key 仍在客户端时等于没搬走 |
| BLA 这类结构防御 | 产物格式与元数据 | 强，默认预算下退出 | 工具查结构，行为要自己验 | 低，`--restore` | 体积膨胀；多数预算可被调用方调高 |

按成立条件选：

- 你的秘密是私钥、签名密钥、核心算法：搬到服务端，别指望任何客户端加固。DISCLAIMER 里也写了这条。
- 你的对手是批量扫描的自动化代理，产物里有 ASAR、WASM、模型元数据这类结构化入口：BLA 这一类结构防御最对路，默认扫描会被打断。
- 你的对手是愿意调高所有预算、能长时间调试的人：它只能增加重试次数，按时间窗口来用，别当访问控制。
- 你在做前端发布、关心体积和首屏：先试 `stealth` 或 `balanced`，`bankrupt` 在我这个 165 B 样例上放大了近千倍体积。
- 你要在 CI 里每次发布都加固：装成 devDependency，挂到 `postbuild`，把 `BLA_STATE_DIR` 指到缓存路径，并把「跑自己的测试」写进流水线。

BLA 自己的风险也摆在这里。默认没有开 self-seal 和 sidecar entangle，我的实测报告把原始 99 分压到 92 分，并在 `Known gaps` 里点名这两项；体积膨胀在真实项目里可能比样例更显著；README 里「300×–2800× Token 放大」和 1195.9× 的聚合值都是内部估算，不是计量过的账单；项目只有四周历史，版本一天发好几版，升级后要重跑 `npx bla-agents@latest setup --yes`，否则 `doctor` 会报 `versionSkew`。

## 本次采集学到的判断

防自动化逆向，目标不是让破解不可能，是让默认扫描拿不到结论。判断一个工具值不值得上，看三件事：它改的是分析器的退出条件还是文件外观；它能不能把「等价」交给可执行的验证；它能不能一键还原到发布前的产物。三件都有的前提下，再去看它撑大多少体积、能不能被调高预算绕过。反过来用也成立：一个只能把文件变大、既不给验证也不给回滚的加固方案，增加的多半是你自己的发布风险。
