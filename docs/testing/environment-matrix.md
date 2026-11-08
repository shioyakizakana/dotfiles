# 環境別制御とTermux相当のテスト

DF-04の環境別制御は、実際のインストールをせずに再現できる。chezmoiの環境データ、PREFIX相当のディレクトリ、PATH、ユーザーID、外部コマンドをテスト用に用意する。

## 実行するコマンド

Python 3.11以上、Bash、chezmoiを利用できる検証環境で、リポジトリのルートから実行する。依存のインストールはこれらのテストに含まない。

```shell
# 環境選択、初期設定データ、tmuxのシェル選択
python3 -B -m unittest discover -s tests -p test_environment_policy.py -v

# root・sudo・APT失敗の再現
python3 -B -m unittest discover -s tests -p test_install_apt.py -v

# Homebrewの導入判定とroot時の新規導入禁止
python3 -B -m unittest discover -s tests -p test_install_brew.py -v

# miseの導入済み判定・再適用・失敗後の再試行
python3 -B -m unittest discover -s tests -p test_mise_helpers.py -v

# 明示的なAPT更新のroot・sudo処理
python3 -B -m unittest discover -s tests -p test_update_apps.py -v

# 上記と既存のPython回帰テスト
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

chezmoiがない場合、環境選択のテストは明示的にskipされる。成功件数だけでなく、skipの有無も確認する。

## 導入対象の期待値

| 環境フラグ | APT | Homebrew | mise一括導入・管理設定 |
| --- | --- | --- | --- |
| nativeUbuntu・wslUbuntu・qemuUbuntu | 対象 | 対象 | 対象 |
| prootUbuntu | 対象 | 既存Bundleも含めて対象外 | 対象 |
| termux | 対象外 | 対象外 | 対象外 |
| 未指定・未知・未対応OS | 対象外 | 対象外 | 対象外 |

APTはrootなら直接実行し、非rootならsudoを必要とする。導入済みなら権限確認と対話も省く。パッケージ一覧の更新が失敗した場合はinstallへ進まない。Homebrewはrootでの新規導入をスキップする。対応Ubuntuに既存brewがある場合の処理は維持し、実際のbrewの権限制約までは模擬しない。

環境別の対象選択は、chezmoi経由の適用に対して働く。`.chezmoiscripts/`のスクリプトを直接起動すると除外設定を経由しないため、単体実行を環境判定の代わりに使わない。

## Termuxとprootを区別する条件

- `.chezmoi.os`がlinuxでも、termuxフラグがtrueならTermuxとして除外する。
- Android版chezmoiを使うproot・QEMUも既存の初期設定が想定している。OS名だけでTermuxと判断せず、ゲスト環境のフラグを確認する。
- termuxフラグがtrueの場合は、Ubuntuフラグが混在していても導入対象にしない。
- prootへPREFIXが引き継がれていても、prootUbuntuフラグでAPT・miseを選ぶ。
- TermuxではUbuntu用mise設定も対象外にする。既存のTermux側設定は取り込まず、上書きしない。Termux向けツール選定と導入手順はDF-09で検討する。

## テストで再現している内容

`test_environment_policy.py`は一時ディレクトリ内に次の構成を作る。実際のホームディレクトリを展開先にしない。

```text
一時ディレクトリ/
├── source/       # ignore設定、実行されないダミースクリプトなど
├── home/         # 検証用の展開先パス
├── config.json   # テストごとの環境フラグ
├── cache/        # 検証用chezmoiキャッシュ
├── state.db      # 検証用chezmoi状態
└── data/data/com.termux/files/usr/bin/
    └── zsh      # 探索だけに使う実行属性付きダミー
