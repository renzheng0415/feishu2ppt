#!/usr/bin/env python3
"""Validate a feishu2ppt deck plan before any PPTX is rendered."""

import argparse
import json
import math
from pathlib import Path
import re

from themes import THEMES


VALID_LAYOUTS = {
    "section_header", "statement", "quote", "content", "two_column", "image_left",
    "image_right", "comparison", "full_bleed", "media_gallery", "cards_2", "cards_3",
    "grid_4", "grid_6", "timeline", "process", "kpi_grid", "table", "chart_focus", "dashboard",
}
ITEM_LAYOUT_LIMITS = {
    "cards_2": 2, "cards_3": 3, "grid_4": 4, "grid_6": 6,
    "timeline": 5, "process": 6, "kpi_grid": 4,
}
PLACEHOLDER_LINE = re.compile(
    r"^(?:请补充(?:内容|此处|本页)?|TODO(?:\s*[：:].*)?|TBD|lorem(?: ipsum)?|x{3,}|待补充(?:\s*[：:].*)?)$",
    re.I,
)
GENERATED_PLACEHOLDERS = {"请根据图表补充这一页最重要的业务判断。"}
CHART_DELIMITERS = re.compile(r"[,;:]")
VALID_CHART_STYLES = {
    "column_compare", "bar_rank", "line_trend", "area_growth", "doughnut_share",
    "waterfall_bridge", "funnel_pipeline", "scatter_relation", "histogram_distribution",
    "treemap_structure", "radar_profile", "combo_target",
}


