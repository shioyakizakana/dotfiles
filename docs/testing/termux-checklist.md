# Termux実機確認の手順と記録

DF-04・DF-09の実機確認は、基礎ツール、Git hooks、共通テスト、アプリの順に分ける。以下のチェックリスト全体の完了報告は受けていない。Termux本体とproot Ubuntuの結果を別々に記録する。

prootでのProton Pass認証・補完・鍵キャッシュについては、別途[利用者の実機成功報告](../setup/proton-pass.md#現在の状態)がある。下記の基礎導入・Git hooks・アプリ確認の結果欄とは分けて扱う。

## 確認前の条件

- APT/dpkg方式のTermuxを使う。通常ユーザーで操作し、作業コピーはTermuxのホーム配下に置く。共有ストレージでの実行属性やリンクの制約を避ける。
- 作業内容と未コミット変更を確認する。認証情報・環境変数全体・秘密鍵・復号済み設定は表示しない。
- 基礎導入は[既存の導入手順](../setup/dependencies.md#termuxでの導入と実機確認)、hookの準備は[Git hooksの手順](git-hooks.md)に従う。導入操作は利用者が選択して実施する。

## 1. 環境と基礎ツール

Termux本体でリポジトリルートから実行する。`--check`は導入や認証を行わない。

```shell
uname -sm
dpkg --print-architecture
git rev-parse HEAD
bash bootstrap/bootstrap-tools.sh --check
command -v bash git chezmoi age python3 make openssl wget flock mise
python3 --version
chezmoi --version
```

Termuxと判定され、Pythonが3.11以上で、必要な実行ファイルがTermux用に準備されていることを確認する。不足があれば導入手順へ戻る。`[--] pkg:名前`は未導入を示す。Proton Pass CLIとpkg対応開発ツールもbootstrapの導入対象だが、認証は今回の確認に含めず、以降のテストにも実認証は不要。

proot Ubuntuを確認する場合はゲスト内で別途実行し、Ubuntuと判定されることを確認する。Termuxの実行ファイルや生成hookをゲストのものと共用しない。

## 2. Git hooks

lefthook 2.2.2と検証ツールを準備する。生成hookのシバン補正が必要な場合は既存手順に従う。次のコマンドを実行し、終了状態と失敗した処理を記録する。

```shell
lefthook version
lefthook validate
lefthook run pre-commit
lefthook run pre-push --force
```

空stageのpre-commitはskipしてもよいが、差分検証の成功とは数えない。pre-pushは`make check`を実行するため時間がかかる。`--force`はこのジョブを実行させる指定で、Gitの強制pushではない。

上記はlefthookの直接起動であり、Gitが生成hookを起動した証拠とは分ける。次回の通常のcommit・pushでhookが動くことを確認し、対応するPR番号と結果を記録する。確認のためだけに空コミットやpushは行わない。

## 3. 共通テスト

pre-pushで`make check`が実行済みなら、その結果を再利用する。未実行なら[必要なツール](checks.md)を確認してから`make check`を実行する。依存不足をテストのskipや成功として処理しない。

合格条件は静的検証・unittest・Batsの成功。任意skipはYazi実起動の1件だけで、識別子と理由を記録する。ホストLinuxでの成功とTermuxでの成功は別に記録する。失敗時は、秘密情報を除いた失敗テスト名・終了状態・ツールの版だけを共有する。

## 4. 設定・アプリの確認

ここからは、対象の設定がすでに適用された環境での確認となる。設定適用が必要なら、内容と対象を確認して別途実施する。共通テストのために`chezmoi apply`や認証処理を実行しない。

| 対象 | 確認する動作 | 不足・失敗時の扱い |
| --- | --- | --- |
| Bash・Zsh | 起動、新しいシェルでのPATH・共通エイリアス、再読み込み | 設定の読み込み失敗と任意ツール不足を分ける |
| tmux | 新規ペインでTermuxのZshを起動、補助キーの動作 | Ubuntu固定パスを使っていないか確認する。Zsh未導入の既定動作と区別する |
| Yazi | 起動、移動、終了、導入済みプラグインのキー操作 | 未導入プラグインの操作は未確認と記録し、成功扱いしない |
| プレビュー | 秘密情報を含まないサンプル画像・PDFなどの表示 | chafa・resvgなどの不足と、端末の描画対応を分ける。miseへのchafa追加は自動で行わない |

### Neovimの起動確認

Termux本体では `ja_JP.utf8` の指定で起動時に `E197` が発生した。chezmoiの `termux` フラグが有効な場合は `C.UTF-8` を指定する。proot Ubuntuなどでは従来の指定を使う。

Termux本体のNeovimで、隔離環境に展開した基本設定の読み込みとUTF-8の文字コードを確認した。PR #18の修正適用後、利用者は通常起動で `E197` が解消したことを確認した。

### プロジェクト別Proton Passの確認

Termux本体では、Androidが管理する親ディレクトリの権限が従来の条件に合わず、プロジェクト別の初期登録と鍵キャッシュのテストが失敗していた。Termux設定と実行時のAndroid判定が一致する場合に限り、標準のアプリ領域へのパス上で、指定の場所・所有者・グループ・モードを満たす親ディレクトリを許可する。秘密ファイルと専用領域には従来の権限条件を適用する。

### Yaziのプラグインとflavor

利用者がTermux本体の通常設定で、以下の操作を確認した。

- `fzf` はショートカットから起動し、検索できた。
- `zoxide` はショートカットから起動し、指定したパスに移動できた。
- `smart-enter.yazi` は `yazi.toml` で指定したファイル種別ごとの処理を実行できた。
- `full-border` は設定どおりに枠線を表示した。
- `bunny.yazi` はショートカットから設定済みのパスに移動できた。
- CatppuccinのLatteとMochaはエラーなく適用できた。

### 追加CLIの導入確認

2026-11-28に、利用者から`feat/cli-tools-and-tlrc`のTermux実機確認結果を受領した。利用者が`make bootstrap-tools`を実行し、ツールが新規導入されたことと、Termuxで除外されているツールがインストールされていないことを確認した。

設定上の追加対象はsd・dust・xh・doggo・hyperfine・navi・moor・glowの8ツール。対象外のツールと、tealdeerを維持する方針は[環境別一覧](../setup/dependencies.md#追加cliの導入対象)を参照する。

今回の報告により、追加CLIの導入と除外の確認を完了とする。実行日時・対象コミットSHA・端末やツールの版・個々の機能の結果は未記録。Codexによる実機での再実行や、下記の共通テストをTermuxで再実行した結果とは区別する。

## 結果の記録欄

実機確認後に利用者が記入する。公開する前に端末名・個人パス・ログに秘密情報が含まれていないか確認する。

| 項目 | 結果 |
| --- | --- |
| 確認日・対象コミット | 初回は2026-11-21、`e20eeb3`（PR #19のマージ後）。SVG対応後の共通テスト結果などは各行に追記。Proton Passの後続結果は[専用記録](../setup/proton-pass.md#利用者の実機確認結果)を参照 |
| Termux本体 / proot Ubuntu、CPU、OS・Termuxの版 | 以下はTermux本体の結果。各確認時のCPU・OS・Termuxの版は未記録。後続のProton Pass検証ではTermux 0.118.3を記録しているが、下記の全確認と同一条件とは扱わない |
| 基礎確認・不足ツール | 基礎パッケージ・pkg対応開発ツールとBatsの導入、共通テストの成功を報告済み。個別の不足一覧は未記録。Neovim用ツールの初回一括導入は[保留中](../setup/dependencies.md#neovim用ツールの一括導入) |
| lefthookの版・直接起動 | Termux本体で2.2.2。設定検証とpre-commitの直接起動に成功。直接起動時はステージ済みファイルがなく、差分検証はskip。利用者は `TMPDIR="$PREFIX/tmp" lefthook run pre-push --force` でテストの通過を確認した |
| 通常commit・pushでのhook起動、PR番号 | Gitからpre-commitとpre-pushが起動し、検証に成功。PR #19のGitHub Actionsも利用者が成功を確認した |
| make checkの結果・件数・skip理由 | Termux本体で `TMPDIR="$PREFIX/tmp" make check` が成功。SVG対応後の `49dc9ec` では静的検証、unittest 362件、Bats 18件が通過し、skipは0件。Proton Passはダミーデータで確認した |
| シェル・tmux | 利用者がTermux本体の通常設定でZshの起動、ウィンドウの追加・削除、ペイン分割を確認 |
| Yazi・プレビュー・プラグイン | 利用者が `ya pkg install` でプラグインを導入し、PNG・PDFのプレビューに成功。Termux向けの `magick` 設定を適用した後、通常起動したYaziでSVGのプレビューにも成功。確認済みのプラグインとflavorは上記に記載 |
| resvgの導入・更新 | 隔離HOMEで、旧版を模した実行ファイルからTermuxでビルドした0.50.0への切り替えとSVGからPNGへの変換に成功。同じ版では再ビルドせず、依存を取得できない場合は旧実行ファイルが残ることを確認 |
| Neovimスナップショット | 展開済みコマンドと実際のlockfileを使い、一時保存先に保存して一覧に表示されることを確認 |
| プロジェクト別Proton Pass | 利用者がTermux本体で検証用PATを登録。グローバルでログイン後、`info` をグローバル、検証用プロファイル、グローバルの順に実行し、前後のグローバルの認証先が一致することを確認。検証用プロファイルの `vault list` には許可した保管庫1件だけが表示された |
