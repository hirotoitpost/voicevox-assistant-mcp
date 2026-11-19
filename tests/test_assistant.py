"""VOICEVOX と再生は差し替えて確かめる(エンジンが動いていなくてよい)。"""

from __future__ import annotations

import io
import random
import time
import wave

import pytest

from voicevox_assistant import engine, hook, hub, player


def _wav(seconds: float = 0.05) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\0\0" * int(24000 * seconds))
    return buf.getvalue()


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    calls: dict[str, list] = {"synth": [], "play": []}
    monkeypatch.setattr(
        engine, "speakers",
        lambda: [
            {"id": 99, "name": "青山龍星", "style": "しっとり"},
            {"id": 47, "name": "ナースロボ＿タイプＴ", "style": "ノーマル"},
        ],
    )

    def synth(text: str, speaker: int, speed: float = 1.0, pitch: float = 0.0) -> bytes:
        calls["synth"].append((text, speaker))
        return _wav()

    monkeypatch.setattr(engine, "synthesize", synth)
    monkeypatch.setattr(player, "play_file", lambda path: calls["play"].append(path))
    monkeypatch.setattr(player, "stop_sound", lambda: None)
    monkeypatch.delenv("VOICE_ASSISTANT_PRESET", raising=False)
    return calls


def _wait(p: player.Player) -> None:
    deadline = time.monotonic() + 5
    while p.busy and time.monotonic() < deadline:
        time.sleep(0.02)
    time.sleep(0.05)


def test_speak_reads_each_sentence(calls: dict[str, list]) -> None:
    h = hub.Hub()
    res = h.handle({"action": "speak", "text": "**完了しました。** テストは全て通っています。"})
    assert res["ok"] and "2文" in res["message"]
    _wait(h.player)
    assert calls["synth"] == [("完了しました。", 99), ("テストは全て通っています。", 99)]
    assert len(calls["play"]) == 2


def test_voice_change_and_unknown(calls: dict[str, list]) -> None:
    h = hub.Hub()
    h.handle({"action": "voice", "preset": "android"})
    h.handle({"action": "speak", "text": "了解しました。"})
    _wait(h.player)
    assert calls["synth"] == [("了解しました。", 47)]
    with pytest.raises(ValueError):
        h.handle({"action": "voice", "preset": "unknown"})


def test_filler_respects_quiet_and_gap(calls: dict[str, list]) -> None:
    h = hub.Hub()
    assert h.handle({"action": "filler", "text": "順調です。", "min_gap": 25})["spoken"] is True
    _wait(h.player)
    assert h.handle({"action": "filler", "text": "順調です。", "min_gap": 25})["spoken"] is False  # 話したばかり
    h.last_said = 0.0
    h.handle({"action": "quiet", "on": True})
    assert h.handle({"action": "filler", "text": "順調です。"})["spoken"] is False


def test_resolve_speaker_fallback() -> None:
    assert player.resolve_speaker(player.PRESETS["voidoll"], []) == 89


def test_hook_choose() -> None:
    class Always(random.Random):
        def random(self) -> float:
            return 0.0

    rng = Always()
    text, gap = hook.choose({"hook_event_name": "UserPromptSubmit"}, rng)  # type: ignore[misc]
    assert text in hook.ACK and gap == 0
    text, gap = hook.choose(
        {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "uv run pytest -q"}}, rng
    )  # type: ignore[misc]
    assert text in hook.BY_KIND["test"] + hook.GENERIC and gap > 0
    assert hook.choose({"hook_event_name": "PreToolUse", "tool_name": "mcp__voice-assistant__speak"}, rng) is None
    assert hook.choose({"hook_event_name": "Stop"}, rng) is None


def test_split_and_clean() -> None:
    assert engine.split_sentences("[リンク](https://x) を見て。`code` です！") == ["リンク を見て。", "code です！"]
