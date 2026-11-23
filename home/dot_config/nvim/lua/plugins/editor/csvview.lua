---@module "lazy"
---@type LazyPluginSpec
return {
  "hat0uma/csvview.nvim",
  cmd = { "CsvViewEnable", "CsvViewDisable", "CsvViewToggle" },
  ft = {
    "csv",
    "tsv",
    "csv_semicolon",
    "csv_whitespace",
    "csv_pipe",
    "rfc_csv",
    "rfc_semicolon",
  },
  keys = { { "<leader>cv", "<Cmd>CsvViewToggle<CR>", desc = "[csv]表形式の表示切替" } },
  ---@module "csvview"
  ---@type CsvView.Options
  opts = {
    parser = { comments = { "#", "//" } },
    keymaps = {
      -- Text objects for selecting fields
      textobject_field_inner = { "if", mode = { "o", "x" }, desc = "[csv]フィールドの内側を選択" },
      textobject_field_outer = { "af", mode = { "o", "x" }, desc = "[csv]区切り文字を含めて選択" },
      -- Excel-like navigation:
      -- Use <Tab> and <S-Tab> to move horizontally between fields.
      -- Use <Enter> and <S-Enter> to move vertically between rows and place the cursor at the end of the field.
      -- Note: In terminals, you may need to enable CSI-u mode to use <S-Tab> and <S-Enter>.
      jump_next_field_end = { "<Tab>", mode = { "n", "v" }, desc = "[csv]次のフィールドの末尾へ移動" },
      jump_prev_field_end = { "<S-Tab>", mode = { "n", "v" }, desc = "[csv]前のフィールドの末尾へ移動" },
      jump_next_row = { "<Enter>", mode = { "n", "v" }, desc = "[csv]次の行へ移動" },
      jump_prev_row = { "<S-Enter>", mode = { "n", "v" }, desc = "[csv]前の行へ移動" },
    },
  },
}
