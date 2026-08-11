#!/usr/bin/env python3
"""Build a portable 20-layout acceptance plan for the feishu2ppt release gate."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.skill_root).resolve()
    image = str((root / "assets" / "showcase.png").resolve())
    text_left = {"tag": "A", "title": "左侧判断", "body": "用于展示双栏文字内容。"}
    text_right = {"tag": "B", "title": "右侧判断", "body": "用于展示双栏文字内容。"}
    slides = [
        {"type": "section_header", "title": "全版式回归", "subtitle": "20 种版式", "number": "01"},
        {"type": "statement", "statement": "每一种版式都必须真实渲染通过。", "support": "结构校验不能代替活体检查。"},
        {"type": "quote", "quote": "可编辑、可复用、可验证。", "source": "Feishu2PPT"},
        {"type": "content", "title": "正文列表", "items": ["第一项", "第二项", "第三项"]},
        {"type": "two_column", "title": "双栏分析", "left": text_left, "right": text_right},
        {"type": "image_left", "title": "左图右文", "left": {"image": image}, "right": text_right},
        {"type": "image_right", "title": "左文右图", "left": text_left, "right": {"image": image}},
        {"type": "comparison", "title": "方案比较", "left": text_left, "right": text_right},
        {"type": "full_bleed", "title": "全屏场景", "body": "真实图片背景与文字叠加。", "image": image},
        {"type": "media_gallery", "title": "媒体画廊", "lead": "正文与媒体同时可见。",
         "media": [{"image": image}, {"image": image}]},
        {"type": "cards_2", "title": "双卡片", "items": [
            {"title": "卡片一", "body": "说明一"}, {"title": "卡片二", "body": "说明二"}]},
        {"type": "cards_3", "title": "三卡片", "items": [
            {"title": f"卡片{i}", "body": f"说明{i}"} for i in range(1, 4)]},
        {"type": "grid_4", "title": "四宫格", "items": [
            {"title": f"能力{i}", "body": f"说明{i}"} for i in range(1, 5)]},
        {"type": "grid_6", "title": "六宫格", "items": [
            {"title": f"模块{i}", "body": f"说明{i}"} for i in range(1, 7)]},
        {"type": "timeline", "title": "时间路径", "items": [
            {"phase": f"阶段{i}", "title": f"节点{i}", "body": f"完成标准{i}"} for i in range(1, 5)]},
        {"type": "process", "title": "执行流程", "items": [
            {"title": f"步骤{i}", "body": f"动作{i}"} for i in range(1, 6)]},
        {"type": "kpi_grid", "title": "关键指标", "items": [
            {"value": f"{i * 25}%", "label": f"指标{i}", "body": f"解释{i}"} for i in range(1, 5)]},
        {"type": "table", "title": "原生表格", "headers": ["项目", "结果"],
         "rows": [[f"项目{i}", f"结果{i}"] for i in range(1, 7)]},
        {"type": "chart_focus", "title": "原生图表", "chart_style": "line_trend",
         "categories": ["1月", "2月", "3月"],
         "series": [{"name": "成交", "values": [10, 14, 21]}], "insight": "成交连续增长。"},
        {"type": "dashboard", "title": "经营仪表盘", "kpis": [
            {"value": "120", "label": "线索"}, {"value": "36", "label": "到访"},
            {"value": "8", "label": "成交"}],
         "chart": {"chart_style": "line_trend", "categories": ["1月", "2月", "3月"],
                   "series": [{"name": "到访", "values": [20, 28, 36]}]},
         "insight": "到访持续增长。", "action": "继续优化线索到访转化。"},
    ]
    plan = {"title": "Feishu2PPT 全版式验收", "theme": "vercel_minimal", "slides": slides}
    Path(args.output).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
