# OfficeCLI Pro PPT V2 Catalog

This catalog separates three decisions that must not be collapsed into one template: visual theme, information layout, and chart recipe.

All themes use `Microsoft YaHei` (微软雅黑) for headings, body text, labels, and data annotations by default.

## Theme Library (23)

### Executive and real-estate

- `realestate_gold` - 地产黑金：高端楼盘、资产提报、品牌发布。
- `executive_navy` - 高管深蓝：经营汇报、董事会、年度策略。
- `financial_green` - 金融墨绿：投资分析、财务报告、资产管理。
- `architectural_sand` - 建筑沙丘：建筑、空间、城市更新、设计提案。

### Editorial and cultural

- `swiss_monocle` - 瑞士墨水：编辑感、杂志感、品牌观点。
- `editorial_ink` - 编辑部墨黑：研究报告、深度文章、文化提案。
- `terracotta_warm` - 暖沙陶土：生活方式、文旅、社区内容。
- `forest_canopy` - 森林墨绿：生态、自然、康养项目。
- `autumn_amber` - 金秋夕照：人文、故事、温暖叙事。

### Minimal and product

- `vercel_minimal` - 极简纯白：通用提报、产品逻辑、干净数据页。
- `apple_keynote` - 苹果发布会：产品发布、创新概念、单点聚焦。
- `brutalist_white` - 新粗野纯白：强观点、创意方案、年轻品牌。
- `bauhaus_primary` - 包豪斯原色：设计提案、展览、视觉概念。
- `soft_pastel` - 柔雾粉彩：轻品牌、教育、女性与生活方式。

### Technology and dark

- `midnight_executive` - 午夜蓝黑：科技战略、AI、平台架构。
- `cyber_neocarbon` - 赛博深光：未来概念、数字展厅、技术发布。
- `catppuccin_mauve` - 猫咪柔紫：创作者工具、轻科技、社区产品。
- `terminal_green` - 终端荧光：开发者、工程、开源项目。
- `cobalt_tech` - 钴蓝科技：企业科技、云服务、数据平台。

### Research and data

- `academic_navy` - 学术海军蓝：研究、政策、行业白皮书。
- `data_journalism` - 数据新闻：市场月报、媒体数据叙事。
- `arctic_frost` - 北极霜蓝：医疗、科学、清洁技术。
- `cherry_bold` - 樱桃高对比：传播战役、品牌复盘、强对比数据。

## Layout Library (20 + cover)

- `section_header` - 章节转场，只承担节奏切换。
- `statement` - 单一强判断或关键结论。
- `quote` - 引用、客户原话、核心主张。
- `content` - 标准正文与要点页，承接飞书二级标题下的普通段落和列表。
- `two_column` - 两组平行信息。
- `comparison` - 现状/目标、方案 A/B、竞品对照。
- `image_left` / `image_right` - 图片或视频与解释文字并置。
- `full_bleed` - 场景图、项目图、案例氛围页。
- `media_gallery` - 一至四张图片或视频的媒体画廊页。
- `cards_2` / `cards_3` - 两到三个独立观点。
- `grid_4` / `grid_6` - 能力矩阵、内容地图、项目清单。
- `timeline` - 有时间先后的阶段规划，最多五段。
- `process` - 输入到输出的执行闭环，最多六步。
- `kpi_grid` - 两到四个关键指标及解释。
- `table` - 精确值、条件和选项对照。
- `chart_focus` - 一张主图表加一个结论栏。
- `dashboard` - 指标、趋势与行动同页。

## Chart Library (12)

- `column_compare` - 同一分类下比较多个系列。
- `bar_rank` - 项目、渠道或区域排名；优先使用横向条形图。
- `line_trend` - 时间趋势、拐点、周期变化。
- `area_growth` - 强调累计增长或规模变化。
- `doughnut_share` - 少量分类的占比结构；分类过多改用条形图。
- `waterfall_bridge` - 收入、利润或预算从起点到终点的增减桥接。
- `funnel_pipeline` - 获客、留资、到访、成交的阶段转化。
- `scatter_relation` - 两个变量的相关性和异常点。
- `histogram_distribution` - 价格、面积、周期等连续值分布。
- `treemap_structure` - 多层级占比和结构。
- `radar_profile` - 少量对象的多维能力轮廓；不用于精确比较。
- `combo_target` - 实际值、趋势线和目标线组合。

## Layout Selection Rules

1. First write the one-sentence conclusion of the slide.
2. Use `statement` when the conclusion itself is the content.
3. Use `comparison` only when the reader must compare two things.
4. Use `timeline` for time; use `process` for causality or operational flow.
5. Use `table` for exact lookup; use charts for patterns and differences.
6. Use `dashboard` only when all KPIs lead to one management action.
7. Avoid repeating card grids across adjacent slides.

## GitHub-Derived Practices

The V2 system translates, rather than copies, ideas from these open-source projects:

- PptxGenJS chart demos: broad native chart coverage and editable series.
- reveal.js layout helpers: explicit alignment, stacking, and stretch behavior.
- Slidev Apple Basic: strong hierarchy, generous whitespace, product-stage pacing.
- Slidev Seriph: editorial typography and image-led composition.
- Marp Core themes: tokenized themes separated from slide content.
- Apache ECharts and Plotly: choose chart form by data relationship, not decoration.

No upstream template files, code, or visual assets are bundled in this library.

## Verification Standard

Every generated deck must pass:

1. `officecli validate <deck.pptx>`
2. `officecli view <deck.pptx> issues --json`
3. `officecli view <deck.pptx> screenshot --page 1-N --grid 4 --out <grid.png>`
4. Human visual inspection of the complete grid and any dense individual slide.
