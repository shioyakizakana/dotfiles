local M = {}

---@type snacks.picker.Config
M.config = {
  sources = {
    keymaps = {
      modes = { "n", "v", "x", "s", "o", "i", "c", "t", "l" },
      transform = require("config.keymap-descriptions").picker_transform,
    },
  },
  formatters = {
    file = {
      filename_first = true,
      truncate = 100,
    },
  },
  layout = {
    default = {
      layout = {
        width = 0.95,
      },
    },
  },
  win = {
    input = {
      -- keys = {},
    },
  },
}

vim.api.nvim_set_hl(0, "SnacksPickerDir", { link = "Comment" })

return M
