---@module "blink.cmp"
---@type blink.cmp.KeymapConfig
return {
  preset = "super-tab",
  ["<Space>"] = {} ,
  ['<C-h>'] = { 'show', 'show_documentation', 'hide_documentation' },
  ["<C-p>"] = { "scroll_documentation_up", "fallback" },
  ["<C-n>"] = { "scroll_documentation_down", "fallback" },
  ["<C-b>"] = {},
  ["<C-f>"] = {},
  ["<Enter>"] = { "accept_and_enter", "fallback" },
  -- よく使うスニペットを展開
  ["<C-y>"] = {
    function(cmp)
      if require("luasnip").expandable() then
        cmp.hide()
        vim.schedule(function()
          require("luasnip").expand()
        end)
        return true
      end
      return false
    end,
    "fallback",
  },
  -- 先頭の大文字小文字を切り替えて補完
  ["<C-v>"] = {
    function(cmp)
      cmp.accept({
        vim.api.nvim_feedkeys(
          vim.api.nvim_replace_termcodes("<Esc>mzBvg~`za", true, false, true),
          "in",
          false
        )
      })
    end,
  },
  -- 連続した単語を入力する場合に接頭された方の単語にのみ補完をきかせたい場合
  -- 直前に入れた空白を削除する
  ["<C-g>"] = {
    function()
      vim.api.nvim_feedkeys(
        vim.api.nvim_replace_termcodes("<Esc>mzBvg~`za", true, false, true),
        "in",
        false
      )
    end,
  },
}
