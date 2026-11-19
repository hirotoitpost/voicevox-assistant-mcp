"""読み上げの順番待ちと再生。1本のスレッドで、1文目を流しながら次の文を作る。"""

from __future__ import annotations

import io
import queue
import sys
import tempfile
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from . import engine


@dataclass(frozen=True)
class Preset:
    label: str
    speaker: str  # VOICEVOX の話者名
    style: str  # スタイル名
    fallback_id: int  # 名前で見つからないときの ID
    speed: float = 1.1
    pitch: float = 0.0


PRESETS: dict[str, Preset] = {
    "jarvis": Preset("落ち着いた執事(ジャービス風)", "青山龍星", "しっとり", 84, speed=1.1, pitch=-0.02),
    "android": Preset("アンドロイド(ナースロボ)", "ナースロボ＿タイプＴ", "ノーマル", 47, speed=1.1),
    "announce": Preset("冷静なオペレーター(No.7 アナウンス)", "No.7", "アナウンス", 30, speed=1.15),
    "voidoll": Preset("ロボット(Voidoll)", "Voidoll", "ノーマル", 89, speed=1.1),
}
DEFAULT_PRESET = "jarvis"


def get_preset(name: str | None, default: str = DEFAULT_PRESET) -> tuple[str, Preset]:
    key = (name or default or DEFAULT_PRESET).strip().lower()
    if key not in PRESETS:
        raise ValueError(f"プリセット {key!r} はありません。使えるのは {', '.join(PRESETS)} です。")
    return key, PRESETS[key]


def resolve_speaker(preset: Preset, voices: list[dict]) -> int:
    """話者名・スタイル名から ID を引く(エンジンの版で ID が変わっても追える)。"""
    for v in voices:
        if v["name"] == preset.speaker and v["style"] == preset.style:
            return int(v["id"])
    return preset.fallback_id


def wav_seconds(data: bytes) -> float:
    with wave.open(io.BytesIO(data)) as w:
        return w.getnframes() / float(w.getframerate() or 1)


def play_file(path: Path) -> None:
    if sys.platform != "win32":
        raise RuntimeError(f"この OS では再生できません(wav は {path})。")
    import winsound

    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)


def stop_sound() -> None:
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(None, 0)


class Player:
    def __init__(self) -> None:
        self._queue: queue.Queue[tuple[int, list[str], int, float, float]] = queue.Queue()
        self._generation = 0
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._tmpdir = Path(tempfile.mkdtemp(prefix="voicevox_assistant_"))
        self.last_error: str | None = None
        self.speaking = False

    @property
    def busy(self) -> bool:
        return self.speaking or not self._queue.empty()

    def say(self, sentences: list[str], speaker: int, speed: float, pitch: float, interrupt: bool) -> None:
        with self._lock:
            if interrupt:
                self._generation += 1
                self._drain()
                stop_sound()
            gen = self._generation
        self._queue.put((gen, sentences, speaker, speed, pitch))
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, name="voicevox-assistant", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._generation += 1
            self._drain()
        stop_sound()

    def _drain(self) -> None:
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass

    def _cancelled(self, gen: int) -> bool:
        return gen != self._generation

    def _run(self) -> None:
        while True:
            gen, sentences, speaker, speed, pitch = self._queue.get()
            if self._cancelled(gen):
                continue
            self.speaking = True
            try:
                self._play_all(gen, sentences, speaker, speed, pitch)
                self.last_error = None
            except Exception as exc:  # noqa: BLE001 - 裏のスレッドなので落とさずに覚えておく
                self.last_error = str(exc)
            finally:
                self.speaking = False

    def _play_all(self, gen: int, sentences: list[str], speaker: int, speed: float, pitch: float) -> None:
        ends_at = 0.0
        for i, sentence in enumerate(sentences):
            audio = engine.synthesize(sentence, speaker, speed=speed, pitch=pitch)
            if self._cancelled(gen):
                return
            while time.monotonic() < ends_at:
                if self._cancelled(gen):
                    return
                time.sleep(0.05)
            path = self._tmpdir / f"s{i % 2}.wav"  # 再生中のファイルは上書きしない
            path.write_bytes(audio)
            play_file(path)
            ends_at = time.monotonic() + wav_seconds(audio) + 0.1
        while time.monotonic() < ends_at and not self._cancelled(gen):
            time.sleep(0.05)
