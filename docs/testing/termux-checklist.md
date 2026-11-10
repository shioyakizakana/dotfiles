# Termux実機確認の手順と記録

DF-04・DF-09の実機確認は、基礎ツール、Git hooks、共通テスト、アプリの順に分ける。この作業環境ではAndroid実機を利用できないため、以下は未実施の確認手順である。Termux本体とproot Ubuntuの結果を別々に記録する。

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

Termuxと判定され、Pythonが3.11以上で、必要な実行ファイルがTermux用に準備されていることを確認する。不足があれば導入手順へ戻る。`[MANUAL]`・`[UNVERIFIED]`は準備完了と数えない。pass-cliの準備・認証は今回の確認に含めず、以降のテストにも実認証は不要。

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

## 結果の記録欄

実機確認後に利用者が記入する。公開する前に端末名・個人パス・ログに秘密情報が含まれていないか確認する。

| 項目 | 結果 |
| --- | --- |
| 確認日・対象コミット | 未実施 |
| Termux本体 / proot Ubuntu、CPU、OS・Termuxの版 | 未実施 |
| 基礎確認・不足ツール | 未実施 |
| lefthookの版・直接起動 | 未実施 |
| 通常commit・pushでのhook起動、PR番号 | 未実施 |
| make checkの結果・件数・skip理由 | 未実施 |
| シェル・tmux | 未実施 |
| Yazi・プレビュー・未導入プラグイン | 未実施 |
| 残件・次の確認 | 未実施 |
