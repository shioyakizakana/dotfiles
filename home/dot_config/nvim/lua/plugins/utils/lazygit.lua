return {
  "kdheepak/lazygit.nvim",
  cond = not vim.g.vscode,
  lazy = true,
  cmd = {
    "LazyGit",
    "LazyGitConfig",
    "LazyGitCurrentFile",
    "LazyGitFilter",
    "LazyGitFilterCurrentFile",
  },
  dependencies = {
    "nvim-lua/plenary.nvim"
  },

  keys = {
    { "<leader>lg", "<cmd>LazyGit<CR>", { desc = "LazyGit" } }
  }
}
