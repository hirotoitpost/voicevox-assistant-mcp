"""VOICEVOX エンジンとのやりとり(audio_query → synthesis)と、読み上げ用の文の整形。"""

from __future__ import annotations

import os
import re
import threading
import time
from collections import OrderedDict
from typing import Any

import httpx

DEFAULT_URL = "http://127.0.0.1:50021"
MAX_CHARS = 300
_CACHE_SIZE = 64
_cache: OrderedDict[tuple[str, int, float, float], bytes] = OrderedDict()
_speakers: tuple[float, list[dict[str, Any]]] | None = None
_lock = threading.Lock()


class VoiceUnavailable(RuntimeError):
    """VOICEVOX のエンジンにつながらない。"""


def engine_url() -> str:
    return (os.environ.get("VOICEVOX_URL") or DEFAULT_URL).rstrip("/")


def _client() -> httpx.Client:
    return httpx.Client(base_url=engine_url(), timeout=httpx.Timeout(60.0, connect=3.0))


def status() -> dict[str, Any]:
    try:
        with _client() as client:
            res = client.get("/version")
            res.raise_for_status()
            return {"ready": True, "version": res.json(), "url": engine_url()}
    except (httpx.HTTPError, ValueError):
        return {"ready": False, "version": None, "url": engine_url()}


def speakers() -> list[dict[str, Any]]:
    """話者とスタイルの一覧(id・話者名・スタイル名)。10分覚えておく。動いていなければ空。"""
    global _speakers
    with _lock:
        if _speakers and time.monotonic() - _speakers[0] < 600:
            return _speakers[1]
    try:
        with _client() as client:
            res = client.get("/speakers")
            res.raise_for_status()
            data = res.json()
    except (httpx.HTTPError, ValueError):
        return []
    flat = [
        {"id": style["id"], "name": speaker["name"], "style": style["name"]}
        for speaker in data
        for style in speaker.get("styles", [])
        if style.get("type", "talk") == "talk"
    ]
    with _lock:
        _speakers = (time.monotonic(), flat)
    return flat


def clean_text(text: str) -> str:
    """Markdown の記号・URL を読ませない形にする。"""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"(?m)^\s*(#{1,6}|>|[-*]|\d+\.)\s+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{2,}", "\n", text).strip()


def split_sentences(text: str, limit: int = 120) -> list[str]:
    """文ごとに分ける(。!?と改行)。長すぎる文は読点か limit で切る。"""
    parts: list[str] = []
    for sentence in re.split(r"(?<=[。！？!?])|\n", clean_text(text)):
        sentence = sentence.strip()
        while len(sentence) > limit:
            cut = sentence.rfind("、", 0, limit)
            cut = cut + 1 if cut > limit // 3 else limit
            parts.append(sentence[:cut])
            sentence = sentence[cut:].strip()
        if sentence:
            parts.append(sentence)
    return parts


def synthesize(text: str, speaker: int, speed: float = 1.0, pitch: float = 0.0) -> bytes:
    """1つの文を wav にする。"""
    text = clean_text(text)[:MAX_CHARS]
    if not text:
        raise ValueError("読む文がありません。")
    key = (text, speaker, round(speed, 2), round(pitch, 3))
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    try:
        with _client() as client:
            query = client.post("/audio_query", params={"text": text, "speaker": speaker})
            query.raise_for_status()
            body = query.json()
            body["speedScale"] = max(0.5, min(2.0, speed))
            body["pitchScale"] = max(-0.15, min(0.15, pitch))
            audio = client.post("/synthesis", params={"speaker": speaker}, json=body)
            audio.raise_for_status()
    except httpx.HTTPError as exc:
        raise VoiceUnavailable(f"VOICEVOX で読めませんでした({engine_url()}): {exc}") from exc
    with _lock:
        _cache[key] = audio.content
        while len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return audio.content
