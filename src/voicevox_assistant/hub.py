"""
声の窓口(ハブ)。PC 全体で1つだけが再生を受け持ち、声が重ならないようにする。

- 最初に起動した MCP サーバーが 127.0.0.1:VOICE_ASSISTANT_PORT(既定 38121)で待ち受ける
- ほかのセッションの MCP サーバーや、フック(相槌)は、そこへ POST する
- 持ち主が終わったら、次に話そうとしたサーバーが持ち主を引き継ぐ
"""

from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import httpx

from . import engine
from .player import PRESETS, Player, get_preset, resolve_speaker


def port() -> int:
    return int(os.environ.get("VOICE_ASSISTANT_PORT") or 38121)


class Hub:
    """実際に声を出す側。speak / filler / stop / quiet / voice / status を受ける。"""

    def __init__(self, player: Player | None = None) -> None:
        self.player = player or Player()
        self.preset = os.environ.get("VOICE_ASSISTANT_PRESET") or "jarvis"
        self.quiet = False
        self.last_said = 0.0

    def handle(self, req: dict[str, Any]) -> dict[str, Any]:
        action = req.get("action", "speak")
        if action == "speak":
            return self._speak(str(req.get("text") or ""), req.get("preset"), bool(req.get("interrupt", True)))
        if action == "filler":
            return self._filler(str(req.get("text") or ""), float(req.get("min_gap") or 0))
        if action == "stop":
            self.player.stop()
            return {"ok": True, "message": "止めました。"}
        if action == "quiet":
            self.quiet = bool(req.get("on", True))
            if self.quiet:
                self.player.stop()
            return {"ok": True, "message": "相槌を止めました。" if self.quiet else "相槌を再開しました。"}
        if action == "voice":
            key, p = get_preset(req.get("preset"), self.preset)
            self.preset = key
            return {"ok": True, "message": f"既定の声を {key}({p.label})にしました。"}
        if action == "status":
            return {
                "ok": True,
                "current": self.preset,
                "quiet": self.quiet,
                "speaking": self.player.busy,
                "last_error": self.player.last_error,
                "presets": {k: {"label": p.label, "voice": f"VOICEVOX:{p.speaker}({p.style})"} for k, p in PRESETS.items()},
                "engine": engine.status(),
            }
        return {"ok": False, "message": f"知らない action です: {action}"}

    def _say(self, text: str, preset: str | None, interrupt: bool) -> int:
        _, p = get_preset(preset, self.preset)
        sentences = engine.split_sentences(text)
        if sentences:
            self.player.say(sentences, resolve_speaker(p, engine.speakers()), p.speed, p.pitch, interrupt)
            self.last_said = time.monotonic()
        return len(sentences)

    def _speak(self, text: str, preset: str | None, interrupt: bool) -> dict[str, Any]:
        n = self._say(text, preset, interrupt)
        if not n:
            return {"ok": False, "message": "読む文がありません。"}
        note = f"(前回の読み上げで失敗: {self.player.last_error})" if self.player.last_error else ""
        return {"ok": True, "message": f"読み上げを始めました({n}文)。{note}"}

    def _filler(self, text: str, min_gap: float) -> dict[str, Any]:
        """相槌。静かにモード・話し中・直前に話したばかりなら言わない。話し中の声は止めない。"""
        if self.quiet or self.player.busy or time.monotonic() - self.last_said < min_gap:
            return {"ok": True, "spoken": False}
        return {"ok": True, "spoken": bool(self._say(text, None, interrupt=False))}


def _handler(hub: Hub) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length") or 0)
                req = json.loads(self.rfile.read(length) or b"{}")
                res = hub.handle(req)
                code = 200
            except Exception as exc:  # noqa: BLE001
                res, code = {"ok": False, "message": str(exc)}, 400
            body = json.dumps(res, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:  # stdout/stderr を汚さない
            pass

    return Handler


class Router:
    """MCP サーバーから使う。自分が持ち主ならその場で、そうでなければ持ち主へ送る。"""

    def __init__(self) -> None:
        self.hub: Hub | None = None
        self._lock = threading.Lock()

    def try_own(self) -> bool:
        with self._lock:
            if self.hub:
                return True
            try:
                server = ThreadingHTTPServer(("127.0.0.1", port()), _handler(hub := Hub()))
            except OSError:
                return False
            threading.Thread(target=server.serve_forever, name="voicevox-assistant-hub", daemon=True).start()
            self.hub = hub
            return True

    def send(self, req: dict[str, Any]) -> dict[str, Any]:
        if self.hub:
            return self.hub.handle(req)
        try:
            return post(req, timeout=5.0)
        except httpx.HTTPError:
            if self.try_own():  # 持ち主がいなくなったので引き継ぐ
                return self.hub.handle(req)  # type: ignore[union-attr]
            return post(req, timeout=5.0)


def post(req: dict[str, Any], timeout: float = 1.0) -> dict[str, Any]:
    res = httpx.post(f"http://127.0.0.1:{port()}/", json=req, timeout=timeout)
    return res.json()
