-- インデント設定
vim.opt.autoindent = true -- 改行時に前の行のインデントを継続
vim.opt.expandtab = true  -- タブ文字をスペースに変換
vim.opt.tabstop = 2       -- Tabキーによるスペースの数
vim.opt.shiftwidth = 2    -- インデントの幅
-- 不可視文字の表示
vim.opt.list = true
-- 各不可視文字に対応する文字表示
vim.opt.listchars = {
  tab = "»·",
  eol = "¶",
  nbsp = "␣",
}

vim.api.nvim_create_autocmd({ "WinEnter", "FocusGained", "BufEnter" }, {
  pattern = "*",
  command = "checktime",
})
