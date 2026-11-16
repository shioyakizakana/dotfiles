# uvの新しいPythonと既存debugpyの検証

2026-11-15、既存のdebugpyからuv管理の新しいPythonをデバッグする構成を確認した。初回の隔離検証でアダプター終了時の警告を観測した。その後、2026-11-16の通常UI確認では全項目が成功し、終了警告もなかった。過去の警告の原因と恒久的な解消は未確認として残す。

## 構成と導入範囲

| 対象 | 使用したもの |
| --- | --- |
| 環境 | 現在のLinux aarch64・proot環境、Neovim v0.12.6 |
| uv | 導入済み0.13.8 |
| デバッグアダプター | 既存のmise管理debugpy 1.8.22、Python 3.13.18 |
| 対象Python | uvで追加したCPython 3.14.10、GILありの通常版 |
| 対象プロジェクト | /tmp/neovim-uv-dap-check-4bkcrl_r/uv project |
| Python指定 | .python-versionに3.14.10、requires-pythonは3.14以上3.15未満 |
| 依存 | pyproject.tomlのdependenciesは空、uv.lockを作成 |

承認されたPythonだけをuv管理領域へ追加し、--no-binでグローバルなPython実行コマンドは追加・変更していない。既存mise Python、debugpy、実プロジェクト、展開済み設定は変更していない。今回の版は跨版検証の対象であり、すべてのプロジェクトへ推奨する最新版を選定したものではない。

導入・同期には専用HOME・キャッシュを使い、実際の認証設定を読み込んでいない。Python追加後の検証は追加ダウンロードを無効にした。.venvへdebugpyは導入しておらず、検証後も通常起動でdebugpyが見つからないことを確認した。デバッグ実行中は既存アダプター側のパッケージを利用する。

## 実体とロックの確認

uv python findのmanaged指定で選ばれる実行ファイルと、.venv/bin/python、sys._base_executableが同じファイルであることを確認した。sys.base_prefixもuvの対象インストール先と同じディレクトリだった。uv lock --check --offlineも成功した。

prootではsys.base_prefixが/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/から始まるホスト側のパスで表示された。単純な前方一致は使わず、同一ファイル・ディレクトリかをstatに基づいて確認した。詳細は確認用フォルダのtarget-python.jsonに記録した。

## only-managedの比較結果

最初はpython-preferenceをonly-managedにした。しかしuvは既存.venvをその条件に合わないと判断した。

| 条件 | 結果 |
| --- | --- |
| 通常の管理領域パス、only-managed、uv run --no-sync | 不整合の警告あり。デバッグ操作は成功 |
| 同じ管理領域をホスト側の同一実体のパスで指定 | 警告なし |
| 通常の管理領域パス、only-managed、同期するuv run | .venvを削除・再作成して実行 |
| 検証プロジェクトをmanagedへ変更 | 通常のuv runを2回実行し、警告・.venv再作成なし。対象版・実体も維持 |

比較はこの一時プロジェクトだけで行った。以前のonly-managedの提案は、このproot環境でそのまま使うことを推奨しない。uvのパス表現に関わる判定と整合するが、他環境や他バージョンでも同じ不具合があるとは扱わない。

現在の確認用プロジェクトはuv既定のmanagedを明記し、uvによる明示導入、版固定、実体確認を組み合わせている。グローバルなuv設定は変更していない。Python本体がuv管理であることと、uvが既存venvをonly-managedに適合すると判断することを区別する。

## 実デバッグの結果

Neovimの通常設定を読み込まず、既存DAP設定と実プラグインを隔離HOMEで起動した。通常の起動とuv run経由の両方で、以下が成功した。

- 現在のDAP設定がプロジェクトの.venv/bin/pythonを選択。
- greet呼び出しのブレークポイントに停止。
- ステップイン・オーバー・アウトで停止位置を確認。
- messageの値がHello, Codexであることを取得。
- デバッグ中のPython版が3.14.10であることを取得。
- 続行後、対象Pythonが終了コード0で終了。

