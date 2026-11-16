local dap = require("dap")

dap.configurations.lua = {
    {
        type = "nlua",
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

-- アダプターのPythonとデバッグ対象のPythonを分離する。
dap.adapters.python = function(callback)
    local command = vim.fn.exepath("debugpy-adapter")
    if command == "" then
        error("debugpy-adapterが見つかりません。debugpyの導入状態とPATHを確認してください。", 0)
    end
    callback({
        type = "executable",
        command = command,
        -- proot等では初回起動がnvim-dap既定の4秒を超える場合がある。
        options = { initialize_timeout_sec = 20 },
    })
end

dap.configurations.python = {
    {
        type = "python",
        request = "launch",
        name = "Launch file",

        program = "${file}",
        pythonPath = function()
            local cwd = vim.fn.getcwd()
            for _, directory in ipairs({ "venv", ".venv" }) do
                local python = vim.fs.joinpath(cwd, directory, "bin", "python")
                if vim.fn.executable(python) == 1 then
                    return python
                end
            end
            for _, name in ipairs({ "python3", "python" }) do
                local python = vim.fn.exepath(name)
                if python ~= "" and vim.fn.executable(python) == 1 then
                    return python
                end
            end
            error("デバッグ対象のPythonが見つかりません。venv・.venvまたはPATHを確認してください。", 0)
        end,
    }
}
