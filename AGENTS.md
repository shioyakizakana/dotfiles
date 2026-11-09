# AGENTS.md — dotfiles Repository

## 1. プロジェクト概要

このリポジトリは、chezmoiを使用して複数の開発環境におけるdotfiles、開発ツールの設定、初期構築スクリプトを一元管理するためのものである。

### 主なディレクトリ構成

```text
.
├── .agents/skills/                 # このリポジトリ専用スキルの正本
│   ├── chezmoi-template-validation/
│   ├── dotfiles-test-runner/
│   └── secret-management-review/
├── .github/workflows/check.yml     # GitHub Actionsの検証ジョブ
├── .chezmoiroot                     # source stateのルートにhomeを指定
├── .chezmoi.toml.tmpl               # chezmoi初期設定・環境フラグ・provider
├── AGENTS.md                       # このリポジトリの作業規約
├── README.md                       # 構築・適用・通常運用の案内
├── Makefile                        # 検証・確認・認証bootstrap・限定展開・適用
├── bootstrap/
│   ├── bootstrap-tools.sh          # Ubuntu・Termux向け基礎ツールの確認・導入
│   └── setup-proton-pass.sh        # 秘密情報の初期構築・認証
├── docs/
│   ├── reviews/dotfiles-audit.md   # 調査結果とDF項目の対応状況
│   ├── setup/proton-pass.md        # 認証構築・既存環境の手動確認手順
│   └── testing/
│       ├── checks.md              # ローカル・CI共通の検証手順
│       └── environment-matrix.md  # 環境別テストと実機確認の範囲
├── home/                           # ホームへ展開するsource state
│   ├── .chezmoiignore              # 環境別の導入対象・管理除外
│   ├── .chezmoiexternal.toml.tmpl   # プラグイン・外部スキルのGit取得
│   ├── .chezmoiscripts/            # APT・Homebrew・miseの適用後処理
│   ├── dot_agents/skills/          # 共通スキルと外部スキルへのリンク定義
│   ├── dot_codex/                  # 共通AGENTS.mdへのリンク定義
│   ├── dot_config/                 # nvim・mise・tmux・yaziなどの設定
│   │   └── ai-agents/AGENTS.md     # AIエージェント共通規約のソース
│   ├── dot_local/
│   │   ├── bin/                    # 認証ラッパー・更新・文章検査コマンド
│   │   └── share/textlint-ja/      # textlint設定・npm依存定義
│   ├── dot_zsh/                    # Zshの設定
│   ├── scripts/desk/              # デスクトップ向け補助スクリプト
│   ├── dot_Brewfile                # Homebrew Bundleの依存定義
│   ├── dot_gitconfig.tmpl          # Proton Pass参照を含むGit設定
│   ├── dot_bashrc                  # Bashの起動設定
│   └── dot_zshrc.tmpl              # Zshの起動設定
└── tests/                          # BatsとPython unittest
```

構造図は主要なファイルを抜粋している。プロジェクト専用スキルはルートの`.agents/skills/`、ホームへ展開する共通スキルは`home/dot_agents/skills/`で管理する。
`home/dot_codex/symlink_AGENTS.md.tmpl`は、展開先の`~/.config/ai-agents/AGENTS.md`を参照するリンク定義。プロジェクト専用スキルはCodexの探索場所へ直接置き、ホームへのリンクやchezmoiの除外設定は追加しない。

### 主な構成要素

- chezmoi：設定ファイルの管理・テンプレート展開
- mise：開発言語・CLIツール・ランタイムのバージョン管理
- Proton Pass CLI：秘密情報の取得
- age：秘密情報の暗号化
- Makefile：セットアップ・メンテナンス操作の入口
- Bash / Python：環境構築および補助スクリプト
- Bats / unittest：利用可能な範囲での自動テスト

### 主な対象環境

- Termux
- Termux + proot Ubuntu
- WSL2 Ubuntu
- その他のLinux環境

Windowsネイティブ環境への対応は将来的な拡張対象とし、現時点での必須要件とはしない。

## 2. 基本原則

グローバルAGENTS.mdの指示に加えて、以下を遵守する。

