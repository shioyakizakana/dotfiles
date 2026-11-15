local M = {}
local node_markers = { "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock" }

function M.deno_root(bufnr)
  local deno = vim.fs.root(bufnr, { "deno.json", "deno.jsonc", "deno.lock" })
  local node = vim.fs.root(bufnr, node_markers)
  -- 入れ子のNodeプロジェクトでは、そのlockfileを境界にする。
  if deno and (not node or #deno >= #node) then
    return deno
  end
end

function M.typescript_root(bufnr)
  if M.deno_root(bufnr) then
    return
  end
  return vim.fs.root(bufnr, { node_markers, { ".git" } }) or vim.fn.getcwd()
end

return M
