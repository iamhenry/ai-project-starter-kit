# Tools reference

## asc CLI (App Store Connect)

```bash
asc auth status --validate
asc apps list --output json                                   # find the app ID
asc status --app <APP_ID> --output json                       # live version, version ID, state
asc localizations list --app <APP_ID> --type app-info --output json   # title, subtitle
asc localizations list --version <VERSION_ID> --output json   # keywords, description, promo text
asc pricing current --app <APP_ID>

# Draft a version (step 8). Never submit.
asc builds list --app <APP_ID> --output json                  # pick a VALID build; user confirms
asc versions list --app <APP_ID> --output json                # reuse an existing PREPARE_FOR_SUBMISSION draft
asc versions create --app <APP_ID> --version <X.Y.Z> --copy-metadata-from <LIVE_VERSION> --release-type MANUAL
asc versions attach-build --version-id <VERSION_ID> --build-id <BUILD_ID>
asc localizations update --version <VERSION_ID> --locale en-US --keywords "..." --promotional-text "..." --whats-new "..."
asc localizations update --app <APP_ID> --type app-info --locale en-US --name "..." --subtitle "..."   # targets the editable app info
asc screenshots list --app <APP_ID> --version <X.Y.Z> --locale en-US   # compare counts with the live version
```

`--release-type MANUAL` is an example; copy the live version's release type and copyright.

Analytics (`asc analytics ...`) needs an API key with the Analytics/Sales role and a vendor number. If it returns forbidden, ask the user for App Store Connect screenshots: Analytics → Overview (window = test window) and Acquisition → Sources filtered to App Store Search.

## Astro MCP

If Astro is a native MCP tool in this session, call it directly. Otherwise call it over HTTP (for example inside a code runner):

```js
const res = await fetch(ASTRO_URL, {
  method: 'POST',
  headers: {
    'content-type': 'application/json',
    accept: 'application/json, text/event-stream',
    'mcp-session-id': SESSION_ID, // from an initialize call, or a known working session
  },
  body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call',
    params: { name: 'search_app_store', arguments: { keyword: 'read later', store: 'us', limit: 10 } } }),
});
// result.content[0].text is a JSON string
```

Tools used by this skill:

| Tool | Use |
|---|---|
| `list_apps` | Find tracked apps and Astro IDs |
| `add_app` | `appStoreId`, `platform: "iphone"`, `store`; `temporary: true` for a research app |
| `add_keywords` | `keywords[]`, `store`, `appId`, `platform`; batches ≤ 30 (larger ones time out client-side but may still finish — wait ~90 s and re-check) |
| `get_app_keywords` | Popularity, difficulty, rank for every tracked phrase |
| `get_keyword_performance` | `keyword`, `store`, `includeHistory: true` — rank history for the day-5/day-14 check |
| `search_app_store` | Live top results (max 50) with rating counts; count small apps here. Run sequentially |
| `extract_competitors_keywords` | Phrases the top apps for a seed rank on, with popularity |
| `get_keyword_suggestions` | More ideas for an app |
| `get_app_ratings` | Rating count and history |
| `manage_tag`, `set_keyword_tag`, `set_keyword_note` | Buckets and notes for human audit |

Rank 1000 in Astro means "not in the top results" — report it as "not in top 50", never as a number.

Save raw responses you rely on to `runs/YYYY-MM-DD/evidence.json` so numbers in the proposal can be traced.
