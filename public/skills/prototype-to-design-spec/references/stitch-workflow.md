# Stitch 外部高保真生成通道

适用场景：本机图像生成能力不足以产出高质量 UI 设计图时，把**风格选定环节**外包给 Google Stitch（AI UI 设计平台），本 Skill 仍负责内容契约、设计简报、验收与规范冻结。Stitch 产物定位与自制稿相同——**探索载体**，必须经用户确认（门禁 D）才进入规范阶段。

## 一、接入方式

1. 用户在对话里给出如下配置（API Key 由用户提供，不得写进任何交付物正文）：

   ```json
   { "mcpServers": { "stitch": { "type": "streamableHttp",
       "url": "https://stitch.googleapis.com/mcp",
       "headers": { "X-Goog-Api-Key": "<用户提供>" } } } }
   ```

2. 合并写入 `~/.workbuddy/mcp.json` 的 `mcpServers`（不得覆盖既有 server；不要写成用户给的顶层 `servers` 键）。
3. 写入后 MCP 不会自动生效，需用户在连接器管理页信任；**信任前**可用「HTTP 直调」继续工作（见下），不要因此阻塞。

### HTTP 直调（绕过未信任状态）

Stitch 端点对浏览器 CORS 放行，可在已登录的浏览器任务空间里用 `fetch` 发 JSON-RPC：

- `initialize` → `tools/list` → `tools/call`，头：`Content-Type: application/json`、`Accept: application/json, text/event-stream`、`X-Goog-Api-Key`。
- 服务端是无状态实现（`StatelessServer`），无需维护 `Mcp-Session-Id`。

## 二、工具地图（与本 Skill 的对应）

| Stitch 工具 | 用途 | 本 Skill 对应 |
|---|---|---|
| `create_project` / `list_projects` | 建项目、找回已有项目 | `design-state.json` 记 `external.stitch.project_id` |
| `generate_screen_from_text` | 文本生成整屏设计 | S2 外部候选稿（`deviceType: MOBILE`） |
| `edit_screens` / `generate_variants` | 迭代与变体 | 否决回路 / 同方向出备选 |
| `list_screens` / `get_screen` | 轮询与读取屏幕 | 生成后取证 |
| `download_file` | 下载截图 / HTML | 归档到 `design/04-stitch/` |
| `upload_design_md` + `create_design_system_from_design_md` | 注入 DESIGN.md 设计系统 | S4 之前统一各 tab 风格 |
| `create_design_system` / `apply_design_system` | 建设计系统并套用到屏幕 | 规范冻结后反向约束 |

## 三、提示词结构（必须完整包含四层）

1. **产品与屏幕定义（功能文字复述）**：用自然语言把原型的这一屏**完整复述**给 Stitch——这一屏是干什么的、从上到下每段有什么信息、每项数据是什么值、有哪些操作。内容契约里的文案**逐字嵌入**，不要只给 token 值。
2. **风格参考**：给**真实产品的设计图 URL**（来源优先级：用户指定的参考站如 uinotes > 选定候选稿），写明「视觉以参考图为准，内容以本提示词为准」，并声明学什么（卡片语言、层级、留白、数字排版）、禁什么（品牌名、Logo、导航结构、营销元素）。
3. **逐段布局**：从上到下每一段写明元素、文案、尺寸与角色，并显式写「do not invent extra modules / do not change wording」+ 排除项（搜索框、图表、徽标等）。
4. **整体性要求**：coherent designed product、无截断、单屏完整呈现。

语言：英文骨架 + 中文文案逐字嵌入，生成质量最稳。

## 三A、参考图取材链路（以 uinotes 为例）

1. 在参考站详情页抓取截图 CDN 地址（uinotes 为阿里云 OSS：`uinotes-img.oss-cn-shanghai.aliyuncs.com/image/480-webp/<id>.webp`，需滚动触发懒加载后从 `img.currentSrc` 收集）。
2. OSS 通常有 **Referer 防盗链**：本机带 `Referer: https://uinotes.com/` 头可直取，但 Stitch 服务器抓取时不会带该头 → **必须转存**：下载到本地后放入静态目录，用 `workbuddy_sites_deploy` 发布成公网站，得到无防盗链的直链（如有 sharecode 门控，URL 需带参数）。
3. 参考图多为 **App Store 营销图**（大标题+手机壳+插画）：可用，但提示词要写「只学界面内的配色/圆角/排版/组件语言，忽略营销标题、插画、手机壳」；若某参考的插画风格会污染输出，换纯界面截图的产品。
4. 参考产品选择是设计决策，按场景匹配度选（如收学费工具选金融级产品做参考），并在 brief 里记录评估过哪些、为何选它。

