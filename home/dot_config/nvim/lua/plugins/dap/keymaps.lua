---@module "lazy"
---@type LazyKeysSpec[]
return {
    {
        "F5",
        function()
            require("dap").continue()
        end,
        desc = "Debug: Continue",
    },
    {
        "F10",
        function()
            require("dap").step_over()
        end,
        desc = "Debug: Step Over",
    },
    {
        "F11",
        function()
            require("dap").step_into()
        end,
        desc = "Debug: Step Into",
    },
    {
        "F12",
        function()
            require("dap").step_out()
        end,
        desc = "Debug: Step Out",
    },
    {
        "<leader>b",
        function()
            require("dap").toggle_breakpoint()
        end,
        desc = "Debug: Toggle breakpoint",
    },
    {
        "<leader>B",
        function()
            require("dap").set_breakpoint(
                nil, nil,
                vim.fn.input("Breakpoint condition: ")
            )
        end,
        desc = "Debug: Set conditional breakpoint",
    },
    {
        "<leader>dr",
        function()
            require("dap").set_breakpoint(
                nil, nil,
                vim.fn.input("Log point message: ")
            )
        end,
        desc = "Debug: Set log point",
    },
    {
        "<leader>dr",
        function()
            require("dap").repl.open()
        end,
        desc = "Debug: Open REPL",
    },
    {
        "<leader>bl",
        function()
            require("dap").run_last()
        end,
        desc = "Debug: Run last debug session",
    },
    {
        "<F7>",
        function()
            require("dap-view").toggle()
        end,
        desc = "Debug: Toggle DAP UI",
    },
}
