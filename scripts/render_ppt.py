"""OfficeCLI presentation engine V2: themes, layouts, charts, media, and QA."""

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from themes import get_theme


SLIDE_W = 33.87
SLIDE_H = 19.05
MARGIN = 1.30
GAP = 0.80


CHART_RECIPES = {
    "column_compare": {"chartType": "column", "legend": "bottom", "dataLabels": "outsideEnd", "gridlines": "E5E7EB:0.5", "gapwidth": "65"},
    "bar_rank": {"chartType": "bar", "legend": "none", "dataLabels": "outsideEnd", "gridlines": "none", "gapwidth": "45"},
    "line_trend": {"chartType": "line", "legend": "bottom", "marker": "circle:6", "linewidth": "2.5", "gridlines": "E5E7EB:0.5"},
    "area_growth": {"chartType": "area", "legend": "bottom", "gridlines": "E5E7EB:0.5", "transparency": "25"},
    "doughnut_share": {"chartType": "doughnut", "legend": "right", "dataLabels": "percent,category", "holeSize": "62", "varyColors": "true"},
    "waterfall_bridge": {"chartType": "waterfall", "legend": "none", "dataLabels": "value", "gridlines": "none"},
    "funnel_pipeline": {"chartType": "funnel", "legend": "none", "dataLabels": "value,percent", "varyColors": "true"},
    "scatter_relation": {"chartType": "scatter", "scatterstyle": "marker", "legend": "bottom", "marker": "circle:7", "gridlines": "E5E7EB:0.5"},
    "histogram_distribution": {"chartType": "histogram", "legend": "none", "gridlines": "E5E7EB:0.5", "gapwidth": "10"},
    "treemap_structure": {"chartType": "treemap", "legend": "none", "dataLabels": "category,value", "varyColors": "true"},
    "radar_profile": {"chartType": "radar", "legend": "bottom", "marker": "circle:5", "transparency": "40"},
    "combo_target": {"chartType": "combo", "legend": "bottom", "gridlines": "E5E7EB:0.5", "secondaryaxis": "2", "referenceline": "100:FF3B30:目标"},
}


def encode_table_data(headers, rows):
    def quote_cell(value):
        return '"' + str(value).replace('"', '""') + '"'

    return ";".join([",".join(quote_cell(v) for v in headers)] +
                    [",".join(quote_cell(v) for v in row) for row in rows])


