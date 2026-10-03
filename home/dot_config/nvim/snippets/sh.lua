local ls = require("luasnip")
local s = ls.snippet
local i = ls.insert_node
local fmt = require("luasnip.extras.fmt").fmt
return {
  s(
    "pipe",
    fmt(
      [[
        {} | {}
      ]],
      { i(1), i(2) }
    )
  ),
  s(
    "h2",
    fmt(
      [[
        # ===========================================================
        # {}
        # ===========================================================
      ]],
      { i(1, "header") }
    )
  ),
  s(
    "h3",
    fmt(
      [=[
        # -----------------------------------------------------------
        # {}
        # -----------------------------------------------------------
      ]=],
      { i(1, "header") }
    )
  ),
  s(
    "h4",
    fmt(
      [=[
        # {}---------------------------------------------------------
      ]=],
      { i(1, "header") }
    )
  ),
  s(
    "if",
    fmt(
      [=[
        if [ {} ]; then
          {}
        fi
      ]=],
      { i(1, "condititon"), i(2, "process") }
    )
  ),
  s(
    "ifelse",
    fmt(
      [=[
        if [ {} ]; then
          {}
        else
          {} 
        fi
      ]=],
      { i(1, "condititon1"), i(2, "process1"), i(3, "other process") }
    )
  ),
  s(
    "for",
    fmt(
      [[
        for ${iter} in ${items}; do
          {process}
        done
      ]],
      {
        iter = i(1, "iter"),
        items = i(2, "items"),
        process = i(3, "process")
      }
    )
  ),
  s(
    "forin",
    fmt(
      [[
        for $<iter> in "${$<collection>[@]}";do
          <process>
        done
      ]],
      {
        iter = i(1, "iter"),
        collection = i(2, "collection"),
        process = i(3, "process")
      },
      { delimiters = "<>" }
    )
  ),
  s(
    "forfile",
    fmt(
      [[
        for <iter> in "$<files>"/*; do
          <process>
        done
      ]],
      {
        iter = i(1, "iter"),
        files = i(2, "files"),
        process = i(3, "process")
      },
      { delimiters = "<>"}
    )
  ),
  s(
    "case",
    fmt(
      [[
        case {} in
          {}
            {}
            ;;
          *)
            {}
            ;;
        esac
      ]],
      {
        i(1, "condition1"),
        i(2, "process1"),
        i(3, "other condition"),
        i(4, "other process")
      }
    )
  ),
  s(
    "options",
    fmt(
      [[
        case "{arg}" in
        -h|--help)
          {help}
        -v|--verbose)
          {verbose}
        ;;
        *)
          {command}
        ;;
        esac
      ]],
      {
        arg = i(1, "arg"),
        help = i(2, "help"),
        verbose = i(3, "verbose"),
        command = i(4, "command")
      }
    )
  ),
  s(
    "function",
    fmt(
      [[
        function <>() {
          <>
        }
      ]],
      { i(1, "name"), i(2, "process") },
      { delimiters = "<>" }
    )
  ),
  s(
    "main",
    fmt(
      [[
        main() {
          <>
        }

        main "$@"
      ]],
      { i(1, "process") },
      { delimiters = "<>" }
    )
  ),
  s(
    "ro",
    fmt(
      [[
        readonly {var}={value}
      ]],
      { var = i(1, "var"), value = i(2, "value") }
    )
  ),
  s(
    "null",
    fmt(
      [[
        {} >/dev/null 2>&1
      ]],
      { i(1, "command") }
    )
  ),
  s(
    "nohas",
    fmt(
      [[
        if ! command -v {} >/dev/null 2>&1; then
          {}
        fi
      ]],
      { i(1, "command"), i(2, "process") }
    )
  ),
  s(
    "seteuop",
    fmt(
      [[
        set -euo pipefile{}
      ]],
      { i(1) }
    )
  ),
  s(
    "shebang",
    fmt(
      [[
        #!/bin/sh{}
      ]],
      { i(1) }
    )
  ),
  s(
    "bashebang",
    fmt(
      [[
        #!/usr/bin/env bash{}
      ]],
      { i(1) }
    )
  ),
  s(
    "basheader",
    fmt(
      [[
        #!/usr/bin/env bash

        set -euo pipefile

        {}
      ]],
      { i(1) }
    )
  ),
  s(
    "readrp",
    fmt(
      [[
        read -rp "{} [y/N]: " confirm
      ]],
      { i(1, "message") }
    )
  ),
  s(
    "log",
    fmt(
      [[
        log() {{
          printf "\n==> %s\n" "$*"
        }}
        {}
      ]],
      { i(1) }
    )
  ),
}
