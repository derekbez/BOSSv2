# Mini-Apps External Requirements & Integration Details

Purpose: authoritative reference for external APIs used by mini-apps, required environment
variables, headers, rate limits, fallback behavior, and validation checks. Keep this in
sync with actual code. When adding a new API, append a row and a subsection.

Legend:
- Env Var: variable expected in process environment (read via `api.get_config_value`) if not
	supplied in manifest `config.api_key`.
- Header Example: minimal required headers.
- Rate Limit: free tier guidance (approximate – verify with provider docs).
- Fallback: behavior when key missing / request fails (must be user-friendly, no tracebacks on screen).

| App | API / Source | Env Var | Auth Type | Header Example | Rate Limit (free) | Fallback Behavior | Notes |
|-----|--------------|---------|-----------|----------------|------------------|-------------------|-------|
| quote_of_the_day | Quotable / (optional They Said So) | THEYSAIDSO_API_KEY (optional) | Key (optional) | `X-Api-Key: <key>` (TheySaidSo) | ~10/min (TheySaidSo) | Show local error line | Currently using Quotable (no key) |
| breaking_news | NewsData.io | NEWSDATA_API_KEY | Key | n/a (query param) | 200 req/day | Friendly "(no news / network error)" | Could add GNews alt later |
| flights_leaving_heathrow | Aviationstack | AVIATIONSTACK_API_KEY | Key | n/a (query param) | 500 req/mo (free) | "(no data / error)" | Share key w/ flight_status app |
| flight_status_favorite_airline | Aviationstack | AVIATIONSTACK_API_KEY | Key | n/a | 500 req/mo | Same as above | Deduplicate calls via refresh interval |
| bird_sightings_near_me | eBird recent observations | EBIRD_API_TOKEN | Token | `X-eBirdApiToken: <token>` | ~10 req/sec (soft) | "(no data / network error)" | Consider region limiting |
| word_of_the_day | Wordnik | WORDNIK_API_KEY | Key | n/a | 1000 req/day | "(error/ no data)" | Cache half-day |
| moon_phase | ipgeolocation.io astronomy | IPGEO_API_KEY | Key | n/a | 1000 req/day | "(error/no data)" | Refresh every 6h |
| today_in_music | Last.fm tag top track | LASTFM_API_KEY | Key | n/a | 5 req/sec | "(error/no data)" | Hourly refresh |
| space_update | NASA (APOD / Mars) | NASA_API_KEY | Key | n/a | 30 req/hr (DEMO_KEY lower) | "(error/no data)" or fallback to DEMO_KEY | Prefer real key for reliability |
| local_tide_times | WorldTides | WORLDTIDES_API_KEY | Key | n/a | 4 req/hr (free) | "(error/no data)" | 3h refresh reduces usage |
| dad_joke_generator | icanhazdadjoke | (none) | None | `Accept: application/json` | Unspecified (light) | "(network error)" | Add UA if throttled |
| joke_of_the_moment | JokeAPI | (none) | None/Query | n/a | Generous | "(error/no data)" | Respect blacklist flags |
| name_that_animal | Zoo Animal API | (none) | None | n/a | Unspecified | "(error/no data)" | Basic JSON |
| color_of_the_day | ColourLovers | (none) | None | n/a | Low (cache encouraged) | "(network error)" | XML parsing; daily refresh |
| on_this_day | byabbe.se | (none) | None | n/a | Unspecified | "(no events / error)" | Half-day refresh control |
| tiny_poem | Poemist | (none) | None | n/a | Unspecified | "(error/no data)" | 3h refresh |
| space_update (Mars) | NASA Mars Rover | NASA_API_KEY | Key | n/a | Shared with APOD | Same fallback | Combined row above covers both |
| top_trending_search | Local backend (Google Trends) | (backend managed) | Depends | n/a | Local | "(no trend / error)" | Document backend separately |
| internet_speed_check | speedtest-cli (future) | (none) | None | n/a | CLI tool executes | Placeholder static values | TODO: integrate library |
| public_domain_book_snippet | Local assets | (none) | None | n/a | n/a | "(no book files)" | Verify asset presence |
| random_local_place_name | Local assets | (none) | None | n/a | n/a | Fallback default list | Provide curated list |
| random_emoji_combo | Local assets | (none) | None | n/a | n/a | Built-in fallback list | Provide emoji.json |
| constellation_of_the_night | Placeholder/local dataset | (future) | TBD | n/a | n/a | Static message | Marked placeholder |

## Environment Variable Naming Conventions
- Use ALL_CAPS snake case. Suffix with `_API_KEY` or `_API_TOKEN`.
- App code: first check manifest `config.api_key`, then `api.get_config_value(<ENVVAR>)`.
- Provide sample `.env.example` (future task) drawing from this table.

## Implementation Guidelines
1. Always set an explicit `timeout` (<= 6s) on network calls.
2. Provide a single-line, user-friendly fallback; avoid raw exception text.
3. Keep refresh intervals >= practical minimal interval to respect rate limits (see table).
4. Batch or cache where documented (tides, word_of_the_day, moon_phase, NASA, history events).
5. For token-in-header APIs (eBird) include proper header key exactly as specified.
6. Do not raise inside app loop; handle errors and continue.

## Fallback & Offline Strategy
- If env var absent and a public demo key exists (NASA), attempt with demo; else display message.
- If repeated failures occur, extend next refresh interval exponentially (future enhancement).

## Validation Checklist (Per API App)
- [ ] Manifest declares `requires_network: true`.
- [ ] Timeout constant or config present.
- [ ] Error path writes concise wrapped message.
- [ ] LED/button usage matches expected interactions.
- [ ] No direct `requests` call without timeout.
- [ ] Uses environment variable name from table (if auth app).

Update this file when adding/removing APIs or changing auth patterns.
