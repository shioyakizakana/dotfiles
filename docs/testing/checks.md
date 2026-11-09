# ローカルとCIで共通の検証

リポジトリのルートで`make check`を実行する。静的検証、Python unittest、Batsの順に実行し、途中で失敗した場合は停止する。検証ターゲットは認証用の`require`や設定適用ターゲットに依存しない。

## コマンドと必要なツール

| コマンド | 内容 | 必須ツール |
| --- | --- | --- |
| `make check` | 静的検証と全テスト | 以下の全ツール |
| `make test` | unittestとBats | 下記2行のツール |
| `make test-unit` | 依存確認とskip判定を含むunittest | Python 3.11以上、Bash、Zsh、chezmoi、Lua、make、mkdir、cat、chmod、dirname |
| `make test-smoke` | ファイル配置のBatsテスト | Python 3.11以上、Bats、Bash、cat |
| `make lint` | 対象を限定した構文・静的検証 | Python 3.11以上、Bash、Zsh、ShellCheck、shfmt、Git |

通常のPOSIX基本コマンドも必要になる。検証中に依存を自動導入する処理はなく、不足時は失敗する。Pythonを変える場合は`make TEST_PYTHON=/path/to/python3 check`と指定する。設定適用用の`CHEZMOI_BIN`とは独立して、テストはPATH上のchezmoiを使う。

個別テストの調査には従来の`python3 -B -m unittest discover -s tests -p test_対象.py -v`も使える。ただし、直接実行した場合は、Makeターゲットで行う必須依存確認とskip判定を省く。最終確認にはMakeの検証ターゲットを使う。

## skipと終了状態

`tests/check.py`は単体テストの必須ツールを、テスト探索前に確認する。ツール不足、テスト失敗、予期しないskip、テスト未発見、全件skipは異常終了とする。件数を固定した判定にはせず、実行結果とskipしたテストの識別子を確認する。

任意の検証として許可するskipは、`test_yazi_config.YaziConfigTests.test_yazi_loads_keymap_in_isolated_terminal`だけ。Yaziがない場合や疑似端末を作成できない場合が対象で、識別子と理由を`[任意検証skip]`として表示する。Yaziがある場合の起動失敗は通常のテスト失敗になる。TOMLの解析とキー定義のテストは、この任意検証とは別に実行する。

検証用の環境に実PAT・age秘密鍵・Proton Passのセッションは不要。既存テストはダミーと隔離HOMEを使う。Batsは配置確認だけを行い、実際のchezmoi適用、実認証、パッケージ操作、update_appsは検証から呼ばない。

## 静的検証の対象と例外

対象一覧は`tests/check.py`で管理する。bootstrap、3本の適用後スクリプト、共通シェル設定、更新・textlint用コマンドをBash構文とShellCheckで確認する。Bashの起動設定は構文確認、`home/dot_zsh/`の`.zsh`ファイルは`zsh -dfn`で確認する。Pythonはtests内の構文、TOMLは管理対象のmise設定とYazi設定を解析する。

Go templateを含むファイルは直接ShellCheck・shfmtへ渡さない。既存unittestが、確認済みのテンプレートをダミーデータと隔離したchezmoi設定で評価する。実ソース全体や実HOMEを使ったテンプレート評価は行わない。

| 対象 | 例外と理由 |
| --- | --- |
| `bootstrap/setup-proton-pass.sh` | ShellCheckのSC2059だけ除外する。ログ関数が呼び出し側の固定書式を受け取り、printfへ渡す仕様のため。ほかの警告は有効 |
| `home/dot_local/bin/executable_update-agent-skills` | Bash構文とShellCheckは実行する。既存の整形差分は今回変更せず、shfmtの対象には含めない |
| 日本語Markdown | CIの必須対象には含めない。既存の技術用語への指摘を含むため、文書変更時にnatural-japanese・textlint-jaで別途確認する |

検証は全dotfiles・全実行環境を網羅するものではない。静的検証に失敗した場合も、自動整形やファイルの書き換えは行わない。

## GitHub Actions

`.github/workflows/check.yml`はmainへのpush、pull request、手動実行を対象とし、Ubuntu 24.04上で`make check`を実行する。`contents: read`だけを指定し、checkoutの認証情報を保存せず、リポジトリの秘密情報は参照しない。

CIジョブの準備段階には、検証用依存の取得・導入が含まれる。ローカルのMakeターゲットからは実行しない。

| 依存 | 取得元・固定方法 |
| --- | --- |
| GitHub checkout | [actions/checkout v6.0.2](https://github.com/actions/checkout/releases/tag/v6.0.2)のコミットSHAを指定 |
| chezmoi | [公式v2.73.0リリース](https://github.com/twpayne/chezmoi/releases/tag/v2.73.0)のlinux_amd64アーカイブ。公開されたSHA256と一致することを確認してから展開 |
| Bats、Zsh、Lua 5.1、ShellCheck、shfmt | Ubuntu 24.04のAPT。導入バージョンをログへ出力。パッケージの修正版まで固定する構成ではない |
| Python・make・Git・curlなど | Ubuntu 24.04のGitHubホストランナーに備わる基本ツール。Pythonのバージョンをログへ出力 |

chezmoiとLuaへのパスはRUNNER_TEMP配下に作成する。dotfiles用のbootstrapやmise installは実行しない。Yaziは追加導入せず、利用できなければ実起動1件だけを任意skipとして報告する。

checkoutやchezmoiを更新する場合は、リリースとコミットSHA・チェックサムの対応を確認し、固定値とこの文書を一緒に更新する。CI依存の固定は、利用者のmise設定のバージョン方針を変更しない。

## GitHub上で利用者が確認すること

ワークフロー追加後も、GitHubホストランナー上で成功したかは別途確認が必要になる。

1. 変更をコミット・pushした後、リポジトリのActionsで`dotfiles checks`の実行結果を確認する。リポジトリ設定でActionsが無効なら利用者が有効にする。
2. 準備ステップの取得・導入と、`make check`の終了状態を確認する。任意skip以外が発生していないことをログで確認する。
3. マージ前の必須チェックにする場合は、成功を確認したジョブをブランチ保護・ルールセットへ利用者が登録する。この設定変更はコード追加には含めない。

Android/Bionic、Termux実機、proot・WSL・ネイティブLinuxでの実インストールはこのCIでは確認しない。[環境別の検証範囲](environment-matrix.md)と[Termux実機確認](../setup/dependencies.md#termuxでの導入と実機確認)を参照する。
