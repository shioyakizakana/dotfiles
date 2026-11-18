# Termux実環境のdotfiles検証：Codex引き継ぎ

作成日：2026-11-19。対象はTermux本体で動くCodexとdotfilesの作業コピー。まず1〜4節を読み、変更を伴わない現状確認から始める。導入・設定適用・認証は、実施対象と承認状況を確認してから進める。

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

--checkは不足があっても正常終了するため、終了コードだけで準備完了としない。pass-cliのMANUAL・UNVERIFIEDも未確認として残す。chezmoi data、環境変数全体、秘密ファイルの内容を表示して現状確認しない。

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
- 基礎bootstrapはTermux用pass-cliを自動導入しない。実行互換性が未解決なら認証段階を保留し、基礎導入・共通テストの結果は別に記録する。
- 不明な配布元やLinux用バイナリへ自動で切り替えない。新しい依存・認証方式・保存場所が必要なら、理由と影響を示して承認を得る。
- PAT、age identity、復号結果、秘密変数を表示・Git追加しない。既存のproot用identityやセッションをTermuxへコピーして解決しない。
- 不具合は再現条件を記録し、最小の修正と対応テストを追加する。テスト失敗を理由に検証条件を弱めない。

## 7. 完了条件・残件・次の報告

Termuxの基礎準備、環境別除外、共通テスト、hook、アプリについて、成功・失敗・未実施と理由をチェックリストに記録する。失敗が残る場合は再現条件と次の対処を示し、確認できた段階までを報告する。認証が未完了なら、認証を含むdotfiles全体構築の完了とは記載しない。

次の報告には、変更ファイル、Termux上の実行結果、適用の有無、未確認事項を含める。実機では確認できない箇所は利用者へ手順を渡す。commit・push・PR作成は、その時点の明示依頼に従う。

SOPS用鍵の保護とmise連携、PAT期限切れ・更新・復旧の追加確認、複数プロジェクトの同時利用、Neovim旧設定整理（NV-06）は別タスクとして残す。これらはTermux検証の開始を妨げない。
