-- プリセットのプラグイン
require("zoxide"):setup({
	update_db = true,
})
require("session"):setup({
	sync_yanked = true,
})

-- 公式プラグイン
local function setup_optional(name, options)
	local ok, plugin = pcall(require, name)
	if not ok then
		-- 私的設定の例外にはパスなどが含まれ得るため、その内容は出力しない。
		ya.err("Optional plugin could not be loaded: " .. name .. "; see docs/setup/dependencies.md")
		return
	end
	-- 導入済みプラグインのsetup失敗は隠さない。
	plugin:setup(options)
end

setup_optional("git")
setup_optional("full-border", {
  type = ui.Border.ROUNDED,
})

-- サードパーテイープラグイン
-- https://github.com/tadashi-aikawa/toki/blob/7fede8c5fc086714e540004471fb2a7139444ea7/mnt/yazi/init.lua#L24
-- `plugins/bunny-private.yazi/main.lua`を作成して設定
-- プライベートなパスを含むため設定を分離
-- ```
-- local function setup()
--  require("bunny"):setup({
--    hops = {
--      { key = "/", path = "/" },
--      { key = "h" , path = "~", desc = "Home directory" },
--      { key = "c", path = "~/.config", desc = "Config files" },
--      { key = "d", path = "~/Downloads", desc = "Downloads"  },
--    },
--  })
-- end
--
-- return { setup = setup }
-- ```
setup_optional("bunny-private")

