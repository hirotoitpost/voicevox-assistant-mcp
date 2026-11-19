# voicevox-assistant-mcp への貢献

[English](../CONTRIBUTING.md) | 日本語

貢献に関心を持っていただきありがとうございます。このドキュメントは voicevox-assistant-mcp への貢献の手引きです。

## 手順

1. **フォークとクローン**
   ```bash
   git clone https://github.com/YOUR_USERNAME/voicevox-assistant-mcp.git
   cd voicevox-assistant-mcp
   ```

2. **ブランチを作る**(名前の付け方は下記)
   ```bash
   git checkout -b feature/YOUR_DESCRIPTION
   ```

3. **変更する**: コード・テスト・ドキュメントを更新

4. **確認する**
   ```bash
   uv run ruff check .
   uv run pytest
   ```

5. **コミット**: [Conventional Commits](https://www.conventionalcommits.org/ja/) の形式
   ```bash
   git commit -m "feat: add new voice preset"
   ```

6. **プッシュしてプルリクエストを作る**

## 貢献の種類

- **バグ修正**: Issue を参照し、テストを付け、PR に修正内容を書く
- **新機能**: まず Issue で提案(プリセット・相槌・対応 OS など)。テストとドキュメントを付ける
- **ドキュメント**: 分かりやすさ・例・誤字・翻訳
- **コード品質**: リファクタリング・最適化・テストの充実

## 開発環境

### 必要なもの

- Windows(実際に再生するとき。テストはどの OS でも動く)
- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/)
- VOICEVOX(手で試すときだけ。テストはエンジンを差し替える)
- Git

### セットアップ

```bash
uv sync
uv run ruff check . && uv run pytest
```

手元のコードを Claude Code で試すとき:

```bash
claude mcp add --scope user voice-assistant -- uv --directory <クローンしたパス> run voicevox-assistant-mcp
```

フックは `uv --directory <クローンしたパス> run voicevox-assistant-hook` に向けます。

## コードの決まり

### Python

- **リンター・フォーマッター**: Ruff(`uv run ruff check .`、`uv run ruff format .`)
- **スタイル**: Ruff が守らせる PEP 8(1 行 130 字)
- **型ヒント**: すべてに付ける
- **localhost の外と通信しない**: 話す相手は VOICEVOX エンジンと自分のハブだけ

### フック

- Claude Code を止めない・失敗させない: 例外はすべて捕まえ、何も出力せず、すぐ 0 で終わる
- ツールの入力・プロンプト・ファイルの中身をどこにも送らない。送るのは選んだ定型文だけ

### 読み上げる文

- 文や説明文は声で読まれる: 短く自然に、記号を入れない

### Markdown

- できるだけ 1 行 100 字以内
- 英語版と日本語版(`docs/*_jp.md`)をそろえる

### 言語

- **主**: ドキュメントは英語。コードのコメントは日本語でもよい
- **副**: 主なドキュメントに日本語版

## ブランチとコミット

### ブランチ名

```
feature/[説明]    # 新機能
fix/[説明]        # バグ修正
docs/[説明]       # ドキュメント
refactor/[説明]   # リファクタリング
test/[説明]       # テスト
chore/[説明]      # ビルド・依存関係など
```

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/ja/) に従う:

```
{feat|fix|docs|style|refactor|test|chore}: 短い説明

必要なら本文に、なぜ・何を・どう確かめるか。
```

## PR のチェックリスト

- [ ] `main` に追いついている
- [ ] 衝突が無い
- [ ] テストが通る: `uv run pytest`
- [ ] リントが通る: `uv run ruff check .`
- [ ] ドキュメントを更新した(README、`docs/README_jp.md`、docstring)
- [ ] CHANGELOG.md の Unreleased を更新した
- [ ] コミットメッセージが Conventional Commits
- [ ] PR の説明に関連 Issue を書いた

## テスト

- 新しい機能には `tests/` にテストを書く
- テストは VOICEVOX エンジンやスピーカーを使わない: `engine.synthesize`、`engine.speakers`、
  `player.play_file`、`player.stop_sound` を差し替える
- 実行: `uv run pytest`

## レビュー

1. PR を出すときにレビュアーを指定する
2. 指摘には早めに対応する
3. 直したらもう一度レビューを頼む
4. すべての会話を解決してからマージする

## 質問・連絡

- **Issue**: バグ報告・機能の要望
- **セキュリティ**: [SECURITY_jp.md](SECURITY_jp.md)

## ライセンス

貢献したものは MIT ライセンスで公開されることに同意したものとします。
