---@module "lazy"
---@type LazyPluginSpec
return {
  "stevearc/quicker.nvim",
  event = "FileType qf",
  opts = {
    keys = {
      {
        ">",
        "<cmd>lua require('quicker').expand()<CR>",
        desc = "[quickfix]前後の行を表示",
      },
      {
        "<",
        "<cmd>lua require('quicker').collapse()<CR>",
        desc = "[quickfix]前後の行を非表示",
      },
      {
        "gr",
        "<cmd>lua require('quicker').refresh()<CR>",
        desc = "[quickfix]内容を更新",
      },
    },
  },
}
