# Security

English | [日本語](docs/SECURITY_jp.md)

## Audit Summary

An internal review was conducted on **2026-11-20** covering all code in `src/voicevox_assistant/`.

**Result: No security issues found.** Notes on the local hub are listed below.

---

## Network Communication

All communication stays on the local machine:

| Destination | Purpose |
|---|---|
| `http://127.0.0.1:50021` | VOICEVOX engine (`/version`, `/speakers`, `/audio_query`, `/synthesis`) |
| `http://127.0.0.1:38121` | The assistant's own hub (MCP servers and hooks → hub) |

No data is sent to any external service. The engine URL is configurable with `VOICEVOX_URL`
and the hub port with `VOICE_ASSISTANT_PORT`.

### Topology

```
Claude Code ─(stdio)─ MCP server ─┐
hooks ────────────────────────────┴─ HTTP 127.0.0.1:38121 ─ hub ─ HTTP 127.0.0.1:50021 ─ VOICEVOX
```

---

## Local Hub

- The hub binds to **127.0.0.1 only**; it is not reachable from other machines.
- It has **no authentication**. Any process on the same machine can make it speak a text, change
  the voice or toggle quiet mode. It cannot read files, run commands or return anything but status.
- Requests are JSON; unknown actions are rejected. Text is truncated to 300 characters per sentence.
- If you change `VOICEVOX_URL` to a remote host, spoken summaries are sent there in plain HTTP.

---

## Hooks

- The hook reads the event JSON that Claude Code passes on stdin (event name, tool name and input).
- It only uses the event name, tool name and, for shell tools, whether the command looks like a
  test / git command, to **pick a canned phrase**. Tool inputs, prompts and file contents are
  **never sent** anywhere; only the canned phrase goes to the hub.
- It prints nothing (so it never injects text into Claude's context) and always exits 0.

---

## Data Handling

- Spoken summaries are written by Claude and held in memory only; nothing is logged.
- Synthesized audio is cached in memory (last 64 sentences) and written to two temporary wav files
  under the system temp directory, overwritten on each sentence.
- No credentials are used or stored.

---

## Code Inspection

The following dangerous patterns were searched for and **not found** in `src/voicevox_assistant/`:

- Dynamic code execution: `eval()`, `exec()`, `compile()`, `__import__()`
- Shell access: `subprocess`, `os.system()`, `popen()`
- Obfuscated code or suspicious imports

---

## Dependencies

| Package | Purpose |
|---|---|
| `mcp` | MCP server (stdio) |
| `httpx` | HTTP client (VOICEVOX engine, hub) |

Standard library: `http.server` (hub), `winsound` (playback), `wave`, `threading`.

---

## Reporting a Vulnerability

If you discover a security issue in this repository, please open a [GitHub Issue](../../issues)
marked **[Security]**, or contact the maintainer directly before public disclosure.
