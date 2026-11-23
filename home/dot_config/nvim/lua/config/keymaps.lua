local luadir = vim.fn.stdpath("config") .. "/lua"
--基本のキーマップ設定
vim.g.mapleader = " " --リーダーキー

--ノーマルモード
vim.keymap.set("n", "<leader>w", ":w<CR>", { desc = "[file]ファイルを保存" })
vim.keymap.set("n", "<leader>q", ":q<CR>", { desc = "[window]ウィンドウを閉じる" })
vim.keymap.set("n", "<leader>fR", "<cmd>oldfiles<CR>", { desc = "[file]履歴ファイルの一覧表示" })

-- インサートモードでエスケープ
vim.keymap.set("i", "<leader>jk", "<Esc>", { desc = "[mode]ノーマルモードに戻る" })

-- 各モードでウィンドウ間を移動するためのキーマップを統一
vim.keymap.set("n", "<A-j>", "<C-w>w", { desc = "[window]次のウィンドウへ移動" })
vim.keymap.set("i", "<A-j>", "<Esc><C-w>w", { desc = "[window]次のウィンドウへ移動" })
vim.keymap.set("t", "<A-j>", "<C-\\><C-n><C-w>w", { desc = "[window]次のウィンドウへ移動" })
-- 逆順にウィンドウ間を移動
vim.keymap.set("n", "<A-k>", "<C-w>W", { desc = "[window]前のウィンドウへ移動" })
vim.keymap.set("i", "<A-k>", "<Esc><C-w>W", { desc = "[window]前のウィンドウへ移動" })
vim.keymap.set("t", "<A-k>", "<C-\\><C-n><C-w>W", { desc = "[window]前のウィンドウへ移動" })
-- ビジュアルモードでインデントを調整
vim.keymap.set("v", "<", "<gv", { desc = "[edit]インデントを減らして選択を維持" })
vim.keymap.set("v", ">", ">gv", { desc = "[edit]インデントを増やして選択を維持" })
-- ビジュアルモードで選択範囲のインデントを自動調整
vim.keymap.set("v", "=", "=gv", { desc = "[edit]インデントを整えて選択を維持" })
-- 基本設定用lua保存ディレクトリへのショートカットキーマップ
vim.keymap.set("n", "<leader>cc", ":cd " .. luadir .. "/config<CR>", { desc = "[directory]基本設定ディレクトリへ移動" })
-- プラグイン設定用lua保存ディレクトリへのショートカットキーマップ
vim.keymap.set("n", "<leader>pl", ":cd " .. luadir .. "/plugins<CR>", { desc = "[directory]プラグイン設定ディレクトリへ移動" })
-- 開発用デイレクトリへのショートカットキーマップ
vim.keymap.set("n", "<leader>dev", ":cd " .. "/home/shioyaki/_dev<CR>", {desc = "[directory]開発ディレクトリへ移動"})

