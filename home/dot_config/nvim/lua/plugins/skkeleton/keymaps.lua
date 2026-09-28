-- skkeletonの有効無効をトグル
vim.keymap.set(
  { "i", "c", "t" },
  "<C-j>",
  "<Plug>(skkeleton-toggle)", { noremap = false }
)
-- pum.vimの候補を次に移動
vim.keymap.set(
  { "i", "c" },
  "<C-n>",
  "<cmd>call pum#map#insert_relative(+1)<CR>"
)
-- pum.vimの候補を前に移動
vim.keymap.set(
  { "i", "c" },
  "<C-p>",
  "<cmd>call pum#map#insert_relative(-1)<CR>"
)
-- pum.vimの候補を確定
vim.keymap.set(
  { "i", "c" },
  "<C-y>",
  "<cmd>call pum#map#confirm()<CR>"
)
-- pum.vimの候補をキャンセル
vim.keymap.set(
  { "i", "c" },
  "<C-e>",
  "<cmd>call pum#map#cancel()<CR>"
)

