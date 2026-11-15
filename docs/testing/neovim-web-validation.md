# Web・汎用LSPの検証記録

2026-11-15、NV-03の継続作業としてWebのプロジェクト判定を修正し、汎用LSPを隔離検証した。Neovimはv0.12.6、実行ホストはLinux aarch64。Pythonの利用者報告についても、訂正されたNeovim版v0.12.6を反映した。

## 確認した問題と修正

| 対象 | 確認した事実 | 修正内容 |
| --- | --- | --- |
| denols | Deno設定がないGitプロジェクトでもroot_dirが返ることを実Neovimで再現 | `.git`だけでは選択しない。deno.json・deno.jsonc・deno.lockを条件にする |
| vtsls | Deno判定がサーバーごとに異なり、deno.lockだけのプロジェクトで重複選択する可能性があった | `lua/config/web-project.lua`でdenolsと同じ判定を使う |
| Conform | Deno判定がカレントディレクトリ基準で、Biome設定がない場合もBiomeを候補にしていた | バッファのパスから判定し、Biome設定がある場合だけbiome-checkを候補にする |
| Biome LSP | 相対コマンドnode_modules/.bin/biomeを指定し、起動時の作業ディレクトリを指定していなかった | プロジェクト内の実行可能ファイルを絶対パスで優先し、なければPATHのbiomeを使う。起動時のcwdも指定する |

後半3件は設定上の潜在的なリスクとして修正した。実プロジェクトでの失敗は再現していない。

DenoとNodeのlockfileが同じ階層ならDenoを優先する。Deno配下にNodeのlockfileがある場合は、そのNodeプロジェクトにvtslsを選ぶ。Node配下のDenoプロジェクトにはdenolsを選ぶ。package.jsonだけではNodeの境界にしない。

Web整形はDenoならLSP fallback、Biome設定があればbiome-checkを優先し、利用できなければprettierdを使う。それ以外はprettierdを使う。Biome自体の実行失敗に対する再試行ではなく、実行可能なformatterの選択である。

## 実行結果

導入済みツールを使い、HOME・XDGディレクトリと確認用ファイルを一時領域に分離した。通常設定の起動やlazy.nvimの取得は行わず、対象のLSP設定を直接読み込んだ。JSON・YAML・TOMLのスキーマ取得を検証用設定で無効にし、外部依存を追加していない。

| 対象 | 確認内容 | 結果 |
| --- | --- | --- |
| cssls | 接続、未知のプロパティの診断1件、修正後0件、LSP整形 | 成功 |
| html | 接続、divの補完、LSP整形 | 成功。診断の検証対象にはしていない |
| jsonls | 接続、構文エラーの診断1件、修正後0件、LSP整形 | 成功 |
| yamlls | 接続、構文エラーの診断1件、修正後0件、LSP整形 | 成功 |
| taplo | 接続、キー重複の診断2件、修正後0件、LSP整形 | 成功 |
| marksman | 接続、別Markdownファイルへのリンクの定義ジャンプ | 成功。診断1件も取得したが、その内容の評価は対象外 |
| Deno・Node・Biome | 通常Git、Deno、入れ子のNode、入れ子のDeno、Biomeの5構成を別cwdから判定 | 成功。実Neovimのファイル探索とConformの候補を確認 |
| Biome整形 | 空白を含むプロジェクト内に導入済みBiome 2.6.7へのリンクを置き、実Conformから整形 | 成功。プロジェクト内の実行ファイル選択と整形出力を確認 |
| 回帰テスト | ルート分岐5件、Biomeのローカル優先・PATH利用2件、バッファ基準の整形1件 | 8件成功 |
| make check | 全体検証 | unittest 246件・Bats 18件成功、skipなし |

回帰テストは`tests/test_web_lsp.py`に追加した。実Neovimの継続確認プロジェクトは`/tmp/neovim-web-check-is4bbr3r`にある。一時領域なので永続的な保存は保証しない。

## 初回の未検証と次の判断

