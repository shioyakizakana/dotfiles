-- プリセットのプラグイン
require("zoxide"):setup({
	update_db = true,
})
require("session"):setup({
	sync_yanked = true,
})

-- 公式プラグイン
require("git"):setup()
require("full-border"):setup({
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
require("bunny-private"):setup()

