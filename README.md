# Personal Symphony

Personal Symphony は、課題管理ツールと連携してコーディングエージェントを動かす、OpenAI Symphony のフォークです。
対象の課題ごとに専用の作業ディレクトリを用意し、Codex が実装と検証を進めます。

このフォークでは、人間がレビューする運用を採用しています。Codex はプルリクエスト（PR）を作成するところまで担当し、レビュー・マージ・課題の完了は人間が行います。

> [!WARNING]
> 信頼できる環境での試用を想定した実験的なソフトウェアです。
> 付属のワークフローでは、Codex に実行ユーザーと同じファイル・ネットワークへのアクセス権を与えます。
> 作業ディレクトリを分けても、セキュリティ上の隔離にはなりません。実行前に[権限ガイド](docs/git-permissions.md)を確認してください。

## 作業の流れ

1. 要件を整理した課題を、実行対象の状態に移します。
2. Symphony が課題管理ツールを定期的に確認し、課題ごとの作業ディレクトリを作成または再利用します。
3. Codex がワークフローとリポジトリの指示を読み、実装・検証を行い、検証結果を添えてPRを作成します。
4. 人間がPRをレビューします。修正が必要なら作業に戻し、承認した変更は人間がマージして課題を完了させます。

Elixir の実装は Linear、GitHub Issues、Jira Cloud、Asana、GitLab に対応しています。
現在の運用では Linear を使っていますが、連携先は変更できます。
対象課題、作業ディレクトリの準備、同時実行数、Codex への指示はワークフローで設定します。

