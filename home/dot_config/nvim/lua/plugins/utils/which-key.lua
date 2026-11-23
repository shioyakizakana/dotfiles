return {
    -- キーバインドのヒントを表示するためのプラグイン
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
        replace = {
            desc = {
                { "<Plug>%(?(.*)%)?", "%1" },
                { "^%+", "" },
                { "<[cC]md>", "" },
                { "<[cC][rR]>", "" },
                { "<[sS]ilent>", "" },
                { "^lua%s+", "" },
                { "^call%s+", "" },
                { "^:%s*", "" },
                require("config.keymap-descriptions").translate,
            },
        },
    },
    keys = {
        {
            "<leader>?",
            function()
                require("which-key").show({})
            end,
            desc = "[keymap]キーマップ一覧を表示（which-key）",
        },
    },
}
