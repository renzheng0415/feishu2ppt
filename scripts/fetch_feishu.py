#!/usr/bin/env python3
"""Fetch a Feishu document and its media into a reusable local workspace."""

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import socket
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


def run_json(args, cwd=None):
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    proc = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def tag_name(element):
    return element.tag.split("}")[-1].lower()


def media_token(element):
    """Return the media token across current and legacy Lark XML schemas."""
    token = (element.attrib.get("token") or element.attrib.get("file_token")
             or element.attrib.get("file-token") or "").strip()
    if token:
        return token
    src = element.attrib.get("src", "").strip()
    parsed = urllib.parse.urlparse(src)
    if src and not parsed.scheme and "/" not in src and "\\" not in src:
        return src
    return ""


def media_url(element):
    url = element.attrib.get("url", "").strip()
    if url:
        return url
    src = element.attrib.get("src", "").strip()
    return src if urllib.parse.urlparse(src).scheme else ""


def media_key(element):
    return media_token(element) or media_url(element)


def local_name(index, element):
    original = element.attrib.get("name", "")
    suffix = Path(original).suffix.lower()
    if not suffix:
        url = media_url(element)
        suffix = Path(url.split("?", 1)[0]).suffix.lower()
    stem = {"img": "image", "source": "media", "whiteboard": "whiteboard"}.get(tag_name(element), "asset")
    token = media_token(element)
    url_identity = media_url(element).split("?", 1)[0]
    identity = token or url_identity or original or f"{stem}-{index}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    return f"{stem}-{index:03d}-{digest}{suffix}"


def parse_xml(content):
    content = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", content)
    return ET.fromstring(f"<feishu-document>{content}</feishu-document>")


def require_public_https(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise RuntimeError(f"拒绝下载非 HTTPS 素材：{url}")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as exc:
        raise RuntimeError(f"素材域名无法解析：{parsed.hostname}") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise RuntimeError(f"拒绝访问本机、内网或保留地址：{parsed.hostname} ({ip})")
    return parsed


def download_https(url, target, max_bytes=50 * 1024 * 1024):
    require_public_https(url)
    request = urllib.request.Request(url, headers={"User-Agent": "feishu2ppt/1.0.0"})
    partial = target.with_name(target.name + ".part")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            final_url = response.geturl()
            require_public_https(final_url)
            declared = int(response.headers.get("Content-Length", "0") or 0)
            if declared > max_bytes:
                raise RuntimeError(f"素材超过 50MB 限制：{declared} bytes")
            written = 0
            with partial.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        raise RuntimeError("素材下载过程中超过 50MB 限制。")
                    handle.write(chunk)
        partial.replace(target)
    finally:
        if partial.exists():
            partial.unlink()


def detected_media_suffix(path):
    with path.open("rb") as handle:
        head = handle.read(16)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return ".webp"
    if len(head) >= 8 and head[4:8] == b"ftyp":
        return ".mp4"
    return ""


def normalize_media_extension(path):
    detected = detected_media_suffix(path)
    current = path.suffix.lower()
    equivalent = current in {".jpg", ".jpeg"} and detected == ".jpg"
    if not detected or detected == current or equivalent:
        return path
    corrected = path.with_suffix(detected)
    if corrected.exists():
        corrected = path.with_name(f"{path.stem}-normalized{detected}")
    path.replace(corrected)
    return corrected


def generate_video_poster(path):
    if path.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}:
        return ""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return ""
    poster = path.with_name(f"{path.stem}-poster.jpg")
    if poster.is_file() and poster.stat().st_size > 0:
        return str(poster.resolve())
    proc = subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", "0.5", "-i", str(path),
        "-frames:v", "1", "-q:v", "3", "-y", str(poster),
    ], text=True, capture_output=True)
    if proc.returncode or not poster.is_file() or poster.stat().st_size == 0:
        if poster.exists():
            poster.unlink()
        return ""
    return str(poster.resolve())


def download_assets(root, workdir):
    assets = workdir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    manifest = []
    elements = [e for e in root.iter() if tag_name(e) in {"img", "source", "whiteboard"}]
    for index, element in enumerate(elements, 1):
        token = media_token(element)
        url = media_url(element)
        name = local_name(index, element)
        target = assets / name
        kind = "whiteboard" if tag_name(element) == "whiteboard" else "media"
        cached = [path for path in sorted(assets.glob(target.stem + ".*"))
                  if path.is_file() and path.stat().st_size > 0]
        if token and cached:
            actual = cached[0]
        elif token:
            relative = str(Path("assets") / target.stem)
            try:
                run_json([
                    "lark-cli", "docs", "+media-download", "--as", "user", "--token", token,
                    "--type", kind, "--output", relative, "--overwrite", "--json",
                ], cwd=workdir)
            except RuntimeError:
                if kind == "whiteboard":
                    raise
                run_json([
                    "lark-cli", "docs", "+media-preview", "--as", "user", "--token", token,
                    "--output", relative, "--json",
                ], cwd=workdir)
            matches = sorted(assets.glob(target.stem + ".*"))
            actual = matches[0] if matches else target
        elif url:
            download_https(url, target)
            actual = target
        else:
            actual = target
        if not actual.exists() or actual.stat().st_size == 0:
            identifier = token or url or element.attrib.get("name", "") or f"asset-{index}"
            raise RuntimeError(f"飞书素材未生成有效本地文件：{identifier}")
        actual = normalize_media_extension(actual)
        poster = generate_video_poster(actual)
        manifest.append({
            "key": media_key(element),
            "token": token,
            "url": url,
            "tag": tag_name(element),
            "name": element.attrib.get("name", ""),
            "path": str(actual.resolve()) if actual.exists() else "",
            "poster": poster,
            "downloaded": actual.exists() and actual.stat().st_size > 0,
        })
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", required=True)
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()
    workdir = Path(args.workdir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    response = run_json([
        "lark-cli", "docs", "+fetch", "--as", "user", "--doc", args.doc,
        "--doc-format", "xml", "--detail", "full", "--scope", "full", "--json",
    ])
    if not response.get("ok"):
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    document = response["data"]["document"]
    content = document.get("content", "")
    (workdir / "source.xml").write_text(content, encoding="utf-8")
    root = parse_xml(content)
    media = download_assets(root, workdir)
    metadata = {
        "document_id": document.get("document_id"),
        "revision_id": document.get("revision_id"),
        "source": args.doc,
        "media": media,
    }
    (workdir / "fetch_manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
