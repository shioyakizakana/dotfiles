local function is_file_too_large(bufnr)
  local size = vim.api.nvim_buf_line_count(bufnr)
  return size > 10000
end

local function is_minified_file(bufnr)
  for i = 0, 5 do
    local lines = vim.api.nvim_buf_get_lines(bufnr, i, i + 1, false)
    if #lines == 0 then
      return false
    end
    if #lines[1] > 300 then
      return true
    end
  end
  return false
end

---@module "lazy"
---@type LazyPluginSpec[]
return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    build = ":TSUpdate",
    lazy = false,

    config = function()
      local language_list = {
        "lua",
        "vim",
        "vimdoc",
        "query",
        "python",
        "go",
        "javascript",
        "typescript",
        "powershell",
        "markdown",
        "rust",
      }
      require("nvim-treesitter").install(language_list)

      local filetypes = {}
      for _, lang in ipairs(require("nvim-treesitter").get_available(2)) do
        for _, filetype in ipairs(vim.treesitter.language.get_filetypes(lang)) do
          table.insert(filetypes, filetype)
        end
      end

      -- ハイライトとインデント
      vim.api.nvim_create_autocmd("FileType", {
        pattern = filetypes,
        group = vim.api.nvim_create_augroup("vim-treesitter-start", {}),
        callback = function(ctx)
          local bufnr = ctx.buf
          if is_minified_file(bufnr) or is_file_too_large(bufnr) then
            return
          end
          pcall(vim.treesitter.start)
          vim.wo.foldexpr = "v:lua.vim.treesitter.foldexpr()"
          vim.bo.indentexpr = "v:lua.require('nvim-treesitter').indentexpr()"
        end,
      })
    end,
  },

  {
    "nvim-treesitter/nvim-treesitter-context",
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    event = { "BufNewFile", "BufRead" },
    keys = {
      { "<space>tc", ":TSContext toggle<CR>" },
    },
    opts = {
      max_lines = 3,
      min_window_height = 30,
      on_attach = function(bufnr)
        -- quickerではオフにする
        return vim.bo[bufnr].filetype ~= "qf"
      end,
    },
  },
}
