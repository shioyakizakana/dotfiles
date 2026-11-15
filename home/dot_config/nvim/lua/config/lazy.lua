local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
local uv = vim.uv or vim.loop
local function bootstrap_error(message)
	vim.api.nvim_echo({ { "Failed to bootstrap lazy.nvim\n", "ErrorMsg" }, { message, "WarningMsg" } }, true, {})
	os.exit(1)
end

if not uv.fs_stat(lazypath) then
	local parent = vim.fn.fnamemodify(lazypath, ":h")
	vim.fn.mkdir(parent, "p")
	-- 同じファイルシステムで取得し、失敗時に消すのは自分の一時領域だけにする。
	local staging, staging_error = uv.fs_mkdtemp(parent .. "/lazy.nvim-XXXXXX")
	if not staging then
		bootstrap_error(tostring(staging_error))
	end
	local function fail(message)
		if vim.fn.delete(staging, "rf") ~= 0 then
			message = message .. "\nFailed to cleanup: " .. staging
		end
		bootstrap_error(message)
	end
	local ok, out = pcall(vim.fn.system, {
		"git",
		"clone",
		"--filter=blob:none",
		"https://github.com/folke/lazy.nvim.git",
		"--branch=stable",
		staging,
	})
	if not ok or vim.v.shell_error ~= 0 then
		fail(tostring(out))
	end
	-- 別の起動や利用者が作った展開先は上書きしない。
	if uv.fs_stat(lazypath) then
		fail("Destination already exists: " .. lazypath)
	end
	local renamed, rename_error = uv.fs_rename(staging, lazypath)
	if not renamed then
		fail(tostring(rename_error))
	end
end
vim.opt.rtp:prepend(lazypath)

local function get_editor(name)
	return "plugins.editor." .. name
end

local function get_utils(name)
	return "plugins.utils." .. name
end

local function get_ui(name)
	return "plugins.ui." .. name
end

-- プラグインの読み込み
require("lazy").setup({
	--プラグインの基本スペック
	spec = {
		{ "nvim-lua/plenary.nvim", lazy = true },

		-- UI関連
		{ "nvim-tree/nvim-web-devicons" },
		{ import = get_ui("barbar") },
		-- カラースキーマ
		{ import = get_ui("colorscheme") },
		{ import = get_ui("indent-blankline") },
		{ import = get_ui("lualine.index") },
		{ import = get_ui("no-neck-pain") },
		{ import = get_ui("nvim-scrollbar") },
		-- { import = get_ui("nvim-tree.index") },
		{ import = get_ui("oil") },
		{ import = get_ui("quicker") },
		{ import = get_ui("rainbow-delimiters") },
		{ import = get_ui("toggleterm") },
		{ import = get_ui("winresizer") },
		{ import = get_ui("yazi") },
		-- エディター機能拡張
		{ import = get_editor("csvview") },
		{ import = get_editor("in-and-out") },
		{ import = get_editor("lsp_signature") },
		{ import = get_editor("md-render") },
		{ import = get_editor("min-surround") },
		{ import = get_editor("mini-test") },
		{ import = get_editor("nvim-autopairs") },
		{ import = get_editor("tiny-cmdline") },
		{ import = get_editor("treesj") },
		{ "kana/vim-operator-replace", dependencies = { "kana/vim-operator-user" } },

		-- ユーティリティー
		{ import = get_utils("lazygit") },
		{ import = get_utils("nvim-hlslens") },
		{ import = get_utils("nvim-treesitter") },
		{ import = get_utils("snacks.index") },
		{ import = get_utils("which-key") },
		-- skk
		-- { import = "plugins.skkeleton.index" },
		-- 補完系
		{ import = "plugins.completion.index" },
		-- LSP
		{ import = "plugins.lsp.index" },
		-- DAP
		{ import = "plugins.dap.index" },

		-- ヘルプの日本語化
		{ "vim-jp/vimdoc-ja", event = "VeryLazy" },
	},
	checker = { enable = true },
})
