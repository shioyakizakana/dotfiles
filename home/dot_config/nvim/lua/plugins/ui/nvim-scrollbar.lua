return {
  "petertriho/nvim-scrollbar",
  cond = not vim.g.vscode,
  event = { "VeryLazy" },
  opts = {
    exclude = {
      filetypes = {
        "prompt",
        "cmp_docs",
        "cmp_menu",
        "noice",
      },
    },
    scrollbar = {
      hide_if_all_visible = true,
      visibility = "active",
    },
  },
}
