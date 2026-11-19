"""音声アシスタントの MCP サーバー(stdio)。"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from .hub import Router

router = Router()

INSTRUCTIONS = (
    "VOICEVOX で、ユーザーへの答えを声で伝える音声アシスタント。"
    "ユーザーへの答え(ターンの最後のメッセージ)を書くたびに、speak を1回呼ぶ。"
    "渡すのは全文ではなく、耳で聞いて分かる要約(1〜3文、おおむね80字以内)。"
    "ユーザーの使う言語で話す。"
    "口調はジャービスやアニメのアンドロイドのような、落ち着いて簡潔な有能アシスタント。"
    "例:「完了しました。テストは全て通っています。」「一点、確認が必要です。画面をご覧ください。」"
    "読まないもの: ファイルパス、コード、URL、コマンド、ID の羅列、表、記号、前置きや決まり文句。"
    "英字は読める語だけカタカナにする(PR→ピーアール、MCP→エムシーピー)。数は必要なものだけ。"
    "詳細は画面に任せ、結論・結果・ユーザーに頼むことだけを話す。"
    "作業中の相槌はフックが自動で言うので、途中経過のために speak を呼ばなくてよい"
    "(長い作業の節目で一言伝えたいときだけ interrupt=False で呼んでよい)。"
    "ユーザーが「静かに」「読み上げ不要」と言ったら set_quiet(true) を呼び、言われるまで speak を呼ばない。"
    "再開を頼まれたら set_quiet(false)。"
)

mcp = MCPServer(name="voice-assistant", instructions=INSTRUCTIONS)


def _message(res: dict[str, Any]) -> str:
    return str(res.get("message") or res)


@mcp.tool()
def speak(text: str, preset: str | None = None, interrupt: bool = True) -> str:
    """要約した文を声で読み上げる(裏で流すので、すぐ返る)。

    text: 話し言葉の要約(1〜3文)。Markdown の記号は外して読む。
    preset: 声(jarvis / android / announce / voidoll)。省略すると今の既定の声。
    interrupt: True なら読み途中の声(相槌を含む)を止めて置き換える。False なら後ろに並べる。
    """
    return _message(router.send({"action": "speak", "text": text, "preset": preset, "interrupt": interrupt}))


@mcp.tool()
def stop_speaking() -> str:
    """読み上げを止め、順番待ちも消す。"""
    return _message(router.send({"action": "stop"}))


@mcp.tool()
def set_quiet(on: bool = True) -> str:
    """静かにモード。on=True で読み上げ中の声と作業中の相槌を止める。False で相槌を再開。"""
    return _message(router.send({"action": "quiet", "on": on}))


@mcp.tool()
def set_voice(preset: str) -> str:
    """既定の声を変える(jarvis / android / announce / voidoll)。ずっと変えるなら環境変数 VOICE_ASSISTANT_PRESET。"""
    return _message(router.send({"action": "voice", "preset": preset}))


@mcp.tool()
def voice_presets() -> dict[str, Any]:
    """声のプリセットの一覧と、今の既定の声・静かにモード・エンジンの状態。"""
    return router.send({"action": "status"})


def main() -> None:
    router.try_own()
    mcp.run()


if __name__ == "__main__":
    main()
