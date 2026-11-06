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

APTはrootなら直接実行し、非rootならsudoを必要とする。パッケージ一覧の更新が失敗した場合は、upgradeやinstallへ進まない。Homebrewはrootでの新規導入をスキップする。対応Ubuntuに既存brewがある場合の処理は維持し、実際のbrewの権限制約までは模擬しない。

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

OS全体のupgradeを通常適用から分離すること、run_afterの再実行条件、対話と終了状態の統一はDF-04の後続段階に残す。実環境への適用は別途承認を得て行う。
