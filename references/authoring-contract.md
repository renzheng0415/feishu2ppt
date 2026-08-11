# Feishu Authoring Contract

## Theme precedence

主题优先级固定为：用户本轮显式传入的 `--theme` > 飞书文档封面区的 `主题：` / `风格：` > `vercel_minimal` 默认主题。

This format lets non-technical team members edit content in Feishu while the agent handles presentation design.

## Document-level structure

- Document title: cover title.
- Metadata paragraphs before the first heading are optional:
  - `主题：极简纯白`
  - `副标题：2026 年度营销提案`
  - `公司：心智数字营销`
  - `作者：项目策略组`
- H1 / 一级标题: chapter transition page.
- H2 / 二级标题: one presentation slide.
- H3 / 三级标题: a subheading or grouped point inside that slide.

## Content below each H2

- Paragraphs and lists: page body; keep to 3-6 blocks.
- Image: placed on the same slide; one image uses a text-image split, multiple images use a gallery.
- Video: embedded as playable media when Office/codec support allows it.
- Table: first row is headers; first column is categories; remaining cells are data.
- Quote: use a Feishu quote block when the page should become a quotation page; the agent may adjust `deck.json` to the `quote` layout.

## Optional page directives

Place these as normal paragraphs directly under an H2. They are consumed as settings and do not appear as body text:

- `版式：表格` - keep a data table as a table instead of charting it.
- `图表：柱状图`
- `图表：条形图`
- `图表：折线图`
- `图表：面积图`
- `图表：环形图`
- `图表：瀑布图`
- `图表：漏斗图`
- `图表：散点图`
- `图表：直方图`
- `图表：矩形树图`
- `图表：雷达图`
- `图表：组合图`
- `结论：4 月以后，到访与认购同步加速。`
- `来源：明源系统，统计截至 2026-08-01。`

## Data table rules

For chart generation, use a clean rectangular table:

| 月份 | 到访 | 认购 |
|---|---:|---:|
| 1月 | 62 | 18 |
| 2月 | 75 | 22 |

- Do not merge cells.
- Do not mix text notes into numeric columns.
- Percentages may use `%`; currency may use `¥` or `￥`.
- Time categories trigger a line chart by default.
- One numeric series triggers a horizontal ranking chart by default.
- Multiple numeric series trigger a grouped column chart by default.

## Quality limits

- One H2 should express one conclusion.
- Keep titles short enough for one or two lines.
- Keep body blocks under 80 Chinese characters when possible.
- Use original high-resolution images; avoid screenshots containing unreadably small text.
- Put an image or video under the H2 where it should appear. Do not collect all media at the end of the document.
- If an H2 contains more than six body blocks or four media items, the system creates continuation slides and reports a warning.
