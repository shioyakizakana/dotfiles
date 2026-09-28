local formatter_list = {
    "djlint",
    "black",
    "isort",
    "stylua",
    "prettier",
}

local diagnostics_list = {
    "yamllint",
}

return {
  -- Masonとnone-ls.nvimとの連携用プラグイン
  -- Masonでインストールしたフォーマッターやリンターをnone-ls.nvimで使えるようにする
  {
    "jay-babu/mason-null-ls.nvim",
    dependencies = {
      "mason-org/mason.nvim",
      "nvimtools/none-ls.nvim",
    },
    config = function()
      require("mason-null-ls").setup({
      automatic_setup = true,
        ensure_installed = vim.iter({ formatter_list, diagnostics_list })
          :flatten()
          :totable(),
        handlers = {}
      })
    end,
    cmd = "Mason",
  },


  -- LSP以外のフォーマッターやリンターをLSPとして使用できるようにする
  {
    "nvimtools/none-ls.nvim",
    requires = "nvim-lua/prenary.nvim",
    config = function()
      local null_ls = require("null-ls")

      -- formatter table
      local foramtting_source = {}
      for _, tool in ipairs(formatter_list) do
        table.insert(foramtting_source, null_ls.builtins.formatting[tool])
      end
      -- diagnostics table
      local diagnostics_sources = {}
      for _, tool in ipairs(diagnostics_list) do
        table.insert(diagnostics_sources, null_ls.builtins.diagnostics[tool])
      end

      -- none-ls setup
      null_ls.setup({
        diagnostics_format = "[#{m}] #{s} (#{c})",
        sources = vim.iter({ foramtting_source, diagnostics_sources })
          :flatten()
          :totable(),
        })
    end,
    event = { "BufReadpre", "BufNewFile" },
    },
}
