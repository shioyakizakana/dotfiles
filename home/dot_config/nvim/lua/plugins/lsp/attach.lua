local function attach_callback(ev)
  local bufopts = function(desc)
    return {
      noremap = true,
      silent = true,
      buffer = ev.buf,
      desc = desc,
    }
  end
  vim.bo[ev.buf].omnifunc = "v:lua.vim.lsp.omnifunc"

  vim.keymap.set("n", "gD", "<cmd>lua vim.lsp.buf.declaration()<CR>", bufopts("[lsp]宣言へジャンプ"))
  vim.keymap.set("n", "gri", "<cmd>lua vim.lsp.buf.implementation()<CR>", bufopts("[lsp]実装へジャンプ"))
  vim.keymap.set(
    "n",
    "<space>D",
    "<cmd>lua vim.lsp.buf.type_definition()<CR>",
    bufopts("[lsp]型定義へジャンプ")
  )
  vim.keymap.set(
    "n",
    "K",
    "<cmd>lua vim.lsp.buf.signature_help()<CR>",
    bufopts("[lsp]シグネチャをポップアップ")
  )
  vim.keymap.set(
    "i",
    "<C-g>h",
    "<cmd>lua vim.lsp.buf.signature_help()<CR>",
    bufopts("[lsp]シグネチャをポップアップ")
  )
  vim.keymap.set(
    "n",
    "grn",
    "<cmd>lua vim.lsp.buf.rename()<CR>",
    bufopts("[lsp]シンボル名をプロジェクト全体でリネーム")
  )
  vim.keymap.set(
    "n",
    "<leader>lc",
    "<cmd>lua vim.diagnostic.open_float()<CR>",
    bufopts("[lsp]診断をポップアップ")
  )
  vim.keymap.set(
    "n",
    "[d",
    "<cmd>lua vim.diagnostic.jump({count=1, float=true})<CR>",
    bufopts("[lsp]次の診断の箇所へジャンプ")
  )
  vim.keymap.set(
    "n",
    "]d",
    "<cmd>lua vim.diagnostic.jump({count=-1, float=true})<CR>",
    bufopts("[lsp]前の診断へジャンプ")
  )
  vim.keymap.set("n", "<leader><leader>r", "<cmd>LspRestart<CR>", bufopts("[lsp]LSPを再起動"))
end

vim.api.nvim_create_autocmd("LspAttach", {
  group = "my_nvim_rc",
  callback = function(ev)
    attach_callback(ev)
  end,
})

vim.api.nvim_create_autocmd({ "FileType" }, {
  group = "my_nvim_rc",
  pattern = { "yaml" },
  callback = function(ev)
    attach_callback(ev)
  end,
})

vim.api.nvim_create_user_command("LspLog", function()
  vim.cmd(string.format("edit %s", vim.lsp.log.get_filename()))
end, {
  desc = "[lsp]LSPログをオープン",
})

vim.api.nvim_create_user_command("LspInfo", function()
  vim.cmd("vertical checkhealth vim.lsp")
end, {})
