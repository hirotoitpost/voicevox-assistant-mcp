# voicevox-assistant-mcp

Claude Code の答えを、[VOICEVOX](https://voicevox.hiroshiba.jp/) で**要約して**読み上げる音声アシスタントです。
ジャービスやアニメのアンドロイドのように、結論だけを落ち着いた声で伝え、作業中はときどき相槌や経過報告をします。

- **MCP サーバー**: Claude が答えの最後に `speak` を呼び、1〜3文の話し言葉の要約を読み上げる(パス・コード・URL・決まり文句は読まない)
- **フック(相槌)**: 依頼を受けたとき「承知しました」、ツールを使うときにランダムで「テストを実行しています」「少々お待ちください」など
- **声が重ならない**: PC 全体で1つのサーバーだけが再生を受け持つ(複数のセッション・ウィンドウを開いていても順番に話す)

## 必要なもの

- Windows(再生に `winsound` を使います)
- [uv](https://docs.astral.sh/uv/)
- VOICEVOX(エンジンが `http://127.0.0.1:50021` で動いていること)

## インストール(ユーザー全体・どのプロジェクトでも使う)

```powershell
# 1. コマンドを入れる(voicevox-assistant-mcp と voicevox-assistant-hook が PATH に入る)
uv tool install git+https://github.com/hirotoitpost/voicevox-assistant-mcp

# 2. MCP サーバーをユーザー全体に登録
claude mcp add --scope user voice-assistant -- voicevox-assistant-mcp
```

3. `~/.claude/settings.json` にフックと許可を足す(相槌を使うとき):

```json
{
  "permissions": {
    "allow": ["mcp__voice-assistant"]
  },
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "voicevox-assistant-hook", "timeout": 3 }] }
    ],
    "PreToolUse": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "voicevox-assistant-hook", "timeout": 3 }] }
    ]
  }
}
```

VS Code の Claude Code 拡張もこの設定を読みます。入れたあとは Claude Code を再起動(VS Code はウィンドウの再読み込み)してください。

更新: `uv tool upgrade voicevox-assistant-mcp`

## 使い方

ふつうに話しかけるだけです。

- 「静かに」→ 読み上げと相槌を止める(`set_quiet`)。「読み上げ再開」で戻る
- 「アンドロイドの声にして」→ 声を変える(`set_voice`)

| プリセット | 声 |
|---|---|
| `jarvis`(既定) | VOICEVOX:青山龍星(しっとり) — 落ち着いた執事 |
| `android` | VOICEVOX:ナースロボ＿タイプＴ(ノーマル) |
| `announce` | VOICEVOX:No.7(アナウンス) — 冷静なオペレーター |
| `voidoll` | VOICEVOX:Voidoll(ノーマル) |

各キャラクターの利用規約に従い、音声を公開するときは「VOICEVOX:(キャラ名)」のクレジットを入れてください。

## 設定(環境変数)

| 変数 | 既定 | 意味 |
|---|---|---|
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | エンジンの場所 |
| `VOICE_ASSISTANT_PRESET` | `jarvis` | 既定の声 |
| `VOICE_ASSISTANT_PORT` | `38121` | サーバー同士・フックがやりとりするポート(127.0.0.1 のみ) |
| `VOICE_ASSISTANT_FILLER` | `on` | `off` で相槌をやめる |
| `VOICE_ASSISTANT_FILLER_RATE` | `0.5` | ツールを使うときに相槌を言う確率 |
| `VOICE_ASSISTANT_FILLER_GAP` | `25` | 前に話してから相槌まで空ける秒数 |
| `VOICE_ASSISTANT_ACK_RATE` | `0.8` | 依頼を受けたときに返事をする確率 |

MCP サーバーの環境変数は `claude mcp add ... -e VOICE_ASSISTANT_PRESET=android -- voicevox-assistant-mcp` で、フックのものは `settings.json` の `env` で渡せます。

## 制限

- Claude が考えている最中は割り込めません。相槌はツールを使う合間に入ります
- 要約するのは Claude 自身です(MCP サーバーの説明文で指示しています)

## 開発

```powershell
uv sync
uv run ruff check .
uv run pytest
```

## ライセンス

MIT
