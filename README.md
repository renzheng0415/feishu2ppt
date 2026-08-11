# Feishu2PPT

> 在飞书里共同写，在 PowerPoint 里专业交付。

Feishu2PPT 把飞书 / Lark 文档转换成可编辑的 PowerPoint。它会保留文档里的文字、图片、视频、表格和数据结构，先生成可以审查的页面计划，再使用 OfficeCLI 渲染成 .pptx。

当前版本：1.0.0

它适合广告公司、咨询团队、房地产营销团队和内部培训场景。你可以在飞书里负责写内容，交给 Skill 负责页面结构、主题、图表、媒体排版和质量检查。

## 能解决什么问题

- 把飞书里的提报内容转换成可编辑 PPT，而不是一张张截图。
- 让标题层级直接对应章节页、内容页和页内分组。
- 把数字表格转换成可编辑的原生图表，把非数字表格保留为可编辑表格。
- 把图片和视频放到对应内容页，不把素材统一堆到最后。
- 先生成页面计划，确认后再渲染，避免内容还没审查就直接出稿。
- 生成后执行 OpenXML 校验、问题扫描和整稿缩略图检查。

当前包含 23 套主题、20 种内容版式和 12 种原生图表方案，默认字体为微软雅黑（Microsoft YaHei）。

![Feishu2PPT 演示](assets/demo.gif)

![Feishu2PPT 版式展示](assets/showcase.png)

## 安装

### 从 GitHub 安装

~~~bash
npx skills add renzheng0415/feishu2ppt -g --all
~~~

安装后，对智能体这样说：

~~~text
使用 feishu2ppt 把这份飞书文档做成可编辑的提报 PPT。先推荐 3 套风格并生成页面计划，未经我确认不要渲染：<飞书文档链接>
~~~

### 从本地文件夹安装

~~~bash
npx skills add /path/to/feishu2ppt -g --all
~~~

也可以使用 Skill 自带的安装器：

~~~bash
# macOS / Linux
bash scripts/install.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
~~~

安装器支持通过以下环境变量指定各个智能体的 Skill 根目录：

- AGENT_SKILLS_ROOT
- CODEX_SKILLS_ROOT
- CLAUDE_SKILLS_ROOT
- WORKBUDDY_SKILLS_ROOT

## 基本使用

### 第一步：诊断环境

~~~bash
python3 scripts/doctor.py
~~~

需要的基础环境：

- Python 3.11 或更高版本。
- Node.js 和 npm，用于运行官方 @larksuite/cli。
- OfficeCLI，用于生成、校验和截图 PPTX。
- ffmpeg 可选，仅用于给嵌入视频生成首帧海报。

首次读取真实飞书文档时，可能会打开浏览器进行授权。登录、验证码和权限确认由本人完成；凭据保存在飞书 CLI 自己的凭据存储中，不写入 Skill。

### 第二步：生成页面计划

真实飞书文档：

~~~bash
python3 scripts/run.py plan \
  --doc "https://example.feishu.cn/docx/xxx" \
  --theme data_journalism \
  --workdir ./output/project-files
~~~

不登录飞书的本地演示：

~~~bash
python3 scripts/run.py plan \
  --source-xml examples/sample-feishu.xml \
  --workdir /tmp/feishu2ppt-demo-files
~~~

计划阶段会生成：

- source.xml：飞书原始结构快照。
- assets/：图片、视频和其他素材。
- deck.json：可以人工调整的页面计划。
- plan-preview.md：按页查看的快速预览。
- plan-report.json：结构、素材、图表和占位符检查报告。

### 第三步：确认后渲染

先检查 plan-preview.md 和 deck.json，确认主题、页数、章节、页面标题、版式、图表和素材分配。确认后再执行：

~~~bash
python3 scripts/run.py render \
  --plan ./output/project-files/deck.json \
  --output ./output/project.pptx \
  --approve-plan
~~~

渲染器会拒绝缺内容、未知主题、损坏素材、错误表格、图表维度不一致或占位符未处理的页面计划。已有 PPT 会先保存为 .bak，只有校验通过的新文件才会替换最终输出。

## 在飞书里怎么组织内容

默认约定：

- 文档标题 → PPT 封面。
- 一级标题 → 章节转场页。
- 二级标题 → 一页 PPT。
- 三级标题 → 页内分组。
- 段落和列表 → 页面正文。
- 图片和视频 → 当前页面的媒体内容。
- 数字表格 → 可编辑图表。
- 非数字表格 → 可编辑表格。

可以在二级标题下使用这些指令：

- 版式：表格
- 图表：柱状图
- 图表：条形图
- 图表：折线图
- 图表：面积图
- 图表：环形图
- 图表：瀑布图
- 图表：漏斗图
- 图表：散点图
- 图表：直方图
- 图表：矩形树图
- 图表：雷达图
- 图表：组合图
- 结论：这一页读者最终要记住的判断。
- 来源：数据来源和统计截止时间。

