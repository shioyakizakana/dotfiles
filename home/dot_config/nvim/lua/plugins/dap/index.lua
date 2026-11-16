return {
  "igorlfs/nvim-dap-view",
  cond = not vim.g.vscode,
  dependencies = {
    "mfussenegger/nvim-dap",
    "jbyuki/one-small-step-for-vimkind",
    { "theHamsta/nvim-dap-virtual-text", opts = {} },
  },

  keys = require("plugins.dap.keymaps"),
  opts = {
    winbar = {
      sections = {
        "console",
        "watches",
        "scopes",
        "exceptions",
        "breakpoints",
        "threads",
        "repl"
      },
    },
  },

  config = function(_, opts)
    local dap = require("dap")
    local dap_view = require("dap-view")

    dap_view.setup(opts)

    dap.listeners.after.event_initialized["dotfiles.dap_view"] = function(session)
      if session.config.type == "nlua" then
        return
      end

      dap_view.open()
    end

    require("plugins.dap.adapters")
  end,
}
