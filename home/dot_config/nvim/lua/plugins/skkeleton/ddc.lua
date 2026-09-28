-- ddc.vimの設定
-- ddc.vimのソースにskkeletonを追加
vim.cmd([[ call ddc#custom#patch_global("sources", ["skkeleton"]) ]])
-- ddc.vimのソースオプションの設定
vim.cmd([[ call ddc#custom#patch_global("sourceOptions", {
  \ "_": {
  \   "matchers": ["matcher_head"],
  \   "sorters": ["sorter_rank"],
  \ },
  \ "skkeleton": {
  \   "mark": "skkeleton",
  \   "matchers": [],
  \   "sorters": [],
  \   "converters": [],
  \   "isVolatile": v:true,
  \   "minAutoCompleteLength": 1,
  \ }
  \})
]])


-- ddc.vimを有効化
vim.cmd([[ call ddc#enable() ]])
-- ddc.vimのUIにpum.vimを使用するための設定
vim.cmd([[ call ddc#custom#patch_global("ui", "pum") ]])
