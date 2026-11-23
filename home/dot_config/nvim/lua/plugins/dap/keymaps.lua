---@module "lazy"
---@type LazyKeysSpec[]
return {
    {
        "<F5>",
        function()
            require("dap").continue()
        end,
        desc = "[debug]実行を開始・継続",
    },
    {
        "<F10>",
        function()
            require("dap").step_over()
        end,
        desc = "[debug]ステップオーバー",
    },
    {
        "<F11>",
        function()
            require("dap").step_into()
        end,
        desc = "[debug]ステップイン",
    },
    {
        "<F12>",
        function()
            require("dap").step_out()
        end,
        desc = "[debug]ステップアウト",
    },
    {
        "<leader>b",
        function()
            require("dap").toggle_breakpoint()
        end,
        desc = "[debug]ブレークポイントを切り替える",
    },
    {
        "<leader>B",
        function()
            require("dap").set_breakpoint(
                nil, nil,
                vim.fn.input("Breakpoint condition: ")
            )
        end,
        desc = "[debug]条件付きブレークポイントを設定",
    },
    {
        "<leader>dL",
        function()
            require("dap").set_breakpoint(
                nil, nil,
                vim.fn.input("Log point message: ")
            )
        end,
        desc = "[debug]ログポイントを設定",
    },
    {
        "<leader>dr",
        function()
            require("dap").repl.open()
        end,
        desc = "[debug]REPLを開く",
    },
    {
        "<leader>bl",
        function()
            require("dap").run_last()
        end,
        desc = "[debug]前回のデバッグを再実行",
    },
    {
        "<F7>",
        function()
            require("dap-view").toggle()
        end,
        desc = "[debug]デバッグ画面を切り替える",
    },
}
