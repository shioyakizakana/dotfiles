---
name: dotfiles-script-maintenance
description: dotfilesのBash・Python・Makefileやツール導入処理を修正するときに、既存の実装規約と再実行条件を確認する。
---

# Dotfiles Script Maintenance

- 実装する言語と処理に応じて[実装規約](references/script-rules.md)を読む。
- 初期構築・通常適用・日常更新を区別し、run_once_/run_onchange_/run_before_/run_after_の条件と順序を確認する。
- miseの管理一覧と既存の導入担当を維持し、npm経由の導入は対応可能なら`mise use -g npm@<tool>`を優先する。
- 利用者がMakefileから操作できるようにし、既存ターゲットの意味を維持して複雑な処理を専用スクリプトへ分離する。
- 冪等性・導入済み判定・失敗時の終了状態・一時ファイルの後始末を実装する。
- [テスト対応表](../dotfiles-test-runner/references/commands.md)から検証を選ぶ。
