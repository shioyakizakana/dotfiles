# 隔離したテンプレート検証

対象リポジトリの`.chezmoiroot`が`home`であり、`tests/test_environment_policy.py`があることを確認する。以下のパスとコマンドはリポジトリルートを基準とする。

## 評価する前の確認

| 対象 | 確認する内容 |
| --- | --- |
| `.chezmoi.toml.tmpl` | 初期入力から環境フラグ・providerへの変換。保存されるlinuxEnvは環境名ではなく真偽値 |
| `home/.chezmoiignore` | 拡張子はtmplではないがGo templateを含む。除外パターンは展開先の名前で指定する |
| `home/dot_config/tmux/tmux.conf.tmpl` | Termux相当のPATH・PREFIXと、zshがない場合の出力 |
| 認証ラッパーのtmpl | ダミーproviderによる展開と、不一致時に秘密情報操作へ進まないこと |
| `home/dot_gitconfig.tmpl` | protonPass呼び出しがあるため、そのまま評価しない。安全なモックを用意できなければ静的確認に留める |
| symlinkのtmpl | 出力されるリンク先が意図した展開先を指すこと。出力文字列をコマンドとして実行しない |

protonPass、output、include、環境変数やファイルを読む関数などは、呼び出し先も含めて確認する。関数名の検索だけで安全とは判断しない。

## 既存テストを使う

```shell
python3 -B -m unittest discover -s tests -p test_environment_policy.py -v
python3 -B -m unittest discover -s tests -p test_proton_pass_setup.py -v
```

`test_environment_policy.py`のrun_chezmoiとrender_init、`test_proton_pass_setup.py`のラッパー展開を参考に、必要なケースを追加する。
初期入力を再現する`execute-template --init`は、実際の`chezmoi init`とは別の操作。隔離した設定と確認済みの初期設定テンプレートに限って使用する。

## fixtureの条件

- sourceには確認済みのファイルだけを置く。実リポジトリ全体やchezmoiexternal設定をコピーしない。
- config・source・destination・cache・persistent-stateを一時ディレクトリへ明示する。実HOMEの設定や状態を参照しない。
- HOME・PATHなど必要な環境変数だけを渡す。認証情報や実際のprovider上書きを継承しない。
- `--refresh-externals=never`と`--no-tty`を指定し、managedまたはexecute-templateを使用する。
- スクリプトは実処理を持ち込まず、実行されないダミーを使う。一時領域はテスト終了時に片付ける。

既存フラグはnativeUbuntu・wslUbuntu・qemuUbuntu・prootUbuntu・termux。Termuxが優先される混在ケース、未知環境、linux・androidの両OS値も必要に応じて確認する。
providerはUbuntu系のenv／keyring、Termux・prootのenv、不正値・不一致を確認する。初期入力のモックには、既存テストと同じプロンプト全文を使用する。

## 展開後の確認

Bashとして展開されるファイルは、ダミーデータで生成した結果をbash -n・ShellCheck・shfmtへ渡す。TOMLはtomllibで解析し、期待する値も確認する。
ファイル名だけでシェルと判断しない。symlink定義やPythonファイルは、対応する形式として扱う。
評価できても出力の意味が正しいとは限らないため、環境別の対象・パス・providerも確認する。

環境ごとの期待値と実機確認の限界は、リポジトリの`docs/testing/environment-matrix.md`を参照する。ARM64メタデータやTermux相当のPATHは、Androidや実バイナリの動作保証とは区別する。