1. 既存の設計と運用方針を尊重する。
2. 変更前に目的・影響範囲・検証方法を説明する。
3. 最小限の変更で根本原因を解決する。
4. 明示的な依頼がない限り、大規模なリファクタリングを行わない。
5. 環境依存の処理を共通処理に混在させない。
6. 既存環境との後方互換性を重視する。
7. 不明な仕様や設計意図を推測だけで確定しない。
8. 新しい外部依存関係の追加は事前に提案し、承認を得る。

## 3. chezmoiの管理規則

### 3.1 Single Source of Truth

chezmoiのソースディレクトリを設定管理の正本とする。

- 原則としてソースディレクトリ内のファイルを編集する。
- ホームディレクトリに展開された設定ファイルを直接編集しない。
- `chezmoi add`、`chezmoi re-add`など、展開先の内容をソースへ取り込む操作は承認を得る。
- `dot_`、`private_`、`executable_`、`symlink_`、`.tmpl`などの命名規則を維持する。
- テンプレートを通常ファイルに変換する場合は理由と影響を説明する。

### 3.2 テンプレート

- chezmoiのGo template構文を維持する。
- `.chezmoi.toml.tmpl`で定義されたデータ構造を尊重する。
- machineType、linuxEnvなどの既存の環境判定変数を優先して使用する。
- 未定義のテンプレート変数を無条件に参照しない。
- 既存の変数名や列挙値を変更する場合は、参照箇所を確認する。
- テンプレート内の秘密情報をログや標準出力に表示しない。

### 3.3 適用操作

以下はユーザーの明示的な承認なしに実行しない。

- `chezmoi apply`
- `chezmoi update`
- `chezmoi init`
- `chezmoi re-add`
- `chezmoi apply`を内部で実行するMakeターゲット
- `chezmoi apply`を伴う自動化スクリプト

`chezmoi diff`や`chezmoi status`は、秘密情報の露出や副作用がないことを確認した範囲で使用する。

## 4. マルチ環境対応

環境ごとの違いを明示的に扱う。

### 4.1 環境判定

- 既存のmachineTypeおよびlinuxEnvを使用する。
- 新しい環境識別子を独断で追加しない。
- OS判定と実行環境判定を混同しない。
- Termux、proot、WSL2、ネイティブLinuxの差異を考慮する。

### 4.2 互換性

- systemdが存在することを前提にしない。
- Secret ServiceやOSのkeyringが利用できることを前提にしない。
- Linux環境で動作するスクリプトを優先する。
- Bash専用構文を使用する場合はシバンを適切に設定する。
- GNU固有のコマンドオプションを使用する場合は対象環境を確認する。
- 特定環境でのみ必要な処理は条件分岐または専用スクリプトに分離する。

## 5. 秘密情報の管理

秘密情報の保護を最優先する。

### 5.1 保護対象

以下の情報を読み取ったり、出力・記録したりしない。

- Proton PassのPAT
- ageの秘密鍵
- 暗号化前の秘密情報
- Proton Passの暗号化キー
- 認証トークンやパスワード
- 秘密情報を含む環境変数の値
- 復号済みの設定ファイル

これらの内容確認が必要な場合は、実データを使用せず、ダミーデータまたはモックを優先する。

### 5.2 Proton Pass CLI

- 既存のProton Pass CLIラッパーを尊重する。
- PAT方式とkeyring方式の既存の切替設計を維持する。
- 秘密情報を恒久的な環境変数に保存しない。
- 認証方式の変更は事前承認を必要とする。
- 認証情報の初期化、更新、削除、ログアウトを自動実行しない。

### 5.3 age

- age秘密鍵を読み取らない。
- 暗号化ファイルの復号は原則として行わない。
- 秘密鍵や復号結果をGit管理対象に追加しない。
- 暗号化方式や保存場所の変更は事前に提案する。

## 6. スクリプト実装規約

### 6.1 Bash

- 原則として `#!/usr/bin/env bash` を使用する。
- 原則として `set -euo pipefail` を使用する。
- 変数展開時は適切に引用符を付ける。
- 外部コマンドの存在確認を行う。
- エラー時の終了状態を適切に扱う。
- 一時ファイルは安全に作成し、終了時に削除する。
- cleanup処理は正常終了・異常終了の両方を考慮する。
- 既存の関数名・定数名・ログ出力規則を尊重する。