```

PATHはこのPREFIX相当のbinだけとし、ホストの`/bin/zsh`や`/usr/bin/zsh`を探索しない。ARM64のメタデータとlinux・androidのOS値を渡し、初期設定からのフラグ生成も確認する。zsh未導入の場合はtmuxのdefault-shellを指定せず、tmux既定の選択を維持する。

chezmoiは明示した検証用config・source・destination・cache・persistent-stateだけを使用する。ソースには秘密取得テンプレートや外部取得設定を持ち込まず、`managed`と`execute-template`のみ実行する。`apply`、`init`、実スクリプトの実行は行わない。

APTのテストはid・apt・sudoをダミーに置き換える。実際のUIDやsudo権限を変更せず、root・非root・sudo欠落を再現する。Homebrewのテストも探索と取得を置き換え、実際の通信・導入を行わない。

## 実機確認が必要な内容

このテストはAndroidのカーネル、Bionic、prootそのものをエミュレートしない。ARM64メタデータを渡すことも、ARM64バイナリの動作検証とは異なる。次の項目は実機確認の残件とする。

- Termuxの実際のPREFIX、実行ファイル、シバン解決とtermux-execの有無。
- 共有ストレージ上の実行属性・リンクなど、Android固有のファイルシステム制約。
- 各ツールのAndroid／ARM64対応と、Ubuntu向けバイナリとの互換性。
- prootでのUID・権限の見え方、実際のAPTやHomebrewの制約。
- 起動済みtmuxへの設定反映と、実際のzshによるペイン起動。

## 通常適用と更新の分離

| 処理 | 通常適用で行うこと | 通常適用で行わないこと |
| --- | --- | --- |
| APT | dpkg-queryで不足を調べ、確認後に不足分をinstall --no-upgrade | OS全体のupgrade |
| Homebrew | Brewfileの構文と依存を確認し、不足があればbundle install --no-upgrade | 自動refresh、明示的なupgrade、cleanup |
| mise | ホームの設定が要求する不足分をinstallし、Rust・LuaRocks・nimlspを確認 | mise useによる設定の書き換え、upgrade |

APTのlibz-devは仮想名なので、導入済み判定には実パッケージ名zlib1g-devを使う。ローカルのdpkgメタデータで提供関係を確認した。

miseのツール一覧は管理対象TOMLへまとめた。従来のPython 3.13・3.12とchafaも維持する。処理は作業中のプロジェクトではなくHOMEで実行するため、HOME配下で読み込まれる利用者の追加設定もmiseの通常の優先順位に従う。設定の信頼確認で停止した場合も、自動でtrustは実行しない。

導入後の補助コマンドにはmiseのPATH情報だけを渡す。env全体を表示・評価しない。Rust固有の環境変数など、PATH以外の設定が必要な実環境での動作は別途確認する。

Homebrewのno-upgradeは明示的なupgradeを抑えるが、不足する依存の導入に必要な既存依存の更新まで禁止するものではない。APTにも依存解決がある。miseのlatest指定では、設定が要求する未導入バージョンが導入されることがある。完全なバージョン再現性はDF-06の残件とする。

日常更新には既存の明示的なコマンドを使う。次は利用者が更新を選択した場合の操作例であり、テストから実行しない。

```shell
update_apps apt
update_apps brew
update_apps mise
```

update_apps aptはrootならsudoを使わず、非rootならsudoを必要とする。既存のautoremove・autocleanも含むため、実行前に処理内容を確認する。

## 再適用と中止の扱い

3本ともrun_afterを維持し、毎回ツール自身の導入状態を確認する。独自の完了ファイルやrun_once・run_onchangeによる実行済み記録は作らない。確認結果に不足がなければ、入力も導入も省く。構成変更で不足が生じた場合は次回に再評価する。

| 状態 | 終了と再試行 |
| --- | --- |
| 対象外・不足なし | 正常終了。対話や導入を省く |
| 明示的な辞退 | 中止を表示して正常終了。未導入のままなので次回再試行できる |
| EOF | 理由を示して非0で終了。自動承認しない |
| 確認・導入の失敗 | 非0で終了し、後続へ進まない。次回に状態を再確認する |

miseは導入後にも不足を確認し、未導入が残る場合は成功扱いにしない。内部の辞退と導入コマンドの終了コードも区別し、同じ番号のエラーを正常終了へ変換しない。

再適用テストでは、ダミーのパッケージ管理状態を変化させて、初回導入・変更なし・構成変更・失敗・辞退・EOF・再試行を確認する。ダミーの状態ファイルはテスト用であり、実装の完了記録ではない。

コードとモックで確認できる範囲は実装済み。実際の配布元、Brewfileの各項目、LuaRocks・Nimbleのパッケージ提供状況は未検証。実環境への適用は別途承認を得て行う。
