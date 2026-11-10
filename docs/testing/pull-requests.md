# ghを使うdotfilesの変更手順

変更ごとに最新の`main`から作業ブランチを作り、PRで差分と必須チェック`check`を確認して取り込む。マージ後は作業ブランチを削除する。

コマンドはリポジトリルートで実行する。以下の`docs/example-change`は作業内容に合う名前へ置き換える。

## 初回の準備

GitHub CLIの`gh`と[Git hooks](git-hooks.md)、[検証ツール](checks.md)を準備する。Termux本体とproot Ubuntuでは、それぞれで動く実行ファイルを使用する。

```shell
gh --version
gh auth status
```

未認証なら、利用者が`gh auth login --hostname github.com`で認証する。トークンを文書やコマンド引数へ記載しない。認証済みの環境で再ログインする必要はない。

本リポジトリではPRと`check`の成功を必須にしている。Allow auto-mergeとブランチ自動削除は有効化済み。これらはGitHub側の設定であり、cloneだけでは再設定されない。

## 作業ブランチを作る

`git status --short --branch`で未コミット変更がないことを確認してから、次を実行する。変更が残っていれば、先に内容と保存先を判断する。

```shell
git switch main
git pull --ff-only origin main
git switch -c docs/example-change
```

`pull --ff-only`が失敗した場合は、ローカルとリモートの履歴が分岐していないか確認する。ローカルの変更やコミットを破棄して解消しない。

## コミットしてPRを作る

変更に合う[検証](checks.md)と差分確認を行う。日本語文書は文章の確認も行う。変更するファイルを指定してstageし、`git diff --cached`で確認してからコミットする。

```shell
git diff --check
git diff
git add docs/example.md
git diff --cached
git commit -m 'docs: 変更の目的と理由を記す'
git push -u origin docs/example-change
gh pr create --base main --template .github/pull_request_template.md
```

`docs/example.md`とコミットメッセージも実際の変更に合わせる。PRの説明には、テンプレートに沿って変更理由・影響範囲・検証結果・適用操作を書く。`--fill`はコミットから説明を生成するため、テンプレートを使う手順では指定しない。[gh pr createの公式説明](https://cli.github.com/manual/gh_pr_create)

pre-commitはステージ済み差分の空白エラーを確認し、pre-pushは`make check`を実行する。失敗した場合は出力を確認して修正する。作業ブランチへのpushだけでは、このリポジトリのPR用CIは開始されない。PR作成後にGitHub Actionsが実行される。

## 差分・チェックを確認する

作業ブランチ上では、次のコマンドがそのブランチのPRを対象にする。別のブランチから操作する場合はPR番号を指定する。

```shell
gh pr view
gh pr diff
gh pr checks --required --watch
```

`check`が登録されるまで表示されない場合は、少し待って再確認する。チェック失敗時はPR画面か`gh run view RUN_ID --log-failed`で原因を調べる。`RUN_ID`は`gh run list --branch docs/example-change`で確認できる。秘密情報を含むログをPRへ転記しない。[gh pr checksの公式説明](https://cli.github.com/manual/gh_pr_checks)

修正は同じ作業ブランチでコミットし、`git push`する。既存のPRが更新され、チェックが再実行される。

## 自動マージを予約する

差分と影響範囲を確認した後、作業ブランチ上で次を実行する。

```shell
gh pr merge --auto --merge
```

必須条件を満たすとマージされる。実行時点ですでに条件を満たしていれば、その場でマージされる場合もある。予約後に変更をpushする場合も、その内容を確認する。`--admin`で必須条件を迂回しない。[gh pr mergeの公式説明](https://cli.github.com/manual/gh_pr_merge)

ここでは個々のコミットを維持するマージコミット方式を例にする。他の方式を使った場合は、ローカル履歴の同期やブランチ削除の判定が変わる。

## マージ後に片付ける

`gh pr view --json state,url`で`MERGED`になったことと、未コミット変更がないことを確認する。GitHub上のブランチは自動削除されるが、ローカルのブランチは残る。

```shell
git switch main
git pull --ff-only origin main
git fetch --prune origin
git branch -d docs/example-change
```

`fetch --prune`は削除済みのリモートブランチに対応する追跡参照を整理する。ローカルの作業ブランチ自体は削除しない。`branch -d`が失敗した場合は未取り込みのコミットやマージ方式を確認し、強制削除へ置き換えない。次の変更は、更新した`main`から別のブランチを作る。

Codexに操作を依頼する場合、コミット・push・PR作成・マージは実施してほしい範囲を明示する。スキルや手順書の参照自体は、これらの操作への承認を意味しない。
