---@module "lazy"
---@type LazyPluginSpec
return {
	"nvim-mini/mini.surround",
	version = "*",
	event = { "VeryLazy" },
	opts = function()
		local jpKakkoTable = {
			["("] = { left = "（", right = "）" },
			[")"] = { left = "（", right = "）" },
			["8"] = { left = "（", right = "）" },
			["9"] = { left = "（", right = "）" },
			["["] = { left = "［", right = "］" },
			["]"] = { left = "［", right = "］" },
			["B"] = { left = "［", right = "］" },
			["}"] = { left = "｛", right = "｝" },
			["{"] = { left = "｛", right = "｝" },
			["<"] = { left = "＜", right = "＞" },
			[">"] = { left = "＜", right = "＞" },
			["k"] = { left = "「", right = "」" },
			["K"] = { left = "『", right = "』" },
			["y"] = { left = "〈", right = "〉" },
			["Y"] = { left = "《", right = "》" },
			["r"] = { left = "【", right = "】" },
			["s"] = { left = "【", right = "】" },
			["t"] = { left = "〔", right = "〕" },
			["a"] = { left = "＜", right = "＞" },
			["A"] = { left = "≪", right = "≫" },
		}
		local surround = require("mini.surround")
		return {
			custom_surroundings = {
				["j"] = {
					input = function()
						local char = surround.user_input("enter for KAKKO: ")
						if char == nil then
							return
						end
						local pair = jpKakkoTable[char]
						if pair == nil then
							error("j" .. char .. " is unsupported :(")
						end
						return { pair.left .. "().-()" .. pair.right }
					end,
					output = function()
						local char = surround.user_input("enter for KAKKO: ")
						if char == nil then
							return
						end
						local pair = jpKakkoTable[char]
						if pair == nil then
							error("j" .. char .. " is unsupported :(")
						end
						return pair
					end,
				},
				["B"] = {
					input = { " ?%*%*().-()%*%* ?" },
					output = { left = " **", right = "** " },
				},
				["^"] = {
					input = { "~~().-()~~" },
					output = { left = "~~", right = "~~" },
				},
				["~"] = {
					input = { "~~().-()~~" },
					output = { left = "~~", right = "~~" },
				},
				-- instead of <CR>
				["\r"] = {
					input = { "\n().-()\n" },
					output = { left = "\n", right = "\n" },
				},
				["M"] = {
					input = { "\n().-()\n" },
					output = { left = "\n", right = "\n" },
				},
			},
			-- 各操作に対応したプリフィックス
			mappings = {
				add = "sa", -- Add surrounding in Normal and Visual modes
				delete = "sd", -- Delete surrounding
				find = "sf", -- Find surrounding (to the right)
				find_left = "sF", -- Find surrounding (to the left)
				highlight = "sh", -- Highlight surrounding
				replace = "sr", -- Replace surrounding

				suffix_last = "l", -- Suffix to search with "prev" method
				suffix_next = "n", -- Suffix to search with "next" method
			},
			silent = true,
		}
	end,
}
