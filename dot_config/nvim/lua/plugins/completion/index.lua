---@module "lazy"
---@type LazyPluginSpec[]
return {

  {
    "saghen/blink.compat",
    version = "2.*",
    lazy = true,
    opts = {
      impersonate_nvim_cmp = true,
    },
  },

  {
    "saghen/blink.cmp",
    cond = not vim.g.vscode,
    event        = { "InsertEnter", "CmdlineEnter" },
    version      = "*",
    dependencies = {
      "Kaiser-Yang/blink-cmp-dictionary",
      { import = "plugins.completion.luasnip" },
      "disrupted/blink-cmp-conventional-commits",
      -- "rinx/cmp-skkeleton",
    },
    build = function()
      require("blink.cmp").build():wait(60000)
    end,
    ---@module "blink.cmp"
    ---@type blink.cmp.Config
    opts         = {
      keymap  = require("plugins.completion.keymaps"),
      cmdline = {
        keymap = {
          preset = "super-tab",
          ["<CR>"] = {
            function(cmp)
              if not vim.tbl_contains({ "/", "?" }, vim.fn.getcmdtype()) then
                return cmp.accept_and_enter()
              end
            end,
            "fallback",
          },

        },
        completion = {
          ghost_text = { enabled = true },
          menu = { auto_show = true },
        },
      },
      -- スニペット
      snippets     = {
        preset = "luasnip",
      },
      -- 補完ソース
      sources = require("plugins.completion.sources"),
      -- 外観
      appearance   = {
        use_nvim_as_default = true,
        nerd_font_variant = "normal",
      },
      completion   = {
        documentation = {
          auto_show = true,
          auto_show_delay_ms = 500,
          window = { border = "double" },
        },
        menu = {
          auto_show = function(ctx)
            return ctx.mode ~= "cmdline"
              or not vim.tbl_contains({ "/", "?" }, vim.fn.getcmdtype())
          end,
        },
        ghost_text = { enabled = true },
        list = {
          selection = {
            aut_insert = false,
          },
        },
      },
      signature    = {
        window = {
          border = "single",
        },
      },
      -- fuzzy        = {
      --  implementation = "prefer_rust_with_warning",
      --},
    },
    opts_extend  = { "sources.default" },
  },
}