## 三B、参考图生效性验证与色相偏差

- **必须先做可证伪对照测试**：拿一张与当前方向反差极大的参考图（如深色稿）在**干净新项目**生成一次，输出跟随参考图则链路成立；不能凭一次正向生成下结论。
- **同项目已有 designTheme 会带偏色相**：项目内多次生成会累积设计主题，后续生成即使给了蓝色系参考图，输出仍可能延续旧主题色相（实测：理财通蓝色参考 → 输出绿色）。要严格验证参考图色相，需**新建干净项目**生成；接受色相延续时在 brief 里如实记录偏差来源。

## 四、执行陷阱（实战确认）

- `generate_screen_from_text` 单次耗时数分钟。**不要在等待中重试**——服务端会重复建屏。官方口径：失败后用 `get_screen` / `list_screens` 轮询取证。
- 宿主环境的页面求值常有 ~15s 超时：**先发射后不管**（fetch 结果写入 `window` 变量），再另起轮询查 `window` 回执与 `list_screens`，双通道取先到者。
- `download_file` / `:download` 端点返回 **JSON 包裹**：截图可能在 `dataString`，也可能在 `image`（均为 base64）；HTML 可能是 `dataString` 或直接文本。落盘前按实际字段解码，并用 `file` 命令验证 magic number（PNG `89504e47`）。
- 终端 HTTP 直调若遇代理 502，先核对终端代理与系统代理是否不同；实测显式使用系统代理后，`tools/list` / `list_screens` / `get_screen` 可直连成功。大文件下载若出现 SSL EOF，可用 `curl --http1.1` 经同一系统代理接收完整 JSON，再解码；不要在生成请求上盲目重试。
- MCP 无图像输入参数，但**参考图可以通过公网 URL 注入提示词**（实测有效）：把选定候选稿/参考截图发布成一个静态站（如 `workbuddy_sites_deploy`），把图片直链写进提示词「REFERENCE IMAGE (source of truth for visual language): <url>」。**必须先用可证伪的对照测试验证 URL 确实被消费**：拿一张与当前方向反差极大的参考图（如深色稿）生成一次，若输出风格跟随参考图则链路成立；不能凭一次正向生成下结论。
- 提示词分层必须显式拆开：「视觉风格以参考图为准，内容以本提示词为准」，并写 HARD CONSTRAINTS 禁止杜撰——实测不写禁令时模型会自行加「核心数据概览」「4项指标」「需处理」徽标、消息铃铛、图表等模块；写了禁令后杜撰为零。
- 生成的 HTML 依赖 Google Fonts / Tailwind CDN，本地预览需联网；交付物以 PNG 为准，HTML 仅作代码参考。
- `edit_screens` 返回的「已修改」文字与 `DomOperationEvent` 只是操作回执，不是文件更新证据。实测可能出现回执已返回、但随后 `download_file` 的 PNG/HTML 仍旧是编辑前版本；必须重新检查实际 HTML 文本与 PNG，不得凭回执宣称通过。若服务端文件滞后，保留初稿，按回执中的精确 DOM 操作修正归档 HTML，并真实渲染验收，同时在 brief 记录这一差异。
- 本地渲染移动端 Stitch HTML 时，设备仿真与 `Page.captureScreenshot` 必须在**同一次浏览器脚本调用**中完成；CDP 的 `Emulation.setDeviceMetricsOverride` 可能在调用结束后失效。等待字体、Tailwind 栅格样式与 `scrollWidth` 均确认后再截图，避免右侧裁切、字体过小或只捕到部分卡片。

## 五、纪律

- Stitch 项目、屏幕 ID、提示词全文、下载文件路径都要写入 `design/04-stitch/` 归档（brief 文档 + PNG + HTML），`design-state.json` 记录 `external.stitch` 与轮次。
- 生成结果先自检（内容契约逐项核对 + 视觉质检），再交给用户；**用户确认前不得冻结任何规范条款**。
- 第三方生成同样不得复刻真实品牌素材；提示词中禁止出现真实产品名/Logo 描述。
