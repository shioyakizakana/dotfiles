local luadir = vim.fn.stdpath("config") .. "/lua"
--基本のキーマップ設定
vim.g.mapleader = " " --リーダーキー

--ノーマルモード
vim.keymap.set("n", "<leader>w", ":w<CR>")     --編集中のファイルを保存
vim.keymap.set("n", "<leader>q", ":q<CR>")     --終了
vim.keymap.set("n", "<leader>fr", ":oldfiles") --最近開いたファイルの一覧表示

-- インサートモードでエスケープ
vim.keymap.set("i", "<leader>jk", "<Esc>")

-- 各モードでウィンドウ間を移動するためのキーマップを統一
vim.keymap.set("n", "<A-j>", "<C-w>w")
vim.keymap.set("i", "<A-j>", "<Esc><C-w>w")
vim.keymap.set("t", "<A-j>", "<C-\\><C-n><C-w>w")
-- 逆順にウィンドウ間を移動
vim.keymap.set("n", "<A-k>", "<C-w>W")
vim.keymap.set("i", "<A-k>", "<Esc><C-w>W")
vim.keymap.set("t", "<A-k>", "<C-\\><C-n><C-w>W")
-- ビジュアルモードでインデントを調整
vim.keymap.set("v", "<", "<gv")
vim.keymap.set("v", ">", ">gv")
-- ビジュアルモードで選択範囲のインデントを自動調整
vim.keymap.set("v", "=", "=gv")
-- 基本設定用lua保存ディレクトリへのショートカットキーマップ
vim.keymap.set("n", "<leader>cc", ":cd " .. luadir .. "/config<CR>", { desc = "Change to core config directory" })
-- プラグイン設定用lua保存ディレクトリへのショートカットキーマップ
vim.keymap.set("n", "<leader>pl", ":cd " .. luadir .. "/plugins<CR>", { desc = "Change to plugins config directory" })
-- 開発用デイレクトリへのショートカットキーマップ
vim.keymap.set("n", "<leader>dev", ":cd " .. "/home/shioyaki/_dev<CR>", {desc = "Change to develop directory"})

