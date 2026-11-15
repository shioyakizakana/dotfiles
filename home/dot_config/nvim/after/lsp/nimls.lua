-- PATHを優先し、非対話起動でもNimbleの既存バイナリを利用できるようにする。
local command = "nimlsp"
if vim.fn.executable(command) == 0 then
  local nimble_dir = vim.env.NIMBLE_DIR
  if not nimble_dir or nimble_dir == "" then
    nimble_dir = vim.fn.expand("~/.nimble")
  end
  local candidate = vim.fs.joinpath(nimble_dir, "bin", "nimlsp")
  if vim.fn.executable(candidate) == 1 then
    command = candidate
  end
end

---@type vim.lsp.Config
return {
  cmd = { command },
  filetypes = { "nim" },
}
