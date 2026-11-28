# Tailwindの依存と起動確認

2026-11-15、NV-03のTailwind接続NG報告を受け、Linux aarch64・Neovim v0.12.6で調査した。依存を導入した確認用プロジェクトで、隔離検証と利用者による通常UIの再確認が成功した。

## 確認した事実

- tailwindcss-language-server 0.16.0とNode 24の実行ファイルは存在し、実行権限があった。
- LSP登録のソースと展開先は一致し、独自のafter/lsp/tailwindcss.luaはなかった。nvim-lspconfigの設定を継承する構成だった。
- 元の確認用フォルダにはtailwind.config.jsがあったが、package.jsonとnode_modules/tailwindcssはなかった。
- 元のフォルダでも、隔離HOMEで自動root選択を使う起動では接続・補完・診断が成功した。利用者が報告した通常UIの接続NGは再現できていない。
- 本体依存なしでも補完や競合診断が得られる場合があったが、ログにはtailwindcss/package.jsonの解決失敗が残った。これをプロジェクト依存の解決成功とは扱わない。

接続NGの直接原因は未確定で、依存不足だけで未接続になるとは判断しない。今回、dotfilesのLSP設定を追加修正する根拠は得られなかった。

## 検証用依存と結果

検証用フォルダは`/tmp/neovim-tailwind-check-jdfuyvgs`。既存の手動確認ファイルは変更せず、別の最小プロジェクトを作成した。

実行承認を受け、このフォルダに限って開発依存のtailwindcss 3.4.17と関連依存を導入した。既存のv3形式の設定で確認するための固定版であり、dotfiles全体や実プロジェクトの推奨版を決めたものではない。miseの定義とグローバル環境は変更していない。v4のCSSエントリ形式は未検証。

導入には隔離HOME・専用npm設定とキャッシュ・npm公式レジストリを使い、インストールスクリプト・audit・fundを無効にした。実際の認証設定は読み込んでいない。package.jsonとpackage-lock.jsonは確認用フォルダ内にある。

| 項目 | 導入後の結果 |
| --- | --- |
| 依存解決 | 確認用node_modules/tailwindcss/package.jsonを解決し、3.4.17と確認 |
| 自動接続 | root_dirを直接指定せず、確認用フォルダをrootに接続 |
| 標準クラス補完 | flex候補を取得 |
| プロジェクト設定 | tailwind.config.cjsの独自色に対応するbg-dotfilesproof候補を取得 |
| 診断 | flexとblockのcssConflict診断2件を取得 |
| 修正後 | blockを除去したバッファで診断0件を確認 |
| 起動ログ | tailwindcss/package.jsonの解決失敗なし |

診断・補完の確認は隔離NeovimのLSP要求で行い、修正後の確認はバッファ内だけで実施した。手動確認用のsrc/index.htmlには、競合するflexとblockを残している。検証スクリプトはprobe.luaとinstalled-probe.lua、結果はoriginal-result.log・minimal-result.log・installed-result.logに記録した。

## 利用者による通常起動の再確認

現行ソースはMason依存と移行用切替を除去済みなので、通常起動する。以下の一時フォルダが消失している場合は、本文の条件に合わせて検証用プロジェクトを用意し直す。

```sh
cd /tmp/neovim-tailwind-check-jdfuyvgs
nvim src/index.html
```

1. `:set filetype?`がhtmlで、`:LspInfo`にtailwindcssが接続していることを確認する。rootは上記フォルダ、実行ファイルはmise管理のtailwindcss-language-serverを期待する。
2. クラス名の途中で補完を開き、flexとbg-dotfilesproofを確認する。後者は検証用設定の独自色である。
3. 保存してflexとblockの競合診断を確認する。blockだけを除去して保存し、競合診断が解消することを確認する。
4. 確認用フォルダのRESULTS.mdへ結果を記入する。

接続しない場合は、設定変更や再インストールを行う前に次を記録する。

```vim
:lua print(vim.fn.executable("tailwindcss-language-server"), vim.fn.exepath("tailwindcss-language-server"))
:lua print(vim.fn.executable("node"), vim.fn.exepath("node"))
:lua print(vim.lsp.is_enabled("tailwindcss"))
:lua print(vim.lsp.log.get_filename())
```

実行可否は両方1、有効化状態はtrueを期待する。ログには今回の起動時刻付近のエラーがあるか確認する。必要ならそのセッションだけ`:lua vim.lsp.log.set_level("debug")`で詳細ログを有効にし、ファイルを開き直す。

## 残件

Tailwindのプロジェクト依存を解決した隔離機能確認と、下記の通常UI確認は完了。以前の接続NGの直接原因は特定していないが、依存を導入した検証用構成では接続と各機能が成功した。設定コードは変更していないので全体テストは再実行せず、文書の文章と差分を確認する。設定適用・Mason削除・DB接続・commit・pushは今回行っていない。

## 通常UIの手動確認結果（2026-11-15）

利用者が`/tmp/neovim-tailwind-check-jdfuyvgs/RESULTS.md`へ記入した結果を確認した。環境はTermux + proot Ubuntu、Neovim v0.12.6。Mason無効化モードでの報告であり、Codexによる再実行結果ではない。

| 確認項目 | 利用者の結果 |
| --- | --- |
| tailwindcss接続 | 成功 |
| root | /tmp/neovim-tailwind-check-jdfuyvgs |
| 実行パス | /home/shioyaki/.local/share/mise/installs/npm-tailwindcss-language-server/latest/node_modules/.bin/tailwindcss-language-server |
| flex補完 | 成功 |
| bg-dotfilesproof補完 | 成功 |
| flex/blockの競合診断 | 成功 |
| block除去・保存後の診断解消 | 成功 |

検証用v3構成の通常UI確認は完了とする。v4や他の実プロジェクト・環境での結果には一般化しない。NV-03ではsqlsのDB機能を未検証として記録し、Mason削除の対象と検証範囲を決める段階へ進む。今回の報告を受けた設定コードの追加修正は行っていない。
