# 秘密情報管理の静的レビュー

対象リポジトリの`.chezmoiroot`と`bootstrap/setup-proton-pass.sh`を確認する。以下はリポジトリルートから見たソースのパスであり、展開済みの秘密情報を調べる手順ではない。

## 対象を選ぶ

| ソース | 確認する処理 |
| --- | --- |
| `.chezmoi.toml.tmpl` | 環境フラグ、provider、CLIラッパーの参照先 |
| `bootstrap/setup-proton-pass.sh` | 設定の事前検証、identity・暗号文の保護、初期認証、一時ファイル |
| `home/dot_local/bin/executable_init-proton-pass.tmpl` | provider確認と通常ラッパーへの委譲 |
| `home/dot_local/bin/executable_proton-pass.tmpl` | PATの復号とCLI・キャッシュへの環境変数の受け渡し |
| `home/dot_local/bin/private_executable_proton-pass-key-cache.py.tmpl` | 常駐プロセス、メモリ内の鍵、ソケット、TTL、接続元UID |
| `home/dot_gitconfig.tmpl` | protonPassを使う参照。実際の展開結果を取得せず呼び出しを調べる |

## 確認観点

- providerと実行環境の不一致を、ロック用ディレクトリ作成・鍵作成・復号・ログインより前に検出するか。Termux・prootではenvを維持するか。
- PATが必要なCLIにだけ渡り、鍵キャッシュの常駐プロセスへ継承されないか。CLI暗号化鍵も不要なプロセスの環境から除かれるか。
- identityやパスフレーズをキャッシュせず、CLI暗号化鍵の保持期間と破棄条件が明確か。通常の参照で期限が延長されないか。
- 暗号文があるのにidentityが欠ける場合、新しい鍵で置き換えず停止するか。recipientとidentityの一致を確認するか。
- 保存先の重複、symlink、所有者、権限、同時実行をどう扱うか。一時ファイルを安全に作成し、異常終了時にも片付けるか。
- PAT・暗号化鍵・復号結果を、引数・ログ・例外・標準出力へ漏らさないか。set -xなどのデバッグも確認する。
- envとkeyringの切替が既存の認証状態と整合するか。Secret Serviceの利用条件と、認証失敗時の停止を扱うか。

これらは確認項目であり、全項目が既にテスト済みとは扱わない。実装で確認した事実と、テストが保証する範囲を分ける。

## 実データを使わずに確かめる

`tests/test_proton_pass_setup.py`は、鍵作成・秘密情報作成・認証などをモックへ置き換え、設定不一致時の停止とラッパーの挙動を確認する。
`tests/test_proton_pass_key_cache.py`は、復号・通信・常駐プロセス起動・CLI実行をモックへ置き換え、PATの継承防止などを確認する。
テストを追加する場合も、HOMEと環境変数を隔離してダミー値だけを使う。新しいテストが実プロセスや秘密ファイルへ到達しないことを読んで確認する。

レビュー中は、保存済みのPAT・秘密鍵・暗号化鍵・復号済み設定を開かない。envやprintenvで環境変数を一覧表示しない。
proton-pass infoもenv方式では復号やキャッシュ起動を伴い得る。pass-cli・age・busctlによる実認証や復号の確認は、静的レビューの代わりに実行しない。
chezmoi dataやdump-configの全出力、実環境でのdiff・status・テンプレート評価も、安全な読み取りと決めつけない。

`docs/setup/proton-pass.md`は利用者向けの実環境手順。内容を参照しても、そこにある認証・適用・移行コマンドをレビューの一部として実行しない。
指摘は`docs/reviews/dotfiles-audit.md`の関連項目と照らし合わせ、修正済みの過去の問題を現在の不具合として報告しない。
