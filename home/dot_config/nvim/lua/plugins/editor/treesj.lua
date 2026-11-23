return {
    "Wansmer/treesj",
    keys = {
        { "<space>m", desc = "[edit]コードの分割・結合を切り替える" },
        { "<space>j", desc = "[edit]コードを結合" },
        { "<space>s", desc = "[edit]コードを分割" },
    },
    dependencies = {
        "nvim-treesitter/nvim-treesitter"
    },
    config = function()
        require("treesj").setup({
            -- [[my config]]
        })
    end,
}
