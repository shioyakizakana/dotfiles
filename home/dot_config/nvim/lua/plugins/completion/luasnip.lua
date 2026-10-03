---@module "lazy"
---@type LazyPluginSpec
return {
  "L3MON4D3/LuaSnip",                                -- スニペットエンジン
  version = "v2.*",
  dependencies = { "rafamadriz/friendly-snippets" }, -- スニペット集
  build = "make install_jsregexp",

  config = function()
    -- ---@type LuaSnip.Loaders.LoadOpts
    -- require("luasnip.loaders.from_snipmate").lazy_load()

    ---@type LuaSnip.Loaders.LoadOpts
    require("luasnip.loaders.from_vscode").load({
      override_priority = 1000,
    })

    ---@type LuaSnip.Loaders.LoadOpts
    require("luasnip.loaders.from_lua").load({
      paths = { vim.fn.stdpath("config") .. "/snippets" },
      override_priority = 2000,
    })

    -- ファイルタイプ別に読み込むスニペットを追加
    require("luasnip").filetype_extend("bash", { "sh" })
    require("luasnip").filetype_extend("zsh", { "sh" })

    -- コマンドでスニペットファイルを編集できるようにする
    vim.api.nvim_create_user_command(
      "LuaSnipEdit",
      ":lua require('luasnip.loaders').edit_snippet_files()",
      {}
    )
  end,
}

