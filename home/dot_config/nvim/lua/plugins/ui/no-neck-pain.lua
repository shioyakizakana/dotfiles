---@module "lazy"
---@type LazyPluginSpec
return {
  "shortcuts/no-neck-pain.nvim",
  version = "*",
  config = function()
    require("no-neck-pain").setup({
      buffers = {
        right = {
          enabled = false,
        },
        scratchPad = {
          enabled = true,
          location = vim.fn["expand"]("~/notes"),
        },
        bo = {
          filetype = "md",
        },
      },
      autocmds = {
        enableonVimEnter = true,
        enabledTabEnter = true,
        reloadOnColorSchemeChange = true,
      },
    })
    vim.keymap.set("n", "<leader>z", "<cmd>NoNeckPain<CR>", { desc = "[window]余白表示を切り替える" })
  end,
}
