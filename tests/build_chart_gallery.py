#!/usr/bin/env python3
"""Build the 12-chart live acceptance plan for the feishu2ppt release gate."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    recipes = [
        ("column_compare", "分组柱状图", ["A", "B", "C", "D"],
         [{"name": "今年", "values": [30, 48, 61, 75]}, {"name": "去年", "values": [24, 38, 52, 64]}]),
        ("bar_rank", "横向排名图", ["项目A", "项目B", "项目C", "项目D"],
         [{"name": "得分", "values": [96, 83, 68, 51]}]),
        ("line_trend", "趋势折线图", ["1月", "2月", "3月", "4月"],
         [{"name": "到访", "values": [32, 46, 41, 69]}, {"name": "成交", "values": [8, 12, 11, 20]}]),
        ("area_growth", "增长面积图", ["1月", "2月", "3月", "4月"],
         [{"name": "规模", "values": [20, 31, 45, 70]}]),
        ("doughnut_share", "结构环形图", ["渠道A", "渠道B", "渠道C", "渠道D"],
         [{"name": "占比", "values": [38, 27, 21, 14]}]),
        ("waterfall_bridge", "利润瀑布图", ["收入", "投放", "人力", "运营", "利润"],
         [{"name": "金额", "values": [120, -24, -31, -15, 50]}]),
        ("funnel_pipeline", "销售漏斗图", ["曝光", "留资", "到访", "认购"],
         [{"name": "人数", "values": [1000, 260, 95, 31]}]),
        ("scatter_relation", "关系散点图", ["1", "2", "3", "4", "5"],
         [{"name": "样本", "values": [12, 18, 17, 29, 33]}]),
        ("histogram_distribution", "价格分布直方图", ["1", "2", "3", "4", "5", "6"],
         [{"name": "样本", "values": [3, 4, 5, 5, 6, 9]}]),
        ("treemap_structure", "结构矩形树图", ["住宅", "商业", "办公", "配套"],
         [{"name": "面积", "values": [58, 18, 16, 8]}]),
        ("radar_profile", "能力雷达图", ["产品", "渠道", "内容", "转化", "服务"],
         [{"name": "方案A", "values": [82, 68, 91, 73, 86]},
          {"name": "方案B", "values": [70, 84, 72, 88, 76]}]),
        ("combo_target", "目标组合图", ["1月", "2月", "3月", "4月"],
         [{"name": "实际", "values": [72, 84, 93, 108]},
          {"name": "增长率", "values": [8, 12, 11, 16]}]),
    ]
    slides = [{
        "type": "chart_focus", "title": title, "chart_style": style,
        "categories": categories, "series": series, "insight": f"{title}活体回归通过。",
    } for style, title, categories, series in recipes]
    plan = {"title": "Feishu2PPT 图表验收", "theme": "data_journalism", "slides": slides}
    Path(args.output).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
