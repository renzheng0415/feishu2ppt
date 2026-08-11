#!/usr/bin/env python3
"""Check feishu2ppt dependencies and Lark user authorization without exposing secrets."""

import json
import os
import platform
import shutil
import subprocess


def command_version(command, args):
    path = shutil.which(command)
    if not path:
        return {"installed": False, "path": None, "version": None}
    proc = subprocess.run([path, *args], text=True, capture_output=True)
    version = (proc.stdout or proc.stderr).strip().splitlines()[0] if (proc.stdout or proc.stderr) else "unknown"
    return {"installed": proc.returncode == 0, "path": path, "version": version}


def lark_status():
    path = shutil.which("lark-cli")
    if not path:
        return {"configured": False, "authorized": False, "reason": "lark-cli_missing"}
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    proc = subprocess.run(
        [path, "auth", "status", "--json", "--verify"], text=True, capture_output=True,
        env=env,
    )
    try:
        data = json.loads(proc.stdout or proc.stderr)
    except json.JSONDecodeError:
        return {"configured": False, "authorized": False, "reason": "status_unreadable"}
    user = data.get("identities", {}).get("user", {})
    return {
        "configured": bool(data.get("appId")),
        "authorized": bool(data.get("verified") and user.get("available")),
        "identity": data.get("identity"),
        "user_status": user.get("status"),
        "token_status": user.get("tokenStatus"),
        "user_name": user.get("userName"),
    }


def report():
    lark = command_version("lark-cli", ["-v"])
    office = command_version("officecli", ["--version"])
    ffmpeg = command_version("ffmpeg", ["-version"])
    auth = lark_status()
    ready = lark["installed"] and office["installed"] and auth["configured"] and auth["authorized"]
    return {
        "ready": ready,
        "platform": platform.system(),
        "python": platform.python_version(),
        "lark_cli": lark,
        "officecli": office,
        "ffmpeg_optional": ffmpeg,
        "lark_auth": auth,
    }


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
