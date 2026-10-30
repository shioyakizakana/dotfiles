local function get_skk_mode()
	local ok, skkelua = pcall(require, "skkelua")

	if not ok then
		return [[SKK off]]
	end

	local mode = skkelua.mode()

	local mode_names = {
		hira = [[ひらがな]],
		kata = [[カタカナ]],
		hankata = [[半角ｶﾀ]],
		zenkaku = [[全角英数]],
	}

	return mode_names[mode] or vim.g.skk_mode
end

---@module "lazy"
---@type LazyPluginSpec
return {
	-- ステータスラインをカスタマイズするためのプラグイン
	"nvim-lualine/lualine.nvim",
	dependencies = { "nvim-tree/nvim-web-devicons" },

	options = {
		icons_enabled = true,
		theme = "auto",
		component_separators = { left = "", right = "" },
		section_separators = { left = "", right = "" },
		disabled_filetypes = {
			statusline = {},
			winbar = {},
		},
		ignore_focus = {},
		always_divide_middle = true,
		globalstatus = false,
		refresh = {
			statusline = 1000,
			tabline = 1000,
			winbar = 1000,
		},
	},
	sections = {
		lualine_a = { "mode" },
		lualine_b = { "branch", "diff", "diagnostics" },
		lualine_c = { "filename" },
		lualine_x = {
			get_skk_mode,
			"encoding",
			{
				"fileformat",
				icons_enabled = "filetype",
			},
		},
		lualine_y = { "progress" },
		lualine_z = { "location" },
	},
	inactive_sections = {
		lualine_a = {},
		lualine_b = {},
		lualine_c = { "filename" },
		lualine_x = { "location" },
		lualine_y = {},
		lualine_z = {},
	},

	config = function(_, opts, sections, inactive_sections)
		require("lualine").setup({ opts, sections, inactive_sections })
	end,
}
