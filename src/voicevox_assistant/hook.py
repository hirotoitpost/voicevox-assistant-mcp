"""
Claude Code のフック: 作業中にランダムで相槌・経過報告を言う。

- UserPromptSubmit: 依頼を受けたときの返事(「承知しました」など)
- PreToolUse: ツールの種類に合った一言(「テストを実行しています」など)。前に話してから
  VOICE_ASSISTANT_FILLER_GAP 秒(既定 25)たっていて、確率 VOICE_ASSISTANT_FILLER_RATE(既定 0.5)で当たったときだけ
- 声はハブ(MCP サーバー)が出す。ハブが話し中・静かにモードなら言わない
- 判断待ちの知らせ(間引かず必ず言う。静かにモードでは言わない):
  - PreToolUse の AskUserQuestion(質問)・ExitPlanMode(計画の承認)
  - Notification の許可待ち(VOICE_ASSISTANT_PERMISSION_ALERT=off で無効)・
    入力待ち(VOICE_ASSISTANT_IDLE_ALERT=on で有効。既定は無効: 答えの要約を既に話しているため)
- 何があっても何も出力せず、すぐ 0 で終わる(Claude の作業を止めない)
- VOICE_ASSISTANT_FILLER=off で相槌だけ無効(判断待ちの知らせは残る)
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
from typing import Any

ACK = ("承知しました。", "かしこまりました。取りかかります。", "了解です。確認します。", "お任せください。", "はい、すぐに。")
GENERIC = ("少々お待ちください。", "順調です。", "引き続き作業中です。", "問題なく進んでいます。", "もう少々お待ちを。")
BY_KIND: dict[str, tuple[str, ...]] = {
    "read": ("資料を確認しています。", "関連する箇所を調べています。", "コードを読んでいます。"),
    "edit": ("修正を加えています。", "ファイルを更新しています。", "書き換えています。"),
    "test": ("テストを実行しています。", "検証を走らせています。結果をお待ちください。", "動作を確かめています。"),
    "git": ("リポジトリを操作しています。", "変更をまとめています。"),
    "shell": ("コマンドを実行します。", "処理を進めています。"),
    "web": ("情報を調べています。", "ウェブで確認しています。"),
    "agent": ("手分けして調査を進めます。", "別動隊を向かわせます。"),
    "tool": ("ツールを呼び出しています。", "処理を依頼しています。"),
}


def tool_kind(tool: str, tool_input: dict[str, Any]) -> str | None:
    if tool.startswith("mcp__voice-assistant__"):
        return None
    if tool in ("Read", "Grep", "Glob", "LS"):
        return "read"
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return "edit"
    if tool in ("WebSearch", "WebFetch"):
        return "web"
    if tool in ("Agent", "Task"):
        return "agent"
    if tool in ("Bash", "PowerShell"):
        cmd = str(tool_input.get("command") or "")
        if re.search(r"\b(pytest|test|ruff|lint|build|tsc|vitest|jest|mypy)\b", cmd):
            return "test"
        if re.search(r"\b(git|gh)\b", cmd):
            return "git"
        return "shell"
    if tool.startswith("mcp__"):
        return "tool"
    return "generic"


PERMISSION = ("許可をお願いします。", "実行の許可をいただけますか。", "ご確認ください。許可が必要です。")
QUESTION = ("ご判断をお願いします。", "一点、ご確認いただけますか。", "選択肢をご用意しました。ご判断を。")
PLAN = ("計画をまとめました。ご確認ください。", "進め方のご承認をお願いします。")
IDLE = ("ご指示をお待ちしています。", "次のご指示をどうぞ。")


def _on(name: str, default: str = "on") -> bool:
    return (os.environ.get(name) or default).lower() not in ("off", "0", "false")


def alert(event: dict[str, Any], rng: random.Random | None = None) -> str | None:
    """ユーザーの判断を待つときの知らせ(相槌と違い、間引かずに必ず言う)。言わないなら None。"""
    rng = rng or random.Random()
    name = event.get("hook_event_name")
    if name == "PreToolUse":
        tool = event.get("tool_name")
        if tool == "AskUserQuestion":
            return rng.choice(QUESTION)
        if tool == "ExitPlanMode":
            return rng.choice(PLAN)
        return None
    if name == "Notification":
        kind = str(event.get("notification_type") or "")
        message = str(event.get("message") or "").lower()
        if kind == "permission_prompt" or (not kind and "permission" in message):
            return rng.choice(PERMISSION) if _on("VOICE_ASSISTANT_PERMISSION_ALERT") else None
        if kind == "elicitation_dialog":
            return rng.choice(QUESTION)
        if kind == "idle_prompt" or (not kind and "waiting for your input" in message):
            return rng.choice(IDLE) if _on("VOICE_ASSISTANT_IDLE_ALERT", "off") else None
    return None


def choose(event: dict[str, Any], rng: random.Random | None = None) -> tuple[str, float] | None:
    """言う文と min_gap(前に話してから空ける秒数)。言わないなら None。"""
    rng = rng or random.Random()
    name = event.get("hook_event_name")
    if name == "UserPromptSubmit":
        if rng.random() > float(os.environ.get("VOICE_ASSISTANT_ACK_RATE") or 0.8):
            return None
        return rng.choice(ACK), 0.0
    if name == "PreToolUse":
        kind = tool_kind(str(event.get("tool_name") or ""), event.get("tool_input") or {})
        if kind is None or rng.random() > float(os.environ.get("VOICE_ASSISTANT_FILLER_RATE") or 0.5):
            return None
        pool = GENERIC if kind == "generic" or rng.random() < 0.3 else BY_KIND[kind]
        return rng.choice(pool), float(os.environ.get("VOICE_ASSISTANT_FILLER_GAP") or 25)
    return None


def main() -> None:
    try:
        event = json.loads(sys.stdin.buffer.read() or b"{}")
        from .hub import post

        if text := alert(event):
            post({"action": "alert", "text": text}, timeout=0.5)
        elif _on("VOICE_ASSISTANT_FILLER") and (picked := choose(event)):
            post({"action": "filler", "text": picked[0], "min_gap": picked[1]}, timeout=0.5)
    except Exception:  # noqa: BLE001 - フックは決して失敗させない
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
