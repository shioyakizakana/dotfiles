---@module "lazy"
---@type LazyPluginSpec[]
return {

  {
    "vim-denops/denops.vim", lazy = false,
  },
  -- ddc.vimおよびpum.vimのインストール
  {
    "Shougo/ddc.vim",
    "Shougo/pum.vim",
    "Shougo/ddc-ui-pum", -- ddc.vimの候補表示にpum.vimを使用するためのプラグイン
  },
  {
    "delphinus/skkeleton_indicator.nvim", -- SKKの状態をステータスラインに表示するためのプラグイン
    cond = not vim.g.vscode,
    config = function()
        require("skkeleton_indicator").setup {}
    end,
  },

  {
    -- SKK入力を提供するプラグイン
    "vim-skk/skkeleton",
    cond = not vim.g.vscode,
    dependencies = {
        "vim-denops/denops.vim",
        "Shougo/ddc.vim",
        "Shougo/pum.vim",
        "k16em/skkeleton-azik-kanatable", -- SKKのかなテーブルを提供するプラグイン
    },

    -- SKKの変換の基本
    -- 変換したい単語の最初の文字をShiftを押しながら入力
    -- 単語の終わりの文字入力後にSpaceキーをタイプして変換処理の開始

    config = function()
      vim.fn["skkeleton#azik#add_table"]("us") -- azikのかなテーブルを追加
      -- skkeletonの設定
      vim.fn["skkeleton#config"]({
        kanaTable             = "azik",
        globalDictionaries    = {
          vim.fn["expand"]("~/skk-dic/SKK-JISYO.L"),
          vim.fn["expand"]("~/skk-dic/SKK-JISYO.jinmei"),
          vim.fn["expand"]("~/skk-dic/SKK-JISYO.fullname"),
          vim.fn["expand"]("~/skk-dic/SKK-JISYO.geo"),
          vim.fn["expand"]("~/skk-dic/SKK-JISYO.station"),
          vim.fn["expand"]("~/skk-dic/SKK-JISYO.propernoun"),
        },
        completionRankFile    = vim.fn["expand"]("~/skk-dic/rank.json"),
        eggLikeNewline        = true, --変換候補を選んでEnterキーをタイプしたときに確定のみ行う
        keepState             = true, -- Insert Modeを抜けても skkeleton の有効/無効の状態を保持する
        showCandidatesCount   = 2,    -- 2回目までの変換では複数の変換候補を表示しない
        registerConvertResult = true,
      })

      require("plugins.skkeleton.ddc")

      require("plugins.skkeleton.keymaps")
    end,
  },
}
