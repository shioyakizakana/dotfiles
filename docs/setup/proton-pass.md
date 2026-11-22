# Proton Passの構築・確認手順

DF-07のコード修正後に、利用者が実環境で行う確認手順。実際の認証・設定適用は自動テストの対象にしていない。
まず1〜4節を確認し、停止した場合は5節を参照する。

1. 既存の認証方式を維持する。初期化済みの環境でproviderを変更する場合は、移行方法を別途決める。
2. PATは対話入力し、コマンドの引数やシェル履歴に記録しない。
3. 初回の全体適用より前に`make wrapper`を実行する。

最終更新：2026-11-22。

## 現在の状態

Termux本体では、初期設定の入力、認証bootstrap、ラッパーのシバン修正後のchezmoi apply成功が利用者から報告されている。プロジェクト別PATの初期登録、グローバル→検証用プロファイル→グローバルの認証切り替え、許可した保管庫1件だけの一覧表示も確認済み。[Termux実機記録](../testing/termux-checklist.md#結果の記録欄)を参照する。

12・13節の停止事例と「実機確認待ち」は2026-11-20時点の履歴。以後の成功報告は上記にまとめ、当時の原因調査と修正経緯は残している。

プロジェクト別PATの選択・保存配置・env限定・PAT用identityの共有は承認済みで、PR #10でmainへ取り込み済み。利用者による実環境への適用と、以下のproot Ubuntuでの動作確認も完了している。6節の設計案や各実装段階の「未実施」は、その時点の記録として読む。

| 対象 | 現在の状態と根拠 |
| --- | --- |
| グローバルとプロジェクトの認証 | 利用者が同じシェルでグローバル→pat-test→グローバルの順にinfoを実行し、前後のグローバルPAT名が一致し、途中だけpat-testになることを確認（11節） |
| テスト用PATの参照範囲 | 1つの保管庫だけを許可したPATで、vault listにもその保管庫だけが表示された（11節） |
| プロジェクトの初期登録とUID対応 | 初期登録の完了と、UID対応版の適用後のpat-test info成功を利用者が確認（8〜10節） |
| 補完 | proton-pass、proton-pass-key-cache.py、setup-proton-pass-projectのTab候補を利用者が確認。実端末でBash・Zshの両方を確認したとの報告ではない（8・10節） |
| 鍵キャッシュ | 15・30・45・60分の選択を実装済み。利用者はロック中の表示、30分でのunlock、残り時間の分・秒表示を確認（7・10節） |

PAT対応時の2026-11-18にコミット前の差分レビューとmake checkを実施し、unittest 347件・Bats 18件が成功、skipは0件だった。これは当時の件数であり、後続の共通検証は[Termux版の引き継ぎ](../CODEX_TERMUX_HANDOFF.md#現在の到達点2026-11-22)を参照する。残り時間の表示変更では関連テスト31件と表示確認9例、認証切り替えでは関連テスト58件と隔離環境の連続切り替え検証1件も成功している。各段階の記録は7〜11節を参照する。

実機での期限経過によるキャッシュ停止、PATの期限切れ・更新・復旧、複数プロジェクトの同時利用、Termux・proot以外の環境の動作は未確認。未許可項目への直接アクセス拒否も未確認であり、上記の成功範囲に含めない。

SOPS用鍵のローカル配置・保護方法と、mise・SOPSのプロジェクト連携は後続の設計・実装対象として残す。プロジェクト側keyring対応とCLI下位オプションの補完は、今回の実装範囲に含めていない。

操作手順は1〜5節がグローバル、7節がプロジェクト指定とTTL、8節が初期登録と補完、9節がUID対応。10〜11節に実機確認の経緯と結果を記載する。

## 1. 実行環境とproviderを確認する

基礎コマンドはREADMEの準備手順で導入済みとする。この手順ではパッケージの追加を行わない。
標準配置なら次のディレクトリへ移動する。別の場所にcloneした場合は、その場所を指定する。

```shell
cd "$HOME/.local/share/chezmoi"
export PATH="$HOME/.local/bin:$PATH"
make require
```

初めて初期化する場合はREADMEの`chezmoi init`を使う。Ubuntu系では`env`または`keyring`を選択する。Termux・prootはenvに固定する。

| 実行環境 | providerと準備 |
| --- | --- |
| Termux | env。keyringは使わない。pass-cli・age・Python 3の実行可否を端末で確認する |
| proot Ubuntu | env。bootstrapはrootを拒否するため、通常ユーザーで作業する。引き継いだ`PREFIX`よりchezmoi設定を優先する |
| WSL2・ネイティブ・QEMUのUbuntu | env、またはD-BusセッションとSecret Serviceが利用できるkeyring |

既存環境では、秘密情報を含まない項目だけを表示する。

```shell
chezmoi --source "$PWD" execute-template '{{ .protonPassProvider }}'
chezmoi --source "$PWD" execute-template 'termux={{ .termux }} proot={{ .prootUbuntu }} wsl={{ .wslUbuntu }} qemu={{ .qemuUbuntu }} native={{ .nativeUbuntu }}'
```

実行環境のフラグが現在の環境と一致し、通常は1つだけtrueであることを確認する。別端末から設定をコピーした場合は特に注意する。
`keyring`を継続利用する場合は、同じログインセッションで次を確認する。Secret Serviceの起動方法はデスクトップ環境によって異なるため、このリポジトリでは自動起動しない。

```shell
busctl --user --timeout=5 introspect \
  org.freedesktop.secrets /org/freedesktop/secrets \
  org.freedesktop.Secret.Service >/dev/null
```

## 2. 既存環境ではラッパー参照先も更新する

以前の初期設定は、ラッパー未展開時に`pass-cli`を直接参照することがある。現在の参照先だけを確認する。

```shell
chezmoi --source "$PWD" execute-template '{{ .chezmoi.config.protonPass.command }}'
```

`pass-cli`や別のPATH上のラッパーを参照している場合は、適用前にchezmoiのローカル設定をバックアップする。
標準の設定ファイルは`~/.config/chezmoi/chezmoi.toml`。独自の設定パスを使う場合は、そのファイルを対象とする。

```shell
cp -p "$HOME/.config/chezmoi/chezmoi.toml" \
  "$HOME/.config/chezmoi/chezmoi.toml.before-df07"
chezmoi init --source "$PWD"
```

バックアップ名が既に存在する場合は、未使用の名前に変更してからコピーする。再初期化はローカル設定を再生成するため、独自に追加した設定はバックアップと比較する。
再初期化では既存の環境フラグとproviderを引き継ぐ。上記の確認を繰り返し、参照先が実際のホームディレクトリ配下の`.local/bin/proton-pass`になったことを確認する。
新規構築ではこの再初期化は不要。

## 3. 認証を構築し、ラッパーを限定展開する

新規環境または初期構築を再開する場合は、通常ユーザーの対話端末で実行する。

```shell
make bootstrap
```

引数なしでchezmoiの環境・providerを使う。明示指定が必要なら、例えば次のように実行できる。両方とも設定と一致しなければ停止する。

```shell
LINUX_ENV=proot-ubuntu bash bootstrap/setup-proton-pass.sh env
```

bootstrapはage identity・暗号化PATなどを作成または検証し、ログインする。既存の暗号文を削除せず、必要なパスフレーズとPATは表示された対話入力で渡す。
認証済みの既存環境では、DF-07のためだけにbootstrapを再実行する必要はない。

```shell
make wrapper
```

このターゲットは`proton-pass`、`proton-pass-key-cache.py`、`setup-proton-pass-project`を限定展開する。chezmoiのスクリプト実行とexternalsの更新を除外する。
`init-proton-pass`は通常の全体適用で更新する。

## 4. ラッパーを通した認証と適用を確認する

```shell
"$HOME/.local/bin/proton-pass" info
```

実際の認証状態を確認する操作。envでは必要に応じてageのパスフレーズ入力と鍵キャッシュの起動が発生する。
出力にはアカウント情報が含まれる可能性があるため、共有ログへ貼り付けない。
TermuxではPython 3とキャッシュソケット、prootでは同じ通常ユーザーのHOME・実行権限も確認する。

認証確認後、差分を手元の端末で確認してから全体を適用する。差分には復号済みデータが含まれる可能性があるため公開しない。

```shell
make diff
make apply
```

`make apply`は確認入力後に設定を反映し、環境別の導入スクリプトや外部取得を伴う。今回のコード検証では実行していない。

## 5. 停止した場合の対処

| 状況 | 確認・対処 |
| --- | --- |
| provider不一致 | 継承した`PROTON_PASS_KEY_PROVIDER`と引数を確認する。不要な上書きなら`unset PROTON_PASS_KEY_PROVIDER`として再実行する。既存の認証方式をその場で変更しない |
| 実行環境の不一致 | 不要な`LINUX_ENV`は`unset LINUX_ENV`で解除する。保存したフラグ自体が誤っている場合はローカル設定をバックアップし、実環境に合うフラグだけをtrueにする |
| keyringの条件を満たさない | 同じユーザーのD-BusセッションとSecret Serviceを確認する。envへの移行は認証方式の変更として別途計画する |
| 暗号文があるのにidentityがない | 停止したまま、正しい暗号化identityとrecipientのバックアップを確認する。鍵の再生成や暗号文の削除で回避しない |
| ラッパーや鍵キャッシュがない | `make wrapper`の成功と`.local/bin`の実行権限を確認する。ソースの`.tmpl`を直接実行しない |
| Termux・prootでCLIが実行できない | CPU・実行形式・通常ユーザー・PATHを確認する。今回のモックテストはAndroidのBionicや実サービスとの互換性までは保証しない |

解決しない場合は、環境名・provider・終了コード・秘密情報を除いたエラーだけを記録し、次の修正依頼で共有する。
PAT、秘密鍵、復号結果、環境変数の値の一覧は添付しない。

用語：providerはCLIの暗号化鍵の供給方法、envはプロセス環境変数、keyringはSecret Serviceを利用する方式。identityはageの復号鍵、recipientは暗号化先を示す公開鍵。

1〜5節の初版更新日：2026-11-08。

## 6. プロジェクト別PATの設計時点の記録（2026-11-18）

既存のグローバル利用を維持し、同じproton-passラッパーでプロジェクト別PATを使うための設計記録。PATはProton Passログイン用であることを利用者に確認した。明示選択・保存配置・プロジェクト側env限定・PAT用identity共有は承認済み。以下の「提案」「承認前」「未実施」は設計時点の記録である。承認後の実装・実機確認は冒頭の「現在の状態」と7〜11節を参照する。SOPS・miseの連携案は引き続き後続検討とし、1〜5節の手順は維持する。

### 責務と対象範囲

| 対象 | 担当 |
| --- | --- |
| Proton Pass CLI | 復旧用秘密鍵とプロジェクト用認証情報の保管・取得 |
| proton-passラッパー | 認証対象の選択、PATの復号、CLIセッションと鍵キャッシュの分離 |
| SOPS + age | プロジェクト設定ファイルの暗号化・復号 |
| mise | ランタイム、実行時の環境変数、各ツールを呼ぶタスクの管理 |

最初の実装対象はPAT選択と認証状態の分離を提案する。SOPS連携は後続で検証する。PATの作成・権限変更・失効、プロジェクトの自動検出、クラウド同期、秘密情報の一括取得は追加しない。

### 調査で確認したこと

実HOMEと環境変数を継承しない一時環境で、pass-cliの版とヘルプだけを確認した。実体は2.6.0（ビルド表示8bcac4c）。認証やセッション情報の表示は行っていない。

- 公式資料ではPROTON_PASS_SESSION_DIRで保存先を指定できる。公式2.6.0のutils.rsでは、指定したディレクトリの下にさらに.sessionを作る。session.jsonとデータベースは、この基準ディレクトリから構成される。
- keyringの資格情報名には保存先のハッシュを使う。ただし、資格情報がなければ共通の旧資格情報を読み、削除時には旧資格情報も消す処理がある。独立した鍵になることは保証されない。
- 強制ログアウトはenv方式でもkeyringの後始末を試みる。プロジェクト側でlogout --forceを実行すると、既存グローバルの旧資格情報に影響する可能性がある。
- 公式資料はPATセッションの有効期間を2時間としている。鍵キャッシュのTTLとは別で、セッション切れに対する再ログイン手順が必要になる。
- miseはSOPS暗号化ファイルを読み込める。復号結果のredact指定があってもmise envは値を表示するため、マスクを秘密情報の非表示保証として扱わない。

公式タグ2.6.0はf90e1062990172b3404a41d6e91b64f549e87b86へ解決した。ビルド表示8bcac4cは公開APIで見つからず、ローカル実行ファイルと公開タグのソースが完全に一致することは未確認。以下の案は、実装時のダミー検証と利用版の確認を条件とする。

### 選択方法と互換性の提案

先頭の--profile NAMEだけをラッパー用の指定として解釈し、残りはpass-cliへ引き渡す。globalを予約名とし、指定なしは従来のグローバル利用とする。プロジェクト内から実行しても、カレントディレクトリで暗黙に切り替えない。

```sh
# 設計時点の操作案。現在は実装済み。
proton-pass login
proton-pass --profile global login
proton-pass --profile demo login
```

名前は先頭を英小文字・数字とし、残りは英小文字・数字・ハイフン・アンダースコア、最大64文字を提案する。空文字、パス、重複指定、未登録名は復号・キャッシュ起動・CLI実行より前に拒否し、globalへフォールバックしない。登録済みかどうかは、後述のディレクトリと必須暗号文で判定し、別の登録台帳は作らない。

グローバルのPAT、identity、provider、キャッシュの既定値と既存の上書き方法を維持する。chezmoiの参照先、Gitテンプレート、引数なしinit-proton-passはグローバル利用を継続する。プロジェクト用にHOMEやXDG全体を差し替えず、セッション保存先だけを対象CLIへ渡す。

プロジェクト利用では、session dir・cache dir・identity等の継承値が計算した対象と矛盾すれば停止する。PATとCLI暗号化鍵の継承値は既存どおり除き、選択対象の値だけを必要な子プロセスへ渡す。loginでPATを引数へ直接指定する操作も拒否し、選択した暗号文の使用を保証する。グローバル利用でPROTON_PASS_SESSION_DIRを明示した場合の既存挙動は維持する。

### 保存先とproviderの提案

| 対象 | グローバル | プロジェクトNAME |
| --- | --- | --- |
| PAT | 既存のproton-pass/token.age | proton-pass/projects/NAME/token.age |
| CLI暗号化鍵 | 既存のproton-pass/encryption-key.age | proton-pass/projects/NAME/encryption-key.age |
| CLI保存先の指定 | 既存の指定またはCLI既定 | proton-pass/projects/NAME/cli |
| 実際のセッション・DB | 既存位置を移動しない | 上記cli/.session以下 |
| 鍵キャッシュ | 既存の既定・上書き | 既定キャッシュ領域のprojects/NAME以下 |
| PAT・CLI鍵の復号identity | 既存の既定・上書き | 初期案では既存identityを共有 |

表のproton-pass配下は${XDG_DATA_HOME:-$HOME/.local/share}を基準とする。プロジェクトのキャッシュは$HOME/.cache/proton-pass-key-cache/projects/NAMEを既定候補とする。専用領域は0700、暗号文は0600。親の所有者・書き込み権限とリンクを確認し、不適切な既存領域は自動chmodせず停止する。保存先が管理リポジトリ内になる指定も拒否する。

プロジェクトの初期対応はenv方式を提案する。CLI暗号化鍵とキャッシュをプロジェクトごとに分け、TTLは現行の既定900秒・上限3600秒を維持する。グローバルのproviderがkeyringでも、プロジェクト用env方式は明示的な別仕様として承認を得る。既存のprovider不一致検出を単純に削除して実現しない。

プロジェクト指定時はlogout --forceを拒否する。実装時には短縮形や別名でも拒否できることを確認する。ログイン失敗・セッション切れでも、自動ログアウト・鍵再生成・自動再ログインは行わない。通常logoutと再loginは利用者が対象を明示して行う。keyring対応は、旧資格情報への影響まで確認できる利用版と検証方法が整った後に検討する。

異なるプロジェクトは独立実行できる構成にする。同一プロジェクトの初期設定とCLI実行は、プロジェクト単位のロックで競合を防ぐ。runで起動した子が同じラッパーを再度呼ぶ場合に無期限待機しないよう、初期実装では競合を待たず非0で停止する。キャッシュ起動用ロックとCLI実行用ロックを混同せず、常駐キャッシュへCLI実行ロックを継承させない。

### 登録・日常利用・復旧の提案

初期設定は既存bootstrapを拡張し、グローバルの無指定動作を維持する。プロジェクト指定では名前・保存先・providerを先に検証し、PATを対話入力する。暗号文を一時領域で完成させてから公開し、再実行で既存PAT・鍵・セッションを置き換えない。PAT差し替えと鍵ローテーションは通常登録から分け、明示的な更新手順を定義する。

日常は登録後に対象を明示してloginし、以後の参照も同じ対象を指定する。キャッシュのlock・status等の管理操作も同じ対象を選べるようにし、globalのキャッシュを誤操作しないことを確認する。キャッシュ期限が切れればCLI暗号化鍵の復号を求め、CLIセッションが切れれば再loginを案内する。期限切れPATは利用者が更新する。PATとセッションの寿命をキャッシュ延長で代用しない。

Proton Passログイン用PATを復号するidentityと、SOPS設定を復号するプロジェクト鍵は役割を分ける。前者を取り出すために同じPATによるProton Passログインが必要な構成は避ける。端末喪失時に必要なidentity・パスフレーズの復旧手段とPATの再発行方法は、当該セッションとは独立して用意する。

SOPS用の鍵はProton Passに復旧用として保管し、日常利用用のローカル配置・保護方法は別途決める。候補はリポジトリ外の非公開鍵ファイル、または暗号化した鍵を実行時だけ復号する方式。今回、新しい鍵ファイルは作らず、既存PAT用identityをSOPSへ流用しない。

### miseとSOPSの連携案

miseのタスクから対象を明示してラッパーを呼ぶ。次は設定例であり、実際のプロジェクトへ配布・適用していない。

```toml
[tasks."secrets:login"]
run = "proton-pass --profile demo login"
```

通常のシェル起動・ディレクトリ移動で、Proton Passへのログインや秘密鍵取得を自動実行しない。PAT・CLI暗号化鍵・SOPS秘密鍵の実値はmise.tomlや恒久環境変数へ書かない。

SOPS連携は、非秘密の通常設定と暗号化環境の読み込みを分ける。復旧・初期準備タスクは暗号化環境を読み込まない構成にする。鍵未配置の状態で、miseがタスク開始前に復号を要求する循環を防ぐためである。

日常の秘密情報の注入は、まず必要なタスク内のSOPS exec-envを候補とする。復号結果を対象プロセスだけに渡し、通常シェル全体へは展開しない。対象プロセスへSOPS秘密鍵やProton Passの鍵まで継承しないことを検証する。鍵のローカル保護方法と合わせて、実行例を後続で確定する。

miseによるSOPSの直接読み込みも選択肢だが、採用前に利用版・鍵形式・読み込み順序をダミーで確認する。秘密値を表示するmise env、デバッグ出力、タスクの出力保存を検証・共有ログへ使わない。SOPSで管理する値とProton Passから直接取得する値はプロジェクトごとに決め、同じ値の二重管理を既定にしない。

### 実装対象と検証条件

| 対象 | 予定する変更・確認 |
| --- | --- |
| 通常ラッパー・鍵キャッシュ | 名前の検証、パス決定、セッション・暗号化鍵・ソケットの分離、既存上書き値との衝突検出 |
| bootstrap | 明示的な対象指定、既存資産の保護、途中失敗・再実行・更新手順 |
| init・Makefile・chezmoi・Git | 参照箇所を確認し、グローバルの無指定動作を回帰検証。必要がなければ変更しない |
| 既存setup・cacheテスト | 隔離HOME、ダミーPAT・鍵、偽CLIで認証先と環境変数を確認 |
| 利用手順 | 登録・再login・通常logout・鍵キャッシュのロック・復旧・PAT更新の対象を明記 |

受け入れ条件は、従来の無指定利用が維持され、プロジェクトA・B・globalでPAT、セッション、CLI暗号化鍵、キャッシュが混線しないこと。不正名、未登録、暗号文欠落、リンク、権限不備、復号失敗、CLI失敗、同時実行、継承値の矛盾をダミーで確認する。PATはloginだけへ渡り、常駐プロセスや通常参照へ継承しない。失敗時は別対象へ切り替えない。

実装後は対応unittest、隔離テンプレート検証、make checkの順に行う。SOPS・mise連携は使い捨ての検証用鍵と暗号文で、鍵欠落時の停止、初期準備の到達性、対象アプリへ渡る環境変数を確認する。実PAT、実鍵、実セッションはテストへ持ち込まない。

導入時はglobalの保存先と資産を移行せず、新規プロジェクトだけを追加する。問題時はプロジェクト指定の利用を止め、globalの動作を確認する。コードを戻す際も新しい暗号文を削除しない。実環境での登録・認証・適用とcommit・pushは別の明示依頼に従う。

### 設計時点の承認事項と調査の限界

設計時点で承認を求めたのは、--profileによる明示選択、新しい保存配置、プロジェクト側env限定、既存PAT用identityの共有であり、現在はいずれも承認済み・実装済み。SOPS用鍵のローカル保護方法は後続設計の判断事項として残す。

設計時点の調査は管理ソース・ダミーテスト・隔離したCLIヘルプ・承認された公式資料に限定し、実認証、keyring操作、SOPSとmiseの実連携は行っていない。その後の利用者による認証確認は10〜11節に記載する。ラッパーの分離は誤接続を防ぐもので、同じOSユーザー権限で動くプロセス間のアクセス隔離を保証しない。

参照した公式資料：

- [Proton Passの設定とPAT](https://protonpass.github.io/pass-cli/get-started/configuration/)
- [公式2.6.0の保存先処理](https://github.com/protonpass/pass-cli/blob/f90e1062990172b3404a41d6e91b64f549e87b86/pass-cli/src/utils.rs)
- [同版のkeyring処理](https://github.com/protonpass/pass-cli/blob/f90e1062990172b3404a41d6e91b64f549e87b86/pass-cli/src/features/keyring.rs)
- [同版のログアウト](https://github.com/protonpass/pass-cli/blob/f90e1062990172b3404a41d6e91b64f549e87b86/pass-cli/src/commands/logout.rs)と[鍵管理](https://github.com/protonpass/pass-cli/blob/f90e1062990172b3404a41d6e91b64f549e87b86/pass-cli/src/features/mod.rs)
- [miseのSOPS連携](https://mise.jdx.dev/environments/secrets/sops.html)
- [SOPSの子プロセスへの受け渡し](https://getsops.io/docs/usage/advanced/)

## 7. プロジェクト別PATとキャッシュ期限の実装（2026-11-18）

通常ラッパー、鍵キャッシュ、bootstrap、Makefileにプロジェクト対応を追加した。指定なしと--profile globalは従来のグローバル利用を継続する。プロジェクト内で実行しても暗黙に切り替わらず、chezmoiとinit-proton-passの参照先も維持する。以下の実認証・適用コマンドは今回の自動検証では実行していない。

### 登録と日常利用

既存のグローバル用identityとrecipientを共用する。先にグローバルの初期設定を済ませる。プロジェクト用の登録は、その既存identityがなければ停止し、新しい鍵は生成しない。

```sh
# 利用者が内容を確認して実行する操作例。
make bootstrap PROTON_PASS_PROFILE=demo
make wrapper
proton-pass --profile demo login
proton-pass --profile demo info
```

bootstrapは登録した対象へログインするため、直後のloginは必須ではない。上のloginはセッション切れ後の再ログインにも使える。infoの出力にはアカウント情報が含まれ得るため、共有ログへ貼り付けない。

保存先は6節の表に従い、プロジェクト別のtoken.age、encryption-key.age、cli/.session、キャッシュを分離する。identityの指定には共有のAGE_IDENTITY_DIRを使える。AGE_IDENTITY_FILEを指定する場合は、その配下のid_proton_pat.ageと一致する必要がある。グローバル単独利用の上書き方法は変更していない。

プロジェクト名は英小文字・数字から始まる64文字以内とし、残りは英小文字・数字・ハイフン・アンダースコアを受け付ける。globalは予約名。ソケットの絶対パスが107バイトを超える場合は、短い名前を使う必要がある。

不正な名前、未登録、秘密ファイルの欠落、リンク、不適切な所有者・権限、リポジトリ内の保存先、env以外の指定、対象と矛盾する継承設定は停止する。同一プロジェクトのCLI実行・bootstrapが競合した場合も、待機や別対象への切り替えをせず非0で終了する。

プロジェクトのloginは追加引数を受け付けず、PATを引数へ直接指定できない。logout --forceと短縮形も拒否する。通常logoutは対象を明示して実行する。セッション切れや認証失敗からの再ログインは自動化していない。

### 鍵キャッシュの期限を選ぶ

キャッシュするのはPATではなく、CLIのデータベース暗号化鍵である。--ttl-minutesで15・30・45・60分を選択でき、未指定は15分。プロファイル指定と期限指定は、unlock等のサブコマンドより前に置く。

```sh
# プロジェクトのキャッシュを30分で開始する。
proton-pass-key-cache.py --profile demo --ttl-minutes 30 unlock
proton-pass-key-cache.py --profile demo status
proton-pass-key-cache.py --profile demo lock

# グローバルのキャッシュを60分で開始する。
proton-pass-key-cache.py --ttl-minutes 60 unlock
```

既存のPROTON_PASS_CACHE_TTLによる秒指定も維持し、1〜3600秒を受け付ける。--ttl-minutesを同時に指定した場合は、コマンド側を優先する。たとえばmiseのタスク環境でPROTON_PASS_CACHE_TTLを1800にすれば、そのタスクから新しく開始するキャッシュを30分にできる。秘密値ではないため、プロジェクト設定へ記載できる。

期限は鍵をキャッシュした時点から計測する。参照・status・再度のunlockでは延長せず、稼働中のキャッシュへ別の期限を指定しても変更しない。期限を変更する場合は、同じ対象のlockを実行してからunlockする。lock直後は常駐プロセスの終了まで短時間競合し得るため、失敗した場合は終了後に再実行する。最大60分の制限は常駐プロセスの起動引数にも適用する。

### 再実行・PAT更新と残件

bootstrapの再実行では既存PATとCLI暗号化鍵を再利用する。PATを更新する場合は、対象の処理を終了し、キャッシュをlockする。通常logoutが成功するなら先に実行する。その後、既存token.ageをリポジトリ外の非公開領域へ別名で退避して、同じ対象のbootstrapで新しいPATを登録する。encryption-key.ageと共有identityは維持する。

通常logoutが認証失敗で停止する場合は、選択対象のcli/.sessionだけを、他の処理が停止した状態で未使用の退避名へ移す方法を検討する。これは保存済みセッションを変更する操作なので、自動では実行しない。退避と再登録の実機確認は残件とし、globalのセッションやkeyringを初期化して回避しない。

ダミー・隔離HOME・偽CLIによる回帰検証を追加した。実PAT・実鍵による登録と認証、SOPS用鍵のローカル保護方法、miseとSOPSの連携、各環境の実機確認は今回の実装に含めていない。利用者は差分確認後にmake wrapperで実行コマンドを展開する。補完の追加適用については8節を参照する。

この実装段階のCodexの検証では、make checkはunittest 334件・Bats 18件が成功し、skipなし。env・keyringで展開した通常ラッパーはBash構文・ShellCheck・shfmtも成功した。ShellCheckのSC2059は既存の固定書式ログ関数を理由に除外した。textlintとnatural-japaneseを実行し、文の長さと語彙反復の統計指摘は、手順と技術用語を明確にするため維持した。この段階では実認証・適用・commit・pushは未実施。その後、利用者による適用・実認証の成功報告を受けた（10〜11節）。

## 8. プロジェクト初期登録コマンドと補完

専用コマンドと補完を含む変更は、利用者が実環境へ適用済み。初期登録の完了と3コマンドのTab候補表示も報告された（9〜10節）。Codexによる適用・実認証は行っていない。

### プロジェクト用の必要ファイルを準備する

```sh
setup-proton-pass-project demo
setup-proton-pass-project --help
```

専用コマンドはdotfilesのbootstrap/setup-proton-pass.sh --profile demo envへ委譲する。PATを対話入力して暗号化し、CLI用の暗号化鍵を生成して暗号化保存した後、対象へログインする。再実行では既存ファイルを利用する。暗号化処理はbootstrapへ集約しており、元のmake bootstrap PROTON_PASS_PROFILE=demoも引き続き使える。

age identityとrecipientは既存の共有ファイルを維持する。プロジェクト別のage identityを新しく作る操作ではない。Proton Pass上でのPAT作成は利用者が行い、秘密値はコマンド引数へ書かない。専用コマンドにはプロジェクト名だけを渡し、global・不正名・余分な引数は拒否する。

展開時に記録したdotfilesのソースからbootstrapを呼ぶため、チェックアウトが必要になる。ソースを移動した場合はテンプレートを再展開する。--helpは初期登録処理を起動しない。

### Bash・Zshの補完

次のコマンドに補完を追加した。

| コマンド | 補完する候補 |
| --- | --- |
| proton-pass | --profile、globalと保存済みプロジェクト名、login・logout・info等の最初のサブコマンド |
| proton-pass-key-cache.py | --profile、--ttl-minutes、15・30・45・60、unlock・status・lock・run |
| setup-proton-pass-project | --helpと既存プロジェクト名。新しい名前も直接入力できる |

補完時は暗号文やidentityを開かず、プロジェクト保存ディレクトリの名前だけを読む。復号・ログイン・鍵キャッシュの起動やディレクトリ作成は行わない。CLI固有の下位サブコマンドや、その詳細オプションは今回の補完に含めない。シェル側でもサブコマンド以降の補完を停止し、入力済みの秘密値を補完用Pythonのプロセス引数へ渡さない。

Bashは~/.config/bash/completions/proton-pass.bashを.bashrcから読む。Zshは~/.zsh/completions/_proton-passを利用し、既存のzcompdumpがあってもcompletion.zshから登録する。どちらもシェル起動時には補完用Pythonを実行しない。

今回の適用対象は、専用コマンド、鍵キャッシュスクリプト、Bashの補完ファイルと.bashrc、Zshの補完ファイルとcompletion.zsh。差分を確認して適用後、新しいシェルを開く。make wrapperだけでは補完ファイルとシェル設定を適用しない。

追加した7件の回帰テストで、専用コマンドの委譲、Bash・Zshの補完候補、暗号文を開かない動作、入力済みの秘密値を補完用プロセスへ渡さない動作を確認した。この追加段階のmake checkはunittest 341件・Bats 18件が成功し、skipなし。専用コマンドの隔離展開後のBash構文・ShellCheck・shfmt、補完の静的検証、文書のtextlintも成功した。この段階のCodex検証では、実際の登録・認証、適用、実端末でのTab操作は未実施。その後の利用者確認は10〜11節を参照する。

## 9. prootのUID変換と所有者検証

利用者の実機確認で、Pythonの実行UIDが1001、PATとCLI鍵の暗号文の所有UIDが10306となり、所有者検証で停止した。chown後も値は変わらなかった。同じ環境のCodex側ではgetuidが1001、/proc/self/statusのUid行が10306であることを確認した。秘密ファイルの内容や復号結果は調べていない。

[PRootの公式マニュアル](https://github.com/termux/proot/blob/master/doc/proot/manual.txt)では、実行ユーザーやファイル所有者のUIDを仮想化し、所有者変更の成功を模擬する場合がある。今回の暗号文のUIDはプロセスのホスト側UIDと一致しており、仮想UIDだけとの比較では同じユーザーを拒否していた。ファイル情報が変換前・変換後のどちらで返るかの差を考慮する必要がある。

鍵キャッシュスクリプトは、os.getuidの値と、同一プロセスの/proc/self/statusから取得した実UIDを所有者判定に用いる。任意のUIDを設定値で許可する方法は追加しない。通常Linuxでは両者が一致し、従来どおりの判定になる。procの値を取得・検証できなければ、os.getuidだけを使う。

ファイル、ディレクトリ、実行ロック、キャッシュソケットと接続元UIDに同じ判定を適用する。別ユーザーのUID、公開された権限、リンク、空の暗号文は引き続き拒否する。proot内の仮想ユーザー間に、ホストの別ユーザーと同じアクセス隔離があるとは扱わない。

利用者はUID対応版を再適用し、infoの成功を確認済み（10節）。次は修正を適用する際の操作例であり、Codexは適用・認証を行っていない。

```sh
chezmoi apply --include=files --refresh-externals=never "$HOME/.local/bin/proton-pass-key-cache.py"
proton-pass --profile pat-test info
```

ログアウト済みなら、同じプロファイルを指定してloginする。既存のPAT・CLI暗号化鍵・共有identityは再生成せず、chownやchmodを繰り返す必要もない。

初期構築で同じidentityのパスフレーズを3回求める処理は、identityと公開鍵の一致確認、PATの復号、CLI暗号化鍵の復号を別々に実行する仕様。UID不一致とは分けて扱う。

UID変換の混在はダミーで修正前の失敗を再現し、修正後の成功と、無関係なUID・不適切な権限の拒否を確認した。procの欠落・不正値、保存領域と接続元UIDも回帰検証した。UID修正段階のmake checkはunittest 347件・Bats 18件が成功し、skipなし。proot上の使い捨てソケットとダミー鍵でも保存・取得・ロックが成功した。textlintも成功し、natural-japaneseの統計指摘は手順と技術用語の明確さを優先して維持した。Codexによる実鍵の変更・復号、実認証、適用は未実施。

## 10. 実機確認と残り時間の表示

利用者から、UID対応版の適用後にpat-testのinfoが成功し、Personal Access Token: pat-testと表示されたとの報告を受けた。また、proton-pass、proton-pass-key-cache.py、setup-proton-pass-projectのTab補完で期待する候補一覧を確認したとの報告を受けた。

実環境でstatusの「ロック中」を確認し、--ttl-minutes 30 unlockの後に「unlock済み（残り1777秒）」と表示された。これにより、確認済み環境でのプロジェクト認証、補完、30分の鍵キャッシュ開始を利用者確認済みとする。期限経過時の停止や他環境の動作まで確認済みとは扱わない。

この報告を受け、statusの表示を分と秒へ変更した。1777秒なら「unlock済み（残り29分37秒）」、60秒なら「unlock済み（残り1分0秒）」と表示する。内部の残り秒数、期限の計算、上限60分、ロック中の表示は維持する。表示変更版の適用後はstatusを再実行すればよく、稼働中のキャッシュを作り直す必要はない。

利用者から、表示変更版の再適用後に、想定どおりの分・秒表記になったとの報告を受けた。残り時間の表示も確認済み環境で利用者確認済みとする。

## 11. 認証先の切り替え検証

Codexは、実PAT・実鍵・実セッションへアクセスせず、隔離HOME、偽age、偽pass-cli、ダミー暗号文とダミーセッションで連続切り替えを確認した。ラッパーは隔離したchezmoiで展開し、鍵キャッシュとソケット通信には管理ソースの実装を使った。検証終了時にダミーキャッシュを停止し、一時領域を片付けた。製品コードは変更していない。

| 確認した条件 | 結果 |
| --- | --- |
| グローバル→A→グローバル→B→A→グローバル | 各指定に対応するダミーの認証名・セッション保存先・CLI暗号化鍵が一致 |
| グローバルのproviderがenvまたはkeyring | 両方でプロジェクト側envとの分離が成功。OSの実keyring操作は未実施 |
| Aをログアウトした後にグローバル・Bを参照 | Aだけが未ログインとなり、他の認証は維持 |
| Aのログアウト後にinit-proton-passを実行 | グローバルだけを再ログイン。Aは未ログインのままで、暗黙の切り替えなし |
| Aを明示して再ログイン | Aが復帰し、認証先が一致 |
| 通常の参照 | 偽CLIへPATを渡していないことも確認 |

関連unittest 58件と、env・keyringの両設定を含む追加の連続切り替え検証1件が成功した。追加検証は一時環境だけで実行し、製品コードや実際の認証状態は変更していない。

上記のCodex検証は呼び出し先の選択とローカル状態の分離を対象とする。実サービスでの成功は、末尾の利用者による実機確認結果に記載する。次は同じシェルで再確認する場合の手順である。確認目的でログアウトや再登録を行う必要はない。

```sh
proton-pass info
proton-pass --profile pat-test info
proton-pass info
```

最初と最後のグローバルのPAT名が同じで、途中だけPersonal Access Token: pat-testとなることを確認する。対象アカウントも想定と一致していることを手元で確認し、infoの全出力は共有しない。

続けて、テスト用PATの参照範囲を確認する。

```sh
proton-pass --profile pat-test vault list
```

テスト用PATへ許可した保管庫が表示され、許可していないdotfiles用等の保管庫が表示されないことを確認する。想定と異なる場合は操作を止め、PATのアクセス権限を管理側で確認する。実秘密値の取得を確認手順には含めない。

セッション切れと表示された場合だけ、対象を明示して再ログインしてから確認をやり直す。プロジェクトはproton-pass --profile pat-test login、グローバルはproton-pass loginを使う。共有する結果は、グローバル前後の一致、pat-testへの切り替え、保管庫一覧が想定どおりかの3点と、秘密情報を除いたエラーだけでよい。

### 利用者による実機確認結果

利用者から、同じシェルでグローバル→pat-test→グローバルの順にinfoを実行し、最初と最後のグローバルのPAT名が一致し、途中だけpat-testとなったとの報告を受けた。さらに、テスト用PATへ1つの保管庫だけを許可した状態で、その保管庫だけがvault listに表示された。

これにより、確認済み環境での認証先の切り替えと、テスト用PATの保管庫一覧が許可範囲と一致することを利用者確認済みとする。Codexによる実認証の再実行や、未許可項目への直接アクセス拒否、他環境での動作まで確認済みとは扱わない。

## 12. Termux初期構築のファイル確定（2026-11-20）

利用者から、配置修正後のchezmoi initではpromptStringOnceが動作したとの報告を受けた。その後のTermux上のbootstrapは、identityの生成・暗号化後、ファイルの確定で停止した。従来はpublish_onceで一時ファイルから宛先へのハードリンクを作成し、lnのエラー詳細を非表示にしていた。

追加確認では、Termux側のPythonにos.linkが存在しなかった。これはPython APIの有無を示す結果であり、lnコマンドが失敗した理由の確定には使わない。利用者のダミー確認では、lnはPermission denied（終了コード1）、宛先が未作成のmv -nTは終了コード0で移動後のファイルも存在した。ハードリンクの失敗と移動の成功は実機で確認できたが、拒否の具体的な原因、既存宛先の上書き防止、bootstrap全体の解消は未確認。

修正案では、同じ保存領域の一時ファイルをmv -nTで確定し、ハードリンクへの依存をなくした。既存ファイルを上書きせず、宛先がディレクトリでもその中へ移動しない。移動がスキップされてもmvが成功を返す場合があるため、一時ファイルが移動済みかも確認する。既存の有効な通常ファイルだけを再利用し、空ファイル・リンク・ディレクトリは拒否する。失敗時にはmvのエラーも表示する。

この共通処理はidentity、recipient、PAT・CLI鍵の暗号文で使う。パスや暗号化方式は変更せず、bootstrapの必須コマンドをlnからmvへ変更した。回帰テスト4件で、ハードリンク非対応、権限維持、既存データの非上書き、不正な宛先、競合、移動失敗時のエラー表示と元データ維持を確認した。関連テスト24件と、make checkのunittest 352件・Bats 18件が成功し、skipは0件。実鍵の生成・復号・認証は行っていない。

利用者が修正版を取得した後に再試行する場合は、同じTermux環境で既存のbootstrap手順を使う。bootstrapはソースから実行するため、この修正のためだけのchezmoi applyは不要。identity・recipient・暗号文の削除や鍵再生成を先に行わず、既存ファイルに不整合があれば停止した状態で確認する。

## 13. Termuxでchezmoiからラッパーを起動できない場合（2026-11-20）

利用者は、TermuxでProton Pass CLIをpkgから導入し、ラッパー経由のPATログイン、保管庫一覧表示、ssh-agentデーモンの起動に成功した。その後のchezmoi applyは.gitconfigのprotonPass呼び出しで、ラッパーへのfork/execがno such file or directoryとなって停止した。秘密値の取得前のプロセス起動段階のエラーである。

ラッパーが存在していても、シバンに指定したインタプリタが存在しなければ同じエラーになる。従来の関連コマンドは/usr/bin/envを指定していた。[Termux公式の実行環境資料](https://github.com/termux/termux-packages/wiki/Termux-execution-environment)でも、シバン補正を利用できない起動ではこの形式が失敗し得ると説明されている。利用者の追加確認では、ラッパーは実行可能で、先頭行は#!/usr/bin/env bashだった。/usr/bin/envは実行不可、PREFIX/bin/envは実行可能だった。存在するラッパーのシバン先を実行できない状態が確認できたため、今回の直接起動失敗の原因をシバン不整合として記録する。修正後の限定適用と通常applyの成功確認は残す。

修正後はtermuxフラグがtrueの場合だけ、proton-pass、init-proton-pass、setup-proton-pass-project、proton-pass-key-cache.pyのシバンをPREFIX/bin/envへ展開する。PREFIXが空または相対パスなら展開を停止する。Linux・prootでは/usr/bin/envを維持し、Bash・Pythonの選択は引き続きPATHに従う。provider、PAT、セッション、キャッシュの配置は変えない。

修正版を取得した利用者は、Termuxで差分を確認してから関連4ファイルだけを適用する。以下は利用者向けの操作例であり、Codexは実行していない。

```sh
chezmoi apply --include=files --refresh-externals=never \
  "$HOME/.local/bin/proton-pass" \
  "$HOME/.local/bin/init-proton-pass" \
  "$HOME/.local/bin/setup-proton-pass-project" \
  "$HOME/.local/bin/proton-pass-key-cache.py"
head -n 1 "$HOME/.local/bin/proton-pass"
head -n 1 "$HOME/.local/bin/proton-pass-key-cache.py"
```

先頭行がTermuxの絶対パスのenvを指すことを確認後、通常のchezmoi applyを再試行する。出力に秘密値が含まれる可能性があるため、共有ログへ貼らない。セッションが有効なら、今回の修正のための再ログイン・鍵再生成・ssh-agent再起動は不要。

隔離したPREFIX・HOMEとダミー処理で、関連4コマンドのシバン、補正ライブラリなしの直接起動、chezmoi経由の起動を確認した。Linux・prootでPREFIXを引き継いでも既存形式を維持することも確認した。make checkはunittest 353件・Bats 18件が成功し、skipは0件。実PAT・実鍵・実セッションは使用していない。
