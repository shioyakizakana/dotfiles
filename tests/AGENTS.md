# テストの規約

パスはリポジトリルート基準とする。

- 既存のBats・unittestと共通検証コマンドを再利用する。
- 環境依存処理と秘密情報はダミー・モック・隔離HOMEで検証する。
- 期待する現在の動作を検証し、実装の写しや削除済み機能の不在だけを検証しない。
- 実環境に副作用を与えるテストを自動実行しない。
- Go templateを残したファイルをShellCheck・shfmtへ直接渡さない。
- 対象・実行方法・skip基準は.agents/skills/dotfiles-test-runner/SKILL.mdを参照する。