- Biome LSPのデーモン接続は未実施。既存デーモンとの共有を避け、今回はコマンド・cwdのモック検証と実CLIによる整形を確認した。
- denols・vtslsの同時自動接続と通常UIの確認は残る。今回は判定関数を検証した。prettierdとDenoの保存時整形には、以前の利用者による成功報告がある。
- emmet_language_server・tailwindcss・oxlint・golangci_lint_lsは、使用対象とプロジェクト設定を確定してから確認する。sqlsはDB接続を伴うため今回の対象外とした。
- 単一ホストの結果であり、Termux単体・WSL・他のネイティブLinuxへ一般化しない。Mason本体・連携プラグイン・既存データは変更していない。

次は利用する追加サーバーを選び、上記の未検証範囲を確認してからMason完全削除を判断する。追加依存やDB認証が必要なら、導入・接続前に対象と用途を確認する。

## 利用者による通常UIの確認

設定適用後、Mason無効化モードで次の確認を行う。適用操作自体は今回実行していない。

1. 通常のTypeScriptプロジェクトを開き、`:LspInfo`でvtslsが接続し、denolsが接続しないことを確認する。
2. deno.jsonがあるフォルダと、その配下にNodeのlockfileがあるフォルダを別々に開き、Deno側はdenols、Node側はvtslsが選ばれることを確認する。
3. Biome設定があるフォルダを別cwdから開き、`:LspInfo`のrootとBiomeの接続を確認する。プロジェクト内にBiomeがあればその実体を、なければPATH上の実体を使うことを確認する。
4. `:ConformInfo`でBiome側の候補にbiome-checkとprettierd、通常Webにprettierd、Deno側に外部formatterなしと表示されることを確認する。Biome側はstop_after_firstにより利用可能な先頭だけを実行する。確認用ファイルを保存し、整形されることを確認する。
5. CSS・HTML・JSON・YAML・TOML・Markdownで上表に対応する操作を試し、環境・サーバーのパス・成功または失敗を記録する。

`biome-check`は整形だけでなくlintの修正とimport整理も行うため、確認用ファイルを使う。

## 通常UIの報告と適用状態の確認（2026-11-15）

利用者が記入した`/tmp/neovim-web-check-is4bbr3r/RESULTS.md`を確認した。依頼文の`/tmp/neovim-web-check-y_is4bbr3r/RESULTS.md`は存在しなかった。報告の環境はTermux + proot Ubuntu、Neovim v0.12.6、設定適用日は2026-11-15。起動時はMason無効化を指定している。以下は利用者報告であり、Codexによる再実行結果ではない。

| 対象 | 報告された成功 | 未確認・問題 |
| --- | --- | --- |
| cssls | 整形 | 接続・補完・診断・定義ジャンプの欄は未確認 |
| html | 接続・補完・整形 | 診断は空欄、定義ジャンプは未確認 |
| jsonls | 接続・補完・診断・整形 | 定義ジャンプは未確認 |
| yamlls / taplo | 接続・診断・整形 | 補完・定義ジャンプは未確認 |
| marksman | 接続・補完・診断・定義ジャンプ | 整形は対象外 |
| plain/src/main.ts | vtslsのみ接続、補完・診断・定義ジャンプ・整形 | なし |
| deno/src/main.ts | denolsのみ接続、補完・診断・定義ジャンプ・整形 | なし |
| deno/node/src/main.ts | 補完・診断・定義ジャンプ・整形 | vtslsとdenolsが両方接続。vtslsのみという期待と異なる |
| plain/deno/src/main.ts | denolsのみ接続、補完・診断・整形 | 定義ジャンプは「OK 未確認」とあり、結果を確定しない |
| biome space/src/main.ts | vtslsのパス、接続・補完・診断・整形。別cwdからも確認 | Biome LSPの接続成功は確認できない。定義ジャンプは「OK 未確認」 |

報告されたcssls・html・jsonls・yamlls・taplo・marksman・vtsls・denoのパスは、いずれもmise管理下だった。Biome側の整形成功だけでは、Biome LSPの起動成功やConformが選んだformatterを確定できない。

