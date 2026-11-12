# 展開ソースの規約

パスはリポジトリルート基準とする。

- この配下をホームへ展開するソースとして編集し、共通スキルとプロジェクト専用スキルの配置を混同しない。
- テンプレートのデータ構造・Go template構文・既存変数を維持し、未定義値を無条件参照せず、変更時は全参照を確認する。
- machineType・linuxEnvと既存フラグを使い、OSとTermux・proot・WSL等の実行環境を区別する。
- systemd・keyring・Secret Serviceを前提にせず、環境固有の処理を分離する。
- 既存のProton PassラッパーとPAT/keyring切替、ageの保管設計を維持する。
- ツールはmiseを優先し、導入担当を無断で移さず、版変更時は互換性を確認する。
- Linux対応スクリプトを優先し、シェル・GNUオプション・CPU・パスの差を確認して対象環境で動く実装を選ぶ。
- 配置説明はREADME.md、環境差はdocs/testing/environment-matrix.mdを参照する。
