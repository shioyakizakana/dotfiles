---@module "lazy"
---@type LazyPluginSpec
return {
	"kjuq/skkelua.nvim",
	config = function()
		require("skkelua").config({
			globalDictionaries = {
				vim.fn["expand"]("~/.skk/dic/SKK-JISYO.L"),
				vim.fn["expand"]("~/.skk/dic/SKK-JISYO.fullname"),
				vim.fn["expand"]("~/.skk/dic/SKK-JISYO.jinmei"),
				vim.fn["expand"]("~/.skk/dic/SKK-JISYO.geo"),
				vim.fn["expand"]("~/.skk/dic/SKK-JISYO.station"),
				vim.fn["expand"]("~/.skk/dic/SKK-JISYO.propernoun"),
			},
			completionRankFile = vim.fn["expand"]("~/.skk/rank.json"),
			completion = {
				enabled = true,
				insertOnSelect = false,
				deferOkuri = true,
			},
			eggLikeNewline = true,
			indicator = {
				alwaysShown = false,
				fadeOutMs = 1000,
				border = "rounded",
			},
			keepMode = true,
			keepState = true,
			pureSpace = false,
			registerConvertResult = true,
			setUndoPoint = true,
		})
		require("skkelua").register_kanatable("rom", {
			["jj"] = "escape",
		})
		-- vim.keymap.set({ "i", "c", "t" }, "<C-j>", "<Plug>(skkelua-toggle)")

		-- Ctrl+j
		vim.keymap.set({ "i", "c", "t" }, "<C-j>", function()
			local skkelua = require("skkelua")
			local mode = skkelua.mode()

			if mode == "" then
				skkelua.handle("enable")
			else
				skkelua.handle("handleKey", {
					["function"] = "hirakana",
				})
			end
		end, { expr = true })

		--Ctrl+eでキャンセル
		vim.keymap.set("i", "<C-e>", function()
			local skkelua = require("skkelua")
			local phase = skkelua.phase()
			if vim.tbl_contains({
				"input:okurinasi",
				"input:okuriari",
				"henkan",
			}, phase) then
				skkelua.handle("handleKey", {
					["function"] = "escape",
				})
			end
			return "<C-e>"
		end, { expr = true })

		-- skkの現在のモードをステータスラインに表示する
		-- skkelua無効化の直前にskkeluaの状態をグローバル変数にセット
		vim.api.nvim_create_autocmd("User", {
			pattern = { "skkelua-disable-pre" },
			callback = function()
				local mode = require("skkelua").mode()

				local mode_names = {
					hira = "SKK off(ひら)",
					kata = "SKK off(カタ)",
					hankata = "SKK off(半角)",
					zenkaku = "Skk off(全角)",
				}

				vim.g.skk_mode = mode_names[mode] or "SKK off"
			end,
		})
		-- skkelua-disable-preの後に発火
		vim.api.nvim_create_autocmd("User", {
			pattern = { "skkelua-mode-changed" },
			callback = function()
				require("lualine").refresh()

				if require("skkelua").mode() ~= "" then
					local ok, blink = pcall(require, "blink.cmp")

					if ok then
						blink.hide()
					end
				end
			end,
		})

		-- このイベントの前にstatus.mde=""が発生してskkeluaが強制的にオフになる
		vim.api.nvim_create_autocmd("User", {
			pattern = { "skkelua-disable-post" },
			callback = function()
				require("lualine").refresh()
			end,
		})

		require("skkelua").initialize()
	end,
}