[![Symphony のデモ動画](.github/media/symphony-demo-poster.jpg)](https://player.vimeo.com/video/1186371009?h=5626e4b899)

デモでは、エージェントが Linear の課題を受け取り、PRを作成する様子を紹介しています。

<a id="running-this-fork"></a>

## このフォークの起動方法

Git、認証済みの Codex CLI、連携する課題管理ツールの認証情報が必要です。
付属のフックでは、認証済みの GitHub CLI（`gh`）と、`mise` で管理する Elixir の実行環境も使います。
サービスを実行するユーザーで `gh auth status` が成功し、対象リポジトリへのpushとPRの作成・クローズができる権限を用意してください。
Git経由のpushと、非公開リポジトリをcloneする場合の認証も必要です。課題管理ツールの認証とは別に確認します。

実装と設定の詳細は[Elixir ガイド（英語）](elixir/README.md)を参照してください。
ソースコードと[配布バイナリ](https://github.com/big-mon/personal-symphony/releases)は、このフォークのものを使います。
ソースコードからビルドする場合は、次を実行します。

```bash
git clone https://github.com/big-mon/personal-symphony
cd personal-symphony/elixir
mise trust
mise install
mise exec -- mix setup
mise exec -- mix build
```

### 課題管理ツールとワークフローを設定する

`elixir/WORKFLOW.md` をチェックアウト先の外にコピーし、実行用ファイルとして使います。
課題ごとの作業ディレクトリも、チェックアウト先とは別に指定してください。
連携先に応じて、次の設定ガイドを参照します。
[Linear](elixir/README.md#linear-adapter-profile)、
[GitHub Issues](elixir/README.md#github-issues-adapter)、
[Jira Cloud](elixir/README.md#jira-cloud-adapter)、
[Asana](elixir/README.md#asana-adapter)、
[GitLab](elixir/README.md#gitlab-adapter)。

実行用ワークフローでは、次の項目を設定します。

- **冒頭のYAML設定**：`tracker.kind`、連携先のプロジェクトなどの対象範囲、認証情報、対応する実行対象・終了状態を指定します。認証情報は、サービスの環境変数やホスト側のシークレット参照で渡します。
- **リポジトリ用フック**：`hooks.after_create` のclone先と、`hooks.before_remove` のPR操作先を対象リポジトリに合わせます。このフォークでは、clone先を `https://github.com/big-mon/personal-symphony` にし、削除前のMixタスクに `--repo big-mon/personal-symphony` を指定します。テンプレートやMixタスクの既定値はフォーク元を指すため、どの課題管理ツールを使う場合も変更が必要です。
- **Markdown本文のプロンプト**：テンプレートにある Linear 用ツール・スキルの指定、作業記録やコメントの操作、状態遷移、PRの紐付け手順を、連携先に合う内容へ書き換えます。`tracker.kind` を変えるだけでは、本文の指示は切り替わりません。

連携先にかかわらず、Codex は実装・検証・PR作成を担当し、人間がマージと課題の完了を行います。
テンプレートの `Merging` への分岐や `land` の実行指示も、この方針に合わせて書き換えてください。
レビュー中は課題を終了状態にせず、エージェントの実行対象から外します。
open/closed のような状態しか扱えない連携先では、独自のレビュー状態を追加する代わりに、`tracker.required_labels` などの対応済みフィルターで実行対象を制御します。
下記の削除前フックは、課題が終了状態になった際に未マージのPRを閉じるため、承認した課題を完了させるのはPRのマージ後にしてください。

### Linear の設定例（現在の運用）

コピーしたワークフローの冒頭のYAMLに、次の設定を反映します。
`your-project-slug` はプレースホルダーです。Linear の対象プロジェクトURLで、`/project/` の直後にあるプロジェクト識別子へ置き換えてください。

```yaml
tracker:
  kind: linear
  provider:
    project_slug: your-project-slug
  active_states:
    - Todo
    - In Progress
    - Rework
hooks:
  after_create: |
    git clone --depth 1 https://github.com/big-mon/personal-symphony .
    if command -v mise >/dev/null 2>&1; then
      cd elixir && mise trust && mise exec -- mix deps.get
    fi
  before_remove: |
    cd elixir && mise exec -- mix workspace.before_remove --repo big-mon/personal-symphony
agent:
  max_concurrent_agents: 1
```

`LINEAR_API_KEY` はサービスの環境変数で渡します。
この例では、レビュー待ちに `Human Review`、修正作業に `Rework`、マージ後の完了に `Done` を使います。
これらの状態を Linear に用意し、作業ディレクトリを残すために `Human Review` は実行対象・終了状態のどちらにも含めないでください。
本文のプロンプトにも、前述の人間によるレビュー・マージ方針を反映します。

### サービスを起動する

`elixir/` から、設定済みの実行用ファイルと、CLIで必須の確認フラグを指定します。

```bash
mise exec -- ./bin/symphony /absolute/path/to/WORKFLOW.md \
  --i-understand-that-this-will-be-running-without-the-usual-guardrails
```

配布バイナリでも、同じファイルパスとフラグを指定できます。
ただし、付属のフックを使う場合は、作業を実行するホストに Elixir の実行環境と `gh` が必要です。
任意で有効にできる[Webダッシュボード](elixir/README.md#web-dashboard)では、実行中や対応待ちの課題を確認できます。

リポジトリ内の `elixir/WORKFLOW.md` はテンプレートです。
稼働中のサービスが読むのは、起動時に指定したファイルです。リポジトリを変更しただけでは、その実行用ファイルには反映されません。
認証情報は環境変数やホスト側のシークレット参照で管理してください。

## このリポジトリを変更するとき

`elixir/` 配下はフォーク元で管理されています。
このフォーク固有の文書・運用手順・スキル・CIは、その外側で管理します。
Elixir 側の変更は、明示的に必要なタスクに限定してください。

- [エージェント向け案内](AGENTS.md)：`elixir/` 外の作業に必要な手順への入口。
- [検証方針](docs/validation.md)：ローカルでの検証とPRの必須チェック。
- [Elixir ガイド（英語）](elixir/README.md)：設定、連携先ごとのアダプター、実環境でのテスト。
- [サービス仕様（英語）](SPEC.md)：実装言語によらない振る舞いの定義。
- [Git権限ガイド](docs/git-permissions.md)：運用への反映時の確認と、権限エラーへの対応。

## ライセンス

[Apache License 2.0](LICENSE) で公開しています。帰属表示は [NOTICE](NOTICE) を参照してください。
