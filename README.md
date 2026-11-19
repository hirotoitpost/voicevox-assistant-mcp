# voicevox-assistant-mcp

English | [日本語](docs/README_jp.md)

A voice assistant for [Claude Code](https://claude.com/claude-code) that reads out a **short spoken summary**
of each reply with [VOICEVOX](https://voicevox.hiroshiba.jp/).
Like JARVIS or an anime android, it tells you only the conclusion in a calm voice, and drops an occasional
acknowledgement or progress report while it works.

> **Disclaimer:** This is an independent, personal project. It is not affiliated with, endorsed by, or
> officially connected to the VOICEVOX developers, the voice characters' rights holders, or Anthropic.

## Features

| Status | Feature |
|--------|---------|
| ✅ | Reads a 1–3 sentence summary of every reply (no paths, code, URLs or boilerplate) |
| ✅ | Acknowledges each request ("承知しました" — "Understood") |
| ✅ | Random fillers and progress reports while working, matched to the tool ("Running the tests") |
| ✅ | Tells you when it is waiting for you: permission prompts, questions, plan approval |
| ✅ | Four voice presets (JARVIS-like butler, android, operator, robot) |
| ✅ | Quiet mode (stops speech and fillers) |
| ✅ | No overlapping voices across sessions and windows (one player per machine) |
| ✅ | Plays the first sentence while synthesizing the next |

Speech is in Japanese by default; Claude is told to speak in the user's language.

## How it works

```
Claude Code ──(stdio)── MCP server ─┐
Claude Code ──(stdio)── MCP server ─┼─ HTTP 127.0.0.1:38121 ─→ hub (first server started) ─→ VOICEVOX
hooks (fillers) ────────────────────┘                             │                         127.0.0.1:50021
                                                                    └─→ speakers (winsound)
```

- **Claude writes the summary itself.** The MCP server's instructions tell Claude to call `speak` at the end
  of every reply with an ear-friendly summary in a JARVIS-like tone.
- **Hub:** the first MCP server to start listens on 127.0.0.1; other servers and the hooks send to it.
  When it exits, the next server that needs to speak takes over.
- **Fillers:** the hook only picks a phrase and posts it to the hub, then exits immediately, so Claude is
  never slowed down. The hub skips a filler while speaking, in quiet mode, or right after speaking.
  `speak` interrupts fillers.
- **Waiting alerts:** when Claude asks a question (`AskUserQuestion`), asks to approve a plan
  (`ExitPlanMode`) or shows a permission prompt (`Notification`), it always says so — queued
  after current speech, never throttled, silent only in quiet mode.

## Requirements

- **Windows** (playback uses `winsound`)
- **Python**: 3.11 or higher (uv provides it)
- **[uv](https://docs.astral.sh/uv/)**
- **VOICEVOX**: the engine running at `http://127.0.0.1:50021` (start the app)
- **Claude Code** (CLI or the VS Code extension)

## Installation (user-wide, available in every project)

### 1. Install the commands

```powershell
uv tool install git+https://github.com/hirotoitpost/voicevox-assistant-mcp
```

This puts `voicevox-assistant-mcp` (MCP server) and `voicevox-assistant-hook` (fillers) in `~/.local/bin`.

### 2. Register the MCP server for your user

```powershell
claude mcp add --scope user voice-assistant -- voicevox-assistant-mcp
```

If you only use the VS Code extension and have no `claude` command, use the bundled binary:
`%USERPROFILE%\.vscode\extensions\anthropic.claude-code-<version>-win32-x64\resources\native-binary\claude.exe`

### 3. Add the hooks and permission

Add to `~/.claude/settings.json` (merge into existing `permissions` / `hooks` if present):

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

Without the permission entry, Claude Code asks before every spoken summary.

### 4. Restart

Restart Claude Code (in VS Code: "Developer: Reload Window").

### Update / uninstall

```powershell
uv tool upgrade voicevox-assistant-mcp    # update, then restart
uv tool uninstall voicevox-assistant-mcp  # also run: claude mcp remove voice-assistant, and remove the hooks
```

## Usage

Just talk to Claude.

- "静かに" / "be quiet" → stops speech and fillers. "読み上げ再開" / "resume speaking" turns them back on
- "アンドロイドの声にして" / "use the android voice" → changes the voice

### Voice presets

| Preset | Voice |
|---|---|
| `jarvis` (default) | VOICEVOX:青山龍星 (しっとり) — calm butler |
| `android` | VOICEVOX:ナースロボ＿タイプＴ (ノーマル) |
| `announce` | VOICEVOX:No.7 (アナウンス) — cool operator |
| `voidoll` | VOICEVOX:Voidoll (ノーマル) |

Follow each character's terms of use: credit "VOICEVOX:(character name)" when publishing recorded audio.

### MCP tools

| Tool | Description |
|---|---|
| `speak(text, preset?, interrupt?)` | Speak a summary (returns immediately) |
| `stop_speaking()` | Stop speaking and clear the queue |
| `set_quiet(on)` | Toggle quiet mode |
| `set_voice(preset)` | Change the default voice |
| `voice_presets()` | Presets, current state and engine status |

## Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | VOICEVOX engine URL |
| `VOICE_ASSISTANT_PRESET` | `jarvis` | Default voice |
| `VOICE_ASSISTANT_PORT` | `38121` | Hub port (127.0.0.1 only) |
| `VOICE_ASSISTANT_FILLER` | `on` | `off` disables fillers |
| `VOICE_ASSISTANT_FILLER_RATE` | `0.5` | Chance of a filler on each tool call |
| `VOICE_ASSISTANT_FILLER_GAP` | `25` | Seconds of silence required before a filler |
| `VOICE_ASSISTANT_ACK_RATE` | `0.8` | Chance of acknowledging a request |
| `VOICE_ASSISTANT_PERMISSION_ALERT` | `on` | Say so when a permission prompt appears |
| `VOICE_ASSISTANT_IDLE_ALERT` | `off` | Say so when Claude has been waiting for input (the summary already says it's done) |

Pass them to the MCP server with `claude mcp add ... -e VOICE_ASSISTANT_PRESET=android -- voicevox-assistant-mcp`,
and to the hooks with `env` in `settings.json`. If you change the port, set the same value in both.

## Troubleshooting

| Symptom | Check |
|---|---|
| No speech at all | Is VOICEVOX running? See `engine.ready` in `voice_presets` |
| Summaries but no fillers | Hooks in `settings.json`; is `voicevox-assistant-hook` on PATH? |
| Hub fails to start | Windows reserves some ports at 49152+ for Hyper-V. Check `netsh interface ipv4 show excludedportrange protocol=tcp` and set `VOICE_ASSISTANT_PORT` to a free port |
| Asked for permission every time | Add `mcp__voice-assistant` to `permissions.allow` |

## Limitations

- It cannot interrupt while Claude is thinking; fillers happen between tool calls
- Summary quality depends on Claude
- Playback is Windows-only (other OSes stop after synthesizing the wav)

## Development

```powershell
git clone https://github.com/hirotoitpost/voicevox-assistant-mcp.git
cd voicevox-assistant-mcp
uv sync
uv run ruff check .
uv run pytest
```

To try local code: `claude mcp add --scope user voice-assistant -- uv --directory <path> run voicevox-assistant-mcp`.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
