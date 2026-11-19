# Contributing to voicevox-assistant-mcp

English | [日本語](docs/CONTRIBUTING_jp.md)

Thank you for your interest in contributing! This document provides guidelines for contributing to
voicevox-assistant-mcp.

## Quick Start Workflow

1. **Fork and Clone**: Fork the repository and clone it to your local machine
   ```bash
   git clone https://github.com/YOUR_USERNAME/voicevox-assistant-mcp.git
   cd voicevox-assistant-mcp
   ```

2. **Create Branch**: Use the naming convention below
   ```bash
   git checkout -b feature/YOUR_DESCRIPTION
   ```

3. **Implement Changes**: Edit code, add tests, and update documentation

4. **Verify Quality**: Run all checks locally
   ```bash
   uv run ruff check .
   uv run pytest
   ```

5. **Commit**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
   ```bash
   git commit -m "feat: add new voice preset"
   ```

6. **Push & Create PR**: Push your branch and open a pull request on GitHub

## Contribution Types

- **Bug Fixes**: Reference Issues, include test cases, detail the fix in the PR description
- **New Features**: Propose via Issues first (new presets, fillers, platforms), include tests and docs
- **Documentation**: Improve clarity, add examples, fix typos, improve translations
- **Code Quality**: Refactor, optimize, improve test coverage

## Development Environment

### Requirements

- Windows (for real playback; tests run on any OS)
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/)
- VOICEVOX (only for manual testing; tests replace the engine)
- Git

### Setup

```bash
uv sync
uv run ruff check . && uv run pytest
```

To try your working copy in Claude Code:

```bash
claude mcp add --scope user voice-assistant -- uv --directory <path-to-clone> run voicevox-assistant-mcp
```

and point the hooks at `uv --directory <path-to-clone> run voicevox-assistant-hook`.

## Code Standards

### Python

- **Linter / formatter**: Ruff (`uv run ruff check .`, `uv run ruff format .`)
- **Style**: PEP 8 as enforced by Ruff (line length 130)
- **Type Hints**: Full type annotations
- **No network beyond localhost**: the assistant talks only to the VOICEVOX engine and its own hub

### Hooks

- A hook must never block or fail Claude Code: catch every exception, print nothing, exit 0 quickly
- Never send tool inputs, prompts or file contents anywhere; send only the chosen canned phrase

### Speech text

- Phrases and instructions are spoken aloud: keep them short, natural and free of symbols

### Markdown

- Maximum 100 characters per line where practical
- Keep English and Japanese (`docs/*_jp.md`) documents in sync

### Language

- **Primary**: English for documentation; code comments may be Japanese
- **Secondary**: Japanese translations for key documents

## Git Workflow & Branch Strategy

### Branch Naming Convention

```
feature/[DESCRIPTION]    # New features
fix/[DESCRIPTION]        # Bug fixes
docs/[DESCRIPTION]       # Documentation updates
refactor/[DESCRIPTION]   # Code refactoring
test/[DESCRIPTION]       # Test additions/improvements
chore/[DESCRIPTION]      # Build, dependencies, etc.
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
{feat|fix|docs|style|refactor|test|chore}: Brief description

Optional body explaining why, what, and how to verify.
```

## PR Checklist Requirements

- [ ] Branch is up to date with `main`
- [ ] No merge conflicts
- [ ] All tests passing: `uv run pytest`
- [ ] Linting passed: `uv run ruff check .`
- [ ] Documentation updated (README, `docs/README_jp.md`, docstrings)
- [ ] CHANGELOG.md updated in the Unreleased section
- [ ] Commit messages follow Conventional Commits
- [ ] PR description references related Issues

## Testing

- Write tests for all new functionality in `tests/`
- Tests must not need a running VOICEVOX engine or speakers: replace `engine.synthesize`,
  `engine.speakers`, `player.play_file` and `player.stop_sound`
- Run tests: `uv run pytest`

## Code Review Process

1. Request reviewers when submitting a PR
2. Address review comments promptly
3. Re-request review after making changes
4. Ensure all conversations are resolved before merging

## Support & Questions

- **Issues**: Bug reports and feature requests
- **Security**: see [SECURITY.md](SECURITY.md)

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
