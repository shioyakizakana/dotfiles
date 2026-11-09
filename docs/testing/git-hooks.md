# dotfilesのGit hooks

リポジトリルートの`lefthook.yml`を共通設定とする。ホームへ展開するファイルではなく、各作業コピーでhookをインストールする。検証版はlefthook 2.2.2で、mise管理設定とCIの取得版をそろえている。

| hook | 実行内容 |
| --- | --- |
| pre-commit | `git diff --cached --check`でステージ済み差分の空白エラーを確認 |
| pre-push | `make check`で静的検証・unittest・Batsを実行 |

自動整形やstage_fixedは設定しない。部分stage時にはlefthookが未stage差分を一時退避する場合があるため、正常終了後もその差分が保持されることを回帰テストで確認する。pre-pushの検証対象は現在の作業ツリーであり、未コミット変更や別refのpush対象とは一致しない場合がある。PRの必須CIも引き続き利用する。

## 共通の導入手順

最初に、利用する環境でlefthook 2.2.2と[make checkの依存](checks.md)を準備する。Ubuntu・WSL・proot Ubuntuでは、既存のmiseを使うなら`mise install lefthook@2.2.2`で準備できる。これは利用者が選択して実行する導入操作であり、hookからは呼ばない。

リポジトリのルートで次を確認する。

```shell
command -v lefthook
lefthook version
git config --show-origin --get-all core.hooksPath
git rev-parse --git-path hooks
```

core.hooksPathが未設定なら、その確認コマンドは出力なし・終了状態1になる。設定がある場合や有効な既存hookがある場合は、その用途を確認してから統合方法を決める。`--force`や`--reset-hooks-path`で既存設定を自動変更しない。

競合がないことを確認した後、次を実行する。[公式のインストール手順](https://lefthook.dev/usage/commands/install/)

```shell
lefthook validate
lefthook install pre-commit pre-push
```

生成hookは`.git/hooks`などGitが指定する場所に置かれ、Git管理には含めない。作業コピーを変えた場合はその環境で再生成する。設定の反映・同期によってhookが更新されることもあるため、端末固有の補正が必要な場合は更新後に確認する。

## Termux本体の確認

Termux本体へのUbuntu用mise設定の展開除外は維持する。Termuxで実行できるlefthook 2.2.2を別途準備し、`lefthook version`と`lefthook validate`で起動できることを確認する。Ubuntuゲストの実行ファイルや、Linux向け配布物をそのままTermuxで使えるとは扱わない。

TermuxネイティブのGoからビルドする場合は、次が候補になる。これは実機未検証の手順であり、現在の作業環境からは実行していない。事前にTermux用のGo・必要なビルド環境を準備する。[v2.2.2のgo.mod](https://github.com/evilmartians/lefthook/blob/v2.2.2/go.mod)はGo 1.27.0以上を要求する。`go env GOOS`がandroidであることを確認し、GOTOOLCHAIN=localで自動的な別版Goの取得を防ぐ。

```shell
go version
go env GOOS
mkdir -p "$HOME/.local/bin"
GOTOOLCHAIN=local GOBIN="$HOME/.local/bin" go install github.com/evilmartians/lefthook/v2@v2.2.2
export PATH="$HOME/.local/bin:$PATH"
lefthook version
```

標準の生成hookは`#!/bin/sh`を使う。Termuxではtermux-execによる変換で実行できる場合もあるが、`/bin/sh`がない環境では、共通のインストール後に生成hookだけを補正する。[Termux公式のシバン補正ツール](https://github.com/termux/termux-fix-shebang)

```shell
command -v termux-fix-shebang
termux-fix-shebang "$(git rev-parse --git-path hooks/pre-commit)"
termux-fix-shebang "$(git rev-parse --git-path hooks/pre-push)"
```

再インストール・同期後もシバンを確認する。Termux本体とproot Ubuntuでは、それぞれの作業コピーで生成することを推奨する。環境が異なる同じ.gitを共用する場合は、実行ファイルのPATHとシバンの違いに注意する。

## PATHとローカル設定

共通設定の`lefthook: lefthook`はPATH上の実行ファイルを指定する。見つからなければ失敗させ、生成hookの別パッケージマネージャーによる探索・導入へは進ませない。[実行ファイルの指定](https://lefthook.dev/configuration/lefthook/)

GitをGUIや非ログインシェルから起動する場合も、lefthookと検証ツールがPATHに必要になる。shimの自動導入などへ依存せず、既存ツールを見つけられる環境を用意する。端末固有の設定は`lefthook-local.yml`へ分離できる。このファイルは`.gitignore`で除外し、実際のホームパスや端末固有設定は共有しない。独自の実行ファイルを指定した場合はhookを再生成して確認する。[ローカル設定](https://lefthook.dev/usage/features/local/)

## 動作確認と限界

```shell
lefthook validate
lefthook run pre-commit
lefthook run pre-push --force
```

送信対象のないpre-push単体実行などはlefthookの判断でskipされる場合がある。検証時の`--force`はジョブを実行させる指定であり、インストール時の`--force`とは異なる。実commit・pushを行わずに確認できるが、pre-pushは全テストを実行するため時間がかかる。

`tests/test_git_hooks.py`は一時リポジトリとダミーmakeを使い、設定の検証、ステージ済み差分、部分stageの保持、失敗伝播、lefthook不足時の停止、Termux相当パスのシバンを確認する。ダミーHEAD用のGitオブジェクトだけを用意し、実リポジトリの履歴やindexは変更しない。CIでも同じlefthook 2.2.2を取得し、このテストを実行する。

Termuxの実バイナリ・Bionic・実際のGit hook起動、WSLやネイティブLinuxそれぞれの実機動作は別途確認が必要。hookを使わない操作も可能なので、main-ciの必須チェックとPR必須の設定は維持する。