完整的飞书写作格式见 references/authoring-contract.md。

## 三个演示案例

### 1. 深圳楼盘月度营销复盘

适合销售月报、直播获客复盘和成交分析。

推荐主题：data_journalism。

核心结构：

~~~text
# 01 核心判断
## 成交增长来自有效到访提升
三条业务判断。

# 02 数据表现
## 到访与认购同步加速
图表：折线图
结论：4 月以后，到访与认购同步加速。
来源：销售日报。
| 月份 | 到访 | 认购 |
|---|---:|---:|
| 1月 | 62 | 18 |
| 2月 | 75 | 22 |

# 03 下一步
## 先解决留资到到访的流失
三步执行动作。
~~~

仓库内的本地示例文件：

- examples/sample-feishu.xml
- examples/showcase-plan.json
- examples/showcase.pptx

### 2. 房地产项目提报

适合开发商提报、楼盘定位、单盘直播方案和广告公司内部启动会。

推荐主题：realestate_gold、architectural_sand 或 swiss_monocle。

内容可以这样组织：

~~~text
# 01 项目判断
## 这个项目真正要解决的是改善客户的决策犹豫
项目现状、客户抗性、竞争替代。

# 02 核心策略
## 用三条内容线把项目优势变成可验证的生活场景
图片：项目实景或区位图。
三条内容线。

# 03 执行样例
## 从短视频到直播间的内容承接
视频：样片或直播片段。
流程、脚本节点和销售承接方式。
~~~

预期页面包括判断页、图文并置页、图片画廊页、流程页和案例页。

### 3. 团队培训课件

适合 WorkBuddy / AI 工具培训、销售培训、直播术语培训和内部 SOP。

推荐主题：vercel_minimal、apple_keynote 或 executive_navy。

内容可以这样组织：

~~~text
# 01 先建立共同语言
## 直播间的三个关键指标
### 曝光
### 停留
### 留资

# 02 再按流程练习
## 一次直播复盘怎么做
图表：漏斗图
结论：先找到流失最大的环节，再决定优化动作。
| 环节 | 人数 | 转化率 |
|---|---:|---:|
| 观看 | 1000 | 100% |
| 留资 | 80 | 8% |

# 03 现场演练
## 从一个楼盘问题写出一条口播
视频：示例视频。
练习要求和交付标准。
~~~

预期页面包括指标卡、流程页、漏斗图页、视频素材页和练习页。

三个案例的完整中文说明见 docs/QUICKSTART_ZH.md，本地演示运行方式见 examples/README.md。

## 主题怎么选

- 通用提报：vercel_minimal。
- 房产和高端项目：realestate_gold 或 architectural_sand。
- 数据复盘：data_journalism。
- 经营汇报：executive_navy。
- 产品或 AI 工具发布：apple_keynote。

主题、版式和图表是三层独立选择。先决定这一页要让读者得出什么结论，再选版式，最后选颜色和图表。

完整目录见 references/style-catalog.md。

## 交付前检查

~~~bash
officecli validate ./output/project.pptx
officecli view ./output/project.pptx issues --json
officecli view ./output/project.pptx screenshot --page 1-20 --grid 4 --out ./output/preview-grid.png
~~~

正确验收顺序是：先确认 validate 通过，再确认 issues 为 0，最后检查完整缩略图和正文密集页。进程退出码正常或 PPT 能打开，都不能替代视觉检查。

运行完整回归：

~~~bash
bash tests/run-tests.sh
~~~

当前发布闸门覆盖：

- 33 个单元测试。
- 2,000 多个异常计划类型变体。
- 20 种版式和 12 类原生图表。
- 混合文字、表格、图片和视频页面。
- 长文本分页、比例文本框、长表格重复表头。
- 当前 Lark src 媒体 token、URL-only 素材、媒体魔数纠正和视频首帧海报。
- 私网 URL 拒绝、缓存替换、旧版本运行时升级和原子发布。
- 强制的“先计划、后批准渲染”两阶段流程。

## 边界与兼容性

- 不修改原飞书文档。
- 未获得飞书授权时，只能停在授权提示，不能假装已经读取在线文档。
- 飞书内嵌电子表格或多维表格需要先通过对应飞书能力读取数据。
- 直接媒体 URL 必须是 HTTPS，单个文件不超过 50 MB。
- Codex 和 Claude Code：支持标准 Agent Skills 目录。
- WorkBuddy 和其他兼容运行时：设置真实 Skill 根目录，或使用 npx skills add 安装。
- macOS / Linux 安装器：已验证。
- Windows 安装器和视频编码行为：已实现，但完整 Windows 验收仍待在 Windows 机器上执行，不能把它写成已验证。

## 许可证

MIT。Lark CLI、OfficeCLI 等外部工具按照各自的许可证和使用条款执行。
