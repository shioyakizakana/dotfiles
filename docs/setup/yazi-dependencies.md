# Yaziの依存一覧と固定候補

調査日：2026-11-11。管理ソースと公開仕様を確認した。プラグインの取得・更新、設定適用、実ホームのプラグイン・私的設定の調査は行っていない。調査後にYZ-01の設定キーだけを修正し、fetcher登録のテストを追加した。キー操作やプラグインの版は変更していない。

## 管理できている範囲

管理対象は`home/dot_config/yazi/`の`init.lua`・`yazi.toml`・`keymap.toml`・`theme.toml`。`package.toml`、プラグイン本体、flavor本体は管理ソースにない。`home/.chezmoiexternal.toml.tmpl`にもYazi用の取得定義はない。

`home/.chezmoiignore:5`は展開先の`.config/yazi/plugins/`を管理対象から外している。これは既存プラグインを削除する指定ではない。以下の「手動準備」は、リポジトリが導入を保証しないという意味であり、実端末に未導入だと確認したものではない。

## プラグインと外部コマンド

| 依存 | ソースでの使用箇所 | 提供元・準備方法 | 未準備時の影響・確認条件 |
| --- | --- | --- | --- |
| zoxide | `init.lua:2`、`keymap.toml:15`の`z i` | Yazi組み込み。外部zoxideと対話選択用fzfが必要 | 履歴追加・移動を確認。zoxideはUbuntu向けmise、fzf本体は手動準備。Termuxは別途準備 |
| session | `init.lua:5` | Yazi組み込み | `sync_yanked`によるセッション間の共有を確認。追加の公開プラグインとして導入しない |
| fzf | `keymap.toml:14`の`z f` | Yazi組み込みと外部fzf | Luaプラグインの存在と、実行ファイルの存在を分けて確認する |
| git | `init.lua:21`、`yazi.toml:5-13` | 公式`yazi-rs/plugins:git`。手動準備 | 読み込み失敗は名前だけ通知して続行する。Git状態表示にはfetcher登録と外部gitも必要 |
| full-border | `init.lua:22-24` | 公式`yazi-rs/plugins:full-border`。手動準備 | 読み込み失敗時は続行。枠の表示とsetupオプションの互換性を確認する |
| smart-enter | `keymap.toml:10`のEnter | 公式`yazi-rs/plugins:smart-enter`。手動準備 | 未導入ならEnterに割り当てた操作は利用できない。ディレクトリとダミーのテキストファイルで確認する |
| toggle-pane | `keymap.toml:11`のCtrl-p | 公式`yazi-rs/plugins:toggle-pane`。手動準備 | `max-preview`でプレビュー領域の最大化・復帰を確認する |
| chmod | `keymap.toml:13`の`c m` | 公式`yazi-rs/plugins:chmod`。手動準備 | Unix系が対象。実機確認は共有ストレージを避け、一時ファイルだけで行う |
| bunny | `keymap.toml:12`の`e`、私的設定例内 | 公開候補は`stelcodes/bunny`。手動準備 | 現在の個人設定がこの提供元を使うかは未確認。ブックマーク表示とfzfによる検索を分けて確認する |
| bunny-private | `init.lua:44` | 利用者がローカルに置く任意設定 | 読み込み失敗は続行する。公開候補のbunnyと同一物ではない。実内容は読まず、Gitへ取り込まない |

