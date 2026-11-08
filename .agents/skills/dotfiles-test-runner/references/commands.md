# 変更対象から検証を選ぶ

対象リポジトリの`.chezmoiroot`が`home`で、以下のテストがあることを確認する。コマンドはリポジトリルートから実行する。

## Python unittest

| 変更対象 | 対応するテストファイル |
| --- | --- |
| 初期設定・環境フラグ・ignore・tmux・スキルの展開範囲 | `tests/test_environment_policy.py` |
| Bash・Zshの共通環境・PATH・エイリアス・起動設定 | `tests/test_shell_config.py` |
| 基礎ツールbootstrap | `tests/test_bootstrap_tools.py` |
| APT導入 | `tests/test_install_apt.py` |
| Homebrew導入 | `tests/test_install_brew.py` |
| mise導入・Rust・LuaRocks・nimlsp | `tests/test_mise_helpers.py` |
| provider・認証前の停止・ラッパー | `tests/test_proton_pass_setup.py` |
| PAT継承・鍵キャッシュ | `tests/test_proton_pass_key_cache.py` |
| 明示的な更新処理 | `tests/test_update_apps.py` |

```shell
# 対象に応じてファイル名を選ぶ。
python3 -B -m unittest discover -s tests -p test_environment_policy.py -v
# 複数の処理へ影響する変更や、コミット前の全体確認。
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

既存テストはダミーコマンドやモックを使用するが、新規・変更されたテストは実行前に確認する。秘密情報取得、外部通信、実パッケージ操作が残っていれば実行を止める。
Python 3.11以上とBashを前提とする。chezmoiやmakeがない場合にskipするケースもあるため、終了コードだけで成功と判断しない。
シェル起動テストはBash・Zsh・chezmoi・mkdirを必要とし、欠けていればskipする。システム補完・Homebrewの固定パス・プラグインはfixtureに置き換え、実際の初期化を避ける。

## 配置と静的確認

```shell
bats tests/smoke.bats
git diff --check
```

Batsは主に配置を確認し、Brewfileの期待パスは`home/dot_Brewfile`。以前のtmplを期待するテストは修正済みだが、実行時の結果を確認し、失敗を隠さない。テスト拡充・CIなどの残件は`docs/reviews/dotfiles-audit.md`のDF-11で確認する。

| 対象 | 検証方法 |
| --- | --- |
| Bashのソース | 対象を限定してbash -n、shellcheck、shfmt -i 2 -d |
| Go templateを含むファイル | 安全なダミー展開を先に行い、出力形式に合う検証へ渡す |
| Zshのソース | Bash用の構文確認を流用せず、利用可能ならzsh -n |
| TOML | Pythonのtomllibで解析。テンプレートなら先に隔離環境で展開 |
| 日本語Markdown | プロジェクトのAGENTS.mdと共通規約に従って文章を確認 |
| Makefile | レシピを読んでから必要なターゲットだけをdry-runで確認 |

ShellCheckのSC2059は既存の固定書式ログで報告されることがある。除外する場合は該当コードと理由を確認して報告し、他の警告まで抑制しない。
Makeのdry-runでも、変数展開中のshell関数や再帰makeなどが動く場合がある。コマンド名だけで安全と判断しない。
現在のMakefileのbootstrapは実認証、wrapperとapplyはchezmoi適用を伴うため、テスト用ターゲットとして使わない。インストールスクリプトの直接実行やupdate_appsも、検証コマンドの代わりには使わない。

## 実行結果の扱い

失敗は、今回の変更に関係するもの、既存の問題、環境不足に分けて根拠を示す。テストを通すために期待値を弱めたり、依頼がテスト実行だけの場合に無断で修正したりしない。
実認証・実インストール・Androidの実行環境は、モックによる成功とは区別する。環境別の範囲は`docs/testing/environment-matrix.md`を参照する。
