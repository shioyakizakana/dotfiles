local ls = require("luasnip")
local s = ls.snippet
local i = ls.insert_node
local fmt = require("luasnip.extras.fmt").fmt
return {
  s(
    "ifbash",
    fmt(
      [=[
        if [[ {} ]]; then
        {}
        fi
      ]=],
      { i(1, "condition"), i(2, "process") }
    )
  ),
  s(
    "arr",
    fmt(
      [[
        {}=(
          {}
        )
      ]],
      { i(1, "array"), i(2, "item") }
    )
  ),
  s(
    "forarr",
    fmt(
      [=[
        for ((i=0; i<<${{#{array}[@]}}; i++)); do
          {process}
        done
      ]=],
      {
        array = i(1, "array"),
        process = i(2, "process")
      }
    )
  ),
}
