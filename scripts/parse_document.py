#!/usr/bin/env python3
"""Convert Feishu DocxXML into an editable deck specification for render_ppt.py."""

import argparse
import json
import math
from pathlib import Path
import re
import urllib.parse
import xml.etree.ElementTree as ET

from themes import ALIASES, THEMES

TABLE_ROWS_PER_SLIDE = 12
CONTENT_ITEMS_PER_SLIDE = 6
CONTENT_CHARS_PER_SLIDE = 420
CONTENT_CHARS_PER_ITEM = 260
CONTENT_LINES_PER_SLIDE = 8
CONTENT_CHARS_PER_LINE = 36
SIDE_BODY_CHARS = 220
LEAD_CHARS = 44


def clean_xml(content):
    content = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", content)
    return ET.fromstring(f"<feishu-document>{content}</feishu-document>")


def tag_name(element):
    return element.tag.split("}")[-1].lower()


def text_of(element):
    return " ".join("".join(element.itertext()).split())


def media_token(element):
    token = (element.attrib.get("token") or element.attrib.get("file_token")
             or element.attrib.get("file-token") or "").strip()
    if token:
        return token
    src = element.attrib.get("src", "").strip()
    parsed = urllib.parse.urlparse(src)
    if src and not parsed.scheme and "/" not in src and "\\" not in src:
        return src
    return ""


def media_key(element):
    token = media_token(element)
    if token:
        return token
    url = element.attrib.get("url", "").strip()
    if url:
        return url
    src = element.attrib.get("src", "").strip()
    return src if urllib.parse.urlparse(src).scheme else ""


def semantic_events(root):
    events = []

    def walk(element):
        tag = tag_name(element)
        if tag == "table":
            events.append((tag, element))
            return
        if tag in {"h1", "h2", "h3", "p", "blockquote", "img", "source", "whiteboard"}:
            events.append((tag, element))
            if tag not in {"img", "source", "whiteboard"}:
                for child in element:
                    if tag_name(child) in {"img", "source", "whiteboard"}:
                        walk(child)
            return
        if tag == "li":
            if text_of(element):
                events.append(("p", element))
            return
        for child in element:
            walk(child)

    for child in root:
        walk(child)
    return events


def table_rows(table):
    rows = []
    for tr in table.iter():
        if tag_name(tr) != "tr":
            continue
        cells = [text_of(c) for c in tr if tag_name(c) in {"td", "th", "tc"}]
        if cells:
            rows.append(cells)
    return rows


def number(value):
    raw = value.replace(",", "").replace("，", "").strip()
    percent = raw.endswith("%")
    raw = raw.rstrip("%").replace("¥", "").replace("￥", "")
    try:
        parsed = float(raw)
        return parsed / 100 if percent else parsed
    except ValueError:
        return None


def chart_from_table(title, rows):
    if len(rows) < 2 or len(rows[0]) < 2:
        return None
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return None
    categories = [row[0] for row in rows[1:]]
    series = []
    for col in range(1, width):
        values = [number(row[col]) for row in rows[1:]]
        if any(value is None for value in values):
            return None
        series.append({"name": rows[0][col], "values": values})
    time_pattern = re.compile(r"(月|季|年|week|q[1-4]|20\d{2})", re.I)
    if any(time_pattern.search(value) for value in categories):
        style = "line_trend"
    elif len(series) == 1:
        style = "bar_rank"
    else:
        style = "column_compare"
    return {
        "type": "chart_focus", "title": title, "chart_style": style,
        "categories": categories, "series": series,
        "insight": "请根据图表补充这一页最重要的业务判断。",
        "source": "来源：飞书文档内嵌数据表",
    }


def media_item(element, media_by_key):
    entry = media_by_key.get(media_key(element), {})
    path = entry.get("path", "")
    if not path:
        return None
    suffix = Path(path).suffix.lower()
    if suffix in {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}:
        item = {
            "video": path,
            "title": entry.get("name") or "视频素材",
            "body": "点击视频即可播放。",
        }
        poster = entry.get("poster", "")
        if poster and Path(poster).is_file():
            item["poster"] = poster
        return item
    return {"image": path}