ただしアダプター自身の終了は、初期の2実行ではコード0、最後の通常同期を伴うuv runではコード1だった。stderrにはSessionの終了処理の例外があり、対象Pythonの終了コード0とは分けて記録する。警告を非表示にしたり、成功扱いへ置き換えたりする修正は行っていない。終了順序等の追加調査は残件。

最終ログはfinal-uv-run-dap-result.logとfinal-uv-run-home/state/nvim/配下。uvの比較はuv-preference-comparison.json・managed-normal-uv-run.jsonにある。一時領域なので永続保存は保証しない。

## 通常UIの手動確認

NV-04の設定は適用済みのため、今回の検証のための設定再適用は不要。次で用意したプロジェクトを開く。

```sh
cd '/tmp/neovim-uv-dap-check-4bkcrl_r/uv project'
uv run --frozen --offline nvim main.py
```

1. :Lazy load nvim-dap-viewで設定を読み込む。
2. 下記のコマンドで、対象がこのプロジェクトの.venv、アダプターが既存mise管理のdebugpyであることを記録する。
3. greet呼び出し行でブレークポイントを設定し、F5で開始する。F11で関数へ入り、F10でmessageの代入を実行する。
4. UIでmessageを確認する。leader + drのREPLで、下記の式により対象Pythonが3.14.10であることも確認する。
5. F12で呼び出し元へ戻り、F5で続行する。対象の処理完了と、アダプター終了時の警告の有無を別々に記録する。

```vim
:lua print(require("dap").configurations.python[1].pythonPath())
:lua print(vim.fn.exepath("debugpy-adapter"))
```

REPLで確認する式は次のとおり。

```python
__import__("platform").python_version()
```

結果記入欄は/tmp/neovim-uv-dap-check-4bkcrl_r/RESULTS.md。警告が出た場合は:DapShowLogと:messagesの今回の操作に対応する内容を記録する。依存の再インストールや既存Pythonの削除は行わない。キー操作の代替コマンドは[DAP手順](../setup/neovim-dap.md)を参照する。

## 今回変更しなかったもの

DAP・miseの設定コード、既存のプロジェクト、既存Python、debugpyの版や専用環境は維持した。全体のmake checkは前回のunittest 269件・Bats 18件成功を再利用し、今回はuvとDAPの実検証、文書確認を行った。chezmoi適用・commit・pushは未実施。新しいPython全般への互換性や終了警告の解消まで確認済みとは扱わない。

## 通常UIの確認結果（2026-11-16）

利用者が/tmp/neovim-uv-dap-check-4bkcrl_r/RESULTS.mdに記入した結果を確認した。環境はTermux + proot Ubuntu、Neovim v0.12.6。以下は利用者の報告であり、Codexによるデバッグ操作の再実行ではない。

| 項目 | 利用者の結果 |
| --- | --- |
| uv runの起動警告 | なし |
| 不要な.venv再作成 | なし |
| 対象Python | 確認用プロジェクトの.venv/bin/python |
| アダプター | mise管理のpipx-debugpy/latest/bin/debugpy-adapter |
| ブレークポイント停止 | 成功 |
| F11・F10・F12 | すべて成功 |
| messageの表示 | Hello, Codex |
| REPLでのPython版 | 3.14.10 |
| 続行・対象の処理完了 | 成功 |
| アダプター終了警告 | なし |

読み取り確認では、報告されたlatestパスはdebugpy 1.8.22の実体を指していた。uv管理の新しいPythonと既存アダプターを分離した構成は、確認済み環境・用途で通常UIまで成功したと記録する。過去の隔離実行で出たアダプター終了コード1の原因を特定したわけではなく、恒久的な解消や他環境での非発生を保証しない。再発時は対象の終了状態とアダプターの警告を分けて記録する。

今回の更新は文書のみ。既存のステージ内容と、別作業のtmux変更はそのまま保持し、設定コード・依存・実環境には変更を加えていない。全体テストは再実行せず、文章と差分を確認した。commit・pushは未実施。
