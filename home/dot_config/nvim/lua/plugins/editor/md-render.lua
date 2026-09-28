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
      desc = "Markdown preview (toggle)"
    },
    {
      "<leader>mt",
      "<Plug>(md-render-preview-tab)",
      desc = "Markdown preview in tab (toggle)"
    },
    {
      "<leader>md",
      "<Plug>(md-render-demo)",
      desc = "Markdown render demo"
    },
  },
}
