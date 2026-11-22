# Codex開発引き継ぎ

作成日：2026-11-17。最終更新：2026-11-22。対象は各環境のdotfiles作業コピー。

この文書は会話とリポジトリを確認してまとめた作業記録。作業規約と操作承認はAGENTS.mdに従い、再開時にはGit状態を再確認する。秘密情報の実値は記載していない。

## 現在の到達点（2026-11-22）

今回の文書整理で確認した基点は、PR #23を取り込んだ `main` の `c859580`。PR #22の `92d9336` からこの基点までの変更は引き継ぎ文書2本だけで、実装の変更はない。再開する環境ごとに作業コピーのブランチ、HEAD、未コミット変更を確認する。

現行仕様と残件は本節を参照する。「作業履歴」と1〜7節は当時の記録であり、ブランチ名、テスト件数、未実装・未決定の記述を現在の状態として扱わない。過去の操作承認も、再開後の作業への承認を意味しない。

| 環境 | 確認済みの範囲と参照先 |
| --- | --- |
| Termux本体 | 基礎パッケージ導入、Bats、共通テスト、通常のpushからのpre-push、tmux、YaziのPNG・PDF・SVG表示、グローバルとプロジェクト別Proton Passの切り替えを確認済み。NeovimのNV-06も適用後にLSP・保存時整形・SKK入力を確認した。[Termux版の引き継ぎ](CODEX_TERMUX_HANDOFF.md)・[実機チェックリスト](testing/termux-checklist.md)・[Neovim実機確認](setup/neovim-dependencies.md#nv-06適用後のtermux実機確認) |
| proot Ubuntu | プロジェクト別Proton Passの認証切り替え・保管庫の参照範囲・補完・鍵キャッシュを確認済み。NeovimのLSP、DAP、スナップショットは個別の検証記録にある範囲で確認済み。[Proton Pass手順書](setup/proton-pass.md#現在の状態)・[Neovimの依存と検証記録](setup/neovim-dependencies.md) |
| WSL2・ネイティブ・QEMUのUbuntu | 対応する環境フラグと導入方法は[環境別の検証範囲](testing/environment-matrix.md)を参照。GitHub ActionsのUbuntuで共通テストは通っている。各環境の通常起動、アプリ操作、実認証の結果は個別に確認する。 |

### 現行仕様の参照先

| 対象 | 確定済みの仕様と参照先 |
| --- | --- |
| 構築と環境制御 | 展開ソースは `home/`。Termuxは専用bootstrapとpkg、Ubuntu系はAPT・miseを使い、prootではHomebrewを除外する。[README](../README.md)・[環境別制御](testing/environment-matrix.md) |
| Proton Pass | `--profile NAME` で明示選択し、指定なしはグローバル利用。プロジェクトごとにPAT暗号文・CLIセッション・暗号化鍵・鍵キャッシュを分離する。プロジェクト側はenv限定で、既存のPAT用identityを共有する。[仕様・実装記録](setup/proton-pass.md) |
| 鍵キャッシュ | CLI暗号化鍵だけを保持し、PATとidentityはキャッシュしない。既定15分、15・30・45・60分を選択できる。[操作手順](setup/proton-pass.md#7-プロジェクト別patとキャッシュ期限の実装2026-11-18) |
| Neovim | Mason依存の除去、DAP修正、NV-06の旧設定整理は実装済み。本体はlatestを維持する。[NVタスク一覧](setup/neovim-dependencies.md#修正候補と推奨順序)・[版管理方針](setup/tool-version-policy.md) |
| スナップショット | `lazy-lock.json` はGit・chezmoi管理から除外し、必要時に手動保存する。`save`・`list`・`show`・`prepare` を備え、復元は別の明示操作で行う。[設計と確認記録](setup/neovim-dependencies.md#nv-05のスナップショット設計2026-11-17) |

直近のTermuxでの共通検証記録は、unittest 362件・Bats 18件成功、skip 0件。今回の文書整理では全体テストを再実行しておらず、現在環境での動作確認結果ではない。[Termuxの検証記録](CODEX_TERMUX_HANDOFF.md#現在の到達点2026-11-22)

### 別環境で再開する手順

1. 対象環境の中で `git status --short --branch`、`git log -3 --oneline`、`uname -sm` を実行する。proot Ubuntuはゲスト側の作業コピーを使い、Termux本体の生成hookや実行ファイルを共用しない。
2. リポジトリと対象ディレクトリの規約を読み、[初期構築手順](../README.md)と[環境別の検証範囲](testing/environment-matrix.md)を確認する。Termux本体ではpkgと専用bootstrapを使う。Ubuntu系ではAPTと既存のmise設定に従い、prootではHomebrewの自動導入を省く。TermuxとprootのProton Pass providerはenv。
3. 必要に応じて `bash bootstrap/bootstrap-tools.sh --check` で基礎ツールを確認する。終了コードと併せて不足表示を見る。必要な依存が揃った環境で `make check` を実行し、結果を環境・コミットごとに記録する。導入、設定適用、認証はAGENTS.mdに従う。[共通検証手順](testing/checks.md)

### 保留と後続作業

- ツール未導入のTermuxを用意できないため、`make bootstrap-neovim-tools` の初回一括導入は保留。既存環境での再実行と、隔離HOMEでのNimLSP初回ビルドは確認済み。[一括導入の手順](setup/dependencies.md#neovim用ツールの一括導入)
- PATの期限切れ・更新・復旧、複数プロジェクトの同時利用、sqlsの実DB接続は別途確認する。SOPSとmiseの連携は、対象プロジェクトが決まってから鍵の保管・復旧とタスクへの値の渡し方を設計する。[Proton Passの残件](setup/proton-pass.md#現在の状態)

## 作業履歴

### 初期化テンプレートの配置修正（2026-11-19）

Termuxでclone後に設定入力が出ないとの報告を受け、初期設定テンプレートをhome/.chezmoi.toml.tmplへ移動した。.chezmoirootがhomeを指定するため、従来のリポジトリ直下ではinitの探索対象にならなかった。本文評価だけだったテストに、隔離した実initで設定生成を確認する回帰テストを追加した。実機への適用・再初期化は別途行う。

### Termux検証への引き継ぎ（2026-11-19）

PR #10はmainへマージ済みで、ローカルの基点はc3fce78。利用者はmain更新後に旧作業ブランチを削除した。次はTermux本体でのdotfiles構築・検証を進める。[Termux側Codexへの引き継ぎ](CODEX_TERMUX_HANDOFF.md)に現在の状態、確認手順、承認条件と完了条件を記載した。以下の2026-11-18の作業ブランチ・PR作成前の記述は当時の記録として読む。

### プロジェクト別PATの実装記録（2026-11-18）

プロジェクト別PATは、その後の合意を経て実装され、利用者による実環境への適用・動作確認まで進んでいる。最新の仕様、検証範囲、残件は[Proton Pass手順書の「現在の状態」](setup/proton-pass.md#現在の状態)を参照する。1〜7節は2026-11-17の引き継ぎ作成時点の記録であり、「未承認」「未実装」やmainブランチに関する記述は当時の状態を示す。

作業ブランチはdocs/proton-pass-project-pat-designで、基点は7b60306。実装・テスト・文書をまとまりごとにコミットし、push・PR作成を行うよう利用者から依頼済み。再開時にはGit履歴・PR・作業ツリーの状態を確認し、残っている変更を保護する。

承認済み・実装済みの範囲は、--profileによる明示選択、プロジェクト別保存配置、プロジェクト側env限定、既存PAT用identityの共有、初期登録コマンド、3コマンドの補完、鍵キャッシュの15・30・45・60分選択、prootのUID対応、残り時間の分・秒表示。グローバルの既存利用は維持する。

利用者は、既存グローバルの認証、pat-testの認証、3コマンドのTab候補、30分キャッシュの開始、分・秒表示を確認済み。最新報告ではグローバル→pat-test→グローバルで認証先が想定どおり切り替わり、テスト用PATで許可した1つの保管庫だけが一覧に表示された。詳細は手順書10〜11節に記録している。

2026-11-18に差分の最終レビューとコミット前のmake checkを実施し、unittest 347件・Bats 18件（skip 0件）が成功した。表示変更と認証切り替えの関連テスト・隔離検証も成功済み。本ブランチの実装・文書整理・最終検証は完了している。実機で未確認の範囲は手順書冒頭に記載した。

SOPS用鍵のローカル保護方法とmise・SOPS連携は後続の設計・実装対象。下記のNeovim関連の次作業案は、今回のPAT対応とは別の作業として扱う。

## 初版の引き継ぎ記録（2026-11-17）

以下の1〜7節は初版を基にした履歴。プロジェクト別PATの実装前の検討、NV-06の未完了、当時のGit状態と検証結果を残している。現在の作業を選ぶときは、冒頭の「現行仕様の参照先」と「保留と後続作業」を使う。

## 1. プロジェクトの目的と現在の範囲

chezmoiを中心に、複数Linux環境のdotfiles、開発ツール、初期構築、秘密情報管理を一元化する。主な対象はTermux、proot Ubuntu、WSL2 Ubuntu、ネイティブUbuntu。QEMU Ubuntuの環境識別も実装されている。実機で確認した範囲は後述する。

開発ツールは主にmise、OS依存はAPT、補助ツールはHomebrew、秘密情報はProton Pass CLIとageで扱う。`.chezmoiroot`は`home`を指定し、`home/`がホームへ展開するソース。展開先の設定を直接編集せず、ソースを変更する。

これまでの主要な手動確認環境はTermux + proot Ubuntu、Neovim v0.12.6。これは検証時の版であり、latestの現在の導入版を保証しない。

直近はNeovim依存整理を進め、Mason依存の除去、DAP修正、lockfileのスナップショット運用まで完了した。次の作業として、Proton Pass CLIラッパーでdotfiles用に加えて開発プロジェクト別のPATを使えるようにしたい、という利用者の希望がある。新機能の実装はまだ始めていない。

## 2. 確定済みの設計・決定事項

### 作業規約と配置

- 日本語で応答・記述し、現在の共通規約、ルートと対象フォルダのAGENTS.mdを読む。
- プロジェクト専用スキルは`.agents/skills/`を維持する。共通スキルの配布元は`home/dot_agents/skills/`、展開先は`~/.agents/skills/`。専用スキルを共通配置へ移さない。
- 本環境の`~/.codex/AGENTS.md`の参照先は`~/.config/ai-agents/AGENTS.md`。その配布元は`home/dot_config/ai-agents/AGENTS.md`。
- 秘密情報・鍵・復号結果・秘密変数は読み取らない。秘密情報の取得・表示・記録、新しい認証方式・保存場所、実適用、パッケージ操作、外部通信、commit・push等はAGENTS.mdの承認条件に従う。
- 以前の操作承認を次タスクへの一括承認とみなさない。今回の引き継ぎ作成は文書作成のみ。

### 環境とツール

- Ubuntu向けAPT・mise設定をTermux単体へ適用しない。prootとTermuxはOS名やPREFIXだけで区別せず、既存の環境フラグを使う。
- Termux・prootのProton Pass providerはenv。対応するUbuntu系はenvまたはkeyringで、後者はSecret Service等の条件を必要とする。
- 通常の設定適用とツールの更新を区別する。`update_apps mise`は`mise --cd "$HOME" outdated`と`upgrade`を使う。
- Neovim本体は**固定しない**。`neovim = "latest"`を維持し、miseの一括更新時に他ツールと同時に更新する。固定候補を選ぶという過去の案は最新の合意ではない。

### Neovimとスナップショット

- LSP・formatter等の実行ファイルはmise・補助導入・プロジェクト依存で用意し、Mason依存の宣言とsetupは除去済み。既存Masonデータの削除はしていない。
- Pythonはbasedpyrightが型解析・補完・定義ジャンプ、Ruffがlint・import整理・整形を担当する。
- DAPのアダプターはmiseのdebugpy、対象Pythonはプロジェクトのvenvを使い分ける。古いmise Pythonは既存ツール用に残し、新しいPythonはuvでプロジェクト単位に用意する運用を尊重する。
- プラグインを頻繁に試すため、`lazy-lock.json`を通常のGit管理・chezmoi展開から除外する。公開プラグインを共有lockfileで常時固定する案は採用しなかった。
- LSP・補完・Treesitter等の大きな変更前に、必要に応じて`nvim_snapshot save`で手動保存する。自動保存・自動削除・クラウド同期は実装していない。
- 保存先は`${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles/neovim-snapshots/<app>/`。`app`はNVIM_APPNAME、既定nvim。原本とmetadata.jsonを日時・ランダムID単位で保存する。
- 記録内容は設定コミット、未コミット変更有無、Neovim・lazy.nvimの版、SHA256等。専用領域は0700/0600、共用親は本人所有・他者書き込み不可。既存の権限を自動変更しない。
- `save`・`list`・`show`・`prepare`を実装。Bash・Zsh共通関数はPythonへ引数・終了コードを渡すだけで、読み込み時にPythonを起動しない。
- 自動巻き戻しは採用しなかった。復旧前に退避し、設定履歴と保存原本を確認してから明示操作で戻す。Neovim本体・プラグイン本体・パーサー・外部ツールのバイナリバックアップではない。

### Proton Passの現在の実装

以下は2026-11-17のソース確認時点の仕様。第6節の未決事項は、その後のプロジェクト別PAT対応で決定・実装された。現行仕様は冒頭の参照先を確認する。

| 対象 | 現状 |
| --- | --- |
| 通常ラッパー | `home/dot_local/bin/executable_proton-pass.tmpl` |
| PAT | `${XDG_DATA_HOME:-$HOME/.local/share}/proton-pass/token.age`を単一の入力として使う |
| identity | AGE_IDENTITY_FILEで上書き可能。既定はage配下のid_proton_pat.age |
| PATの利用 | login時のみ復号し、pass-cliのPROTON_PASS_PERSONAL_ACCESS_TOKENへ渡す。他の操作では同変数をunsetする |
| provider | テンプレートのprotonPassProviderと上書き値の一致を要求し、env/keyringを扱う |
| env方式 | `proton-pass-key-cache.py`へ委譲し、pass-cliに必要なデータベース暗号化鍵を渡す |
| キャッシュ | encryption-key.ageとランタイムディレクトリを使う。既定TTL 900秒、上限3600秒。常駐プロセスへPAT・暗号化鍵を継承させない処理がある |
| 初期認証 | `bootstrap/setup-proton-pass.sh`。token.ageとencryption-key.ageを扱い、既存鍵・暗号文の保護やprovider確認を行う |
| chezmoi | `home/.chezmoi.toml.tmpl`のprotonPass.commandはホーム配下の通常ラッパーを指す |

キャッシュはPATそのものを保持する仕組みではない。次の設計で、PAT、CLIのログイン状態、データベース暗号化鍵を混同しないこと。

## 3. 実装状況

| 分野 | 状況 |
| --- | --- |
| bootstrap・環境制御・日常更新 | 基礎導入と環境別制御、通常導入と更新の分離、回帰テストを整備済み。全環境の実機完了とは扱わない |
| CI・PR・hooks | `.github/workflows/check.yml`とlefthookを実装。pre-commitはstage差分確認、pre-pushはmake check |
| Neovim NV-03 | 確認済み環境・用途でMason除去と主要LSP・整形の移行を完了 |
| NV-04 | Python・LuaのDAP修正、debugpy導入定義、回帰22件、通常UI確認を完了 |
| NV-05 | 保存CLI・共通関数・Git除外・手順を実装。実機保存、復元準備、Lazy restore後の主要機能を確認し完了 |
| プロジェクト別PAT | 未実装。利用者の希望と実施順序だけ確認済み。設計・操作仕様・保存形式は未決定 |
| NV-06 | 旧LSP・整形・SKK設定の用途確認と整理が残る。PAT対応との依存は現時点の静的確認では見当たらない |

本書作成時点で実装中のコードはない。現在の作業は引き継ぎ文書の作成だけ。

## 4. 直前の作業状態

### Gitとマージ

- リポジトリ：`/home/shioyaki/.local/share/chezmoi`。
- 現在ブランチ：`main`、HEAD：`7b60306`（PR #9のマージ）。ローカルGitで確認した。
- PR #9：[lockfileスナップショットによる保存・復旧を整備](https://github.com/shioyakizakana/dotfiles/pull/9)。利用者がGitHub Actions成功を確認後にマージし、mainをpullして作業ブランチを削除したと報告。リモートへの再照会は今回していない。
- 作成前の作業ツリーはクリーン。作成後の未コミット変更は本書`docs/CODEX_HANDOFF.md`のみとなる。commit・pushは依頼されていないため行わない。
- 直前の作業ブランチはchore/neovim-reproducibility。次タスクのブランチはまだ作成していない。

PR #9のコミットは、2563be9（Python CLI・テスト）、311ee38（共通関数・Git除外）、26a3ef3（設計・確認記録）、77042da（実復旧結果・latest方針）。

### 直前の変更ファイル

| ファイル | 内容 |
| --- | --- |
| `home/dot_local/bin/executable_nvim-snapshot.py` | 保存・表示・整合性確認・復元準備 |
| `home/dot_config/shell/functions.sh` | nvim_snapshot共通関数 |
| `home/dot_config/shell/env.sh` | 共通関数の読み込み |
| `.gitignore` | ソース側のlazy-lock.jsonを明示除外 |
| `tests/test_neovim_snapshot.py` | スナップショットの回帰32件 |
| `tests/test_shell_config.py` | 共通関数とGit除外の5件を追加 |
| `tests/check.py` | 共通関数を静的確認へ追加 |
| `.agents/skills/dotfiles-test-runner/references/commands.md` | 対応テストの案内 |
| `docs/setup/neovim-dependencies.md` | 設計・実装・利用者確認・復旧手順 |
| `docs/setup/tool-version-policy.md` | Neovimはlatestを維持する方針 |

### 検証と利用者確認

- 直近のpre-pushを含むmake checkは、unittest **306件**・Bats **18件**が成功し、skipなし。今回の文書作成で全体テストは再実行しない。
- Pythonの回帰はダミーlockfile・偽Git/Neovim・隔離HOMEを使用。権限、形式、SHA256、異常時の後始末、ID衝突、同時保存、公開直後の割り込みを確認した。
- ShellCheck・shfmt・構文確認と追加文書のtextlintを実施済み。natural-japaneseの統計指摘は用語・手順を優先して残した箇所がある。
- Codexは実機のlockfileを非公開領域へ保存し、一覧・show・prepareと一時領域への原本復元を確認した。稼働中のlockfileは上書きしなかった。
- 利用者はchezmoi apply後、共通関数とlist・show・prepareが警告なく標準出力されることを確認した。
- 利用者はNeovim終了後に復旧直前の保存を行い、過去の原本を実機へ戻して`:Lazy restore`を実行した。/tmp以下の確認用環境で起動、LSP接続・補完・診断、保存時整形、Treesitter表示、DAPに異常がないと報告した。Codexによる再実行結果とは区別する。

記録済みの保存IDは`20261117T031547Z-41a4638b`。保存時には未コミット変更があり、設定コミットだけで当時の内容を完全再現できるとは扱わない。実機データの所在は`docs/setup/neovim-dependencies.md`を参照する。今回それらのファイルは読み直していない。

## 5. 未解決事項・注意点

- **既知の観測**：NV-04の隔離自動検証でdebugpyアダプター終了コード1が一度記録されている。後続の通常UI確認では警告なし。原因・恒久的解消は未確認で、現在必ず失敗する不具合とは扱わない。
- **prootの制約**：uvのonly-managed指定で、実体はuv管理でもパス表現の違いから既存venvの不整合・再作成を確認した。検証用プロジェクトではmanagedと版指定を使い、グローバル設定は変更していない。詳細はuv DAP検証文書。
- **対象外の確認**：sqlsの実DB機能、Termux単体・WSL等での各実機操作、lazy.nvimの実通信を伴う初回取得・失敗復旧、取得元消失時の復旧は、すべて確認済みとは扱わない。
- **文書の履歴**：監査文書やNeovim文書には、当時の「未適用」「未実装」「commit未実施」が残る。最新の完了記録・コード・今回の利用者報告を優先し、古い状態を現在の不具合として再報告しない。
- **一時ファイル**：過去の/tmp確認用プロジェクトやログは消失し得る。永続資料はdocsを使い、必要ならダミーで作り直す。
- **Git運用**：mainはPRとcheck必須にしたと利用者から報告済み。auto-mergeとブランチ自動削除も有効化報告あり。直pushや自動マージを勝手に行わない。
- **認証の過去事例**：このセッションのSSH pushはpublickeyエラーになり、ghの既存認証を使うHTTPS pushで成功した。originのSSH URLや認証設定は変更していない。今の認証状態を保証する記述ではない。トークンの取り出し・表示で解決しない。

## 6. プロジェクト別PATの設計案（実装前の記録）

### 最優先：プロジェクト別PAT対応の設計

**確定した希望**：dotfiles用のグローバルなPATを維持し、開発プロジェクトごとに作成したPATもラッパーから使えるようにしたい。NV-06より先に進めることへの既知の依存上の支障は見当たらない。

**未決定・要確認**：

| 確認事項 | 現時点の状態 |
| --- | --- |
| PATの用途 | 現行コードのPATはProton Passログイン用。新しいPATも同用途か、GitHub等の別サービスのPAT取得・注入を指すかは、利用者へ明確に確認する |
| 選択方法 | 明示オプション、コマンド単位の指定、プロジェクト設定による選択等は未選定。カレントディレクトリから自動切替する仕様は合意していない |
| 保存・初期設定 | 暗号化PATの配置、登録方法、既存token.ageからの互換性、identityの共有範囲は未決定 |
| 状態分離 | pass-cliのログイン状態、暗号化鍵・キャッシュ・ソケット・keyringを何単位で分けるか未決定。CLI側の対応能力も未調査 |
| 対象環境 | 現行のenv/keyringをどこまで同時に対応させるか、まず利用する環境を確認する |

単一ファイルの名前差し替えだけで解決すると決めつけず、CLIの認証状態と鍵キャッシュへの影響を確認する。一方で、不要な汎用アカウント管理機構まで拡張しない。

### 推奨順序

1. 本書とAGENTS.mdを読み、Git状態を確認する。未コミットの本書を保護し、次タスク用のブランチをmainから作る。ブランチ名の例は`feat/proton-pass-project-pat`だが、作成済みではない。
2. 通常ラッパー・bootstrap・initラッパー・鍵キャッシュ・chezmoiの呼び出し元を静的に読む。secret-management-reviewと既存の対応表を使い、実認証や秘密ファイルで現状を調べない。
3. 上記の用途と最小の選択仕様を利用者と決める。新しい保存場所・認証方式・依存が必要なら、具体案と互換性を示して承認を得る。公式資料の外部参照も必要な承認を確認してから行う。
4. 最小の仕様を設計文書へ記録し、既存のグローバル利用とプロジェクト指定のテストをダミーで追加する。その後、共通箇所から修正し、必要なbootstrap・文書・呼び出し元を合わせる。
5. 対象テストと隔離テンプレート検証、最後にmake checkを実行する。実機の認証・登録・移行は別に承認を得るか、利用者へ手順を渡す。
6. 変更目的・結果・未確認・残件を報告する。commit・push・PRはその時点の明示依頼に従う。NV-06と他環境の確認は別作業として残す。

### 提案段階の完了条件と検証

以下は新しいPAT機能の確定仕様ではなく、設計時に合意すべき確認条件。

- 従来の指定なし利用で、dotfiles用認証とchezmoiからの参照が従来どおり動作する。
- プロジェクト用を明示指定した場合に意図したPAT・認証状態だけを使い、不正・未登録の指定は復号やログインより前に停止する。
- 異なるプロジェクトの実行が混線せず、対象外の子プロセスや常駐キャッシュへPATを継承しない。
- PAT・鍵・復号結果を引数、ログ、標準出力、Git、恒久環境変数へ漏らさない。取得した値を出す機能が必要なら、別途用途・出力範囲を明示して合意する。
- 対応するprovider、秘密ファイル欠落、権限、シンボリックリンク、認証失敗、再実行、同時実行を、隔離HOME・ダミーデータ・モックで検証する。

既存テストを読むときは、PATのキャッシュではなくデータベース鍵のキャッシュを検証している点に注意する。

```sh
python3 -B -m unittest discover -s tests -p test_proton_pass_setup.py -v
python3 -B -m unittest discover -s tests -p test_proton_pass_key_cache.py -v
make check
```

上記は次タスクの候補コマンド。新しいコード・fixtureの副作用を確認してから実行する。実HOMEのchezmoiテンプレートを直接評価しない。

## 7. 参照すべきファイル

| 分類 | ファイル |
| --- | --- |
| 最優先の規約 | [AGENTS.md](../AGENTS.md)、[home/AGENTS.md](../home/AGENTS.md)、[tests/AGENTS.md](../tests/AGENTS.md)、[共通規約の配布元](../home/dot_config/ai-agents/AGENTS.md) |
| 規約・スキル配置 | [移動対応表](agents/rule-mapping.md)、`.agents/skills/`、共通のcoding-workflow・implementation-planning・systematic-debugging・natural-japanese |
| 秘密管理の確認手順 | [secret-management-review](../.agents/skills/secret-management-review/SKILL.md)、[確認観点](../.agents/skills/secret-management-review/references/checklist.md) |
| テンプレート・テスト | [chezmoi-template-validation](../.agents/skills/chezmoi-template-validation/SKILL.md)、[テスト対応表](../.agents/skills/dotfiles-test-runner/references/commands.md)、[共通チェック](testing/checks.md) |
| Proton Passのソース | [通常ラッパー](../home/dot_local/bin/executable_proton-pass.tmpl)、[鍵キャッシュ](../home/dot_local/bin/private_executable_proton-pass-key-cache.py.tmpl)、[initラッパー](../home/dot_local/bin/executable_init-proton-pass.tmpl)、[bootstrap](../bootstrap/setup-proton-pass.sh) |
| Proton Passの呼び出し元 | [初期設定テンプレート](../home/.chezmoi.toml.tmpl)、[Git設定テンプレート](../home/dot_gitconfig.tmpl)、[Makefile](../Makefile) |
| Proton Passの検証 | [setupテスト](../tests/test_proton_pass_setup.py)、[鍵キャッシュテスト](../tests/test_proton_pass_key_cache.py)、[利用者向け手順](setup/proton-pass.md) |
| Neovimの設計と履歴 | [依存・NVタスク一覧](setup/neovim-dependencies.md)、[版管理方針](setup/tool-version-policy.md)、[DAP手順](setup/neovim-dap.md)、[uv DAP検証](testing/neovim-uv-python-dap.md) |
| 直近の実装 | [スナップショットCLI](../home/dot_local/bin/executable_nvim-snapshot.py)、[共通関数](../home/dot_config/shell/functions.sh)、[mise設定](../home/dot_config/mise/config.toml)、[スナップショットテスト](../tests/test_neovim_snapshot.py) |
| 全体の背景 | [README](../README.md)、[監査・改善履歴](reviews/dotfiles-audit.md)、[環境別制御](testing/environment-matrix.md)、[PR運用](testing/pull-requests.md) |

本書はtextlint・natural-japanese、ローカルリンク、テスト件数、差分書式を確認した。既存の全体テスト結果を再利用し、実認証・復号・設定適用・パッケージ操作・外部通信は行っていない。
