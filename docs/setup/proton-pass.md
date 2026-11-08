# Proton Passの構築・確認手順

DF-07のコード修正後に、利用者が実環境で行う確認手順。実際の認証・設定適用は自動テストの対象にしていない。
まず1〜4節を確認し、停止した場合は5節を参照する。

1. 既存の認証方式を維持する。初期化済みの環境でproviderを変更する場合は、移行方法を別途決める。
2. PATは対話入力し、コマンドの引数やシェル履歴に記録しない。
3. 初回の全体適用より前に`make wrapper`を実行する。

## 1. 実行環境とproviderを確認する

基礎コマンドはREADMEの準備手順で導入済みとする。この手順ではパッケージの追加を行わない。
標準配置なら次のディレクトリへ移動する。別の場所にcloneした場合は、その場所を指定する。

```shell
cd "$HOME/.local/share/chezmoi"
export PATH="$HOME/.local/bin:$PATH"
make require
```

初めて初期化する場合はREADMEの`chezmoi init`を使う。Ubuntu系では`env`または`keyring`を選択する。Termux・prootはenvに固定する。

| 実行環境 | providerと準備 |
| --- | --- |
| Termux | env。keyringは使わない。pass-cli・age・Python 3の実行可否を端末で確認する |
| proot Ubuntu | env。bootstrapはrootを拒否するため、通常ユーザーで作業する。引き継いだ`PREFIX`よりchezmoi設定を優先する |
| WSL2・ネイティブ・QEMUのUbuntu | env、またはD-BusセッションとSecret Serviceが利用できるkeyring |

既存環境では、秘密情報を含まない項目だけを表示する。

```shell
chezmoi --source "$PWD" execute-template '{{ .protonPassProvider }}'
chezmoi --source "$PWD" execute-template 'termux={{ .termux }} proot={{ .prootUbuntu }} wsl={{ .wslUbuntu }} qemu={{ .qemuUbuntu }} native={{ .nativeUbuntu }}'
```

実行環境のフラグが現在の環境と一致し、通常は1つだけtrueであることを確認する。別端末から設定をコピーした場合は特に注意する。
`keyring`を継続利用する場合は、同じログインセッションで次を確認する。Secret Serviceの起動方法はデスクトップ環境によって異なるため、このリポジトリでは自動起動しない。

```shell
busctl --user --timeout=5 introspect \
  org.freedesktop.secrets /org/freedesktop/secrets \
  org.freedesktop.Secret.Service >/dev/null
```

## 2. 既存環境ではラッパー参照先も更新する

以前の初期設定は、ラッパー未展開時に`pass-cli`を直接参照することがある。現在の参照先だけを確認する。

```shell
chezmoi --source "$PWD" execute-template '{{ .chezmoi.config.protonPass.command }}'
```

`pass-cli`や別のPATH上のラッパーを参照している場合は、適用前にchezmoiのローカル設定をバックアップする。
標準の設定ファイルは`~/.config/chezmoi/chezmoi.toml`。独自の設定パスを使う場合は、そのファイルを対象とする。

```shell
cp -p "$HOME/.config/chezmoi/chezmoi.toml" \
  "$HOME/.config/chezmoi/chezmoi.toml.before-df07"
chezmoi init --source "$PWD"
```

バックアップ名が既に存在する場合は、未使用の名前に変更してからコピーする。再初期化はローカル設定を再生成するため、独自に追加した設定はバックアップと比較する。
再初期化では既存の環境フラグとproviderを引き継ぐ。上記の確認を繰り返し、参照先が実際のホームディレクトリ配下の`.local/bin/proton-pass`になったことを確認する。
新規構築ではこの再初期化は不要。

## 3. 認証を構築し、ラッパーを限定展開する

新規環境または初期構築を再開する場合は、通常ユーザーの対話端末で実行する。

```shell
make bootstrap
```

引数なしでchezmoiの環境・providerを使う。明示指定が必要なら、例えば次のように実行できる。両方とも設定と一致しなければ停止する。

```shell
LINUX_ENV=proot-ubuntu bash bootstrap/setup-proton-pass.sh env
```

bootstrapはage identity・暗号化PATなどを作成または検証し、ログインする。既存の暗号文を削除せず、必要なパスフレーズとPATは表示された対話入力で渡す。
認証済みの既存環境では、DF-07のためだけにbootstrapを再実行する必要はない。

```shell
make wrapper
```

このターゲットは`proton-pass`と`proton-pass-key-cache.py`だけを展開する。chezmoiのスクリプト実行とexternalsの更新を除外する。
`init-proton-pass`は通常の全体適用で更新する。

## 4. ラッパーを通した認証と適用を確認する

```shell
"$HOME/.local/bin/proton-pass" info
```

実際の認証状態を確認する操作。envでは必要に応じてageのパスフレーズ入力と鍵キャッシュの起動が発生する。
出力にはアカウント情報が含まれる可能性があるため、共有ログへ貼り付けない。
TermuxではPython 3とキャッシュソケット、prootでは同じ通常ユーザーのHOME・実行権限も確認する。

認証確認後、差分を手元の端末で確認してから全体を適用する。差分には復号済みデータが含まれる可能性があるため公開しない。

```shell
make diff
make apply
```

`make apply`は確認入力後に設定を反映し、環境別の導入スクリプトや外部取得を伴う。今回のコード検証では実行していない。

## 5. 停止した場合の対処

| 状況 | 確認・対処 |
| --- | --- |
| provider不一致 | 継承した`PROTON_PASS_KEY_PROVIDER`と引数を確認する。不要な上書きなら`unset PROTON_PASS_KEY_PROVIDER`として再実行する。既存の認証方式をその場で変更しない |
| 実行環境の不一致 | 不要な`LINUX_ENV`は`unset LINUX_ENV`で解除する。保存したフラグ自体が誤っている場合はローカル設定をバックアップし、実環境に合うフラグだけをtrueにする |
| keyringの条件を満たさない | 同じユーザーのD-BusセッションとSecret Serviceを確認する。envへの移行は認証方式の変更として別途計画する |
| 暗号文があるのにidentityがない | 停止したまま、正しい暗号化identityとrecipientのバックアップを確認する。鍵の再生成や暗号文の削除で回避しない |
| ラッパーや鍵キャッシュがない | `make wrapper`の成功と`.local/bin`の実行権限を確認する。ソースの`.tmpl`を直接実行しない |
| Termux・prootでCLIが実行できない | CPU・実行形式・通常ユーザー・PATHを確認する。今回のモックテストはAndroidのBionicや実サービスとの互換性までは保証しない |

解決しない場合は、環境名・provider・終了コード・秘密情報を除いたエラーだけを記録し、次の修正依頼で共有する。
PAT、秘密鍵、復号結果、環境変数の値の一覧は添付しない。

用語：providerはCLIの暗号化鍵の供給方法、envはプロセス環境変数、keyringはSecret Serviceを利用する方式。identityはageの復号鍵、recipientは暗号化先を示す公開鍵。

最終更新：2026-11-08。