組み込みの確認根拠はYazi v26.9.1の[session](https://github.com/sxyazi/yazi/blob/v26.9.1/yazi-plugin/preset/plugins/session.lua)、[zoxide](https://github.com/sxyazi/yazi/blob/v26.9.1/yazi-plugin/preset/plugins/zoxide.lua)、[fzf](https://github.com/sxyazi/yazi/blob/v26.9.1/yazi-plugin/preset/plugins/fzf.lua)。zoxideの`update_db`は外部コマンドを使い、対話選択にもfzfを使うため、組み込みだけで機能が完結するとは扱わない。

公式追加プラグインの提供元は[公式一覧](https://github.com/yazi-rs/plugins)。個別の設定は[git](https://github.com/yazi-rs/plugins/tree/main/git.yazi)、[full-border](https://github.com/yazi-rs/plugins/tree/main/full-border.yazi)、[smart-enter](https://github.com/yazi-rs/plugins/tree/main/smart-enter.yazi)、[toggle-pane](https://github.com/yazi-rs/plugins/tree/main/toggle-pane.yazi)、[chmod](https://github.com/yazi-rs/plugins/tree/main/chmod.yazi)で確認した。bunnyは[作者の説明](https://github.com/stelcodes/bunny.yazi)を確認したが、既存の私的設定との対応は確定していない。

## テーマとその他のコマンド

`theme.toml:2-3`は`catppuccin-latte`・`catppuccin-mocha`を参照する。公開候補は[公式flavors一覧](https://github.com/yazi-rs/flavors)の同名ディレクトリで、手動準備と互換性確認が必要。管理ソースには本体も取得定義もない。個人の導入状態は未確認。[flavorの配置・互換性](https://yazi-rs.github.io/docs/flavors/overview/)も参照する。

`yazi.toml`のedit openerは`EDITOR`を使う。preview openerにはmacOS向け`qlmanage`が宣言されているが、現行のopenルールからの参照はない。Linuxでの自動実行や動作不良は確認していない。画像・PDFなどのプレビュー依存は[既存の依存一覧](dependencies.md)で別に扱う。

## 固定前に扱う項目

| ID | 事実・評価 | 推奨する対応と検証 | 状態 |
| --- | --- | --- | --- |
| YZ-01 | 修正前の`yazi.toml:5,10`が`prepend_feachers`で、正式キーの登録テストが失敗した。実機の障害再現は未実施 | `prepend_fetchers`へ修正。TOML解析後に2件のgit fetcherのurl・run・group・順序を検証する | 修正済み・未適用 |
| YZ-02 | `init.lua:23`の`type = ui.Border.ROUNDED`は、確認したfull-borderの現行実装で非推奨。互換処理は残るため、起動不能とは扱わない | 採用revisionを決め、その版の`set = "rounded"`対応を確認してから設定とモックを更新する | 潜在的な互換性リスク |
| YZ-03 | 公開プラグイン・flavorのrevisionをリポジトリから復元できない。個人環境で動いている組合せも未確認 | 公開依存だけの管理方法を選び、確認済みの組合せを記録する。bunny-privateは対象外とする | DF-06の固定値選定に先行 |

YZ-01の根拠は[gitの登録例](https://github.com/yazi-rs/plugins/tree/main/git.yazi)と[fetcher設定の公式仕様](https://yazi-rs.github.io/docs/configuration/yazi/#fetchers)。YZ-02は[full-borderの実装](https://github.com/yazi-rs/plugins/blob/main/full-border.yazi/main.lua)で`type`の互換処理と警告を確認した。公開mainの内容は変わり得るため、固定時は選んだrevisionで再確認する。

## 本体と依存を固定する候補

| 対象 | 候補・扱い | 採用前の条件 |
| --- | --- | --- |
| Yazi・ya | `26.9.1`を最初の評価候補とする。miseの`latest`は今回は変更しない | 過去に隔離keymap読み込みを確認した版。実init.lua・テーマ・プラグイン全体が動作確認済みという意味ではない。yaも同じ版を使う |
| 組み込みプラグイン | 本体と一緒に版をそろえる | zoxide・fzfなどの外部コマンドは別に確認する |
| 公式追加プラグイン・bunny・flavor | 具体的revisionは未選定 | 選んだYazi版に対応し、設定・実操作の確認が済んだrevisionを採用する。調査日のmainを無条件に固定しない |
| bunny-private | 共有する固定対象から除外 | 個人パスをダミーに置き換えた確認方法だけを共有する |

Yazi・yaの同一版利用と、依存の`rev`・`hash`による復元は[公式CLI仕様](https://yazi-rs.github.io/docs/cli/)に従う。`package.toml`の通常のrevision記録は`ya pkg upgrade`で更新され得る。更新も抑える固定には`rev`の先頭に`=`を付ける方式がある。これは今後の管理案であり、今回はファイルを生成しない。

管理案は、公開依存だけの`package.toml`をソース管理し、プラグイン本体は現在どおり除外する方式を第一候補とする。導入手順が必要になる一方、取得元とrevisionを記録できる。chezmoi externalsによる取得も代替案だが、現時点では追加せず、二重管理を避ける。ホームの既存package.tomlを無条件に取り込まない。

公式pluginsは最新のYaziコードを前提にする旨を[README](https://github.com/yazi-rs/plugins)で案内している。本体の安定版だけを固定して、公開プラグインのmainへ追従する組合せは互換性の保証にならない。

## 次の作業と確認順序

1. YZ-01は正式キーへの修正とfetcher登録テストの追加まで完了した。実プラグインでの状態表示は、公開依存を準備した後に確認する。
2. 公開依存の管理案と採用する本体版を決める。取得・導入が必要な作業は、対象と保存場所を確認して別途実施する。
3. 採用revisionでfull-borderのオプションを確認し、対応する設定とモックを更新する。現在のモックは既存オプションを確認するだけで、実APIの互換性は保証しない。
4. 利用者が実機で下記の操作を確認し、Yazi・yaの版、公開依存のrevision、OS・CPU、合否を記録する。動作する組合せが揃ってからmiseの固定値を変更する。

| 確認対象 | ダミー素材による確認 | 結果 |
| --- | --- | --- |
| 初期化・flavor | 公開設定と導入済みの公開依存で起動し、明暗両方の配色と枠を確認する。私的設定は持ち込まない | 未実施 |
| smart-enter・toggle-pane | ダミーディレクトリとテキストでEnter、Ctrl-pの往復を確認する | 未実施 |
| git | 一時Gitリポジトリの未追跡ファイル・変更済みファイルを表示する。実リポジトリのindexを変更しない | 未実施 |
| chmod | 一時ファイルの権限だけを変更する。Termuxではホーム配下と共有ストレージを区別する | 未実施 |
| fzf・zoxide | ダミーの選択対象と隔離した履歴で移動を確認する。実際の履歴を読み出さない | 未実施 |
| bunny・session | 公開のダミーブックマークと一時セッションで動作を確認する。bunny-privateは使わない | 未実施 |

## 既存テストの範囲

`tests/test_optional_dependencies.py`はrequire・UI・通知をモック化し、追加依存欠落時の継続、setupオプション、setup失敗の伝播を確認する。実プラグインをロードしない。

`tests/test_yazi_config.py`はTOML構文とキー定義、正式な`prepend_fetchers`へのgit登録2件を確認する。任意の実起動テストはkeymapだけをコピーし、init.luaを終了用fixtureへ置き換える。fetcherの実行・flavor・追加プラグインの互換性は対象外。この差を埋めるために既存テストを弱めたり、私的設定を使ったりしない。
