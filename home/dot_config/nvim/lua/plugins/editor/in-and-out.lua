return {
    -- カーソル位置の括弧や引用符の内側と外側を切り替えるためのプラグイン
    "ysmb-wtsg/in-and-out.nvim",
    keys = {
        {
            "<C-CR>",
            function()
                require("in-and-out").in_and_out()
            end,
            mode = "i"
        }
    },
    opts = { additional_targets = { "“", "”" } }
}
