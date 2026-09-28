local M = {}

---@type snacks.picker.Config
M.config = {
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
