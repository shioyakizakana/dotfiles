---
name: chezmoi-template-validation
description: dotfilesのchezmoiテンプレートや環境別除外を変更した際に、隔離環境とダミーデータで展開結果を検証する。
---

# Chezmoi Template Validation

リポジトリのAGENTS.mdに従い、テンプレートの評価方法と確認項目を選ぶ。

1. 作業ディレクトリからGitルートを確認し、対象ソースと既存の環境フラグを調べる。
2. 評価前に、秘密情報取得・外部コマンド実行・ファイル参照を伴う処理を確認する。
3. [検証手順](references/validation.md)に沿って、既存の隔離テストを再利用する。
4. テンプレートの評価結果と、展開後ファイルの構文・内容を分けて確認する。

結果には対象、使用したダミーデータ、検証結果、実機での未確認事項を記載する。
テスト全体の選択はdotfiles-test-runner、秘密情報の保持・受け渡しの評価はsecret-management-reviewが担当する。同じ検証の実行結果は共有する。
