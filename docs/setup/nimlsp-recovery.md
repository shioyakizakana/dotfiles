# Nim更新後のNimLSPを再ビルド・復旧する

NimLSPはビルド時のNimと実行時のNimを一致させる。導入済みのnimlspがあっても、Nim更新後に同じバイナリを使えるとは限らない。[NimLSP公式のビルド説明](https://github.com/PMunch/nimlsp#compile-nimlsp)では、Nimのコンパイラ・nimsuggestのソースが必要とされている。

## 版を確認する

```shell
nim --version
nimlsp --version
```

後者のbuilt for Nim versionと前者の版を比較する。通常導入スクリプトは、導入済みの場合と新規導入後の両方で確認する。版不一致、実行ファイルの欠落、版取得の失敗、解析できない出力は非0で終了し、正常導入として扱わない。既存バイナリを自動削除・再導入する処理は加えていない。

## 既存ソースだけで一時ビルドする

以下は今回確認したNim 2.4.2・NimLSP 0.4.7の構成に対応する手順。実行は利用者が選択して行う。外部取得や実HOMEへの導入は行わず、既存の公開パッケージから/tmpにビルドする。Nimbleが配置したソースを、ビルド時に必要なsrc/構造へ戻す。

複数版のパッケージがある場合は停止する。対象版を確認してパスを選び直す。Nimの配置やNIMBLE_DIRを変更した環境では、先に以下のパスを実環境へ合わせる。

```python
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

nim_root = Path.home() / ".local/share/mise/installs/nim/2.4.2"
packages = Path.home() / ".nimble/pkgs2"

def one(pattern):
    matches = list(packages.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"対象パッケージを選んでください: {pattern}")
    return matches[0]

package = one("nimlsp-0.4.7-*")
dependencies = [one(name + "-*") for name in
                ("asynctools", "jsonschema", "ast_pattern_matching")]
compiler = nim_root / "bin/nim"
if not compiler.is_file():
    raise RuntimeError("Nim 2.4.2の実コンパイラが見つかりません")

work = Path(tempfile.mkdtemp(prefix="nimlsp-rebuild-", dir="/tmp"))
print("ビルド先:", work, flush=True)
source = work / "source"
src = source / "src"
src.mkdir(parents=True)
(work / "home").mkdir()
shutil.copy2(package / "nimlsp.nimble", source / "nimlsp.nimble")
for name in ("nimlsp.nim", "nimlsp.nim.cfg"):
    shutil.copy2(package / name, src / name)
shutil.copytree(package / "nimlsppkg", src / "nimlsppkg")

env = {"HOME": str(work / "home"),
       "PATH": str(nim_root / "bin") + ":" + os.defpath,
       "LANG": "C.UTF-8"}
command = [str(compiler), "c", "--skipUserCfg:on", "--skipParentCfg:on",
           "--hints:off", f"--nimcache:{work}/cache",
           f"--out:{work}/nimlsp", f"--path:{nim_root}"]
command += ["--path:" + str(path) for path in dependencies]
subprocess.run(command + [str(src / "nimlsp.nim")],
               cwd=source, env=env, check=True)
subprocess.run([str(work / "nimlsp"), "--version"], env=env, check=True)
```

生成したnimlspの版を確認し、[確認用プロジェクト](../testing/neovim-nim-rust.md)で診断・修正後の解消・定義ジャンプを検証してから切り替える。コンパイル成功だけで正常動作と判断しない。この手順は依存の更新や別版のNimへの互換性を保証するものではない。

## 今回の切り替えと復元

2026-11-14、利用者の承認後、既存バイナリを次へ退避した。manifest.jsonには切替先、変更前後の版とSHA256を記録している。

```text
/home/shioyaki/.local/state/dotfiles/nimlsp-backups/20261114T082944Z/
  nimlsp
  manifest.json
```

~/.nimble/bin/nimlspのシンボリックリンクを保持し、リンク先のNimLSP 0.4.7だけをNim 2.4.2向けバイナリへ切り替えた。パッケージの追加取得、NimLSPの版更新、nimlsp_debugの置き換えは行っていない。

旧バイナリへ戻す場合は、Neovimを終了してから次を実行する。復元するとNim 2.4.2との版不一致も戻るため、通常の解決手順としては使わない。この復元コマンドは今回実行していない。

```shell
install -m 755 \
  "$HOME/.local/state/dotfiles/nimlsp-backups/20261114T082944Z/nimlsp" \
  "$HOME/.nimble/pkgs2/nimlsp-0.4.7-c38e7fa0bb4b8f15cc6c9320afd0e0eaa18a3fe2/nimlsp"
```

切り替え前から動いているLSPプロセスは古いバイナリを使用する。Neovimを再起動し、Mason無効化モードで版警告が出ないことと、診断の検出・解消を再確認する。

## 検証範囲と残件

切替前の一時バイナリと切替後の実環境のnimlspを、それぞれ隔離HOME・専用プロジェクトで起動した。型エラー2件の検出、修正後の診断0件、greetings.nimへの定義ジャンプ、版不一致警告なしを確認した。利用者の編集済み確認用ファイルは変更していない。その後、利用者がPATHを明示した起動で通常UIの保存時診断5件、フロート表示、修正・保存後の診断解消を確認した。その後、補助探索と共通PATH設定の反映を経て、利用者がPATHを明示しない通常起動でも接続・ハイライト・保存時の診断5件・フロート表示・修正後の診断解消を確認した。今回の復旧確認は完了。

ハイライトは別件。隔離したNeovim v0.12.6ではNimのfiletype判定はできたが、標準のsyntax/nimファイルはなかった。当初のTree-sitter導入一覧にはNimがなかった。その後、承認された対応としてnimを追加し、nim_format_stringを含む隔離ビルドとハイライト検証が成功した。実環境への適用・通常UIでの表示は[確認手順](../testing/neovim-nim-rust.md#pathの補助探索とハイライトの適用)に従う。

関連する導入処理のunittestは33件、make check全体はunittest 225件・Bats 18件が成功し、skipなし。Bash構文・ShellCheck・shfmtと差分の確認も成功した。新しい版一致判定は、切替後の実ツールでも成功した。
