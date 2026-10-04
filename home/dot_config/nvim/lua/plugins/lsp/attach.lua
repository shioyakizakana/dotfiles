local function attach_callback(ev)
  local bufopts = { noremap = true, silent = true, buffer = ev.buf }
  vim.bo[ev.buf].omnifunc = "v:lua.vim.lsp.omnifunc"
  vim.keymap.set(
    "n",
    "gD",
    "<cmd>lua vim.lsp.buf.declaration()<CR>",
    bufopts
  )
  vim.keymap.set(
    "n",
    "gri",
    "<cmd>lua vim.lsp.buf.implementation()<CR>",
    bufopts
  )
  vim.keymap.set(
    "n",
    "<space>D",
    "<cmd>lua vim.lsp.buf.type_definition()<CR>",
    bufopts
  )
  vim.keymap.set("n", "K", "<cmd>lua vim.lsp.buf.signature_help()<CR>", bufopts)
  vim.keymap.set(
    "i",
    "<C-g>h",
    "<cmd>lua vim.lsp.buf.signature_help()<CR>",
    bufopts
  )
  vim.keymap.set("n", "grn", "<cmd>lua vim.lsp.buf.rename()<CR>", bufopts)
  vim.keymap.set(
    "n",
    "<leader>lc",
    "<cmd>lua vim.diagnostic.open_float()<CR>",
    bufopts
  )
  vim.keymap.set(
    "n",
    "[d",
    "<cmd>lua vim.diagnostic.jump({count=-1, float=true})<CR>",
    bufopts
  )
  vim.keymap.set(
    "n",
    "]d",
    "<cmd>lua vim.diagnostic.jump({count=-1, float=true})<CR>",
    bufopts
  )
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

-- vim.lsp.log.set_format_func(function(item)
-- 	return (vim.inspect(item):gsub("[\r\n]+", ""))
-- end)

vim.api.nvim_create_user_command("LspLog", function()
  vim.cmd(string.format("edit %s", vim.lsp.get_log_path()))
end, {
  desc = "Opens the Nvim LSP client log.",
})

vim.api.nvim_create_user_command("LspInfo", function()
  vim.cmd("vertical checkhealth vim.lsp")
end, {})
