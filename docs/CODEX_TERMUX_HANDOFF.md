# Termux実環境のdotfiles検証：Codex引き継ぎ

作成日：2026-11-19。最終更新：2026-11-27。対象はTermux本体で動くCodexとdotfilesの作業コピー。proot Ubuntuなどで再開する場合は[全体版の環境別手順](CODEX_HANDOFF.md#別環境で再開する手順)を参照する。

<a id="現在の到達点2026-11-22"></a>
<a id="現在の到達点2026-11-23"></a>

## 現在の到達点（2026-11-27）

今回の基点はPR #27を取り込んだ `main` の `4ab32d7`。利用者の依頼で、このmainから `test/proton-pass-recovery` を作成した。Proton Passの更新・復旧・同時利用・キャッシュ期限の隔離結合テスト6件と、利用者の実機確認手順を追加し、その後のTermux・prootの実機報告を文書へ反映した。Codexは製品コードと実際の認証情報を変更していない。

PR #24ではREADME・docsの現行仕様と過去記録を整理し、長いセクションを分割した。PR #25〜#27の完了内容は次節を参照する。下記の基礎ツール・Neovimの実機結果は以前の記録を維持し、今回のProton Pass実機結果は後述する。作業再開時は、対象端末内でブランチ、HEAD、未コミット変更を確認する。

- Termux本体で基礎パッケージ導入、設定適用、lefthook 2.2.2とBats 1.13.0の動作を確認した。PR #22の通常pushでpre-pushが起動し、静的検証・unittest 362件・Bats 18件が通過した。skipは0件。[実機チェックリスト](testing/termux-checklist.md)・[共通テストの手順](testing/checks.md)
- 利用者が、設定適用後にzenoのソケット不具合が再発していないことを確認した。展開済みの共通PATH設定はソースと一致し、隔離Bash・ZshのPATH回帰テストは5件通過した。tmuxのウィンドウ操作・ペイン分割と、YaziのPNG・PDF・SVGプレビュー、報告済みのプラグイン操作も確認した。TermuxのSVG表示にはImageMagickを使う。[実機チェックリスト](testing/termux-checklist.md)・[SVGプレビューの手順](setup/dependencies.md#termuxでのsvgプレビューと変換)
- 利用者がプロジェクト別PATを登録し、グローバル、テスト用プロファイル、グローバルの順に認証先を確認した。前後のグローバルの認証先は一致し、テスト用プロファイルでは許可した保管庫1件だけが表示された。[実機チェックリスト](testing/termux-checklist.md)
- PR #22でNeovimの旧LSP・整形・SKK設定を整理した。適用後の通常起動でLSP接続・保存時整形・skkeluaによる日本語入力を確認した。Svelte・Tailwindの起動パスも確認済み。[NV-06の実機結果](setup/neovim-dependencies.md#nv-06適用後のtermux実機確認)

### PR #25〜#27の完了内容とTermuxでの扱い

- PR #25ではproot Ubuntuの既存Linux版miseを優先し、npm CLIによる導入とCodex・Oxlint・TypeScriptの起動確認を追加した。Nodeをlatestへ変更し、npm関連20ツールを3日、その他を24時間保留する。利用者がprootで起動確認と `upd mise` の正常終了を確認した。Ubuntu向けmise設定はTermux本体へ展開せず、Termuxのpkg運用を維持する。[更新方針](setup/tool-version-policy.md)
- PR #26ではnvim-scrollbarをv2の書式へ移行した。利用者が設定適用・プラグイン更新・再起動後に通知の解消と正常表示を確認した。[移行記録](setup/neovim-dependencies.md#nvim-scrollbar-v2への移行)
- PR #27ではキーマップの競合とQuicker等の設定不備を修正し、descriptionを `[処理の種類]処理の内容` の日本語へ統一した。内部生成分はwhich-keyとSnacksの表示時に変換する。利用者がLSP・Quickfix・再配置キーと日本語表示を確認した。[キーマップの記録](setup/neovim-dependencies.md#キーマップの衝突整理2026-11-23)

PR #27のpre-pushではunittest 385件・Bats 18件、skip 0件で成功し、Lua 21ファイルの静的検証とGitHub Actionsも成功した。これらをTermux本体での再検証結果とは扱わない。Termuxの直近の記録は上記の362件・18件を維持する。共通のNeovim変更をTermuxへ適用する際は、その環境で起動とキー操作を確認する。

### Proton Pass検証の到達点

Proton Passの隔離結合テストでは、既存の隔離HOME・ダミー鍵・偽CLIを使い、復旧時のデータ維持、A・Bの並列実行と同一プロファイルの排他、短いTTLでのキャッシュ停止を確認した。追加6件の3回繰り返しは計18件成功した。[全体版の検証結果](CODEX_HANDOFF.md#proton-pass検証の進め方)を参照する。

最終の `make check` はunittest 391件・Bats 18件、skip 0件で成功した。Proton Pass関連71件を含み、初回の起動待ちタイムアウトは[検証記録](setup/proton-pass.md#隔離結合テストの範囲)に残している。今回はLinux環境の結果であり、Termux本体での再検証ではない。

Termuxでこの作業を再開する場合も、Codexの隔離検証では実PAT・実鍵・実セッションへアクセスしない。Unixソケットのパス長とアプリ領域の権限は既存fixtureの条件を維持する。実サービスでの認証・PAT更新は利用者の実機確認として分ける。上記の追加テストは、Termux本体での実行結果ではない。

利用者の2026-11-25〜27の記録では、Termux 0.118.3・pass-cli 2.7.1で2プロファイルの登録、2機種での同時・順次利用、Aのlogout・lock後のBとglobalの認証維持、5秒TTLと再unlockが成功した。同じPATの再登録と別の新PATへの更新でも、CLI暗号化鍵・共有identity・recipientと他の認証を維持した。

長時間経過後のinfo失敗から、明示的なloginとinfoがともに終了コード0となる復帰も確認した。失敗原因は未確定で、自然失効の確認済み結果には含めない。実行版、日時、エラーと未記録項目は[利用者の実機確認結果](setup/proton-pass.md#利用者の実機確認結果)を参照する。調査用の記録MarkdownはGitへ追加しない。

### 次に確認すること

ツール未導入のTermuxを用意できないため、`make bootstrap-neovim-tools` の初回一括導入は保留。導入済み環境で不足分の再取得がないことと、隔離HOMEでのNimLSP初回ビルド・配置は確認済み。新規環境を用意できたときは、初回実行から再実行まで確認する。[一括導入の手順](setup/dependencies.md#neovim用ツールの一括導入)

今回の結合検証追加・手順整備・実機結果の整理は完了。初回の検証用キャッシュ起動待ちタイムアウトとTermuxのinfo失敗の原因特定、PATそのものの期限経過による失効、logout失敗時の実機復旧、未許可項目への直接アクセス拒否は未確認として残す。sqlsの実DB接続とSOPSの鍵保護・mise連携の設計は別タスク。[後続作業と別環境への引き継ぎ](CODEX_HANDOFF.md#保留と後続作業)

## 作業履歴

以下は各時点の状況と確認手順。未完了の記述や当時のブランチ名は、上の到達点と照らし合わせる。導入・設定適用・認証はAGENTS.mdの承認条件に従う。

### zenoのSQLite読み込みエラー（2026-11-21）

利用者はPR #15のマージ・取得後、Termuxでbootstrap-tools.sh --checkとmake bootstrap-toolsを実行し、各種ツールを導入したと報告した。Zsh再起動では、zenoが取得したSQLite共有ライブラリの依存libm.so.6を読み込めず、ソケットサーバーの起動に失敗した。以下のpkg一括導入前の記録は当時の状態として読む。

修正ではTermuxフラグが有効なZsh設定だけ、読み取り可能なPREFIX/lib/libsqlite3.soをDENO_SQLITE_PATHへ設定する。既存の明示指定を保持し、Ubuntu・prootは変更しない。libsqliteは既存のPythonの依存に含まれるため、追加導入は行わない。秘密情報、zenoの履歴、Denoキャッシュにはアクセスしていない。

次は[SQLiteエラーの確認手順](setup/dependencies.md#zenoのsqlite読み込みエラー)で、ライブラリの存在と一時指定でのzeno起動を実機確認する。新しい設定の限定適用は利用者が差分を確認して行う。Codex側では隔離テストを使い、Termuxでの実起動・適用は行っていない。

### pkg導入の追加（当時の記録）

利用者はPR #14のマージ・取得後、修正版をTermuxへ適用し、chezmoi applyの正常終了を確認した。以下のシバン修正後のapply未確認という記述は当時の記録として読む。

今回の変更では、bootstrap-tools.shがTermux本体と確認できた場合に限り、Proton Pass CLI・Codexとpkg対応の開発ツールを導入する。対象は同スクリプトのTERMUX_PACKAGES。Ubuntu用mise設定・導入処理はTermuxへ展開せず、重複導入を防ぐ。Ubuntu・prootの導入方法と認証の初期化処理は変更しない。

次は[Termuxの導入手順](setup/dependencies.md#termuxでの導入と実機確認)で対象一覧と不足を確認し、利用者の承認範囲でbootstrapを実行する。make bootstrap-toolsでも実行可能。既存のローカルmise設定と導入済みツールは削除しないため、PATHの競合、pkg版の違い、LSP・DAPの不足を確認する。新しい一括導入はモック検証の対象であり、Termux実機での成功はまだ確認していない。

### chezmoiからのラッパー起動失敗と修正（2026-11-20追記）

PR #13はmainへ取り込み済み。別セッションのハードリンク対応後、利用者はTermuxでpkg install proton-pass-cliを実施し、基礎bootstrap、ラッパー経由のPATログイン、保管庫一覧表示、ssh-agent起動の成功を報告した。続くchezmoi applyは.gitconfigのprotonPassからラッパーを直接起動する段階で停止した。以下のbootstrap成功前の記録は当時の状態として読む。

作業ブランチはfix/termux-proton-pass-shebangで、基点は5e62543。Termuxの場合だけ関連4コマンドのシバンをPREFIX/bin/envへ展開し、シバン補正に依存しない形へ修正した。Linux・prootは従来どおり。ローカルのmake checkはunittest 353件・Bats 18件が成功、skip 0件。利用者の追加確認で、ラッパーは実行可能、先頭行は#!/usr/bin/env bash、/usr/bin/envは実行不可、PREFIX/bin/envは実行可能と分かった。実ファイルの欠落ではなく、シバン先を実行できない状態を確認済み。修正後の限定適用と通常applyの実機確認は未完了。

次は修正版を取得し、[Proton Pass手順書13節](setup/proton-pass.md#13-termuxでchezmoiからラッパーを起動できない場合2026-11-20)に従って関連4ファイルを限定適用した後、通常のapplyを再試行する。既存の認証情報を移行・削除しない。Codex側では実認証・秘密値の取得・実環境への適用を行っていない。

### Termux初期構築の停止と修正案（2026-11-20）

PR #12はmainへ取り込み済み。利用者はTermuxで再度chezmoi initを実行し、promptStringOnceが正常に動作したと報告した。次のbootstrapはidentity生成後のファイル確定で停止したため、fix/termux-bootstrap-publishをmainの1c43852から作成した。

従来の確定処理はハードリンクに依存し、失敗したlnの詳細を隠していた。Termux側Pythonにはos.linkがなかった。利用者の追加ダミー確認ではlnがPermission denied（終了コード1）、未作成の宛先へのmv -nTが終了コード0で移動成功だった。拒否の具体的な原因は未確定であり、既存宛先の保護とbootstrap全体の成功は実機未確認。

修正案はmv -nTによる上書き禁止の確定処理で、保存先や暗号化方式を変えず、既存ファイルの再利用と不正な宛先の拒否を維持する。ローカルの関連テスト24件と、make checkのunittest 352件・Bats 18件が成功し、skipは0件。詳細は[Proton Pass手順書の追加記録](setup/proton-pass.md#12-termux初期構築のファイル確定2026-11-20)を参照する。Termuxでの修正後の再試行・実認証は未実施。既存鍵や暗号文は削除しない。以下の11月19日の未実施記録は当時の状態として読む。

### 再開位置（2026-11-19追記）

PR #11はmainへ取り込み済みで、今回の修正ブランチはinvestigate/chezmoi-init-template-path、基点はe92a5c7。初期設定テンプレートの移動と関連修正、生成物のGit除外をまとめてcommit・push・PR作成するよう利用者から依頼済み。反映状況はGit履歴とPRで確認する。Termux側では、配置修正を含むコミットを取得してから検証を再開する。下記の「文書作成時点」の表は初版の記録として残す。

修正後はhome/.chezmoi.toml.tmplが存在し、リポジトリ直下の同名ファイルは存在しないことを確認する。本文は移動前と一致する。隔離した実initで設定ファイルの生成を確認し、同じ回帰テストで旧配置の失敗も再現した。ローカルのmake checkはunittest 348件・Bats 18件が成功、skip 0件。Termux本体での修正後の初期化確認は未実施。

.gitignoreにはPythonのバイトコードと__pycache__、作業コピー直下の.venv、node_modulesを追加した。依存定義とhome/.chezmoi.toml.tmplはGit管理対象に残す。これはGitへの追加を除外する設定であり、chezmoiの展開対象を指定するhome/.chezmoiignoreとは役割が異なる。

## 初版の目的と実装記録（2026-11-19）

以下の1・2節と初期化テンプレートの説明は、初版時点の目的・Git状態・確認範囲を残した記録。Termuxでの未実施の記述は当時の状態を示す。現在の到達点と残件は冒頭、再開時に使う規約・手順は3〜7節を参照する。

## 1. 今回の目的と開始位置

利用者は、次のタスクとしてTermux実環境でのdotfiles構築・検証を希望している。SOPS・mise連携やNeovimの旧設定整理を先に完了させる必要はなく、Termux検証から着手できる。

この文書の作成依頼は、作業ブランチと引き継ぎ文書の作成まで。Termuxでのパッケージ導入、chezmoi初期化・適用、認証、外部通信、commit・pushを一括して承認したものではない。再開後の明示依頼と、実環境のAGENTS.mdに従う。

| 項目 | 文書作成時点の状態 |
| --- | --- |
| mainの基点 | c3fce78（PR #10のマージコミット） |
| 今回の作業ブランチ | docs/termux-verification-handoff。上記mainから作成 |
| 前回の作業ブランチ | docs/proton-pass-project-pat-design。利用者からマージ・main更新・ローカル削除の報告あり |
| Termux側Codex | 利用者が導入済みと報告。依存ツールと設定の状態は未確認 |
| Termux実機検証 | チェックリスト全体の完了報告なし。今回もまだ実行していない |

別のcloneへ移る場合は、引き継ぎ文書がその作業コピーにも届いているか確認する。ローカルのブランチや未コミット文書は別cloneへ自動では移らない。実際のブランチ・コミット・未コミット変更を再確認し、既存の変更を保護する。

## 初期化テンプレートの配置修正

Termuxでchezmoi init shioyakizakanaを実行してcloneは成功したが、設定入力が出なかったとの報告があった。従来は.chezmoi.toml.tmplがリポジトリ直下にあり、.chezmoirootが指定するhome配下に存在しなかった。修正後はhome/.chezmoi.toml.tmplを使う。

修正版を取得した後、既存のローカル設定と変更を保護し、承認された範囲でchezmoi initを--applyなしで再実行する。cloneし直すためにリポジトリや認証情報を削除する必要はない。既存データがあれば入力が省略される項目もある。Termux本体での修正後の確認は未実施。

## 2. 引き継いだ実装と確認済み範囲

chezmoiの展開ソースはhome/、bootstrap/・docs/・tests/はリポジトリ内の管理用。実装を直す場合はソースを変更し、展開先を直接編集しない。

| 対象 | 現在の状態 |
| --- | --- |
| Proton Pass | グローバルとプロジェクト別PATの明示選択、暗号文・CLIセッション・鍵キャッシュの分離を実装済み |
| 初期登録・補完 | setup-proton-pass-projectと3コマンドのBash・Zsh補完を実装済み |
| 鍵キャッシュ | CLI暗号化鍵だけを保持。既定15分、15・30・45・60分を選択可能。残り時間は分・秒表示 |
| proot対応 | 仮想UIDと同一プロセスのホスト側UIDを考慮。無関係なUID・不適切な権限の拒否は維持 |
| Neovim | Mason依存の除去、DAP修正、lockfileのスナップショット運用まで実施。本体はmiseのlatest方針を維持 |

利用者はproot側で、グローバル→テスト用プロジェクト→グローバルの認証切り替え、許可した保管庫だけの一覧表示、3コマンドのTab候補、30分キャッシュの開始と分・秒表示を確認済み。Termux本体で同じ動作を確認した記録とは区別する。

PR #10の最終検証は、ローカルでunittest 347件・Bats 18件が成功し、skip 0件。GitHubの必須checkも成功したが、Yazi未導入による実起動1件は任意skipだった。CIで指摘されたShellCheck SC2015は明示的なifへ修正済み。これらはTermux本体の実行互換性やパッケージ導入成功を保証するものではない。

## 3. 最初に読む規約・手順・ソース

- 実環境の共通AGENTS.md、リポジトリの[AGENTS.md](../AGENTS.md)、変更対象フォルダのAGENTS.md。
- [README](../README.md)：初期構築の順序と環境別の扱い。
- [Termux実機チェックリスト](testing/termux-checklist.md)：確認の順序、合否条件、結果欄。検証結果はここへ追記する。
- [依存一覧のTermux手順](setup/dependencies.md#termuxでの導入と実機確認)：基礎導入と対象外の処理。
- [共通検証手順](testing/checks.md)、[環境別の検証範囲](testing/environment-matrix.md)、[Git hooks](testing/git-hooks.md)。
- [Proton Passの現在の状態](setup/proton-pass.md#現在の状態)：認証周辺の確認済み範囲と残件。
- ソースはbootstrap/bootstrap-tools.sh、home/.chezmoiignore、Makefile、tests/check.py、tests/test_bootstrap_platforms.py、tests/test_environment_policy.pyを先に読む。

既存の[Codex引き継ぎ](CODEX_HANDOFF.md)の2026-11-17・18の記述は過去の記録。PAT対応はPR #10でmainへ取り込み済みであり、旧ブランチから再開しない。

調査・計画はimplementation-planning、修正・結果報告はcoding-workflow、不具合調査はsystematic-debuggingを使う。リポジトリ側ではdotfiles-script-maintenance・dotfiles-test-runnerを参照し、テンプレート変更にはchezmoi-template-validationを使う。共通スキルが未配置なら、配布元home/dot_agents/skills/に対応ファイルがあるか確認する。

## 4. 最初の現状確認

Termuxのホーム配下の作業コピーで実行する。共有ストレージやproot側の作業コピー・生成hookとの共用は避ける。次は導入・認証・設定適用を行わない確認例である。

```shell
git status --short --branch
git log -3 --oneline
uname -sm
dpkg --print-architecture
bash bootstrap/bootstrap-tools.sh --check
command -v bash git chezmoi age age-keygen python3 make openssl wget flock mise
command -v zsh lua bats shellcheck shfmt lefthook
```

存在したコマンドだけバージョンを確認し、OS・CPU、対象コミット、導入済みと不足を記録する。Pythonは3.11以上が必要。Termux本体と判定されることを確かめ、Ubuntuと判定された場合は実行場所と継承設定を調べる。

--checkは不足があっても正常終了するため、終了コードだけで準備完了としない。pkg管理対象はパッケージの導入状況も確認する。chezmoi data、環境変数全体、秘密ファイルの内容を表示して現状確認しない。

## 5. 検証を進める順序と条件

| 段階 | 実施内容と合格条件 |
| --- | --- |
| 基礎導入 | 不足一覧と導入対象を示し、承認後に既存bootstrapの--installを使う。導入後の配置と版、再実行で導入済みが省かれることを確認 |
| 共通テスト | testing/checks.mdの必須依存を用意し、Termux本体でmake checkを実行。失敗・skip・未実施の理由を記録 |
| Git hooks | lefthook 2.2.2のTermuxでの実行可否と既存hookを確認。導入・生成hookのシバン補正は承認後に既存手順に従う。直接起動と実commit・push時の起動を区別 |
| 設定適用 | 現状の手動設定を保護し、環境フラグと限定した差分を確認。内容と対象の承認後に必要範囲を適用 |
| アプリ | 新しいシェルのPATH・エイリアス・補完、tmuxの新規ペイン、Yaziとプレビューをチェックリストに沿って確認 |
| 認証を含む全体構築 | pass-cliのTermux上での準備・実行互換性を確認し、実認証の承認後に別段階として実施 |

共通テストのmake checkは実PAT・実鍵・実セッションを必要とせず、認証用requireにも依存しない。make requireはpass-cli未準備なら失敗するため、共通テストの開始条件にしない。必須依存不足をskipに置き換えて成功扱いしない。任意skipの対象はtesting/checks.mdに記載されたYazi実起動1件だけ。

Termuxパッケージのchezmoiで設定適用用Makeターゲットを使う場合は、CHEZMOI_BIN="$PREFIX/bin/chezmoi"を指定する。共通テストはPATH上のchezmoiを使うため、この指定とは独立している。

## 6. 維持する仕様と停止条件

- 対象はAPT/dpkg方式のTermux。Ubuntu用APT導入、Homebrew、Ubuntu用mise設定と一括導入スクリプトの展開除外を維持する。mise本体を導入できても、Ubuntu用ツール一式が利用可能とは判断しない。
- bootstrapはTermux用proton-pass-cliをpkgで導入する。認証は自動実行せず、導入・共通テストの結果と実認証の確認を分けて記録する。
- 不明な配布元やLinux用バイナリへ自動で切り替えない。新しい依存・認証方式・保存場所が必要なら、理由と影響を示して承認を得る。
- PAT、age identity、復号結果、秘密変数を表示・Git追加しない。既存のproot用identityやセッションをTermuxへコピーして解決しない。
- 不具合は再現条件を記録し、最小の修正と対応テストを追加する。テスト失敗を理由に検証条件を弱めない。

## 7. 完了条件・残件・次の報告

Termuxの基礎準備、環境別除外、共通テスト、hook、アプリについて、成功・失敗・未実施と理由をチェックリストに記録する。失敗が残る場合は再現条件と次の対処を示し、確認できた段階までを報告する。認証が未完了なら、認証を含むdotfiles全体構築の完了とは記載しない。

次の報告には、変更ファイル、Termux上の実行結果、適用の有無、未確認事項を含める。実機では確認できない箇所は利用者へ手順を渡す。commit・push・PR作成は、その時点の明示依頼に従う。

最新の保留事項と後続作業は、冒頭の[次に確認すること](#次に確認すること)を参照する。