### 6.2 Python

- 既存の対応Pythonバージョンを維持する。
- パス操作には原則としてpathlibを使用する。
- 標準ライブラリで対応可能な場合は外部依存を増やさない。
- テストには既存のunittestを優先する。
- 秘密情報を例外メッセージに含めない。

### 6.3 mise

- 開発ツールの導入・バージョン管理にはmiseを優先する。
- mise管理対象のツールを無断で別のパッケージマネージャーに移行しない。
- npm経由のツールは、対応可能な場合 `mise use -g npm@<tool>` を優先する。
- バージョン更新による互換性への影響を確認する。
- グローバルツールのインストールや更新は承認後に実行する。

### 7. Makefileとセットアップ処理

- Makefileは利用者向けの操作入口とする。
- 複雑な処理は可能な限り専用スクリプトへ分離する。
- 既存ターゲットの名前と意味を維持する。
- 副作用を持つターゲットは実行前に内容を確認する。
- 初期構築と日常的な更新処理を区別する。
- 冪等性を意識し、再実行時の破壊的動作を避ける。
- `run_once_`、`run_onchange_`、`run_after_`などの実行条件と順序を考慮する。
- ネットワークアクセス、パッケージ更新、インストールを伴う処理は承認を得る。

## 8. 検証とテスト

変更内容に応じて、実行可能で安全な検証を選択する。

- 既存のテストがあれば優先して実行する。
- バグ修正時は可能な限り再現テストを追加する。
- OSや環境に依存する処理はモックを活用する。
- 実環境に副作用を与えるテストは自動実行しない。
- 秘密情報を含まない範囲でテンプレートを検証する。
- Go template構文が残るファイルを、そのままShellCheckやshfmtに渡さない。
- 実環境への適用前に、安全性を確認した範囲で差分を確認する。
- 成功・失敗・skip・未実施を区別し、未実施やskipの理由を報告する。

### 8.1 プロジェクト固有スキル

具体的な手順とコマンドは、作業内容に合うスキルを参照する。

| 用途 | スキル |
| --- | --- |
| chezmoiテンプレートと環境別対象の検証 | [chezmoi-template-validation](.agents/skills/chezmoi-template-validation/SKILL.md) |
| 既存テストと静的検証の選択・実行 | [dotfiles-test-runner](.agents/skills/dotfiles-test-runner/SKILL.md) |
| 秘密情報管理の静的レビュー | [secret-management-review](.agents/skills/secret-management-review/SKILL.md) |

スキルはこの文書の作業規約を補足する。スキルの選択や参照は、操作の承認や依頼範囲の拡大を意味しない。

## 9. Git運用

- 作業開始前に変更状態を確認する。
- ユーザーの未コミット変更を保持する。
- 無関係なファイルを変更しない。
- `git reset --hard`や`git clean -fd`などの破壊的操作を行わない。
- `git commit`、`git push`は明示的な指示がある場合のみ実行する。
- 秘密情報をコミットしない。
- コミット履歴の書き換えは承認を必要とする。

## 10. 作業手順

原則として以下の順序で進める。

1. 対象ファイルと関連ファイルを確認する。
2. 既存の設計・依存関係・影響範囲を調査する。
3. 変更計画を提示する。
4. 必要な承認を得て実装する。
5. 静的検証およびテストを実施する。
6. 差分を確認する。
7. 変更内容・検証結果・残る注意点を報告する。

調査のみの依頼ではファイルを変更しない。

## 11. 作業完了時の報告

報告には以下を含める。

- 変更の目的
- 変更したファイル
- 主な変更内容
- 実施したテストと結果
- 実施できなかった検証
- 環境依存の注意点
- ユーザーが実行すべき適用操作

実施していないテストを成功したと報告しない。

## 12. 禁止事項

明示的な承認なしに以下を行わない。

- 実環境への設定適用
- パッケージのインストール・更新・削除
- 秘密情報の取得・復号・表示
- 認証情報の更新・削除
- 既存設定の大規模な置換
- リポジトリ外のファイル変更
- Git履歴の破壊的操作
- 外部サービスへの秘密情報の送信

安全性と既存環境の維持を優先し、不明点があれば実行前に確認する。
