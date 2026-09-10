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
-- `plugins/bunny-private.yazi/main.lua`を作成して設定
-- プライベートなパスを含むため設定を分離
require("bunny-private"):setup()
