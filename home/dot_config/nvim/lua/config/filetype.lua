-- ファイルの種別ごとに挙動を設定

local group_name = "my_nvim_rc"

local filename_map = {
	[".bashrc.tmpl"] = "bash",
	["dot_bashrc.tmpl"] = "bash",
	[".zshrc.tmpl"] = "zsh",
	["dot_zshrc.tmpl"] = "zsh",
	["Brewfile.tmpl"] = "ruby",
	["dot_Brewfile.tmpl"] = "ruby",
	[".gitconfig.tmpl"] = "gitconfig",
	["dot_gitconfig.tmpl"] = "gitconfig",
	[".gitignore"] = "gitignore",
	["dot_gitignore.tmpl"] = "gitignore",
	["ignore.tmpl"] = "gitignore",
}

local suffix_map = {
	{ "%.toml%.tmpl$", "toml" },
	{ "%.ya?ml%.tmpl$", "yaml" },
	{ "%.json%.tmpl$", "json" },
	{ "%.sh%.tmpl$", "sh" },
	{ "%.py%.tmpl$", "python" },
}

local function detect_shebang(buf)
	local line = vim.api.nvim_buf_get_lines(buf, 0, 1, false)[1] or ""

	-- インタープリター名の直後が空白・オプション・行末かを判定
	local function matches_interpreter(name)
		return line:match("^#!.*[/ ]" .. name .. "[%s%-]") or line:match("^#!.*[/ ]" .. name .. "$")
	end

	if matches_interpreter("bash") then
		return "bash"
	elseif matches_interpreter("zsh") then
		return "zsh"
	elseif matches_interpreter("sh") then
		return "sh"
	end

	return nil
end

local function detect_template_filetype(buf)
	local path = vim.api.nvim_buf_get_name(buf)
	local name = vim.fn.fnamemodify(path, ":t")

	if not name:match("%.tmpl$") then
		return
	end

	-- 1. シバンを最優先
	local ft = detect_shebang(buf)
	if ft then
		vim.bo[buf].filetype = ft
		return
	end

	-- 2. 特定のファイル名
	ft = filename_map[name]
	if ft then
		vim.bo[buf].filetype = ft
		return
	end

	-- 3. 特定の拡張子
	for _, entry in ipairs(suffix_map) do
		if name:match(entry[1]) then
			vim.bo[buf].filetype = entry[2]
			return
		end
	end

	-- 4. その他のテンプレート
	vim.bo[buf].filetype = "gotmpl"
end
-- ----------------------------------------------------
-- ファイルタイプの判定
-- ----------------------------------------------------

vim.filetype.add({
	extension = {
		mdx = "mdx",
	},
})

vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
	group = group_name,
	pattern = { "*.csv" },
	callback = function()
		vim.opt_local.filetype = "csv"
	end,
})

vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
	group = group_name,
	pattern = { "Brewfile", ".Brewfile" },
	callback = function()
		vim.opt_local.filetype = "ruby"
	end,
})
-- chezmoiの.tmplファイルを判定
vim.api.nvim_create_autocmd("BufReadPost", {
	group = group_name,
	callback = function(args)
		detect_template_filetype(args.buf)
	end,
})

-- 拡張子のない既存スクリプトもシバンから判定
vim.api.nvim_create_autocmd("BufReadPost", {
	group = group_name,
	callback = function(args)
		local path = vim.api.nvim_buf_get_name(args.buf)
		local name = vim.fn.fnamemodify(path, ":t")

		-- 拡張子付きファイルはテンプレート処理に任せる
		if name:match("%.[^./]+$") then
			return
		end

		local ft = detect_shebang(args.buf)
		if ft then
			vim.bo[args.buf].filetype = ft
		end
	end,
}) -- ----------------------------------------------------
-- ファイルタイプごとの処理
-- ----------------------------------------------------

vim.api.nvim_create_autocmd({ "FileType" }, {
	group = group_name,
	pattern = { "help", "man" },
	callback = function()
		vim.keymap.set("n", "q", "<Cmd>quit<CR>", { buffer = true, silent = true })
	end,
})
