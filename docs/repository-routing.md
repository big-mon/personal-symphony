# Repository運用

設定・制約・課題ごとの実行手順は [`WORKFLOW.md`](../WORKFLOW.md) を正本とします。

## セットアップ・設定変更

1. 実プロセス・待受・課題キューを確認する。設定変更前に実行中のセッションの終了を待ち、WORKFLOW・helper・RUNBOOKを退避する。
2. 正本をもとに実行用WORKFLOWを用意し、[`scripts/repository_bootstrap.py`](../scripts/repository_bootstrap.py) を実行ユーザーの `~/.config/symphony/repository_bootstrap.py` へ配置する（Python 3.9以上）。
   WORKFLOWとhelperは同じ版を使い、変更時は無関係な設定を保持する。
   ホストとCodexのコマンド環境へ `LINEAR_API_KEY` を継承する。helperは標準の課題ディレクトリ名（`TEAM-123`）を使う。
3. [検証方針](validation.md)に従い、YAML・プロンプト展開・差分を確認して反映する。
4. 通常起動前にキューとcleanup対象を確認する。未完了の作業を破棄するかは人間が判断する。

## 実環境検証

専用課題・受付ラベル・別workspaceルート・別ポートを使う。
2つの対象の選択、失敗時のCodex未起動、再利用、PRの対象を確認し、削除・クローズには専用資材を使う。
静的確認・隔離検証・設定反映・通常稼働を区別して報告する。

起動停止・復旧手順と証跡はホスト側で管理する。認証情報・実プロジェクト識別子・登録パスを公開しない。
復旧はWORKFLOWとhelperを退避版へ揃え、対象変更だけを戻す。
