return {
  -- LSP以外のフォーマッターやリンターをLSPとして使用できるようにする
  {
    "nvimtools/none-ls.nvim",
    dependencies = {
      "nvim-lua/prenary.nvim",
      "gbprod/none-ls-shellcheck.nvim",
    },
    event = { "BufReadpre", "BufNewFile" },
    config = function()
      local null_ls = require("null-ls")

      null_ls.register(require("none-ls-shellckeck").diagnostics)
      null_ls.register(require("none-ls-shellcheck.code_actions"))

      -- formatter table
      local formatting_sources = {}
      vim.list_extend(formatting_sources {
        null_ls.builtins.formatting.gofumpt,
        null_ls.builtins.formatting.shfmt,
        null_ls.builtins.formatting.stylua,
        null_ls.builtins.formatting.prettierd,
        null_ls.builtins.formatting.ruff_format,
      })
      -- diagnostics table
      local diagnostics_sources = {}
      vim.list_extend(diagnostics_sources, {
        null_ls.builtins.diagnostics.golangci_lint,
        null_ls.builtins.diagnostics.shellcheck,
        null_ls.builtins.diagnostics.ruff,
      })

      local sources = vim.iter({
        formatting_sources,
        diagnostics_sources
      }):flatten():totable()

      -- none-ls setup
      null_ls.setup({
        diagnostics_format = "[#{m}] #{s} (#{c})",
        sources = sources,
      })
    end,
  },
}
