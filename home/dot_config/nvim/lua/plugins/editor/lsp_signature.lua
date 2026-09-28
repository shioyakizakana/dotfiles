---@module "lazy"
---@type LazyPluginSpec
return {
  "ray-x/lsp_signature.nvim",
  event = "InsertEnter",
  opts = {
    bind = true,
    border = "rounded",
  },
  vim.keymap.set(
    { "n" }, "<C-k>", function ()
      require("lsp_signature").toggle_float_win()
    end,
    { silent = true, noremap = true, desc = "toggle signature"}
  ),
  vim.keymap.set(
    { "n" }, "<leader>k", function ()
      vim.lsp.buf.signature_help()
    end,
    { silent = true, noremap = true, desc = "toggle signature" }
  ),
}
