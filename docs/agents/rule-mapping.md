# 規約の移動対応と字数管理

2026-11-12の再編前の各指示を引用し、現在の適用先を記録する。以下の引用は比較用の履歴であり、実作業では現行のAGENTS.mdと該当スキルに従う。

## 配置

- プロジェクト規則はルート、home、bootstrap、testsのAGENTS.mdに置く。
- 作業手順は既存3スキルとdotfiles-script-maintenance、共通のcoding-workflowに置く。
- グローバル規約のソースはhome/dot_config/ai-agents/AGENTS.mdとし、リンクは維持する。
- 構成図と責務の説明はREADME.mdのディレクトリ構成、環境差はdocs/testing/environment-matrix.mdを参照する。
- 共通スキルの実体はhome/dot_agents/skills、プロジェクト専用スキルは.agents/skillsで管理する。

## 指示の対応

Pは旧プロジェクト規約、Gは旧共通規約を表す。移動先のスキルは、下記の配置表に従って読む。

| ID | 旧節 | 元の指示（履歴） | 適用先 |
| --- | --- | --- | --- |
| P001 | 1. プロジェクト概要 | chezmoi：設定ファイルの管理・テンプレート展開 | README.md・docs/testing/environment-matrix.md |
| P002 | 1. プロジェクト概要 | mise：開発言語・CLIツール・ランタイムのバージョン管理 | README.md・docs/testing/environment-matrix.md |
| P003 | 1. プロジェクト概要 | Proton Pass CLI：秘密情報の取得 | README.md・docs/testing/environment-matrix.md |
| P004 | 1. プロジェクト概要 | age：秘密情報の暗号化 | README.md・docs/testing/environment-matrix.md |
| P005 | 1. プロジェクト概要 | Makefile：セットアップ・メンテナンス操作の入口 | README.md・docs/testing/environment-matrix.md |
| P006 | 1. プロジェクト概要 | Bash / Python：環境構築および補助スクリプト | README.md・docs/testing/environment-matrix.md |
| P007 | 1. プロジェクト概要 | Bats / unittest：利用可能な範囲での自動テスト | README.md・docs/testing/environment-matrix.md |
| P008 | 1. プロジェクト概要 | Termux | README.md・docs/testing/environment-matrix.md |
| P009 | 1. プロジェクト概要 | Termux + proot Ubuntu | README.md・docs/testing/environment-matrix.md |
| P010 | 1. プロジェクト概要 | WSL2 Ubuntu | README.md・docs/testing/environment-matrix.md |
| P011 | 1. プロジェクト概要 | その他のLinux環境 | README.md・docs/testing/environment-matrix.md |
| P012 | 2. 基本原則 | 既存の設計と運用方針を尊重する。 | 共通規約・ルートAGENTS.md |
| P013 | 2. 基本原則 | 変更前に目的・影響範囲・検証方法を説明する。 | 共通規約・ルートAGENTS.md |
| P014 | 2. 基本原則 | 最小限の変更で根本原因を解決する。 | 共通規約・ルートAGENTS.md |
| P015 | 2. 基本原則 | 明示的な依頼がない限り、大規模なリファクタリングを行わない。 | 共通規約・ルートAGENTS.md |
| P016 | 2. 基本原則 | 環境依存の処理を共通処理に混在させない。 | 共通規約・ルートAGENTS.md |
| P017 | 2. 基本原則 | 既存環境との後方互換性を重視する。 | 共通規約・ルートAGENTS.md |
| P018 | 2. 基本原則 | 不明な仕様や設計意図を推測だけで確定しない。 | 共通規約・ルートAGENTS.md |
| P019 | 2. 基本原則 | 新しい外部依存関係の追加は事前に提案し、承認を得る。 | 共通規約・ルートAGENTS.md |
| P020 | 3.1 Single Source of Truth | 原則としてソースディレクトリ内のファイルを編集する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P021 | 3.1 Single Source of Truth | ホームディレクトリに展開された設定ファイルを直接編集しない。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P022 | 3.1 Single Source of Truth | `chezmoi add`、`chezmoi re-add`など、展開先の内容をソースへ取り込む操作は承認を得る。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P023 | 3.1 Single Source of Truth | `dot_`、`private_`、`executable_`、`symlink_`、`.tmpl`などの命名規則を維持する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P024 | 3.1 Single Source of Truth | テンプレートを通常ファイルに変換する場合は理由と影響を説明する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P025 | 3.2 テンプレート | chezmoiのGo template構文を維持する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P026 | 3.2 テンプレート | `.chezmoi.toml.tmpl`で定義されたデータ構造を尊重する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P027 | 3.2 テンプレート | machineType、linuxEnvなどの既存の環境判定変数を優先して使用する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P028 | 3.2 テンプレート | 未定義のテンプレート変数を無条件に参照しない。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P029 | 3.2 テンプレート | 既存の変数名や列挙値を変更する場合は、参照箇所を確認する。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P030 | 3.2 テンプレート | テンプレート内の秘密情報をログや標準出力に表示しない。 | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P031 | 3.3 適用操作 | `chezmoi apply` | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P032 | 3.3 適用操作 | `chezmoi update` | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P033 | 3.3 適用操作 | `chezmoi init` | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P034 | 3.3 適用操作 | `chezmoi re-add` | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P035 | 3.3 適用操作 | `chezmoi apply`を内部で実行するMakeターゲット | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P036 | 3.3 適用操作 | `chezmoi apply`を伴う自動化スクリプト | ルートAGENTS.md・home/AGENTS.md・chezmoi-template-validation |
| P037 | 4.1 環境判定 | 既存のmachineTypeおよびlinuxEnvを使用する。 | home/AGENTS.md |
| P038 | 4.1 環境判定 | 新しい環境識別子を独断で追加しない。 | home/AGENTS.md |
| P039 | 4.1 環境判定 | OS判定と実行環境判定を混同しない。 | home/AGENTS.md |
| P040 | 4.1 環境判定 | Termux、proot、WSL2、ネイティブLinuxの差異を考慮する。 | home/AGENTS.md |
| P041 | 4.2 互換性 | systemdが存在することを前提にしない。 | home/AGENTS.md |
| P042 | 4.2 互換性 | Secret ServiceやOSのkeyringが利用できることを前提にしない。 | home/AGENTS.md |
| P043 | 4.2 互換性 | Linux環境で動作するスクリプトを優先する。 | home/AGENTS.md |
| P044 | 4.2 互換性 | Bash専用構文を使用する場合はシバンを適切に設定する。 | home/AGENTS.md |
| P045 | 4.2 互換性 | GNU固有のコマンドオプションを使用する場合は対象環境を確認する。 | home/AGENTS.md |
| P046 | 4.2 互換性 | 特定環境でのみ必要な処理は条件分岐または専用スクリプトに分離する。 | home/AGENTS.md |
| P047 | 5.1 保護対象 | Proton PassのPAT | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P048 | 5.1 保護対象 | ageの秘密鍵 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P049 | 5.1 保護対象 | 暗号化前の秘密情報 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P050 | 5.1 保護対象 | Proton Passの暗号化キー | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P051 | 5.1 保護対象 | 認証トークンやパスワード | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P052 | 5.1 保護対象 | 秘密情報を含む環境変数の値 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P053 | 5.1 保護対象 | 復号済みの設定ファイル | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P054 | 5.2 Proton Pass CLI | 既存のProton Pass CLIラッパーを尊重する。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P055 | 5.2 Proton Pass CLI | PAT方式とkeyring方式の既存の切替設計を維持する。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P056 | 5.2 Proton Pass CLI | 秘密情報を恒久的な環境変数に保存しない。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P057 | 5.2 Proton Pass CLI | 認証方式の変更は事前承認を必要とする。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P058 | 5.2 Proton Pass CLI | 認証情報の初期化、更新、削除、ログアウトを自動実行しない。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P059 | 5.3 age | age秘密鍵を読み取らない。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P060 | 5.3 age | 暗号化ファイルの復号は原則として行わない。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P061 | 5.3 age | 秘密鍵や復号結果をGit管理対象に追加しない。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P062 | 5.3 age | 暗号化方式や保存場所の変更は事前に提案する。 | ルートAGENTS.md・home/AGENTS.md・secret-management-review |
| P063 | 6.1 Bash | 原則として `#!/usr/bin/env bash` を使用する。 | dotfiles-script-maintenance |
| P064 | 6.1 Bash | 原則として `set -euo pipefail` を使用する。 | dotfiles-script-maintenance |
| P065 | 6.1 Bash | 変数展開時は適切に引用符を付ける。 | dotfiles-script-maintenance |
| P066 | 6.1 Bash | 外部コマンドの存在確認を行う。 | dotfiles-script-maintenance |
| P067 | 6.1 Bash | エラー時の終了状態を適切に扱う。 | dotfiles-script-maintenance |
| P068 | 6.1 Bash | 一時ファイルは安全に作成し、終了時に削除する。 | dotfiles-script-maintenance |
| P069 | 6.1 Bash | cleanup処理は正常終了・異常終了の両方を考慮する。 | dotfiles-script-maintenance |
| P070 | 6.1 Bash | 既存の関数名・定数名・ログ出力規則を尊重する。 | dotfiles-script-maintenance |
| P071 | 6.2 Python | 既存の対応Pythonバージョンを維持する。 | dotfiles-script-maintenance |
| P072 | 6.2 Python | パス操作には原則としてpathlibを使用する。 | dotfiles-script-maintenance |
| P073 | 6.2 Python | 標準ライブラリで対応可能な場合は外部依存を増やさない。 | dotfiles-script-maintenance |
| P074 | 6.2 Python | テストには既存のunittestを優先する。 | dotfiles-script-maintenance |
| P075 | 6.2 Python | 秘密情報を例外メッセージに含めない。 | dotfiles-script-maintenance |
| P076 | 6.3 mise | 開発ツールの導入・バージョン管理にはmiseを優先する。 | dotfiles-script-maintenance |
| P077 | 6.3 mise | mise管理対象のツールを無断で別のパッケージマネージャーに移行しない。 | dotfiles-script-maintenance |
| P078 | 6.3 mise | npm経由のツールは、対応可能な場合 `mise use -g npm@<tool>` を優先する。 | dotfiles-script-maintenance |
| P079 | 6.3 mise | バージョン更新による互換性への影響を確認する。 | dotfiles-script-maintenance |
| P080 | 6.3 mise | グローバルツールのインストールや更新は承認後に実行する。 | dotfiles-script-maintenance |
| P081 | 7. Makefileとセットアップ処理 | Makefileは利用者向けの操作入口とする。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P082 | 7. Makefileとセットアップ処理 | 複雑な処理は可能な限り専用スクリプトへ分離する。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P083 | 7. Makefileとセットアップ処理 | 既存ターゲットの名前と意味を維持する。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P084 | 7. Makefileとセットアップ処理 | 副作用を持つターゲットは実行前に内容を確認する。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P085 | 7. Makefileとセットアップ処理 | 初期構築と日常的な更新処理を区別する。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P086 | 7. Makefileとセットアップ処理 | 冪等性を意識し、再実行時の破壊的動作を避ける。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P087 | 7. Makefileとセットアップ処理 | `run_once_`、`run_onchange_`、`run_after_`などの実行条件と順序を考慮する。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P088 | 7. Makefileとセットアップ処理 | ネットワークアクセス、パッケージ更新、インストールを伴う処理は承認を得る。 | bootstrap/AGENTS.md・dotfiles-script-maintenance |
| P089 | 8. 検証とテスト | 既存のテストがあれば優先して実行する。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P090 | 8. 検証とテスト | バグ修正時は可能な限り再現テストを追加する。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P091 | 8. 検証とテスト | OSや環境に依存する処理はモックを活用する。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P092 | 8. 検証とテスト | 実環境に副作用を与えるテストは自動実行しない。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P093 | 8. 検証とテスト | 秘密情報を含まない範囲でテンプレートを検証する。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P094 | 8. 検証とテスト | Go template構文が残るファイルを、そのままShellCheckやshfmtに渡さない。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P095 | 8. 検証とテスト | 実環境への適用前に、安全性を確認した範囲で差分を確認する。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P096 | 8. 検証とテスト | 成功・失敗・skip・未実施を区別し、未実施やskipの理由を報告する。 | tests/AGENTS.md・dotfiles-test-runner・chezmoi-template-validation |
| P097 | 9. Git運用 | 作業開始前に変更状態を確認する。 | ルートAGENTS.md・共通規約 |
| P098 | 9. Git運用 | ユーザーの未コミット変更を保持する。 | ルートAGENTS.md・共通規約 |
| P099 | 9. Git運用 | 無関係なファイルを変更しない。 | ルートAGENTS.md・共通規約 |
| P100 | 9. Git運用 | `git reset --hard`や`git clean -fd`などの破壊的操作を行わない。 | ルートAGENTS.md・共通規約 |
| P101 | 9. Git運用 | `git commit`、`git push`は明示的な指示がある場合のみ実行する。 | ルートAGENTS.md・共通規約 |
| P102 | 9. Git運用 | 秘密情報をコミットしない。 | ルートAGENTS.md・共通規約 |
| P103 | 9. Git運用 | コミット履歴の書き換えは承認を必要とする。 | ルートAGENTS.md・共通規約 |
| P104 | 10. 作業手順 | 対象ファイルと関連ファイルを確認する。 | 共通規約・coding-workflow |
| P105 | 10. 作業手順 | 既存の設計・依存関係・影響範囲を調査する。 | 共通規約・coding-workflow |
| P106 | 10. 作業手順 | 変更計画を提示する。 | 共通規約・coding-workflow |
| P107 | 10. 作業手順 | 必要な承認を得て実装する。 | 共通規約・coding-workflow |
| P108 | 10. 作業手順 | 静的検証およびテストを実施する。 | 共通規約・coding-workflow |
| P109 | 10. 作業手順 | 差分を確認する。 | 共通規約・coding-workflow |
| P110 | 10. 作業手順 | 変更内容・検証結果・残る注意点を報告する。 | 共通規約・coding-workflow |
| P111 | 11. 作業完了時の報告 | 変更の目的 | ルートAGENTS.md・coding-workflow |
| P112 | 11. 作業完了時の報告 | 変更したファイル | ルートAGENTS.md・coding-workflow |
| P113 | 11. 作業完了時の報告 | 主な変更内容 | ルートAGENTS.md・coding-workflow |
| P114 | 11. 作業完了時の報告 | 実施したテストと結果 | ルートAGENTS.md・coding-workflow |
| P115 | 11. 作業完了時の報告 | 実施できなかった検証 | ルートAGENTS.md・coding-workflow |
| P116 | 11. 作業完了時の報告 | 環境依存の注意点 | ルートAGENTS.md・coding-workflow |
| P117 | 11. 作業完了時の報告 | ユーザーが実行すべき適用操作 | ルートAGENTS.md・coding-workflow |
| P118 | 12. 禁止事項 | 実環境への設定適用 | ルートAGENTS.md |
| P119 | 12. 禁止事項 | パッケージのインストール・更新・削除 | ルートAGENTS.md |
| P120 | 12. 禁止事項 | 秘密情報の取得・復号・表示 | ルートAGENTS.md |
| P121 | 12. 禁止事項 | 認証情報の更新・削除 | ルートAGENTS.md |
| P122 | 12. 禁止事項 | 既存設定の大規模な置換 | ルートAGENTS.md |
| P123 | 12. 禁止事項 | リポジトリ外のファイル変更 | ルートAGENTS.md |
| P124 | 12. 禁止事項 | Git履歴の破壊的操作 | ルートAGENTS.md |
| P125 | 12. 禁止事項 | 外部サービスへの秘密情報の送信 | ルートAGENTS.md |
| G001 | 1. 基本方針 | 常に日本語で応答する。ファイル名、関数名、コマンド名、API名、識別子、エラーメッセージなどは無理に翻訳しない。 | 共通規約・coding-workflow |
| G002 | 1. 基本方針 | 正確性、安全性、既存動作の維持を優先する。 | 共通規約・coding-workflow |
| G003 | 1. 基本方針 | まず最も単純な解決策を検討し、要求を満たす最小限の変更を選ぶ。 | 共通規約・coding-workflow |
| G004 | 1. 基本方針 | 一時しのぎのパッチより根本原因の修正を優先する。ただし原因を断定できない場合は推測を明示する。 | 共通規約・coding-workflow |
| G005 | 1. 基本方針 | 既存の設計、命名、スタイル、公開インターフェース、互換性要件を尊重し、依頼と無関係な変更を加えない。 | 共通規約・coding-workflow |
| G006 | 1. 基本方針 | 単純な修正を過剰に抽象化・汎用化しない。新しい設計パターンや依存関係を導入する前に既存の仕組みで足りるか確認する。 | 共通規約・coding-workflow |
| G007 | 2. 共通指示ファイルの管理 | グローバルな開発規約は共通の`AGENTS.md`を唯一の正本として管理する。 | 共通規約 |
| G008 | 2. 共通指示ファイルの管理 | エージェント固有の指示ファイルがシンボリックリンクの場合、リンクを独立した通常ファイルに置き換えない。 | 共通規約 |
| G009 | 2. 共通指示ファイルの管理 | 共通規約の変更が必要な場合は、変更案と理由を提示し、ユーザーの承認を得る。 | 共通規約 |
| G010 | 2. 共通指示ファイルの管理 | 特定のエージェントにしか適用できない指示は、原則として共通規約に追加しない。 | 共通規約 |
| G011 | 2. 共通指示ファイルの管理 | chezmoiで管理されているファイルを変更する場合は、chezmoiのソースと展開先の関係を確認し、管理状態を壊さない。 | 共通規約 |
| G012 | 3. 指示の適用範囲と承認 | 現在のユーザー指示とプロジェクト固有の規約を確認し、この文書は共通の既定方針として扱う。矛盾がある場合は適用範囲と優先関係を明確にする。 | 共通規約・ルートAGENTS.md |
| G013 | 3. 指示の適用範囲と承認 | 明示的に依頼された実装・修正は、指定範囲の作業に着手する承認があるものとみなす。 | 共通規約・ルートAGENTS.md |
| G014 | 3. 指示の適用範囲と承認 | 設計案の提示、レビュー、調査のみを依頼された場合は、無断で実装しない。 | 共通規約・ルートAGENTS.md |
| G015 | 3. 指示の適用範囲と承認 | 大きな設計変更、公開仕様の変更、依頼範囲の拡大、複雑なリファクタリングでは、最小構成の案と影響を説明し、実装前に承認を得る。 | 共通規約・ルートAGENTS.md |
| G016 | 3. 指示の適用範囲と承認 | 削除、上書き、既存変更の破棄、外部公開、デプロイ、pushなど重大または取り消し困難な操作は、明示的な許可なく行わない。 | 共通規約・ルートAGENTS.md |
| G017 | 3. 指示の適用範囲と承認 | ユーザーの未コミット変更や他者の作業を上書きしない。許可なくコミットしない。 | 共通規約・ルートAGENTS.md |
| G018 | 4. 調査・仕様・計画 | 変更前に関連コード、既存テスト、設定、ドキュメント、Gitの変更状況を必要な範囲で確認する。 | implementation-planning・共通規約・coding-workflow |
| G019 | 4. 調査・仕様・計画 | 不明な仕様を勝手に補完しない。既存実装から推測できる内容と未確定事項を区別する。 | implementation-planning・共通規約・coding-workflow |
| G020 | 4. 調査・仕様・計画 | 3ステップ以上の作業、複数ファイルにまたがる重要な変更、設計判断を伴う作業では、実装前に簡潔な計画を提示する。 | implementation-planning・共通規約・coding-workflow |
| G021 | 4. 調査・仕様・計画 | 計画には目的、仕様・受け入れ条件、対象範囲、実装手順、検証方法、主要なリスクを含める。 | implementation-planning・共通規約・coding-workflow |
| G022 | 4. 調査・仕様・計画 | 単純で明白な変更では長い仕様書や形式的な計画を作らず、目的と期待結果を短く確認する。 | implementation-planning・共通規約・coding-workflow |
| G023 | 4. 調査・仕様・計画 | 進行中に前提が崩れた、調査結果が想定と異なった、重大な副作用が見つかった場合は、作業を止めて計画を見直す。必要に応じて承認を取り直す。 | implementation-planning・共通規約・coding-workflow |
| G024 | 4. 調査・仕様・計画 | 作業の区切りごとに、何を変更したか、次に何を検証するかを簡潔に共有する。逐一の些細な操作報告は不要。 | implementation-planning・共通規約・coding-workflow |
| G025 | 5. 実装・編集 | 変更は必要な箇所に限定し、既存機能と互換性への影響を最小化する。 | 共通規約・coding-workflow/references/implementation.md |
| G026 | 5. 実装・編集 | 症状だけを隠さず、ログ、失敗したテスト、再現手順、コードの振る舞いから原因を調べる。 | 共通規約・coding-workflow/references/implementation.md |
| G027 | 5. 実装・編集 | バグ修正を明示的に依頼された場合、承認済みの範囲内では追加の細かな指示を待たず調査・修正・検証を進める。 | 共通規約・coding-workflow/references/implementation.md |
| G028 | 5. 実装・編集 | ワークアラウンドが不可避な場合は理由、制約、解消条件を説明し、黙って恒久解決と扱わない。 | 共通規約・coding-workflow/references/implementation.md |
| G029 | 5. 実装・編集 | 関連のない整形、命名変更、ファイル移動、依存関係更新を混ぜない。 | 共通規約・coding-workflow/references/implementation.md |
| G030 | 5. 実装・編集 | 編集方法は差分の大きさと安全性で選ぶ。多数の細かな編集より、一括・範囲単位の編集を優先する。 | 共通規約・coding-workflow/references/implementation.md |
| G031 | 5. 実装・編集 | 全体の書き換えは、翻訳や大規模な機械的変更などで明らかに安全かつ効率的な場合に限定し、既存内容・書式・改行コード・エンコーディングの保持を確認する。 | 共通規約・coding-workflow/references/implementation.md |
| G032 | 5. 実装・編集 | ユーザーに不要な作業の切り替えを要求せず、利用可能な環境で完結できる作業は自ら実施する。権限や環境上の制約があれば明示する。 | 共通規約・coding-workflow/references/implementation.md |
| G033 | 6. テスト・検証・完了条件 | 実装計画には必ず検証方法を含める。変更内容に応じて再現テスト、単体テスト、統合テスト、静的解析、ビルド、ログ確認を選ぶ。 | coding-workflow/references/verification.md・共通規約 |
| G034 | 6. テスト・検証・完了条件 | 可能なら修正前に不具合を再現し、修正後に同じ条件で改善を確認する。 | coding-workflow/references/verification.md・共通規約 |
| G035 | 6. テスト・検証・完了条件 | テストコードは期待される現在の振る舞い（What）を表し、実装内部や変更前との差分、削除済み機能の不在だけに依存するテストは避ける。 | coding-workflow/references/verification.md・共通規約 |
| G036 | 6. テスト・検証・完了条件 | 既存CIの失敗が今回の変更と関連する場合は原因を調査し、承認済みの範囲内で修正する。無関係な失敗は根拠とともに報告し、無断で修正範囲を広げない。 | coding-workflow/references/verification.md・共通規約 |
| G037 | 6. テスト・検証・完了条件 | テストを通すためだけにテストを弱めたり、検証を削除したりしない。 | coding-workflow/references/verification.md・共通規約 |
| G038 | 6. テスト・検証・完了条件 | タスクの完了を宣言する前に、実行した検証、その結果、未実施の検証、残るリスクを明記する。 | coding-workflow/references/verification.md・共通規約 |
| G039 | 6. テスト・検証・完了条件 | 検証できない場合は完了や成功を断定しない。実行できなかった理由と代替確認方法を示す。 | coding-workflow/references/verification.md・共通規約 |
| G040 | 7. コード・コメント・コミット | コード自体は処理の仕組み（How）が読み取れるように、分かりやすい名前と単純な構造で記述する。 | coding-workflow・coding-workflow/references/implementation.md |
| G041 | 7. コード・コメント・コミット | テストでは期待する振る舞い（What）を明示する。 | coding-workflow・coding-workflow/references/implementation.md |
| G042 | 7. コード・コメント・コミット | コメントはコードを読めば分かる処理の逐語説明ではなく、判断理由、制約、採用しなかった方法とその理由（Why / Why not）を必要に応じて残す。 | coding-workflow・coding-workflow/references/implementation.md |
| G043 | 7. コード・コメント・コミット | コメントやドキュメントは原則日本語とし、識別子や仕様上の固有名詞は維持する。ただしプロジェクト固有の規約があれば従う。 | coding-workflow・coding-workflow/references/implementation.md |
| G044 | 7. コード・コメント・コミット | コミットが依頼・許可された場合、コミットメッセージには変更の目的と理由（Why）を簡潔に記す。 | coding-workflow・coding-workflow/references/implementation.md |
| G045 | 8. 学習・ルール改善 | ユーザーからの修正や指摘は、その場の回答・実装へ反映する。 | 共通規約 |
| G046 | 8. 学習・ルール改善 | 同じ種類の誤りを防ぐための再利用可能な教訓が得られた場合、適切なルール追加・変更を提案する。 | 共通規約 |
| G047 | 8. 学習・ルール改善 | グローバル規約には全プロジェクト共通の原則だけを置き、言語やリポジトリ固有の教訓は各プロジェクトのAGENTS.mdや関連ドキュメントに置く。 | 共通規約 |
| G048 | 8. 学習・ルール改善 | ルールファイルを変更する際は、ユーザーの依頼・承認と既存内容の確認を必要とする。失敗のたびに無条件でルールを追加しない。 | 共通規約 |
| G049 | 8. 学習・ルール改善 | 同じ失敗が繰り返された場合は、既存ルールが曖昧・矛盾・過剰・実行不能でないか見直し、必要なら検証方法も改善する。 | 共通規約 |
| G050 | 8. 学習・ルール改善 | 不要になったルールは削除または統合し、指示の肥大化を避ける。 | 共通規約 |
| G051 | 9. 作業結果の報告 | 最後に、変更の要点、影響したファイル、検証結果、未解決事項を簡潔にまとめる。 | 共通規約・coding-workflow |
| G052 | 9. 作業結果の報告 | エラーや失敗について説明する際は、確認できたログ・テスト結果と推測を区別する。 | 共通規約・coding-workflow |
| G053 | 9. 作業結果の報告 | 実行していないコマンドや未確認のテストを実施済みとして報告しない。 | 共通規約・coding-workflow |
| G054 | 10. 日本語文書の品質管理 | ユーザーへの応答および文書の作成は、原則として自然で読みやすい日本語を使用する。 | 共通規約・coding-workflow/references/verification.md |
| G055 | 10. 日本語文書の品質管理 | 日本語の文書を新規作成・推敲する場合は、natural-japaneseスキルの適用を優先する。 | 共通規約・coding-workflow/references/verification.md |
| G056 | 10. 日本語文書の品質管理 | Markdown等の日本語文書を作成・変更した場合は、可能な範囲でnatural-japaneseの検査スクリプトおよびtextlint-jaによる検査を実施する。 | 共通規約・coding-workflow/references/verification.md |
| G057 | 10. 日本語文書の品質管理 | textlint-jaはユーザー共通の文章検査コマンドとして利用できる。 | 共通規約・coding-workflow/references/verification.md |
| G058 | 10. 日本語文書の品質管理 | プロジェクトに独自のtextlint設定や検査コマンドが存在する場合は、そちらを優先する。 | 共通規約・coding-workflow/references/verification.md |
| G059 | 10. 日本語文書の品質管理 | リンターの指摘は機械的に置換せず、文脈・専門用語・固有名詞を考慮して修正の要否を判断する。 | 共通規約・coding-workflow/references/verification.md |
| G060 | 10. 日本語文書の品質管理 | コード、識別子、コマンド、API名、引用文などは、文章の自然さを優先して意味を変更しない。 | 共通規約・coding-workflow/references/verification.md |
| G061 | 10. 日本語文書の品質管理 | リンターが実行できない場合は、実行できなかった理由を報告する。 | 共通規約・coding-workflow/references/verification.md |
| G062 | 10. 日本語文書の品質管理 | 短い対話応答やコード中心の変更では、不要な検査を省略してよい。 | 共通規約・coding-workflow/references/verification.md |

## スキルの配置先

| 略記 | ソース |
| --- | --- |
| coding-workflow | home/dot_agents/skills/coding-workflow/SKILL.md |
| implementation-planning | home/dot_agents/skills/implementation-planning/SKILL.md |
| dotfiles-script-maintenance | .agents/skills/dotfiles-script-maintenance/SKILL.md |
| chezmoi-template-validation | .agents/skills/chezmoi-template-validation/SKILL.md |
| dotfiles-test-runner | .agents/skills/dotfiles-test-runner/SKILL.md |
| secret-management-review | .agents/skills/secret-management-review/SKILL.md |

スキル参照は操作の承認を意味しない。Bash専用構文のシバン、外部コマンド確認、Pythonの対応版と標準ライブラリ、npm・miseの選択、テスト結果の区別は移動先でも維持する。
旧規約の構造図・ツール列挙・対象環境・リンク生成説明はREADMEの既存説明へ集約し、安全規則と承認条件はルートと共通規約へ集約する。
旧プロジェクト8.1節のスキル表は既存3スキルへの案内として維持し、手順の詳細は各referencesに残す。
