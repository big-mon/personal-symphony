# Personal Symphony

Linear の課題を受け取り、Codex が実装・検証・PR作成まで進める OpenAI Symphony のフォークです。
レビュー・マージ・課題の完了は人間が行います。

> 信頼できる環境での試用を想定しています。作業ディレクトリの分離はセキュリティ上の隔離ではありません。
> 実行権限は使用するワークフローに依存します。[権限ガイド](docs/git-permissions.md)を確認してください。

<a id="running-this-fork"></a>

## 使い始める

このリポジトリを開いたAIエージェントに、セットアップや制約の確認を依頼してください。
設定・実行手順の正本は [`WORKFLOW.md`](WORKFLOW.md)、セットアップ・設定変更は[運用手順](docs/repository-routing.md)です。
[配布バイナリ](https://github.com/big-mon/personal-symphony/releases)やソースからの起動は[Elixirガイド](elixir/README.md)を参照します。

Linear の `Repository` 子ラベルで、`~/Repos/<ラベル名>` にあるリポジトリを選びます。
Codex はそのoriginから課題専用のcloneを作り、PRを作成します。登録元のローカルリポジトリは変更しません。

## 開発

エージェントは [AGENTS.md](AGENTS.md) から、作業に必要な手順を参照してください。
`elixir/` はフォーク元で管理し、このフォーク固有の変更は原則としてその外側に置きます。

## ライセンス

[Apache License 2.0](LICENSE)。帰属表示は [NOTICE](NOTICE) を参照してください。
