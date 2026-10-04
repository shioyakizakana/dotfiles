-- https://github.com/golang/tools/blob/v0.23.0/gopls/doc/vim.md#neovim-imports
-- LSP Code Action
--
-- Diagnostic:
--   Diagnosticが存在する場合は、そのままCode Actionを実行する
--   Diagnosticがまだ存在しない場合だけ、DiagnosticChangedを一度待つ。
--
-- Source:
--   ファイル全体を対象とするCode Actionを現在のバッファに対して
--   一度だけ実行する

local M = {}


-- ====================================================
-- 設定
-- ====================================================
local code_actions = {
  -- Diagnosticの位置ごとに実行 
  diagnostic = {
    javascript = {
      "quickfix.biome.style.useImportType",
    },
    typescript = {
      "quickfix.biome.style.useImportType",
    },
    javascriptreact = {
      "quickfix.biome.style.useImportType",
    },
    typescriptreact = {
      "quickfix.biome.style.useImportType",
    },
  },
  -- 全体のバッファに対して一度だけ実行
  source = {
    go = {
      "source.organizeImports",
    },
  },
}

-- DiacnosticChangedの最大待機時間
local diagnostics_wait_timeout = 3000
-- モジュールの読み込み時に一度だけ作成
-- 実際の待機処理ではautocmdだけを一時的に削除する
local wait_group = vim.api.nvim_create_augroup(
  "MyCodeActionWait",
  { clear = true }
)
-- ====================================================
-- 共通処理
-- ====================================================
---@param kinds string[]
---@return boolean
local function has_code_action(kinds)
  return kinds and #kinds > 0
end

---@param kinds string[]
local function apply_code_actions(kinds)
  if not has_code_action(kinds) then
    return
  end

  vim.lsp.buf.code_action({
    -- 選択UIを表示せず条件に一致したCode Actionを適用
    apply = true,
    -- 指定したCode Action kindだけを対象にする
    context = {
      only = kinds,
    },
  })
end

---@param kind "diagnostic"|"source"
---@return string[]|nil
local function get_code_action_kinds(kind)
  local filetype = vim.bo.filetype

  return code_actions[kind][filetype]
end

-- ====================================================
-- Diagnostic Code Actions
-- ====================================================
-- ----------------------------------------------------
-- DiacnosticChanged
-- ----------------------------------------------------
---@param bufnr integer
---@param callback function
local function wait_for_diagnostics(bufnr, callback)

  local finished = false
  local timer = vim.uv.new_timer()

  local function finish()
    if finished then
      return
    end

    finished =true
    -- タイマーを停止/破棄
    if timer then
      timer:stop()
      timer:close()
      timer = nil
    end

    vim.api.nvim_clear_autocmds({
      group = wait_group,
      buffer = bufnr,
    })

    callback()
  end

  -- Diagnsticが更新されたときだけ処理
  vim.api.nvim_create_autocmd("DiagnosticChanged", {
    group = wait_group,
    buffer = bufnr,
    callback = function(ev)
      if ev.buf ~= bufnr then
        return
      end

      local diagnostics = ev.data and ev.data.diagnostics or {}

      if #diagnostics == 0 then
        return
      end

      finish()
    end,
  })

  -- LSPがDiagnosticを返さない場合に備えてタイムアウトを設定
  timer:start(
    diagnostics_wait_timeout,
    0,
    vim.schedule_wrap(function()
      finish()
    end)
  )
end

-- ----------------------------------------------------
-- Diagnostic Code Action
-- ----------------------------------------------------
function M.apply_diagnostic_actions()
  local kinds = get_code_action_kinds("diagnostic")

  if not has_code_action(kinds) then
    vim.notify(
      ("Diagnostic用Code Actionが設定されていません: %s")
        :format(vim.bo.filetype),
      vim.log.levels.INFO
    )
    return
  end

  local bufnr = vim.api.nvim_get_current_buf()
  local diagnostics = vim.diagnostic.get(bufnr)

  -- 既にDiagnosticがある場合は待機しない
  --Note: diagnosticsが「まだない」のか「0件なのか」の区別が不完全
  if #diagnostics > 0 then
    M._run_diagnostic_actions()
    return
  end

  -- LSPからのDiagnostic更新を待機
  wait_for_diagnostics(bufnr, function()

    -- Neovimのイベントループに処理を戻してから実行
    vim.schedule(function()
      M._run_diagnostic_actions()
    end)
  end)
end

-- Diagnsticの準備が完了した後に呼び出される
function M._run_diagnostic_actions()

  local kinds = get_code_action_kinds("diagnostic")

  if not has_code_action(kinds) then
    return
  end
  -- 現在のDiagnscticをlocation-listへ設定
  vim.diagnostic.setloclist(
    ---@vim.diagnostics.setloclist.Opts
    {
      open = false
    }
  )
  -- location-listの各項目に移動しながら対象のCodeActionを実行
  vim.cmd("ldo call v:lua.require('plugins.lsp.code-actions')._apply_diagnostic()")
  vim.cmd("lclose")
end

function M._apply_diagnostic()
  local kinds = get_code_action_kinds("diagnostic")

  if not has_code_action(kinds) then
    return
  end

  apply_code_actions(kinds)
end

-- ====================================================
-- Source Code Actions
-- ====================================================
function M.apply_source_actions()
  local kinds = get_code_action_kinds("source")

  if not has_code_action(kinds) then
    vim.notify(
      ("Source用Code Actionが設定されていません: %s")
        :format(vim.bo.filetype),
      vim.log.levels.INFO
    )
    return
  end

  apply_code_actions(kinds)
end

-- ====================================================
-- User commands
-- ====================================================
vim.api.nvim_create_user_command("MyDiagnosticAction", function()
  M.apply_diagnostic_actions()
end, {
  desc = "Diagnosticに対するCode Actionsを一括適用",
})

vim.api.nvim_create_user_command("MySourceAction", function()
  M.apply_source_actions()
end, {
  desc = "Source Code Actionをカレントバッファに適用",
})

return M
