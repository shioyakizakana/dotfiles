-- 基本設定

-- telescope.nvimと競合するため無効化
vim.api.nvim_set_var("loaded_netrw", 1)
vim.api.nvim_set_var("loaded_netrwPlugin", 1)
-- タイムアウトの設定
vim.opt.timeoutlen = 500

-- 言語設定
vim.cmd.language("ja_JP.utf8")
vim.opt.helplang = "ja"
if vim.fn.has("gui_running") == 1 then
    vim.o.guifont = "HackGen Console NF:h14"
end
local function to_boolean(val)

  if val == nil then return false end
  if type(val) == "boolean" then return val end
  if type(val) == "string" then

    if val == "false" or val == "0" or val == "" then

      return false
    end
  end
  if val == 0 then return false end

  return true
end

-- 現在のキーマップをKEYMAPS.mdとして出力
vim.api.nvim_create_user_command("ExportKeymaps", function ()

  local modes = {
    n = "Normal",
    i = "Insert",
    v = "Visual(including Select)",
    t = "Terminal",
    o = "Operator",
    c = "Cmd-line"
  }

  local lines = {}

  table.insert(lines, "# Neovim Keymaps")
  table.insert(lines, "")

  for mode, title in pairs(modes) do

    table.insert(lines, "## "..title.." Mode")
    table.insert(lines, "")
    table.insert(lines, "| Key | Desc | RHS | Callback | Noremap | Silent | Expr | Nowait |")
    table.insert(lines, "|-----|-----|-----|-----|-----|-----|-----|-----|")

    local maps = vim.api.nvim_get_keymap(mode)

    table.sort(maps, function(a, b)
      return a.lhs < b.lhs
    end)

    for _, map in ipairs(maps) do

      table.insert(
        lines,
        string.format(
          "| `%s` | %s | `%s` | %s | %s | %s | %s | %s |",
          map.lhs or "",
          map.desc or "",
          map.rhs or "",
          map.callback and "Yes" or "No",
          to_boolean(map.noremap),
          to_boolean(map.silent),
          to_boolean(map.expr),
          to_boolean(map.nowait)
        )
      )
    end

    table.insert(lines, "")
  end

  local outfile = vim.fn.stdpath("config") .. "/KEYMAPS.md"

  vim.fn.writefile(lines, outfile)

  vim.notify("Exported: " .. outfile)
end, {})
