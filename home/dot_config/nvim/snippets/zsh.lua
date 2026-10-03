local ls = require("luasnip")
local s = ls.snippet
local i = ls.insert_node
local fmt = require("luasnip.extras.fmt").fmt
return {
  s(
    "zsnb",
    fmt(
      [[
        #!usr/bin/env zsh{}
      ]],
      { i(1) }
    )
  ),
  s(
    "zheader",
    fmt(
      [[
        #!usr/bin/env zsh

        set -euo pipefile

        {}
      ]],
      { i(1) }
    )
  ),
  s(
    "zarr",
    fmt(
      [[
        local {}=(
          {}
        )
      ]],
      { i(1, "array"), i(2, "item") }
    )
  ),
}