class DeckBuilder:
    def __init__(self, config, output):
        self.cfg = config
        self.output = output
        self.theme = get_theme(config.get("theme", "vercel_minimal"))
        self.commands = []
        self.slide_count = 0
        self.total = 1 + len(config.get("slides", []))

    @staticmethod
    def cm(value):
        return f"{value:.2f}cm"

    def add(self, parent, element_type, **props):
        clean = {k: str(v) for k, v in props.items() if v is not None and v != ""}
        self.commands.append({"command": "add", "parent": parent, "type": element_type, "props": clean})

    def rect(self, slide, x, y, w, h, fill=None, line="none", radius=False):
        self.add(
            f"/slide[{slide}]", "shape", geometry="roundRect" if radius else "rect",
            x=self.cm(x), y=self.cm(y), width=self.cm(w), height=self.cm(h),
            fill=fill or self.theme["surface"], line=line,
            adj="adj:val 6000" if radius else None,
        )

    def text(self, slide, text, x, y, w, h, size=18, color=None, bold=False,
             font=None, align="left", valign="top", line_spacing="1.25x"):
        self.add(
            f"/slide[{slide}]", "textbox", text=text, x=self.cm(x), y=self.cm(y),
            width=self.cm(w), height=self.cm(h), size=f"{size}pt",
            color=color or self.theme["ink"], bold=str(bold).lower(),
            font=font or self.theme["body_font"], align=align, valign=valign,
            lineSpacing=line_spacing, autoFit="normal", margin="0",
        )

    def note(self, slide, note):
        self.add(f"/slide[{slide}]", "notes", text=note or "按页面标题陈述核心结论，再解释证据。")

    def media(self, slide, source, x, y, w, h, poster=None):
        if not source:
            return
        ext = os.path.splitext(source.lower())[1]
        if ext in {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}:
            self.add(
                f"/slide[{slide}]", "media", src=source, poster=poster,
                x=self.cm(x), y=self.cm(y), width=self.cm(w), height=self.cm(h),
                autoPlay="false", loop="false", volume="80",
            )
        else:
            self.add(
                f"/slide[{slide}]", "picture", src=source,
                x=self.cm(x), y=self.cm(y), width=self.cm(w), height=self.cm(h),
                alt="演示文稿配图",
            )

    def new_slide(self, background=None, chrome=True, section=""):
        self.slide_count += 1
        slide = self.slide_count
        self.add("/", "slide", layout="blank", background=background or self.theme["background"])
        if chrome:
            self.text(slide, section.upper(), MARGIN, 0.48, 20, 0.42, 8,
                      self.theme["primary"], True, self.theme["mono_font"])
            self.text(slide, f"{slide:02d} / {self.total:02d}", 30.2, 0.48, 2.35, 0.42,
                      8, self.theme["muted"], False, self.theme["mono_font"], "right")
        return slide

    def slide_title(self, slide, title, kicker=""):
        if kicker:
            self.text(slide, kicker.upper(), MARGIN, 1.15, 28, 0.48, 9,
                      self.theme["primary"], True, self.theme["mono_font"])
        self.text(slide, title, MARGIN, 1.55, 30.5, 1.9, 36,
                  self.theme["ink"], True, self.theme["heading_font"])

    def cover(self):
        slide = self.new_slide(chrome=False)
        motif = self.cfg.get("motif", "edge_band")
        if motif == "edge_band":
            self.rect(slide, MARGIN, 2.2, 0.18, 13.8, self.theme["primary"])
        self.text(slide, self.cfg.get("eyebrow", "STRATEGIC PRESENTATION"), 2.05, 2.25, 20, 0.5,
                  10, self.theme["primary"], True, self.theme["mono_font"])
        self.text(slide, self.cfg.get("title", "演示文稿"), 2.05, 3.35, 28.5, 5.2,
                  42, self.theme["ink"], True, self.theme["heading_font"], line_spacing="1.14x")
        subtitle = self.cfg.get("subtitle", "")
        if subtitle:
            self.text(slide, subtitle, 2.05, 9.2, 25.5, 2.0, 20, self.theme["muted"])
        self.text(
            slide,
            f"{self.cfg.get('company', '心智数字营销')}  ·  {self.cfg.get('author', '策略团队')}  ·  {self.cfg.get('date', '2026')}",
            2.05, 15.4, 28, 0.6, 10, self.theme["muted"], False, self.theme["mono_font"],
        )
        self.note(slide, self.cfg.get("cover_note", "用一句话交代提报对象、目标与本次希望确认的决定。"))

    def section(self, spec):
        slide = self.new_slide(background=self.theme["ink"], chrome=False)
        self.text(slide, str(spec.get("number", f"{slide-1:02d}")), MARGIN, 2.0, 8, 1.4, 52,
                  self.theme["accent"], True, self.theme["mono_font"])
        self.text(slide, spec.get("title", "章节标题"), MARGIN, 5.0, 28.5, 3.0, 38,
                  self.theme["background"], True, self.theme["heading_font"])
        self.text(slide, spec.get("subtitle", ""), MARGIN, 9.0, 24, 2.0, 20,
                  self.theme["muted"])
        self.note(slide, spec.get("notes", "章节过渡，说明接下来要回答的问题。"))

    def statement(self, spec):
        slide = self.new_slide(section=spec.get("section", "KEY POINT"))
        self.text(slide, spec.get("statement", spec.get("title", "核心判断")), 2.1, 4.0, 29.6, 6.0,
                  42, self.theme["ink"], True, self.theme["heading_font"], line_spacing="1.18x")
        self.rect(slide, 2.1, 11.0, 4.2, 0.12, self.theme["accent"])
        self.text(slide, spec.get("support", ""), 2.1, 12.1, 24.0, 2.7, 20, self.theme["muted"])
        self.note(slide, spec.get("notes", "先说判断，再解释这项判断如何影响后续决策。"))

    def quote(self, spec):
        slide = self.new_slide(section=spec.get("section", "QUOTE"))
        self.text(slide, "“", 1.8, 2.6, 3, 2.5, 72, self.theme["accent"], True, self.theme["heading_font"])
        self.text(slide, spec.get("quote", "引用内容"), 3.7, 4.0, 27.5, 7.0, 34,
                  self.theme["ink"], True, self.theme["heading_font"], line_spacing="1.25x")
        self.text(slide, spec.get("source", ""), 3.7, 12.5, 20, 0.7, 14, self.theme["muted"])
        self.note(slide, spec.get("notes", "解释引用与当前方案之间的关系。"))

    def content(self, spec):
        slide = self.new_slide(section=spec.get("section", "CONTENT"))
        self.slide_title(slide, spec.get("title", "页面标题"), spec.get("kicker", ""))
        items = spec.get("items") or [x for x in spec.get("body", "").split("\n") if x.strip()]
        items = items[:6]
        start_y = 4.35
        texts = [item.get("body", item.get("text", "")) if isinstance(item, dict) else str(item)
                 for item in items]
        line_counts = [sum(max(1, math.ceil(len(line) / 36)) for line in (text.splitlines() or [""]))
                       for text in texts]
        raw_heights = [max(1.25, lines * 1.0 + 0.2) for lines in line_counts]
        scale = min(1.0, 11.6 / max(1.0, sum(raw_heights)))
        heights = [height * scale for height in raw_heights]
        y = start_y
        for text, row_h in zip(texts, heights):
            self.add(f"/slide[{slide}]", "shape", geometry="ellipse", x=self.cm(MARGIN), y=self.cm(y + 0.18),
                     width="0.28cm", height="0.28cm", fill=self.theme["primary"], line="none")
            self.text(slide, text, MARGIN + 0.7, y, 29.5, row_h - 0.15, 18,
                      self.theme["ink"], line_spacing="1.22x")
            y += row_h
        self.note(slide, spec.get("notes", "按页面结论组织要点，不逐字朗读。"))

    def media_gallery(self, spec):
        slide = self.new_slide(section=spec.get("section", "MEDIA"))
        self.slide_title(slide, spec.get("title", "图片与视频"), spec.get("kicker", ""))
        lead = spec.get("lead", "")
        if lead:
            self.text(slide, lead, MARGIN, 3.55, SLIDE_W - 2 * MARGIN, 1.2, 18,
                      self.theme["muted"], line_spacing="1.25x")
        media = spec.get("media", [])[:4]
        count = max(1, len(media))
        top = 5.15 if lead else 4.05
        available_h = 10.65 if lead else 11.8
        if count == 1:
            slots = [(MARGIN, top, SLIDE_W - 2 * MARGIN, available_h)]
        elif count == 2:
            slots = [(MARGIN, top, 15.23, available_h), (17.34, top, 15.23, available_h)]
        else:
            half_h = (available_h - 0.65) / 2
            slots = [
                (MARGIN, top, 15.23, half_h), (17.34, top, 15.23, half_h),
                (MARGIN, top + half_h + 0.65, 15.23, half_h),
                (17.34, top + half_h + 0.65, 15.23, half_h),
            ]
        for item, (x, y, w, h) in zip(media, slots):
            self.rect(slide, x, y, w, h, self.theme["surface"], f"{self.theme['border']}:0.8", True)
            source = item.get("video") or item.get("image") or item.get("source")
            self.media(slide, source, x + 0.2, y + 0.2, w - 0.4, h - 0.4, item.get("poster"))
        self.note(slide, spec.get("notes", "结合图片或视频解释页面结论。"))

    def two_column(self, spec, media_side=None):
        slide = self.new_slide(section=spec.get("section", "ANALYSIS"))
        self.slide_title(slide, spec.get("title", "双栏内容"), spec.get("kicker", ""))
        left_x, right_x, col_w = MARGIN, 17.34, 15.23
        top, height = 4.1, 12.8
        left = spec.get("left", {})
        right = spec.get("right", {})
        for side, x, item in (("left", left_x, left), ("right", right_x, right)):
            source = item.get("video") or item.get("image")
            if source:
                self.rect(slide, x, top, col_w, height, self.theme["surface"], f"{self.theme['border']}:0.8", True)
                self.media(slide, source, x + 0.35, top + 0.35, col_w - 0.7, 7.1, item.get("poster"))
                self.text(slide, item.get("title", ""), x + 0.55, 12.0, col_w - 1.1, 1.3, 24,
                          self.theme["ink"], True, self.theme["heading_font"])
                self.text(slide, item.get("body", ""), x + 0.55, 13.5, col_w - 1.1, 2.7, 18, self.theme["muted"])
            else:
                self.rect(slide, x, top, col_w, height, self.theme["surface"], f"{self.theme['border']}:0.8", True)
                self.text(slide, item.get("tag", side.upper()), x + 0.65, top + 0.7, col_w - 1.3, 0.5, 9,
                          self.theme["primary"], True, self.theme["mono_font"])
                self.text(slide, item.get("title", ""), x + 0.65, top + 1.65, col_w - 1.3, 1.8, 26,
                          self.theme["ink"], True, self.theme["heading_font"])
                self.text(slide, item.get("body", ""), x + 0.65, top + 4.0, col_w - 1.3, 7.2, 18,
                          self.theme["muted"], line_spacing="1.38x")
        self.note(slide, spec.get("notes", "按左右顺序比较，不逐字朗读卡片。"))

    def full_bleed(self, spec):
        slide = self.new_slide(background="image:" + spec["image"], chrome=False)
        self.rect(slide, 0, 0, 16.5, SLIDE_H, "000000", "none")
        self.commands[-1]["props"]["opacity"] = "0.64"
        self.text(slide, spec.get("kicker", "CASE STUDY"), MARGIN, 2.2, 12, 0.5, 10,
                  "FFFFFF", True, self.theme["mono_font"])
        self.text(slide, spec.get("title", "全屏案例"), MARGIN, 3.4, 13.8, 4.0, 38,
                  "FFFFFF", True, self.theme["heading_font"])
        self.text(slide, spec.get("body", ""), MARGIN, 8.3, 12.7, 4.4, 20, "E5E7EB")
        self.note(slide, spec.get("notes", "用画面建立场景，再落回到业务结论。"))

    def cards(self, spec, columns=3):
        slide = self.new_slide(section=spec.get("section", "FRAMEWORK"))
        self.slide_title(slide, spec.get("title", "结构矩阵"), spec.get("kicker", ""))
        items = spec.get("items", [])
        rows = max(1, (len(items) + columns - 1) // columns)
        usable_w = SLIDE_W - 2 * MARGIN - (columns - 1) * GAP
        card_w = usable_w / columns
        usable_h = 12.65
        card_h = (usable_h - (rows - 1) * GAP) / rows
        for i, item in enumerate(items):
            row, col = divmod(i, columns)
            x = MARGIN + col * (card_w + GAP)
            y = 4.05 + row * (card_h + GAP)
            self.rect(slide, x, y, card_w, card_h, self.theme["surface"], f"{self.theme['border']}:0.8", True)
            self.text(slide, item.get("tag", f"{i+1:02d}"), x + 0.55, y + 0.45, card_w - 1.1, 0.45, 9,
                      self.theme["primary"], True, self.theme["mono_font"])
            self.text(slide, item.get("title", ""), x + 0.55, y + 1.2, card_w - 1.1, 1.2, 22,
                      self.theme["ink"], True, self.theme["heading_font"])
            self.text(slide, item.get("body", item.get("desc", "")), x + 0.55, y + 2.75,
                      card_w - 1.1, max(1.2, card_h - 3.2), 18, self.theme["muted"], line_spacing="1.34x")
        self.note(slide, spec.get("notes", "先讲整体框架，再点出最重要的一项。"))

    def timeline(self, spec):
        slide = self.new_slide(section=spec.get("section", "ROADMAP"))
        self.slide_title(slide, spec.get("title", "阶段路径"), spec.get("kicker", ""))
        items = spec.get("items", [])[:5]
        count = max(1, len(items))
        x0, x1, y_line = 2.0, 31.8, 8.2
        self.rect(slide, x0, y_line, x1 - x0, 0.06, self.theme["border"])
        for i, item in enumerate(items):
            x = x0 + i * (x1 - x0) / max(1, count - 1)
            self.add(f"/slide[{slide}]", "shape", geometry="ellipse", x=self.cm(x - 0.28), y=self.cm(y_line - 0.25),
                     width="0.56cm", height="0.56cm", fill=self.theme["primary"], line="none")
            self.text(slide, item.get("phase", f"STEP {i+1}"), max(MARGIN, x - 1.2), 5.2, 3.2, 0.5, 9,
                      self.theme["primary"], True, self.theme["mono_font"], "center")
            self.text(slide, item.get("title", ""), max(MARGIN, x - 2.1), 9.2, 4.3, 1.2, 20,
                      self.theme["ink"], True, self.theme["heading_font"], "center")
            self.text(slide, item.get("body", item.get("desc", "")), max(MARGIN, x - 2.1), 10.8, 4.3, 3.5, 18,
                      self.theme["muted"], align="center")
        self.note(slide, spec.get("notes", "说明当前位于哪一阶段，以及下一节点的完成标准。"))

    def process(self, spec):
        slide = self.new_slide(section=spec.get("section", "PROCESS"))
        self.slide_title(slide, spec.get("title", "流程闭环"), spec.get("kicker", ""))
        items = spec.get("items", [])[:6]
        count = max(1, len(items))
        usable = SLIDE_W - 2 * MARGIN - (count - 1) * 0.55
        w = usable / count
        for i, item in enumerate(items):
            x = MARGIN + i * (w + 0.55)
            self.rect(slide, x, 5.6, w, 7.5, self.theme["surface"], f"{self.theme['border']}:0.8", True)
            self.text(slide, f"{i+1:02d}", x + 0.35, 6.1, w - 0.7, 1.0, 28,
                      self.theme["primary"], True, self.theme["mono_font"])
            self.text(slide, item.get("title", ""), x + 0.35, 7.7, w - 0.7, 1.4, 19,
                      self.theme["ink"], True, self.theme["heading_font"])
            self.text(slide, item.get("body", item.get("desc", "")), x + 0.35, 9.6, w - 0.7, 2.7, 18, self.theme["muted"])
            if i < count - 1:
                self.add(f"/slide[{slide}]", "connector", x=self.cm(x + w), y="9.20cm",
                         width="0.55cm", height="0cm", color=self.theme["primary"],
                         lineWidth="1.5pt", tailEnd="arrow")
        self.note(slide, spec.get("notes", "沿流程说明输入、动作与输出，重点指出断点。"))

    def kpis(self, spec):
        slide = self.new_slide(section=spec.get("section", "METRICS"))
        self.slide_title(slide, spec.get("title", "核心指标"), spec.get("kicker", ""))
        items = spec.get("items", [])[:4]
        for i, item in enumerate(items):
            row, col = divmod(i, 2)
            x, y = MARGIN + col * 16.13, 4.1 + row * 6.45
            self.rect(slide, x, y, 15.33, 5.65, self.theme["surface"], f"{self.theme['border']}:0.8", True)
            self.text(slide, item.get("value", item.get("num", "0")), x + 0.65, y + 0.55, 7.0, 1.8, 44,
                      self.theme["primary"], True, self.theme["heading_font"])
            self.text(slide, item.get("label", ""), x + 0.65, y + 2.55, 13.8, 0.9, 20,
                      self.theme["ink"], True, self.theme["heading_font"])
            self.text(slide, item.get("body", item.get("desc", "")), x + 0.65, y + 3.65, 13.8, 1.4, 18, self.theme["muted"])
        self.note(slide, spec.get("notes", "不要重复数字，解释指标变化意味着什么。"))

    def table(self, spec):
        slide = self.new_slide(section=spec.get("section", "TABLE"))
        self.slide_title(slide, spec.get("title", "对比表"), spec.get("kicker", ""))
        rows = spec.get("rows", [])
        headers = spec.get("headers", [])
        data = encode_table_data(headers, rows)
        self.add(f"/slide[{slide}]", "table", rows=str(len(rows) + 1), cols=str(len(headers)),
                 data=data, x=self.cm(MARGIN), y="4.15cm", width=self.cm(SLIDE_W - 2 * MARGIN),
                 height="11.80cm", style="Medium2", font=self.theme["body_font"], size="18pt")
        self.note(slide, spec.get("notes", "先说表格结论，再解释两处关键差异。"))

    def chart(self, spec):
        slide = self.new_slide(section=spec.get("section", "DATA"))
        self.slide_title(slide, spec.get("title", "数据图表"), spec.get("kicker", ""))
        recipe = dict(CHART_RECIPES.get(spec.get("chart_style", "column_compare"), CHART_RECIPES["column_compare"]))
        categories = spec.get("categories", [])
        series = spec.get("series", [])
        data = ";".join(f"{s.get('name', f'系列{i+1}')}:{','.join(map(str, s.get('values', [])))}" for i, s in enumerate(series))
        props = {
            **recipe,
            "categories": ",".join(map(str, categories)),
            "data": data,
            "colors": ",".join(self.theme["series"][:max(1, len(series))]),
            "x": self.cm(MARGIN), "y": "4.05cm", "width": "22.70cm", "height": "12.40cm",
            "chartFill": "none", "plotFill": "none", "plotborder": "none",
            "axisfont": f"11:{self.theme['muted']}:{self.theme['body_font']}",
            "legendFont": f"11:{self.theme['muted']}:{self.theme['body_font']}",
            "labelfont": f"11:{self.theme['ink']}:{self.theme['body_font']}",
        }
        if recipe.get("chartType") == "waterfall":
            props.update(increaseColor=self.theme["primary"], decreaseColor="D64545", totalColor=self.theme["accent"])
        self.add(f"/slide[{slide}]", "chart", **props)
        self.rect(slide, 25.0, 4.05, 7.55, 12.4, self.theme["surface"], f"{self.theme['border']}:0.8", True)
        self.text(slide, spec.get("insight_tag", "CHART INSIGHT"), 25.55, 4.7, 6.4, 0.45, 9,
                  self.theme["primary"], True, self.theme["mono_font"])
        self.text(slide, spec.get("insight", "请补充这张图最重要的业务判断。"), 25.55, 5.7, 6.4, 5.1, 22,
                  self.theme["ink"], True, self.theme["heading_font"])
        self.text(slide, spec.get("source", ""), 25.55, 14.4, 6.4, 1.0, 10, self.theme["muted"])
        self.note(slide, spec.get("notes", "先讲趋势或差异，再点出对业务决策的影响。"))

    def dashboard(self, spec):
        slide = self.new_slide(section=spec.get("section", "DASHBOARD"))
        self.slide_title(slide, spec.get("title", "经营仪表盘"), spec.get("kicker", ""))
        kpis = spec.get("kpis", [])[:3]
        for i, item in enumerate(kpis):
            x = MARGIN + i * 10.75
            self.rect(slide, x, 4.0, 9.95, 3.15, self.theme["surface"], f"{self.theme['border']}:0.8", True)
            self.text(slide, item.get("value", "0"), x + 0.5, 4.45, 4.8, 1.2, 32,
                      self.theme["primary"], True, self.theme["heading_font"])
            self.text(slide, item.get("label", ""), x + 0.5, 5.85, 8.9, 0.5, 13, self.theme["muted"])
        chart_spec = dict(spec.get("chart", {}))
        recipe = dict(CHART_RECIPES.get(chart_spec.get("chart_style", "line_trend"), CHART_RECIPES["line_trend"]))
        series = chart_spec.get("series", [])
        data = ";".join(f"{s.get('name', f'系列{i+1}')}:{','.join(map(str, s.get('values', [])))}" for i, s in enumerate(series))
        self.add(
            f"/slide[{slide}]", "chart", **recipe,
            categories=",".join(map(str, chart_spec.get("categories", []))), data=data,
            colors=",".join(self.theme["series"][:max(1, len(series))]), x=self.cm(MARGIN), y="7.85cm",
            width="21.40cm", height="8.65cm", chartFill="none", plotFill="none", plotborder="none",
            axisfont=f"10:{self.theme['muted']}:{self.theme['body_font']}",
        )
        self.rect(slide, 23.55, 7.85, 9.02, 8.65, self.theme["surface"], f"{self.theme['border']}:0.8", True)
        self.text(slide, spec.get("insight", "关键经营判断"), 24.1, 8.5, 7.9, 3.0, 22,
                  self.theme["ink"], True, self.theme["heading_font"])
        self.text(slide, spec.get("action", "下一步行动"), 24.1, 12.2, 7.9, 2.8, 18, self.theme["muted"])
        self.note(slide, spec.get("notes", "按指标、趋势、行动的顺序讲解。"))

    def build(self):
        target = Path(self.output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.stem}-", suffix=".pptx", dir=target.parent)
        os.close(fd)
        os.unlink(temporary_name)
        temporary = Path(temporary_name)
        try:
            subprocess.run(["officecli", "create", str(temporary)], check=True)
            self.cover()
            routes = {
                "section_header": self.section,
                "statement": self.statement,
                "quote": self.quote,
                "content": self.content,
                "two_column": self.two_column,
                "image_left": self.two_column,
                "image_right": self.two_column,
                "comparison": self.two_column,
                "full_bleed": self.full_bleed,
                "media_gallery": self.media_gallery,
                "cards_2": lambda s: self.cards(s, 2),
                "cards_3": lambda s: self.cards(s, 3),
                "grid_4": lambda s: self.cards(s, 2),
                "grid_6": lambda s: self.cards(s, 3),
                "timeline": self.timeline,
                "process": self.process,
                "kpi_grid": self.kpis,
                "table": self.table,
                "chart_focus": self.chart,
                "dashboard": self.dashboard,
            }
            for spec in self.cfg.get("slides", []):
                routes.get(spec.get("type", "statement"), self.statement)(spec)
            proc = subprocess.run(
                ["officecli", "batch", str(temporary), "--json"],
                input=json.dumps(self.commands, ensure_ascii=False), text=True, capture_output=True,
            )
            if proc.returncode:
                raise RuntimeError(proc.stderr or proc.stdout)
            subprocess.run(["officecli", "save", str(temporary)], check=True)
            if target.exists():
                shutil.copy2(target, str(target) + ".bak")
            os.replace(temporary, target)
            return {"slides": self.slide_count, "commands": len(self.commands)}
        finally:
            if temporary.exists():
                temporary.unlink()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: pro_ppt_engine.py <config.json> <output.pptx>")
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        config = json.load(handle)
    result = DeckBuilder(config, sys.argv[2]).build()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