def split_long_text(text, limit=CONTENT_CHARS_PER_ITEM):
    text = text.strip()
    if len(text) <= limit:
        return [text] if text else []
    sentences = [part.strip() for part in re.split(r"(?<=[。！？!?；;])\s*|\n+", text) if part.strip()]
    chunks = []
    current = ""
    for sentence in sentences:
        pieces = [sentence[i:i + limit] for i in range(0, len(sentence), limit)]
        for piece in pieces:
            candidate = piece if not current else current + "\n" + piece
            if current and len(candidate) > limit:
                chunks.append(current)
                current = piece
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def visible_lead(bodies):
    if not bodies:
        return ""
    lead = " ".join(bodies[0].split())
    return lead if len(lead) <= LEAD_CHARS else lead[:LEAD_CHARS - 1].rstrip() + "…"


def estimated_lines(text):
    logical_lines = text.splitlines() or [""]
    return sum(max(1, math.ceil(len(line) / CONTENT_CHARS_PER_LINE)) for line in logical_lines)


def slide_specs(title, bodies, media, tables, section, warnings):
    directives = {}
    visible_bodies = []
    for body in bodies:
        match = re.match(r"^(版式|图表|结论|来源)[：:]\s*(.+)$", body)
        if match:
            directives[match.group(1)] = match.group(2).strip()
        else:
            visible_bodies.append(body)
    bodies = visible_bodies
    def content_slides(page_title, content):
        expanded = [chunk for body in content for chunk in split_long_text(body)]
        pages = []
        groups, current, chars, lines = [], [], 0, 0
        for item in expanded:
            item_lines = estimated_lines(item)
            if current and (len(current) >= CONTENT_ITEMS_PER_SLIDE
                            or chars + len(item) > CONTENT_CHARS_PER_SLIDE
                            or lines + item_lines > CONTENT_LINES_PER_SLIDE):
                groups.append(current)
                current, chars, lines = [], 0, 0
            current.append(item)
            chars += len(item)
            lines += item_lines
        if current:
            groups.append(current)
        if len(groups) > 1:
            warnings.append(f"“{page_title}”正文较长，已按可读字数自动拆为 {len(groups)} 页。")
        for index, group in enumerate(groups):
            suffix = "" if index == 0 else f"（续 {index + 1}）"
            pages.append({"type": "content", "section": section, "title": page_title + suffix,
                          "items": group})
        return pages

    def media_slides(page_title, items, lead="", notes=""):
        pages = []
        for index in range(0, len(items), 4):
            suffix = "" if index == 0 else f"（续 {index // 4 + 1}）"
            pages.append({"type": "media_gallery", "section": section, "title": page_title + suffix,
                          "media": items[index:index + 4], "lead": lead, "notes": notes})
        return pages

    if tables:
        pages = []
        mixed = bool(bodies or media or len(tables) > 1)
        if bodies:
            pages.extend(content_slides(title, bodies))
        force_table = directives.get("版式") == "表格" or directives.get("图表") == "表格"
        chart_aliases = {
            "柱状图": "column_compare", "条形图": "bar_rank", "排名图": "bar_rank",
            "折线图": "line_trend", "面积图": "area_growth", "环形图": "doughnut_share",
            "瀑布图": "waterfall_bridge", "漏斗图": "funnel_pipeline", "散点图": "scatter_relation",
            "直方图": "histogram_distribution", "矩形树图": "treemap_structure",
            "雷达图": "radar_profile", "组合图": "combo_target",
        }
        for table_index, rows in enumerate(tables, 1):
            page_title = title if not mixed else f"{title}｜数据 {table_index}"
            chart = None if force_table else chart_from_table(page_title, rows)
            if chart:
                if directives.get("图表") in chart_aliases:
                    chart["chart_style"] = chart_aliases[directives["图表"]]
                if directives.get("结论"):
                    chart["insight"] = directives["结论"]
                if directives.get("来源"):
                    chart["source"] = directives["来源"]
                chart["section"] = section
                pages.append(chart)
            else:
                data_rows = rows[1:]
                if len(data_rows) > TABLE_ROWS_PER_SLIDE:
                    warnings.append(
                        f"“{page_title}”表格超过 {TABLE_ROWS_PER_SLIDE} 行，已自动拆为续页并重复表头。"
                    )
                for offset in range(0, len(data_rows), TABLE_ROWS_PER_SLIDE):
                    page_number = offset // TABLE_ROWS_PER_SLIDE + 1
                    suffix = "" if page_number == 1 else f"（续 {page_number}）"
                    pages.append({"type": "table", "section": section, "title": page_title + suffix,
                                  "headers": rows[0],
                                  "rows": data_rows[offset:offset + TABLE_ROWS_PER_SLIDE]})
        if media:
            pages.extend(media_slides(f"{title}｜素材", media))
        if mixed:
            warnings.append(f"“{title}”包含混合内容，已拆为 {len(pages)} 页并保留全部正文、表格和媒体。")
        return pages
    if len(media) == 1 and bodies and len("\n".join(bodies)) <= SIDE_BODY_CHARS:
        return [{
            "type": "image_right", "section": section, "title": title,
            "left": {"tag": "KEY POINTS", "title": "核心内容", "body": "\n".join(bodies[:6])},
            "right": {"title": "", "body": "", **media[0]},
        }]
    if len(media) == 1 and bodies:
        pages = content_slides(title, bodies)
        pages.extend(media_slides(f"{title}｜素材", media, visible_lead(bodies), "\n".join(bodies)))
        warnings.append(f"“{title}”单图页正文过长，已拆分正文与素材页以避免文字溢出。")
        return pages
    if media:
        return media_slides(title, media, visible_lead(bodies), "\n".join(bodies))
    if not bodies:
        return [{"type": "statement", "section": section, "statement": title, "support": ""}]
    return content_slides(title, bodies)


