# Repositoryラベルで作業先を選ぶ

Linear の `Repository` ラベルグループから子ラベルを1つ選びます。
対象のローカルGitリポジトリは、実行ユーザーの `~/Repos/<子ラベル名>` です。
例えば `example-app` なら `~/Repos/example-app`。説明欄は取得・解釈しません。

ラベル名は英数字で始まり、英数字・`_`・`.`・`-` だけの単一ディレクトリ名にします。
`owner/repo`、`..`、絶対パス、シェル構文は受け付けず、対応するディレクトリが
なければ停止します。symlinkの解決先も `~/Repos` の直下に限定します。

登録先は読み取り専用の参照元です。Gitルートであることと、単一の `origin` の
fetch/push先が一致することを確認します。対応するoriginは認証情報を含まない
`https://github.com/OWNER/REPO[.git]` または `git@github.com:OWNER/REPO[.git]`。
ローカルの未コミット変更は持ち込まず、そのoriginから課題専用の `repo/` にcloneします。
認証は既存のGit/GitHub設定で行い、URLへトークンを埋め込みません。

## WORKFLOWだけで成立する構成

ルートの [`WORKFLOW.md`](../WORKFLOW.md) が設定と実行手順の正本です。
`after_create` の固定cloneを外し、空ディレクトリから起動したCodexが、
注入された `linear_graphql` で課題ラベルの名前と親グループを取得します。
外部のbootstrapヘルパーやElixir本体の変更は不要です。
Python 3.9以上の標準ライブラリを使う検証コードをWORKFLOWに含め、
Codexが作業ルートの一時ファイルへそのまま保存して実行します。
コードはラベル値をシェルへ展開せず、Gitには引数配列で渡します。

ラベル取得は課題UUIDを指定し、全ページを取得します。親が `Repository` の子を
厳密に1つ要求し、取得失敗、部分的なGraphQLエラー、ページ欠落、重複、
ページ取得中の課題更新を停止理由にします。表示用の `issue.labels` は使いません。

作業ルートの `.repository-binding.json` に課題・ラベル・親のID、ラベル名、解決済みパス、
検証済みoriginを保存します。再試行時もLinearから取り直し、この記録と
cloneのfetch/push originが一致する場合だけ再利用します。
未コミット変更は保持します。対象変更、未登録の既存clone、壊れたclone、
不完全なbindingや旧形式のbindingは自動修復せず、Human Reviewへ引き渡します。
ラベル取得自体ができなければ停止理由をローカルに残します。

各ターン・継続・再試行の開始時とcommit/push/PR操作直前に再検証します。
これはエージェントが守る手順であり、サーバー側の実行禁止機構ではありません。
Linearの更新とGitHubへの書き込みを原子的にロックする仕組みはありません。
作業中の対象変更は止めて人間が扱い、別リポジトリに差分を移しません。

空のremoteも有効な未コミットのcloneとして保持します。ただしPRのbase branchが
存在しなければ人間へ引き渡し、default branchへ直接pushしてレビューを迂回しません。
実行対象の状態はSymphonyが設定から判定し、Repository検証コードには重複定義しません。

clone後は対象側のAGENTSと開発手順を読みます。PR操作にはbindingの
`owner/repo` を必ず明示し、添付済みPRも対象一致を確認します。
作成後にURL・base repository・head SHAを読み返して照合します。
人間がマージ・課題完了を担当し、終了時の標準cleanupは課題workspaceだけを
削除します。`before_remove` でPRを閉じる処理はありません。

## 既存運用へ差分適用する

1. 起動中のプロセス、待受ポート、実行・再試行中の課題を確認します。
   作業中のセッションを残したまま切り替えません。実運用WORKFLOWとRUNBOOKを退避します。
2. WORKFLOWの `after_create` の固定clone/setup、リポジトリ依存の
   `before_run` / `after_run` / `before_remove` を削除します。
   新しいテンプレートでは `hooks: {}`。必要な独自フックは依存と副作用を確認します。
3. 本文にルートWORKFLOWのRepository bootstrap全体を追加し、
   すべての実装・PR操作より前に実行させます。clone先は `repo/`。
   固定リポジトリ、Elixir専用setup、固定default branch、必須のローカルskill、
   自動PRクローズ／既存作業の削除と矛盾する指示を直します。
   状態遷移は状態判定の手順、workpad規則は作成・更新の手順に集約します。
   別の状態一覧やGuardrailsに同じ規則を重ねず、必要な箇所から参照します。
4. tracker、対象プロジェクト、認証参照、モデル、課金、並列数、ポーリング、
   workspaceルート、sandbox、人間によるマージ方針は保持します。
   権限不足を回避するためにエージェント自身がsandboxを変更してはいけません。
5. YAMLとLiquidのrendering、変更差分を確認します。既存のルート直下cloneは
   自動移行しません。残す差分・PRを人間が確認してからworkspaceを整理します。
6. 専用の検証ラベル／課題と別workspaceルート・別ポートを使って起動します。
   元プロジェクトを使う場合も `required_labels` で検証課題だけに限定します。
   終了状態の既存課題を含め、cleanup対象も別ルートの外に出ないことを確認します。
7. 成功後、実運用ファイルへ同じ差分を反映します。サービスの通常起動は、
   キューを確認してから行います。設定の反映と通常課題の実行成功は別の結果です。
   RUNBOOKには現行の前提・起動停止・復旧手順を残し、過去のPID・SHAや検証経緯は
   ホスト側の証跡へ退避してリンクします。

rollbackは退避との差分から今回の変更だけを戻します。`repo/` 構成のworkspaceを
旧固定clone運用へ自動で引き継がせず、人間が保存・退避を判断してください。

## 検証と証跡

自動チェック：`python3 tests/test_repository_workflow.py`。
WORKFLOW内のコードそのものを抽出し、2つの専用Git fixtureでclone先の選択、
再試行と未コミット変更の保持、対象変更の拒否、ページ欠落・取得エラー、
未指定・複数・不正ラベル、origin不一致、途中clone、旧workspace、入力非実行を検証します。
Git通信だけをローカルfixtureへ接続し、実運用の認証やGitHubは使いません。

実環境では、配布版エンジンから空ディレクトリでCodexを起動し、注入ツールの
ページングを含む実レスポンスを確認します。異なる2つの登録ラベルでclone先を
確認し、専用リポジトリでのみcommit/push/PR作成と必要なクローズを試します。
再試行・ラベル変更・失敗ケースは専用workspaceで行い、通常課題を使いません。
PRを削除・クローズする検証が必要でも通常PRには触れません。

レポートでは「静的確認・ローカルfixture」「隔離した実環境」
「運用ファイル反映」「通常キュー稼働」を分けます。実プロジェクトID、
認証情報、検証用のローカル絶対パスは公開文書に記載せず、ホストの証跡に残します。
