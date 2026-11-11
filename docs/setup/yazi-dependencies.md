# Yaziの依存一覧と固定候補

調査日：2026-11-11。管理ソースと公開仕様を確認した後、一時HOMEで公開依存の取得・復元と隔離起動を検証した。共有manifestを追加し、Yaziを26.9.1へ固定、full-borderのオプションを更新した。Codexから実ホームへの導入・設定適用や、私的設定の調査は行っていない。利用者からは適用後のrounded表示確認の報告を受けた。

## 管理できている範囲

管理対象は`home/dot_config/yazi/`の`init.lua`・`yazi.toml`・`keymap.toml`・`theme.toml`と、公開依存だけの`package.toml`。プラグイン・flavor本体は管理しない。Yazi用のchezmoi externalsや、自動導入スクリプトは追加しない。

`home/.chezmoiignore:5-6`で展開先の`.config/yazi/plugins/`と`.config/yazi/flavors/`を除外する。既存の本体やbunny-privateは削除しない。以下の「手動準備」は、利用者がmanifestを確認・配置した後に`ya pkg install`を実行するという意味。実端末の導入状態は未確認。

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

`theme.toml:2-3`は`catppuccin-latte`・`catppuccin-mocha`を参照する。[公式flavors一覧](https://github.com/yazi-rs/flavors)の同名ディレクトリをmanifestで指定する。手動準備が必要で、個人の導入状態は未確認。[flavorの配置・互換性](https://yazi-rs.github.io/docs/flavors/overview/)も参照する。

`yazi.toml`のedit openerは`EDITOR`を使う。preview openerにはmacOS向け`qlmanage`が宣言されているが、現行のopenルールからの参照はない。Linuxでの自動実行や動作不良は確認していない。画像・PDFなどのプレビュー依存は[既存の依存一覧](dependencies.md)で別に扱う。

## 固定前に扱う項目

| ID | 事実・評価 | 推奨する対応と検証 | 状態 |
| --- | --- | --- | --- |
| YZ-01 | 修正前の`yazi.toml:5,10`が`prepend_feachers`で、正式キーの登録テストが失敗した。実機の障害再現は未実施 | `prepend_fetchers`へ修正。TOML解析後に2件のgit fetcherのurl・run・group・順序を検証する | 設定適用の報告あり・Git状態表示は未確認 |
| YZ-02 | 旧`type`は採用revisionでも非推奨 | `set = "rounded"`へ変更。モックと公開実装を使った隔離描画で確認した | 修正済み・利用者が適用後のrounded表示を確認 |
| YZ-03 | 公開依存を再現するmanifestがなかった | 公開プラグイン6件・flavor 2件を完全SHAと内容ハッシュで記録。別の空HOMEへ復元できた | 管理方式を実装済み・実機確認は残件 |

YZ-01の根拠は[gitの登録例](https://github.com/yazi-rs/plugins/tree/main/git.yazi)と[fetcher設定の公式仕様](https://yazi-rs.github.io/docs/configuration/yazi/#fetchers)。YZ-02は[full-borderの実装](https://github.com/yazi-rs/plugins/blob/main/full-border.yazi/main.lua)で`type`の互換処理と警告を確認した。公開mainの内容は変わり得るため、固定時は選んだrevisionで再確認する。

## 本体と依存を固定する候補

| 対象 | 候補・扱い | 採用前の条件 |
| --- | --- | --- |
| Yazi・ya | `26.9.1`を採用する検証基準とし、miseも同版へ固定する | 公開設定・依存を使った隔離起動と描画まで確認。全キー操作・Termux等の実機互換性を保証するものではない。yaも同じ版を使う |
| 組み込みプラグイン | 本体と一緒に版をそろえる | zoxide・fzfなどの外部コマンドは別に確認する |
| 公式追加プラグイン・bunny・flavor | 下記のrevisionをmanifestへ固定 | 復元・初期化・描画は確認済み。個々のキー操作は未確認。更新時はソース変更と再検証を同じPRで行う |
| bunny-private | 共有する固定対象から除外 | 個人パスをダミーに置き換えた確認方法だけを共有する |

Yazi・yaの同一版利用と、依存の`rev`・`hash`による復元は[公式CLI仕様](https://yazi-rs.github.io/docs/cli/)に従う。manifestでは`rev`の先頭に`=`を付けて更新を抑える。内容ハッシュには、一時HOMEでyaが生成した管理用の値を使用する。

| 提供元 | 固定コミット | 対象 |
| --- | --- | --- |
| yazi-rs/plugins | `1ef5fe02a6122f8f3bb47a41056aab3f4b8598bf` | git・full-border・smart-enter・toggle-pane・chmod |
| stelcodes/bunny.yazi | `8f3f84e20ea0545d032c134cf184784eaff55d13` | bunny |
| yazi-rs/flavors | `38c08d8eb9ea0d28c8c911a249a08f27ba2151ac` | catppuccin-latte・catppuccin-mocha |

公開依存だけのmanifestをソース管理し、取得は利用者の`ya pkg install`に分離する。chezmoi externalsとの二重管理はしない。既存package.tomlは自動統合されないため、適用前に利用者が退避・差分確認する。個人用の依存を保持したい場合は適用を止め、統合方針を決める。私的設定や個人専用の取得元を共有ソースへ取り込まない。

公式pluginsは最新のYaziコードを前提にする旨を[README](https://github.com/yazi-rs/plugins)で案内している。本体の安定版だけを固定して、公開プラグインのmainへ追従する組合せは互換性の保証にならない。

## 次の作業と確認順序

1. 既存環境では、manifestを配布する前に個人用依存の統合を利用者が確認する。手順は[依存一覧](dependencies.md#yazi)に従う。
2. 配置した共有manifestを確認し、同じ版のYazi・yaで`ya pkg install`する。この操作は通信と展開先の変更を伴い、自動実行しない。
3. 利用者が実機で下記のキー操作を確認し、Yazi・yaの版、OS・CPU、合否を記録する。Termux本体ではUbuntu用mise設定を展開せず、同版の実行ファイルを別途準備する。
4. 次の更新では、manifestと本体版、setupオプションを合わせて変更する。隔離検証を先行し、実機での適用結果とは分けて記録する。

| 確認対象 | ダミー素材による確認 | 結果 |
| --- | --- | --- |
| 初期化・flavor | 公開設定と依存で起動し、明暗両flavorの読み込み・一覧描画・正常終了を確認する | Linux ARM64の隔離環境で成功。利用者も適用後のrounded表示を確認。実機のOS・実行版・明暗両flavorの結果は未記録 |
| smart-enter・toggle-pane | ダミーディレクトリとテキストでEnter、Ctrl-pの往復を確認する | 未実施 |
| git | 一時Gitリポジトリの未追跡ファイル・変更済みファイルを表示する。実リポジトリのindexを変更しない | 未実施 |
| chmod | 一時ファイルの権限だけを変更する。Termuxではホーム配下と共有ストレージを区別する | 未実施 |
| fzf・zoxide | ダミーの選択対象と隔離した履歴で移動を確認する。実際の履歴を読み出さない | 未実施 |
| bunny・session | 公開のダミーブックマークと一時セッションで動作を確認する。bunny-privateは使わない | 未実施 |

## 既存テストの範囲

`tests/test_optional_dependencies.py`はrequire・UI・通知をモック化し、追加依存欠落時の継続、setupオプション、setup失敗の伝播を確認する。実プラグインをロードしない。

`tests/test_yazi_config.py`はTOML構文とキー定義、正式な`prepend_fetchers`へのgit登録2件を確認する。任意の実起動テストはkeymapだけをコピーし、init.luaを終了用fixtureへ置き換える。fetcherの実行・flavor・追加プラグインの互換性は対象外。この差を埋めるために既存テストを弱めたり、私的設定を使ったりしない。

追加したオフラインテストは、設定で参照する公開プラグイン・flavorとmanifestの対応、完全SHAによる固定、内容ハッシュ、本体版の固定を確認する。環境別テストはmanifestだけが管理され、本体ディレクトリと私的プラグインが除外されることを確認する。

今回の公開依存を使った検証は、HOME・XDG・Git設定・実行環境を一時領域に限定した別の確認。外部fzf・zoxideの実動作は確認せず、zoxideはダミー、bunny-privateも公開のダミー設定へ置換した。公開モジュールの読み込みと明暗両flavorの描画後、正常終了した。取得時だけ通信し、通常の自動テストへネットワーク依存は追加していない。
