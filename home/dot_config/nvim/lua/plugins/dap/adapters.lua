local dap = require("dap")

dap.configuration.lua = {
    {
        tyoe = "nlua",
        request = "attach",
        name = "Attach to running Neovim instance",
    }
}

dap.adapters.nlua = function(callback, config)
    callback({
        type = "server",
        host = config.host or "127.0.0.1",
        port = config.port or 8086
    })
end

dap.configuration.python = {
    {
        type = "python",
        request = "launch",
        name = "Launch file",

        program = "${file}",
        python_path = function()
            local cwd = vim.fn.getcwd()
            if vim.fn.executable(cwd .. "venv/bin/python") == 1 then
                return cwd .. "venv/bin/python"
            elseif vim.fn.executable(cwd .. ".venv/bin/python") == 1 then
                return cwd .. ".venv/bin/python"
            else
                return "usr/bin/python"
            end
        end,
    }
}