Biomeフォルダをcwdにした際、相対コマンド`{ "node_modules/.bin/biome", "lsp-proxy" }`の起動に失敗したというログがあった。読み取りのみで展開済み設定とソースを比較し、次の事実を確認した。

- `~/.config/nvim/after/lsp/biome.lua`は相対コマンドを指定する旧設定で、ソースのcmd関数と異なる。
- 展開済みdenols.luaは、Nodeのlockfileを境界にしない旧root判定だった。
- vtsls.luaとconform.luaにもソースとの差分があり、新しい`lua/config/web-project.lua`は展開先になかった。
- 確認用プロジェクト内のBiomeリンク先には実行権限があり、Node用package-lock.jsonも存在した。

今回の修正が展開先へ未反映であることは確認済み。二重接続は旧root判定と整合し、Biomeログのcmdも旧設定と一致する。ただし、失敗時のプロセス内設定を取得したわけではなく、修正後の実環境で両症状が解消することは未確認とする。追加のソース修正は行わず、設定適用後に新しいNeovimプロセスで再確認する。

### 次に行う再確認

1. 利用者が今回のソースをchezmoiで適用し、Neovimを終了してからMason無効化モードで起動し直す。今回Codexは適用操作を行っていない。
2. `deno/node/src/main.ts`でvtslsだけが接続し、denolsが接続しないことを確認する。
3. Biomeフォルダをcwdにした場合と別cwdの場合を試し、`:LspInfo`でBiomeの接続とrootを確認する。
4. `:ConformInfo`でbiome-checkが選ばれることを確認し、整形を試す。
5. 結果ファイルに再確認日と結果を追記する。「OK 未確認」の箇所とcsslsの接続確認も、確認できた範囲を記録する。

NV-03とMasonの完全削除は引き続き保留する。

## 設定適用後の再確認結果（2026-11-15）

利用者がchezmoi apply後、次の結果を報告した。Codexによる再実行ではない。

| 対象 | 利用者の結果 | 判定 |
| --- | --- | --- |
| deno/node/src/main.ts | vtslsだけが接続 | 二重接続の解消を確認 |
| Biome LSP | Biomeフォルダ内・別cwdの両方で接続 | 起動失敗の解消を確認 |
| ConformInfo | 初回報告ではbiome-checkとprettierdの両方が表示。続報ではbiome・biome-checkがそれぞれ先頭に表示 | 表示だけでは実行対象を確定しない |
| list_formatters_to_run(0) | `{ "biome-check" }`を出力 | 実行予定がbiome-checkのみであることを利用者が確認 |

Conformの設定は`{ "biome-check", "prettierd", stop_after_first = true }`。biome-checkが利用可能ならそれだけを実行し、利用できなければprettierdを選ぶ。biome-checkの実行が失敗した場合にprettierdで再試行する設定ではない。以前の手順では候補表示と実行対象の違いが不明確だったため、説明を補足した。

実行予定のformatter名だけを確認するには、対象バッファで次を使う。整形処理やファイルへの書き込みは行わない。

```vim
:lua local fs = require("conform").list_formatters_to_run(0); print(vim.inspect(vim.tbl_map(function(f) return f.name end, fs)))
```

利用者が上記コマンドを実行し、期待値の`{ "biome-check" }`が出力されたことを確認した。Conformの実行予定がbiome-checkのみであることを通常UIでも確認済みとする。このコマンドは整形を実行しないため、設定適用後の保存時実行ログまで確認済みとは扱わない。実ConformによるBiome整形は、上記の隔離検証で成功している。

今回のDeno・Nodeの接続分岐とBiome LSPの起動修正は、利用者の環境で確認済み。NV-03全体は追加サーバーの用途・未確認機能・環境別の整理が残るため対応を継続し、Masonの完全削除はまだ行わない。

追加サーバーについては、その後[Emmet・Tailwind・Oxlint・golangci-lint・sqlsの確認](neovim-extra-lsp-validation.md)を実施した。Emmetの補完と2つのlinterの診断・解消が成功し、Tailwindの依存不足とsqlsのDB機能は残件として記録した。
