#!/usr/bin/env bash
set -Eeuo pipefail

readonly NIM_COMMIT=b27dcb4f70883978e984e427cc24b64eeb7c875f
readonly NIMLSP_VERSION=0.4.7
readonly NIMLSP_COMMIT=20205a927b8485d169e78a176e9d534e3a2436d0

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

nim_info="$("$PREFIX/bin/nim" --version)"
[[ "$nim_info" == *'[Android:'* ]] || die "TermuxのNimが必要です"
nim_version="$(awk 'NR == 1 { print $4 }' <<<"$nim_info")"
expected="nimlsp v$NIMLSP_VERSION - built for Nim version $nim_version"
if command -v nimlsp >/dev/null; then
  [[ "$(nimlsp --version)" == *" - built for Nim version $nim_version" ]] ||
    die "既存のnimlspとNimの版が一致しません。ビルド済みのnimlspを確認してください"
  exit 0
fi
[[ "$nim_info" == *"git hash: $NIM_COMMIT"* ]] ||
  die "このNimの版に対応するNimLSPのビルド手順がありません"

target="$HOME/.local/bin/nimlsp"
[[ ! -e "$target" && ! -L "$target" ]] || die "既存のnimlspがあるため配置を中止しました"
work="$(mktemp -d "$HOME/.local/bin/.termux-nimlsp-XXXXXXXX")"
trap 'command rm -rf -- "$work"' EXIT
fetch_source() {
  local repo="$1" revision="$2" destination="$3"
  mkdir -p -- "$destination"
  curl -fsSL --retry 3 "https://codeload.github.com/$repo/tar.gz/$revision" -o "$work/source.tar.gz" ||
    die "$repo のソースを取得できません"
  tar -xzf "$work/source.tar.gz" --strip-components=1 -C "$destination"
}

fetch_source nim-lang/Nim "$NIM_COMMIT" "$work/nim"
# Nimのkoch.nimが指定する依存コミットを使う。
fetch_source nim-lang/checksums 5c132cd332cce5d64a0da9ac3e4c9664313dccb4 "$work/nim/dist/checksums"
fetch_source nim-lang/nimony 668edddcaa5651051e7683a38a04f31fba778f35 "$work/nim/dist/nimony"
fetch_source PMunch/nimlsp "$NIMLSP_COMMIT" "$work/nimlsp-src"
fetch_source PMunch/jsonschema 7b41c03e3e1a487d5a8f6b940ca8e764dc2cbabf "$work/jsonschema"
fetch_source nim-lang/ast-pattern-matching eb8b99d595517fd5d41ccc954edb896267f2db78 "$work/ast-pattern-matching"

# Androidではasynctoolsが必要とするaddProcessがなく、既存の同期I/O経路を使う。
sed -i \
  -e 's/^import asynctools\/asyncproc$/when not defined(android):\n  import asynctools\/asyncproc/' \
  -e 's/when outs is AsyncFile: await asyncproc/when outs is AsyncFile and not defined(android): await asyncproc/' \
  -e 's/^when defined(windows):$/when defined(windows) or defined(android):/' \
  "$work/nimlsp-src/src/nimlsp.nim"
# 実行時はTermuxの標準ライブラリを参照し、ビルド時だけ取得したソースを使う。
sed -i 's/switch "path", explicitSourcePath/if not defined(android): switch "path", explicitSourcePath/' \
  "$work/nimlsp-src/src/config.nims"

"$PREFIX/bin/nim" c -d:release "--nimcache:$work/cache" "--out:$work/nimlsp" \
  "-d:explicitSourcePath=$PREFIX/lib/nim" "--path:$work/nim" \
  "--path:$work/jsonschema/src" "--path:$work/ast-pattern-matching/src" "$work/nimlsp-src/src/nimlsp.nim"
[[ "$("$work/nimlsp" --version)" == "$expected" ]] || die "ビルドしたnimlspの版が一致しません"

chmod 0755 "$work/nimlsp"
mv -nT -- "$work/nimlsp" "$target"
[[ ! -e "$work/nimlsp" ]] || die "既存のnimlspがあるため配置を中止しました"