def all_text(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from all_text(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_text(item)
    elif isinstance(value, str):
        yield value


def has_placeholder(text):
    normalized = text.strip()
    if any(value in normalized for value in GENERATED_PLACEHOLDERS):
        return True
    return any(PLACEHOLDER_LINE.fullmatch(line.strip()) for line in normalized.splitlines() if line.strip())


def is_finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def is_existing_path(value):
    return isinstance(value, str) and bool(value.strip()) and Path(value).is_file()


def validate(plan):
    if not isinstance(plan, dict):
        return {"ok": False, "errors": ["页面计划必须是对象。"], "warnings": [],
                "slides": 0, "theme": None}
    errors = list(plan.get("_errors", []))
    warnings = list(plan.get("_warnings", []))
    if not str(plan.get("title") or "").strip():
        errors.append("封面标题为空。")
    if not isinstance(plan.get("theme"), str) or plan.get("theme") not in THEMES:
        errors.append(f"无效主题：{plan.get('theme')}")
    slides = plan.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append("没有可渲染页面。")
        slides = []
    content_slides = [s for s in slides if isinstance(s, dict) and s.get("type") != "section_header"]
    if slides and not content_slides:
        errors.append("只有章节页，没有内容页。")

    def validate_series(prefix, categories, series, label):
        if not isinstance(categories, list) or not isinstance(series, list) or not categories or not series:
            errors.append(f"{prefix}{label}缺少分类或数据系列。")
            return
        unsafe_labels = [str(value) for value in categories if CHART_DELIMITERS.search(str(value))]
        for item_index, item in enumerate(series, 1):
            if not isinstance(item, dict):
                errors.append(f"{prefix}第 {item_index} 个{label}系列必须是对象。")
                continue
            name = str(item.get("name") or "")
            values = item.get("values", [])
            if not isinstance(values, list):
                errors.append(f"{prefix}{label}系列“{name}”的 values 必须是数组。")
                continue
            if len(values) != len(categories):
                errors.append(f"{prefix}{label}系列“{name}”与分类数量不一致。")
            if any(not is_finite_number(value) for value in values):
                errors.append(f"{prefix}{label}系列“{name}”包含非有限数字。")
            if CHART_DELIMITERS.search(name):
                unsafe_labels.append(name)
        if unsafe_labels:
            errors.append(
                f"{prefix}{label}标签含 OfficeCLI 数据分隔符（逗号、分号或冒号）："
                + "、".join(unsafe_labels[:3])
            )

    for index, slide in enumerate(slides, 1):
        prefix = f"第 {index} 个页面计划"
        if not isinstance(slide, dict):
            errors.append(f"{prefix}必须是对象。")
            continue
        kind = slide.get("type")
        if kind not in VALID_LAYOUTS:
            errors.append(f"{prefix}使用未知版式：{kind}")
            continue
        if kind == "section_header":
            required = slide.get("title")
        elif kind == "statement":
            required = slide.get("statement") or slide.get("title")
        elif kind == "quote":
            required = slide.get("quote")
        else:
            required = slide.get("title")
        if not str(required or "").strip():
            errors.append(f"{prefix}缺少标题或核心内容。")

        for text in all_text(slide):
            if has_placeholder(text):
                errors.append(f"{prefix}仍含占位文案：{text[:50]}")
                break

        if kind == "content":
            items = slide.get("items", [])
            if not isinstance(items, list) or not items:
                errors.append(f"{prefix}正文内容为空。")
                items = []
            elif len(items) > 6:
                errors.append(f"{prefix}正文超过 6 个内容块。")
            for item_index, item in enumerate(items, 1):
                valid = ((isinstance(item, str) and item.strip()) or
                         (isinstance(item, dict) and
                          str(item.get("body") or item.get("text") or "").strip()))
                if not valid:
                    errors.append(f"{prefix}第 {item_index} 个正文项缺少可显示文本。")

        if kind in ITEM_LAYOUT_LIMITS:
            items = slide.get("items", [])
            if not isinstance(items, list) or not items:
                errors.append(f"{prefix}缺少版式所需的内容项。")
                items = []
            elif len(items) > ITEM_LAYOUT_LIMITS[kind]:
                errors.append(f"{prefix}内容项超过 {ITEM_LAYOUT_LIMITS[kind]} 个，渲染时会被截断。")
            for item_index, item in enumerate(items, 1):
                if not isinstance(item, dict):
                    errors.append(f"{prefix}第 {item_index} 个内容项必须是对象。")
                    continue
                if kind == "kpi_grid":
                    if item.get("value") is None and item.get("num") is None:
                        errors.append(f"{prefix}第 {item_index} 个 KPI 缺少 value 或 num。")
                    if not str(item.get("label") or "").strip():
                        errors.append(f"{prefix}第 {item_index} 个 KPI 缺少 label。")
                elif not str(item.get("title") or item.get("body") or item.get("desc") or "").strip():
                    errors.append(f"{prefix}第 {item_index} 个内容项缺少 title/body/desc。")

        if kind in {"two_column", "image_left", "image_right", "comparison"}:
            for side in ("left", "right"):
                item = slide.get(side)
                if not isinstance(item, dict):
                    errors.append(f"{prefix}{side}必须是对象。")
                    continue
                path = item.get("video") or item.get("image")
                if path and not is_existing_path(path):
                    errors.append(f"{prefix}{side}媒体文件不存在：{path}")
                if not path and not str(item.get("title") or item.get("body") or "").strip():
                    errors.append(f"{prefix}{side}缺少媒体或可显示文字。")

        if kind == "media_gallery":
            media = slide.get("media", [])
            if not isinstance(media, list) or not media:
                errors.append(f"{prefix}没有媒体文件。")
                media = []
            elif len(media) > 4:
                errors.append(f"{prefix}媒体超过 4 个，渲染时会被截断。")
            for item_index, item in enumerate(media, 1):
                if not isinstance(item, dict):
                    errors.append(f"{prefix}第 {item_index} 个媒体项必须是对象。")
                    continue
                path = item.get("video") or item.get("image") or item.get("source")
                if not is_existing_path(path):
                    errors.append(f"{prefix}媒体文件不存在：{path or '<empty>'}")

        if kind == "full_bleed":
            image = slide.get("image")
            if not is_existing_path(image):
                errors.append(f"{prefix}全屏版式图片不存在：{image or '<empty>'}")

        if kind == "table":
            headers = slide.get("headers", [])
            rows = slide.get("rows", [])
            if not isinstance(headers, list) or not isinstance(rows, list) or not headers or not rows:
                errors.append(f"{prefix}表格缺少表头或数据行。")
            else:
                if any(not isinstance(row, list) for row in rows):
                    errors.append(f"{prefix}每个表格数据行必须是数组。")
                elif any(len(row) != len(headers) for row in rows):
                    errors.append(f"{prefix}表格行列数量不一致。")
                if len(rows) > 12:
                    errors.append(f"{prefix}表格超过 12 行；请拆成带重复表头的续页。")

        if kind == "chart_focus":
            style = slide.get("chart_style", "column_compare")
            if not isinstance(style, str) or style not in VALID_CHART_STYLES:
                errors.append(f"{prefix}使用未知图表样式：{slide.get('chart_style')}")
            validate_series(prefix, slide.get("categories", []), slide.get("series", []), "图表")
            if not str(slide.get("insight") or "").strip():
                errors.append(f"{prefix}图表缺少业务结论。")

        if kind == "dashboard":
            kpis = slide.get("kpis", [])
            if not isinstance(kpis, list) or not kpis:
                errors.append(f"{prefix}仪表盘缺少 KPI。")
                kpis = []
            elif len(kpis) > 3:
                errors.append(f"{prefix}仪表盘 KPI 超过 3 个，渲染时会被截断。")
            for item_index, item in enumerate(kpis, 1):
                if not isinstance(item, dict):
                    errors.append(f"{prefix}第 {item_index} 个仪表盘 KPI 必须是对象。")
                    continue
                if item.get("value") is None or not str(item.get("label") or "").strip():
                    errors.append(f"{prefix}第 {item_index} 个仪表盘 KPI 缺少 value 或 label。")
            chart = slide.get("chart", {})
            if not isinstance(chart, dict):
                errors.append(f"{prefix}仪表盘 chart 必须是对象。")
                chart = {}
            style = chart.get("chart_style", "line_trend")
            if not isinstance(style, str) or style not in VALID_CHART_STYLES:
                errors.append(f"{prefix}仪表盘使用未知图表样式：{chart.get('chart_style')}")
            validate_series(prefix, chart.get("categories", []), chart.get("series", []), "仪表盘图表")
            if not str(slide.get("insight") or "").strip() or not str(slide.get("action") or "").strip():
                errors.append(f"{prefix}仪表盘必须同时提供 insight 与 action。")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "slides": len(slides), "theme": plan.get("theme")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    result = validate(plan)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).write_text(payload, encoding="utf-8")
    print(payload)
    raise SystemExit(0 if result["ok"] else 2)


if __name__ == "__main__":
    main()
