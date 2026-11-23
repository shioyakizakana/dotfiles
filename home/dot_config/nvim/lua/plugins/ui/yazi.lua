---@type LazySpec
return {
  "mikavilpas/yazi.nvim",
  version = "*", -- use the latest stable version
  event = "VeryLazy",
  dependencies = {
    { "nvim-lua/plenary.nvim", lazy = true },
  },
  keys = {
    {
      "<Space>y",
      mode = { "n", "v" },
      "<cmd>Yazi<cr>",
      desc = "[ui]現在のファイルの場所でYaziを開く",
    },
    {
      "<Space>cy",
      "<cmd>Yazi cwd<cr>",
      desc = "[ui]作業ディレクトリでYaziを開く",
    },
    {
      "<Space>Y",
      "<cmd>Yazi toggle<cr>",
      desc = "[ui]前回のYaziを再開",
    },
  },
  ---@type YaziConfig | {}
  opts = {
    -- if you want to open yazi instead of netrw, see below for more info
    open_for_directories = false,
    keymaps = {
      show_help = "<f1>",
      open_file_in_vertical_split = "<c-CR>",
      open_file_in_horizontal_split = "<c-s>",
      open_file_in_tab = "<c-t>",
      -- grep_in_directory = "<c-s>",
      -- replace_in_directory = "<c-g>",
      -- cycle_open_buffers = "<tab>",
      copy_relative_path_to_selected_files = "<c-y>",
      send_to_quickfix_list = "<c-s-q>",
      change_working_directory = "<c-\\>",
      open_and_pick_window = "<c-o>",
    },
  },
}
