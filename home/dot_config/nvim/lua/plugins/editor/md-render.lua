return {
  "delphinus/md-render.nvim",
  version = "*",
  dependencies = {
    { "nvim-tree/nvim-web-devicons", version = "*" }, -- optional
    { "delphinus/budoux.lua", version = "*" }, -- optional: CJK p
  },
  keys = {
    {
      "<leader>mp",
      "<Plug>(md-render-preview)",
      desc = "[markdown]プレビューを切り替える"
    },
    {
      "<leader>mt",
      "<Plug>(md-render-preview-tab)",
      desc = "[markdown]タブ内のプレビューを切り替える"
    },
    {
      "<leader>md",
      "<Plug>(md-render-demo)",
      desc = "[markdown]描画のデモを表示"
    },
  },
}
