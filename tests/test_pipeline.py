#!/usr/bin/env python3

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from parse_document import CONTENT_LINES_PER_SLIDE, estimated_lines, parse
from fetch_feishu import download_assets, local_name, parse_xml as parse_fetch_xml, require_public_https
from render_ppt import DeckBuilder, encode_table_data
from run import render_plan
from validate_plan import validate


class PipelineTests(unittest.TestCase):
    def parse_xml(self, xml, theme="vercel_minimal", media=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.xml"
            manifest = root / "manifest.json"
            output = root / "deck.json"
            source.write_text(xml, encoding="utf-8")
            manifest.write_text(json.dumps({"media": media or []}), encoding="utf-8")
            return parse(source, manifest, theme, output)

    def test_missing_h2_is_rejected(self):
        plan = self.parse_xml("<title>测试</title><h1>章节</h1><p>正文</p>")
        result = validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("二级标题" in error for error in result["errors"]))

    def test_unknown_theme_is_rejected(self):
        plan = self.parse_xml("<title>测试</title><h2>页面</h2><p>正文</p>", theme="not-a-theme")
        self.assertFalse(validate(plan)["ok"])

    def test_placeholder_chart_insight_is_rejected(self):
        xml = """<title>测试</title><h2>趋势</h2><table>
        <tr><th>月份</th><th>成交</th></tr><tr><td>1月</td><td>10</td></tr></table>"""
        plan = self.parse_xml(xml)
        self.assertFalse(validate(plan)["ok"])
        self.assertTrue(any("占位文案" in error for error in validate(plan)["errors"]))

    def test_prompt_examples_are_not_misclassified_as_unfinished_placeholders(self):
        xml = ("<title>测试</title><h2>提示词示例</h2>"
               "<p>请输入【XX 产品】，请根据客户需求生成 3 个方案，格式为 1.XXX 2.XXX。</p>")
        self.assertTrue(validate(self.parse_xml(xml))["ok"])

    def test_standalone_todo_is_rejected(self):
        plan = self.parse_xml("<title>测试</title><h2>页面</h2><p>TODO: 补写结论</p>")
        self.assertFalse(validate(plan)["ok"])

    def test_table_delimiters_are_quoted(self):
        encoded = encode_table_data(["项目", "结论"], [["深圳,南山", '甲;乙"丙']])
        self.assertEqual(encoded, '"项目","结论";"深圳,南山","甲;乙""丙"')

    def test_multi_media_keeps_visible_lead(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_a = Path(tmp) / "a.png"
            image_b = Path(tmp) / "b.png"
            image_a.write_bytes(b"x")
            image_b.write_bytes(b"x")
            xml = """<title>测试</title><h2>图文</h2><p>核心结论必须可见。</p>
            <img token="a"/><img token="b"/>"""
            media = [{"token": "a", "path": str(image_a)}, {"token": "b", "path": str(image_b)}]
            plan = self.parse_xml(xml, media=media)
            self.assertEqual(plan["slides"][0]["lead"], "核心结论必须可见。")
            self.assertTrue(validate(plan)["ok"])

    def test_multi_media_lead_is_bounded_to_one_safe_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            images = []
            media = []
            for index in range(2):
                image = root / f"{index}.png"
                image.write_bytes(b"x")
                images.append(image)
                media.append({"token": str(index), "path": str(image)})
            xml = ("<title>测试</title><h2>图文</h2><p>" + "很长的导语" * 20 + "</p>"
                   '<img token="0"/><img token="1"/>')
            plan = self.parse_xml(xml, media=media)
            self.assertLessEqual(len(plan["slides"][0]["lead"]), 44)

    def test_single_media_long_text_splits_into_readable_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "x.png"
            image.write_bytes(b"x")
            bodies = ["正文段落" + str(index) + "。" + "内容" * 70 for index in range(4)]
            xml = "<title>测试</title><h2>长文图文</h2>" + "".join(f"<p>{body}</p>" for body in bodies) + '<img token="x"/>'
            plan = self.parse_xml(xml, media=[{"token": "x", "path": str(image)}])
            self.assertNotIn("image_right", [slide["type"] for slide in plan["slides"]])
            self.assertEqual(plan["slides"][-1]["type"], "media_gallery")
            rendered_text = "\n".join(
                item for slide in plan["slides"] if slide["type"] == "content" for item in slide["items"]
            )
            self.assertTrue(all(body in rendered_text for body in bodies))
            for slide in plan["slides"]:
                if slide["type"] == "content":
                    self.assertLessEqual(sum(estimated_lines(item) for item in slide["items"]),
                                         CONTENT_LINES_PER_SLIDE)

    def test_video_poster_and_label_are_preserved_in_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "demo.mp4"
            poster = Path(tmp) / "poster.jpg"
            video.write_bytes(b"video")
            poster.write_bytes(b"poster")
            xml = '<title>测试</title><h2>视频</h2><p>短说明</p><source token="v"/>'
            plan = self.parse_xml(xml, media=[{
                "token": "v", "path": str(video), "poster": str(poster), "name": "演示视频.mp4",
            }])
            right = plan["slides"][0]["right"]
            self.assertEqual(right["poster"], str(poster))
            self.assertEqual(right["title"], "演示视频.mp4")

    def test_chart_series_length_must_match(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "chart_focus", "title": "图表", "categories": ["A", "B"],
            "series": [{"name": "值", "values": [1]}], "insight": "明确结论",
        }]}
        self.assertFalse(validate(plan)["ok"])

    def test_chart_delimiters_are_rejected_instead_of_corrupted(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "chart_focus", "title": "图表", "categories": ["深圳,南山", "福田"],
            "series": [{"name": "成交量", "values": [10, 20]}], "insight": "南山更高",
        }]}
        result = validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("数据分隔符" in error for error in result["errors"]))

    def test_empty_content_layout_is_rejected(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "content", "title": "空页面", "items": [],
        }]}
        self.assertFalse(validate(plan)["ok"])

    def test_incomplete_dashboard_is_rejected(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "dashboard", "title": "经营情况", "kpis": [], "chart": {},
            "insight": "", "action": "",
        }]}
        result = validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("仪表盘" in error for error in result["errors"]))

    def test_mixed_page_preserves_all_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "x.png"
            image.write_bytes(b"x")
            xml = """<title>测试</title><h2>混合页面</h2><p>正文结论</p>
            <table><tr><th>项目</th><th>值</th></tr><tr><td>A</td><td>10</td></tr></table>
            <table><tr><th>项目</th><th>说明</th></tr><tr><td>B</td><td>文字</td></tr></table>
            <img token="x"/>"""
            plan = self.parse_xml(xml, media=[{"token": "x", "path": str(image)}])
            self.assertEqual([slide["type"] for slide in plan["slides"]],
                             ["content", "chart_focus", "table", "media_gallery"])
            self.assertEqual(plan["slides"][0]["items"], ["正文结论"])
            self.assertEqual(plan["slides"][2]["rows"], [["B", "文字"]])
            self.assertEqual(plan["slides"][3]["media"][0]["image"], str(image))

    def test_explicit_theme_wins_over_document_theme(self):
        xml = """<title>测试</title><p>主题：data_journalism</p><h2>页面</h2><p>正文</p>"""
        plan = self.parse_xml(xml, theme="vercel_minimal")
        self.assertEqual(plan["theme"], "vercel_minimal")

    def test_document_theme_is_used_without_explicit_theme(self):
        xml = """<title>测试</title><p>主题：data_journalism</p><h2>页面</h2><p>正文</p>"""
        plan = self.parse_xml(xml, theme=None)
        self.assertEqual(plan["theme"], "data_journalism")

    def test_unknown_chart_style_is_rejected(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "chart_focus", "title": "图表", "chart_style": "made_up",
            "categories": ["A"], "series": [{"name": "值", "values": [1]}], "insight": "结论",
        }]}
        result = validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("未知图表样式" in error for error in result["errors"]))

    def test_render_failure_keeps_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "existing.pptx"
            output.write_bytes(b"original")

            def fake_run(args, **kwargs):
                if args[1] == "create":
                    Path(args[2]).write_bytes(b"temporary")
                    return __import__("subprocess").CompletedProcess(args, 0, "", "")
                if args[1] == "batch":
                    return __import__("subprocess").CompletedProcess(args, 1, "", "batch failed")
                return __import__("subprocess").CompletedProcess(args, 0, "", "")

            with patch("render_ppt.subprocess.run", side_effect=fake_run):
                with self.assertRaises(RuntimeError):
                    DeckBuilder({"title": "测试", "slides": []}, str(output)).build()
            self.assertEqual(output.read_bytes(), b"original")
            self.assertFalse(Path(str(output) + ".bak").exists())

    def test_missing_media_is_rejected(self):
        xml = """<title>测试</title><h2>项目实景</h2><p>必须保留图片。</p><img token="missing"/>"""
        plan = self.parse_xml(xml)
        result = validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("素材未成功下载" in error for error in result["errors"]))

    def test_non_finite_chart_values_are_rejected(self):
        for invalid in ("abc", True, float("nan"), float("inf")):
            plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
                "type": "chart_focus", "title": "图表", "chart_style": "line_trend",
                "categories": ["A"], "series": [{"name": "值", "values": [invalid]}],
                "insight": "结论",
            }]}
            with self.subTest(invalid=invalid):
                self.assertFalse(validate(plan)["ok"])

    def test_post_render_validation_failure_keeps_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "deck.json"
            output = root / "existing.pptx"
            plan.write_text(json.dumps({"title": "测试", "theme": "vercel_minimal", "slides": []}),
                            encoding="utf-8")
            output.write_bytes(b"original")

            def fake_execute(args, allow_failure=False):
                if "validate_plan.py" in str(args[1]):
                    return __import__("subprocess").CompletedProcess(args, 0, '{"ok": true}', "")
                if "render_ppt.py" in str(args[1]):
                    Path(args[-1]).write_bytes(b"candidate")
                    return __import__("subprocess").CompletedProcess(args, 0, "", "")
                if args[:2] == ["officecli", "validate"]:
                    raise RuntimeError("validation failed")
                return __import__("subprocess").CompletedProcess(args, 0, "", "")

            with patch("run.execute", side_effect=fake_execute):
                with self.assertRaises(RuntimeError):
                    render_plan(plan, output, root, True)
            self.assertEqual(output.read_bytes(), b"original")
            self.assertFalse(Path(str(output) + ".bak").exists())
            self.assertEqual(list(root.glob(".*-candidate-*.pptx")), [])

    def test_changed_media_token_never_reuses_old_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir()
            old_element = next(iter(parse_fetch_xml('<img token="old-token" name="photo.png"/>')))
            new_element = next(iter(parse_fetch_xml('<img token="new-token" name="photo.png"/>')))
            old_path = assets / local_name(1, old_element)
            old_path.write_bytes(b"old")

            def fake_run_json(args, cwd=None):
                relative = Path(args[args.index("--output") + 1])
                (Path(cwd) / relative).with_suffix(".png").write_bytes(b"new")
                return {"ok": True}

            with patch("fetch_feishu.run_json", side_effect=fake_run_json):
                manifest = download_assets(parse_fetch_xml(
                    '<img token="new-token" name="photo.png"/>'
                ), root)
            new_path = Path(manifest[0]["path"])
            self.assertNotEqual(new_path, old_path)
            self.assertEqual(new_path.read_bytes(), b"new")
            self.assertEqual(old_path.read_bytes(), b"old")

    def test_current_lark_src_media_token_is_downloaded_and_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xml = '<title>测试</title><h2>实景</h2><img src="current-file-token" name="photo.jpeg"/>'

            def fake_run_json(args, cwd=None):
                relative = Path(args[args.index("--output") + 1])
                (Path(cwd) / relative).with_suffix(".jpeg").write_bytes(b"image")
                return {"ok": True}

            with patch("fetch_feishu.run_json", side_effect=fake_run_json):
                manifest = download_assets(parse_fetch_xml(xml), root)
            self.assertEqual(manifest[0]["token"], "current-file-token")
            self.assertTrue(Path(manifest[0]["path"]).is_file())
            plan = self.parse_xml(xml, media=manifest)
            self.assertEqual(plan["slides"][0]["type"], "media_gallery")
            self.assertEqual(plan["slides"][0]["media"][0]["image"], manifest[0]["path"])

    def test_mislabeled_download_is_renamed_from_magic_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def fake_run_json(args, cwd=None):
                relative = Path(args[args.index("--output") + 1])
                (Path(cwd) / relative).with_suffix(".jpg").write_bytes(
                    b"\x89PNG\r\n\x1a\n" + b"payload"
                )
                return {"ok": True}

            with patch("fetch_feishu.run_json", side_effect=fake_run_json):
                manifest = download_assets(parse_fetch_xml(
                    '<img src="mislabeled-token" name="photo.jpeg"/>'
                ), root)
            path = Path(manifest[0]["path"])
            self.assertEqual(path.suffix, ".png")
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))

    def test_url_media_is_refreshed_even_when_cache_path_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir()
            element = next(iter(parse_fetch_xml(
                '<img url="https://example.com/project.png" name="project.png"/>'
            )))
            cached = assets / local_name(1, element)
            cached.write_bytes(b"old")

            def fake_download(url, target, max_bytes=50 * 1024 * 1024):
                target.write_bytes(b"new")

            with patch("fetch_feishu.download_https", side_effect=fake_download):
                manifest = download_assets(parse_fetch_xml(
                    '<img url="https://example.com/project.png" name="project.png"/>'
                ), root)
            self.assertEqual(Path(manifest[0]["path"]).read_bytes(), b"new")

    def test_multiple_url_only_media_keep_distinct_manifest_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xml = ("<title>测试</title><h2>实景</h2>"
                   '<img src="https://example.com/a.png" name="a.png"/>'
                   '<img src="https://example.com/b.png" name="b.png"/>')

            def fake_download(url, target, max_bytes=50 * 1024 * 1024):
                target.write_bytes(url.encode("utf-8"))

            with patch("fetch_feishu.download_https", side_effect=fake_download):
                manifest = download_assets(parse_fetch_xml(xml), root)
            self.assertEqual([item["key"] for item in manifest], [
                "https://example.com/a.png", "https://example.com/b.png",
            ])
            plan = self.parse_xml(xml, media=manifest)
            paths = [item["image"] for item in plan["slides"][0]["media"]]
            self.assertEqual(len(set(paths)), 2)

    def test_private_and_local_media_urls_are_rejected(self):
        for url in (
            "http://example.com/image.png",
            "https://127.0.0.1/image.png",
            "https://10.0.0.1/image.png",
            "https://169.254.169.254/latest/meta-data",
            "https://[::1]/image.png",
        ):
            with self.subTest(url=url):
                with self.assertRaises(RuntimeError):
                    require_public_https(url)

    def test_long_source_table_is_split_with_repeated_headers(self):
        rows = "".join(f"<tr><td>{i}</td><td>项目{i}</td></tr>" for i in range(1, 31))
        xml = ("<title>测试</title><h2>明细</h2><p>版式：表格</p>"
               f"<table><tr><th>序号</th><th>项目</th></tr>{rows}</table>")
        plan = self.parse_xml(xml)
        self.assertEqual(len(plan["slides"]), 3)
        self.assertEqual([len(slide["rows"]) for slide in plan["slides"]], [12, 12, 6])
        self.assertTrue(all(slide["headers"] == ["序号", "项目"] for slide in plan["slides"]))
        self.assertEqual(plan["slides"][1]["title"], "明细（续 2）")
        self.assertTrue(validate(plan)["ok"])

    def test_manual_long_table_is_rejected(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "table", "title": "长表格", "headers": ["序号", "项目"],
            "rows": [[i, f"项目{i}"] for i in range(13)],
        }]}
        result = validate(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("超过 12 行" in error for error in result["errors"]))

    def test_object_layouts_reject_string_items(self):
        for kind in ("cards_2", "cards_3", "grid_4", "grid_6", "timeline", "process", "kpi_grid"):
            plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
                "type": kind, "title": "页面", "items": ["错误结构"],
            }]}
            with self.subTest(kind=kind):
                self.assertFalse(validate(plan)["ok"])

    def test_dashboard_rejects_string_kpi_and_series(self):
        plan = {"title": "测试", "theme": "vercel_minimal", "slides": [{
            "type": "dashboard", "title": "仪表盘", "kpis": ["错误结构"],
            "chart": {"categories": ["A"], "series": ["错误结构"]},
            "insight": "结论", "action": "动作",
        }]}
        self.assertFalse(validate(plan)["ok"])

    def test_validator_reports_malformed_types_without_crashing(self):
        cases = [
            {"title": "x", "theme": {}, "slides": [{"type": "content", "title": "x", "items": ["x"]}]},
            {"title": "x", "theme": "vercel_minimal", "slides": [{
                "type": "chart_focus", "title": "x", "chart_style": {},
                "categories": ["A"], "series": [{"name": "值", "values": [1]}], "insight": "结论"}]},
            {"title": "x", "theme": "vercel_minimal", "slides": [{
                "type": "full_bleed", "title": "x", "image": {"bad": "path"}}]},
        ]
        for plan in cases:
            with self.subTest(plan=plan):
                result = validate(plan)
                self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