def parse(source, manifest, theme, output):
    root = clean_xml(Path(source).read_text(encoding="utf-8"))
    metadata = json.loads(Path(manifest).read_text(encoding="utf-8")) if Path(manifest).exists() else {"media": []}
    media_by_key = {
        item.get("key") or item.get("token") or item.get("url"): item
        for item in metadata.get("media", [])
        if item.get("key") or item.get("token") or item.get("url")
    }
    title = "飞书文档提报"
    subtitle = ""
    company = ""
    author = ""
    current_section = ""
    current_title = None
    bodies, media, tables = [], [], []
    slides, warnings, errors = [], [], []
    seen_structure = False
    requested_theme = theme
    document_theme = None

    def flush():
        nonlocal current_title, bodies, media, tables
        if current_title:
            slides.extend(slide_specs(current_title, bodies, media, tables, current_section, warnings))
        current_title, bodies, media, tables = None, [], [], []

    for tag, element in semantic_events(root):
        text = text_of(element)
        if tag == "h1":
            flush()
            seen_structure = True
            current_section = text
            slides.append({"type": "section_header", "title": text, "subtitle": "", "number": f"{len([s for s in slides if s['type']=='section_header']) + 1:02d}"})
        elif tag == "h2":
            flush()
            seen_structure = True
            current_title = text
        elif tag == "h3" and current_title:
            bodies.append(text)
        elif tag in {"p", "blockquote"} and text:
            if not seen_structure and current_title is None:
                match = re.match(r"^(主题|风格|副标题|公司|作者)[：:]\s*(.+)$", text)
                if match:
                    key, value = match.groups()
                    if key in {"主题", "风格"}:
                        document_theme = value
                    elif key == "副标题":
                        subtitle = value
                    elif key == "公司":
                        company = value
                    elif key == "作者":
                        author = value
                    continue
            if current_title:
                bodies.append(text)
            elif title == "飞书文档提报":
                title = text
        elif tag in {"img", "source", "whiteboard"}:
            item = media_item(element, media_by_key)
            if item:
                media.append(item)
            else:
                identifier = (media_token(element) or element.attrib.get("name")
                              or element.attrib.get("url") or element.attrib.get("src") or tag)
                errors.append(f"素材未成功下载或本地文件不存在：{identifier}")
        elif tag == "table":
            rows = table_rows(element)
            if rows:
                tables.append(rows)
    flush()
    title_node = next((text_of(e) for e in root if tag_name(e) == "title" and text_of(e)), "")
    if title_node:
        title = title_node
    theme = requested_theme or document_theme or "vercel_minimal"
    normalized_theme = ALIASES.get(theme, theme)
    if normalized_theme not in THEMES:
        errors.append(f"未知主题：{theme}。请从 style-catalog.md 中选择有效主题。")
    else:
        theme = normalized_theme
    if not any(slide.get("type") != "section_header" for slide in slides):
        errors.append("未找到可生成内容页的二级标题；请用二级标题定义每一页。")
    deck = {
        "theme": theme,
        "title": title,
        "subtitle": subtitle,
        "company": company or "",
        "author": author or "",
        "date": "",
        "slides": slides,
        "_warnings": warnings,
        "_errors": errors,
    }
    Path(output).write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    return deck


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--theme")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    deck = parse(args.source, args.manifest, args.theme, args.output)
    print(json.dumps({"slides": len(deck["slides"]), "warnings": deck["_warnings"],
                      "errors": deck["_errors"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
