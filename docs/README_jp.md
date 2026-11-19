# voicevox-assistant-mcp

[English](../README.md) | 日本語

[Claude Code](https://claude.com/claude-code) の答えを、[VOICEVOX](https://voicevox.hiroshiba.jp/) で
**要約して**読み上げる音声アシスタントです。
ジャービスやアニメのアンドロイドのように、結論だけを落ち着いた声で伝え、作業中はときどき相槌や経過報告をします。

> **免責:** 個人の作品です。VOICEVOX の開発者・各キャラクターの権利者・Anthropic とは関係がなく、
> それらから承認を受けたものでもありません。

## 機能

| 状態 | 機能 |
|------|------|
| ✅ | 答えごとに 1〜3 文の要約を読み上げる(パス・コード・URL・決まり文句は読まない) |
| ✅ | 依頼を受けたときの返事(「承知しました」など) |
| ✅ | 作業中のランダムな相槌・経過報告(ツールの種類に合わせる: 「テストを実行しています」など) |
| ✅ | 判断待ちを知らせる(許可を求めるとき・質問するとき・計画の承認を求めるとき) |
| ✅ | 声のプリセット 4 種(ジャービス風・アンドロイド・オペレーター・ロボット) |
| ✅ | 静かにモード(読み上げと相槌を止める) |
| ✅ | 複数のセッション・ウィンドウでも声が重ならない(PC 全体で 1 か所が再生) |
| ✅ | 1 文目を流しながら次の文を作る(待ち時間は 1 文目の分だけ) |

## 仕組み

```
Claude Code ──(stdio)── MCP サーバー ─┐
Claude Code ──(stdio)── MCP サーバー ─┼─ HTTP 127.0.0.1:38121 ─→ ハブ(最初に起動したサーバー) ─→ VOICEVOX
フック(相槌) ───────────────────────┘                              │                 127.0.0.1:50021
                                                                     └─→ スピーカー(winsound)
```

- **要約は Claude 自身が書きます。** MCP サーバーの説明文(instructions)に「答えの最後に `speak` を呼び、
  耳で聞いて分かる要約を渡す」「口調はジャービス風」などを書いてあり、Claude はそれに従います
- **ハブ:** 最初に起動した MCP サーバーが 127.0.0.1 で待ち受け、ほかのサーバーとフックはそこへ送ります。
  持ち主が終わったら、次に話そうとしたサーバーが引き継ぎます
- **相槌:** フックは文を選んでハブに送るだけで、すぐ終わります(Claude の作業を止めません)。
  ハブは、話し中・静かにモード・直前に話したばかりのときは言いません。`speak` は相槌を止めて割り込みます
- **判断待ちの知らせ:** 質問(`AskUserQuestion`)・計画の承認(`ExitPlanMode`)・許可の確認(`Notification`)のときは
  必ず知らせます。話し中なら後ろに並べ、間引きません(静かにモードでは言いません)

## 必要なもの

- **Windows**(再生に `winsound` を使います)
- **Python**: 3.11 以上(uv が用意します)
- **[uv](https://docs.astral.sh/uv/)**
- **VOICEVOX**: エンジンが `http://127.0.0.1:50021` で動いていること(アプリを起動しておく)
- **Claude Code**(CLI または VS Code 拡張)

## インストール(ユーザー全体・どのプロジェクトでも使う)

### 1. コマンドを入れる

```powershell
uv tool install git+https://github.com/hirotoitpost/voicevox-assistant-mcp
```

`voicevox-assistant-mcp`(MCP サーバー)と `voicevox-assistant-hook`(相槌)が `~/.local/bin` に入ります。

### 2. MCP サーバーをユーザー全体に登録する

```powershell
claude mcp add --scope user voice-assistant -- voicevox-assistant-mcp
```

VS Code 拡張だけを使っていて `claude` コマンドが無いときは、拡張に入っている `claude.exe` を使えます:
`%USERPROFILE%\.vscode\extensions\anthropic.claude-code-<版>-win32-x64\resources\native-binary\claude.exe`

### 3. フックと許可を足す

`~/.claude/settings.json` に足します(既にある `permissions` や `hooks` には中身だけを足す):

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
      {
        "matcher": "*",
        "hooks": [{ "type": "command", "command": "voicevox-assistant-hook", "timeout": 3 }]
      }
    ],
    "Notification": [
      { "hooks": [{ "type": "command", "command": "voicevox-assistant-hook", "timeout": 3 }] }
    ]
  }
}
```

`permissions` を足さないと、読み上げのたびに許可を聞かれます。

### 4. 再起動する

Claude Code を再起動します(VS Code は「ウィンドウの再読み込み」)。

### 更新・削除

```powershell
uv tool upgrade voicevox-assistant-mcp   # 更新(そのあと再起動)
uv tool uninstall voicevox-assistant-mcp # 削除(claude mcp remove voice-assistant と settings.json のフックも外す)
```

## 使い方

ふつうに話しかけるだけです。

- 「静かに」「読み上げ不要」→ 読み上げと相槌を止める。「読み上げ再開」で戻る
- 「アンドロイドの声にして」→ 声を変える

### 声のプリセット

| プリセット | 声 |
|---|---|
| `jarvis`(既定) | VOICEVOX:青山龍星(しっとり) — 落ち着いた執事 |
| `android` | VOICEVOX:ナースロボ＿タイプＴ(ノーマル) |
| `announce` | VOICEVOX:No.7(アナウンス) — 冷静なオペレーター |
| `voidoll` | VOICEVOX:Voidoll(ノーマル) |

各キャラクターの利用規約に従い、録音した音声を公開するときは「VOICEVOX:(キャラ名)」のクレジットを入れてください。

### MCP ツール

| ツール | 内容 |
|---|---|
| `speak(text, preset?, interrupt?)` | 要約を読み上げる(すぐ返る) |
| `stop_speaking()` | 読み上げを止め、順番待ちも消す |
| `set_quiet(on)` | 静かにモードの切り替え |
| `set_voice(preset)` | 既定の声を変える |
| `voice_presets()` | プリセット・今の状態・エンジンの状態 |

## 設定(環境変数)

| 変数 | 既定 | 意味 |
|---|---|---|
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | エンジンの場所 |
| `VOICE_ASSISTANT_PRESET` | `jarvis` | 既定の声 |
| `VOICE_ASSISTANT_PORT` | `38121` | ハブのポート(127.0.0.1 のみ) |
| `VOICE_ASSISTANT_FILLER` | `on` | `off` で相槌をやめる |
| `VOICE_ASSISTANT_FILLER_RATE` | `0.5` | ツールを使うときに相槌を言う確率 |
| `VOICE_ASSISTANT_FILLER_GAP` | `25` | 前に話してから相槌まで空ける秒数 |
| `VOICE_ASSISTANT_ACK_RATE` | `0.8` | 依頼を受けたときに返事をする確率 |
| `VOICE_ASSISTANT_PERMISSION_ALERT` | `on` | 許可を求めるときに知らせる |
| `VOICE_ASSISTANT_IDLE_ALERT` | `off` | 入力待ちが続いたときに知らせる(答えの要約で終わりは伝わるので既定は無効) |

MCP サーバーへは `claude mcp add ... -e VOICE_ASSISTANT_PRESET=android -- voicevox-assistant-mcp` で、
フックへは `settings.json` の `env` で渡します。ポートを変えるときは両方に同じ値を渡してください。

## 困ったとき

| 症状 | 確かめること |
|---|---|
| 何も話さない | VOICEVOX が起動しているか。`voice_presets` の `engine.ready` |
| 答えは話すが相槌が無い | `settings.json` のフック。`voicevox-assistant-hook` が PATH にあるか |
| ハブが起動しない | Windows は 49152 以上のポートの一部を Hyper-V 用に予約します。`netsh interface ipv4 show excludedportrange protocol=tcp` で確かめ、`VOICE_ASSISTANT_PORT` を空いている番号に |
| 毎回許可を聞かれる | `permissions.allow` に `mcp__voice-assistant` |

## 制限

- Claude が考えている最中は割り込めません。相槌はツールを使う合間に入ります
- 要約の質は Claude しだいです
- 再生は Windows のみ(ほかの OS では wav を作るところまで)

## 開発

```powershell
git clone https://github.com/hirotoitpost/voicevox-assistant-mcp.git
cd voicevox-assistant-mcp
uv sync
uv run ruff check .
uv run pytest
```

手元のコードで試すときは `claude mcp add --scope user voice-assistant -- uv --directory <パス> run voicevox-assistant-mcp`。
詳しくは [CONTRIBUTING_jp.md](CONTRIBUTING_jp.md)、セキュリティは [SECURITY_jp.md](SECURITY_jp.md)。

## ライセンス

[MIT](../LICENSE)
