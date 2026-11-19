# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Playback on macOS / Linux
- User-defined presets and filler phrases

---

## [0.2.0] - 2026-11-20

### Added

- **Waiting alerts** — the hook always speaks when Claude waits for the user: `AskUserQuestion`
  (question), `ExitPlanMode` (plan approval) and `Notification` permission prompts. Alerts are queued
  after current speech, never throttled, and silent in quiet mode. `VOICE_ASSISTANT_PERMISSION_ALERT`
  (default on) and `VOICE_ASSISTANT_IDLE_ALERT` (default off) control the notifications
- The settings example adds a `Notification` hook

### Changed

- `VOICE_ASSISTANT_FILLER=off` now disables only fillers; waiting alerts stay on

---

## [0.1.0] - 2026-11-20

### Added

- **MCP server (`voicevox-assistant-mcp`)** — `speak`, `stop_speaking`, `set_quiet`, `set_voice`,
  `voice_presets`. Its instructions tell Claude to speak a 1–3 sentence, JARVIS-like summary of every
  reply and to skip paths, code, URLs and boilerplate
- **Filler hook (`voicevox-assistant-hook`)** — acknowledgement on `UserPromptSubmit`, random
  tool-aware progress reports on `PreToolUse`; throttled, never blocks Claude Code
- **Local hub** — the first server listens on 127.0.0.1:38121 so all sessions and hooks share one
  player; takeover when the owner exits
- **Voice presets** — `jarvis` (青山龍星 しっとり), `android` (ナースロボ＿タイプＴ), `announce` (No.7),
  `voidoll` (Voidoll); speaker ids resolved by name
- Pipelined playback (synthesize the next sentence while the current one plays)
- English and Japanese docs: README, CONTRIBUTING, SECURITY
