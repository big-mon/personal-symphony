---
name: linear
description: Use Symphony's linear_graphql tool for issue queries, state changes, comments, PR links, and uploads.
---

# Linear GraphQL

Use the `linear_graphql` tool in Symphony app-server sessions; it supplies the
configured auth. Send one operation per call as
`{"query": "<GraphQL document>", "variables": {"id": "<issue-id>"}}`.
Treat top-level `errors` or mutation `success: false` as failure. Request only
needed fields, and read back changed content/state to confirm the result.

## Find an issue

Start with its key or known internal ID:

```graphql
query Issue($id: String!) {
  issue(id: $id) {
    id identifier title description url branchName updatedAt
    state { id name type }
    project { id name }
  }
}
```

If identifier search is needed, use this fallback, then reuse the internal ID:

```graphql
query IssueByIdentifier($identifier: String!) {
  issues(filter: { identifier: { eq: $identifier } }, first: 1) {
    nodes { id identifier title }
  }
}
```

Add `attachments { nodes { id title url sourceType } }` or
`links { nodes { id url title } }` to the issue selection when inspecting links.

## Change state

Read the issue's team states first; use the exact destination ID, subject to the
runtime workflow's ownership and transition rules:

```graphql
query IssueTeamStates($id: String!) {
  issue(id: $id) {
    team { id key name states { nodes { id name type } } }
  }
}
```

```graphql
mutation MoveIssue($id: String!, $stateId: String!) {
  issueUpdate(id: $id, input: { stateId: $stateId }) {
    success
    issue { id identifier state { id name } }
  }
}
```

## Comments

```graphql
mutation CreateComment($issueId: String!, $body: String!) {
  commentCreate(input: { issueId: $issueId, body: $body }) {
    success
    comment { id url }
  }
}
```

```graphql
mutation UpdateComment($id: String!, $body: String!) {
  commentUpdate(id: $id, input: { body: $body }) {
    success
    comment { id body }
  }
}
```

## PR and URL attachments

Prefer the GitHub-specific operation for PR link metadata:

```graphql
mutation AttachGitHubPR($issueId: String!, $url: String!, $title: String) {
  attachmentLinkGitHubPR(
    issueId: $issueId, url: $url, title: $title, linkKind: links
  ) {
    success
    attachment { id title url }
  }
}
```

For a plain URL, use
`attachmentLinkURL(issueId: $issueId, url: $url, title: $title)` with the same
variables and result selection.

## Upload media

1. Request a signed upload URL:

   ```graphql
   mutation FileUpload(
     $filename: String!, $contentType: String!, $size: Int!, $makePublic: Boolean
   ) {
     fileUpload(
       filename: $filename, contentType: $contentType,
       size: $size, makePublic: $makePublic
     ) {
       success
       uploadFile { uploadUrl assetUrl headers { key value } }
     }
   }
   ```

2. Upload the local bytes with `curl -X PUT` using the exact returned headers and
   signed `uploadUrl`. Confirm the upload succeeds.
3. Include `assetUrl` in `commentCreate` or `commentUpdate`.

Use shell only for the signed upload, not raw-token GraphQL helpers.

## Discover unfamiliar operations

Use targeted introspection when a field, mutation, or input shape is unclear:

```graphql
query InputShape($name: String!) {
  __type(name: $name) {
    inputFields { name type { kind name ofType { kind name } } }
  }
}
```

Use an input name such as `CommentCreateInput`. For available operations, query
`__type(name: "Mutation") { fields { name } }` (or `"Query"`). For argument types,
select `fields { name args { name type { kind name ofType { kind name } } } }`;
expand `ofType` as needed. Discover only the missing schema information.
