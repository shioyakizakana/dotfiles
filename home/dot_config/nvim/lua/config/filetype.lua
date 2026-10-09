-- ファイルの種別ごとに挙動を設定

local group_name = "my_nvim_rc"

vim.filetype.add({
  extension = {
    mdx = "mdx",
  },
})

vim.api.nvim_create_autocmd({ "FileType" }, {
  group = group_name,
  pattern = { "help", "man" },
  callback = function()
    vim.keymap.set("n", "q", "<Cmd>quit<CR>", { buffer = true, silent = true })
  end,
})

vim.api.nvim_create_autocmd({ "BufNewFile", "BufRead" }, {
  group = group_name,
  pattern = { "*.csv" },
  callback = function()
    vim.opt_local.filetype = "csv"
  end,
})

-- chezmoiのテンプレートファイル対応
local chezmoi_ft = vim.api.nvim_create_augroup("chezmoi_file_type", { clear = true })
local tmpl_map = {
  { pattern = { "*.toml.tmpl" }, ft = "toml" },
  { pattern = { "*.yaml.tmpl", "*.yml.tmpl" }, ft = "yaml" },
  { pattern = { "*.sh.tmpl" }, ft = "sh" },
  { pattern = { "*.json.tmpl" }, ft = "json" },
  { pattern = { "Brewfile.tmpl", "dot_Brewfile.tmpl" }, ft = "ruby" },
  { pattern = { ".bashrc.tmpl", "dot_bashrc.tmpl" }, ft = "bash" },
  { pattern = { ".zshrc.tmpl", "dot_zshrc.tmpl" }, ft = "zsh" },
}

for _, entry in ipairs(tmpl_map) do
  vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
    group = chezmoi_ft,
    pattern = entry.pattern,
    callback = function()
      vim.bo.filetype = entry.ft
    end,
  })
end
