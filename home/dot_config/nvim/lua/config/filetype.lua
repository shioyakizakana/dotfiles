-- ファイルの種別ごとに挙動を設定

local group_name = "my_nvim_rc"

vim.api.nvim_create_autocmd({ "FileType" }, {
  group = group_name,
  pattern = { "help", "man" },
  callback = function()
    vim.keymap.set("n", "q", "<Cmd>quit<CR>", { buffer = true, silent = true })
  end,
})

vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
  group = group_name,
  pattern = { "*.csv" },
  callback = function()
    vim.opt_local.filetype = "csv"
  end,
})
