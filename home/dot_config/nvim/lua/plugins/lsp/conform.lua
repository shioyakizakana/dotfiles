return {
  "stevearc/conform.nvim",
  cmd = { "FormatDisable", "FormatEnable" },
  event = "BufWritePre",
  opts = function ()
    -- https://github.com/stevearc/conform.nvim/blob/016802de402556da54c36bd7359b441266b01cdd/doc/recipes.md?plain=1#L78
    vim.api.nvim_create_user_command("FormatDisable", function ()
      vim.b.disable_autoformat = true
    end, { desc = "[lsp]カレントバッファのオートフォーマット無効化" })

    vim.api.nvim_create_user_command("FormatEnable", function ()
      vim.b.disable_autoformat = false
    end, { desc = "[lsp]カレントバッファのオートフォーマット有効化" })

    local web_formatters = function (bufnr)
      if require("config.web-project").deno_root(bufnr) then
        -- Denoの場合はLSPのFormatterを使用
        return {}
      end
      if vim.fs.root(bufnr, { "biome.json", "biome.jsonc" }) then
        return { "biome-check", "prettierd", stop_after_first = true }
      end
      return { "prettierd" }
    end

    return {
      formatters_by_ft = {
        lua = { "stylua" },
        go = { "goimports" },
        python = {
          "ruff_fix",
          "ruff_organize_imports",
          "ruff_format"
        },
        -- shell
        bash = { "shfmt" },
        zsh = { "shfmt" },

        -- web
        javascript = web_formatters,
        typescript = web_formatters,
        json = web_formatters,
        jsonc = web_formatters,
        html = web_formatters,
        css = web_formatters,
      },
      format_on_save = function(bufnr)
        -- オートフォーマットの状態を優先
        if vim.g.disable_autoformat or vim.b[bufnr].disable_autoformat  then
          return
        end
        -- conformで定義したformatterが存在しない場合はLSPのフォーマッターを使用
        return { timeout_ms = 1500, lsp_format = "fallback" }
      end,
    }
  end,
}
