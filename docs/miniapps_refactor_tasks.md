# Mini-Apps v2 Screen/API Migration Tracker

Purpose: Track mandatory refactors to align every mini-app with `miniapps_api_events_v2.md` (no legacy screen API, proper event usage, LED parity, secrets/env validation).

Status Legend:
- [ ] Not started
- [~] In progress / partial
- [x] Complete (PR merged)
- [blk] Blocked (note reason)

## Global Migration Requirements
1. Remove all uses of legacy screen methods: `write_line`, `write_wrapped`, `clear_body`, and any direct references to `width`/`height` on `api.screen` (except where provided by v2 if retained). Use ONLY:
   - `api.screen.display_text(text, **options)`
   - `api.screen.display_image(image, **options)` (if/when needed)
   - `api.screen.clear_screen()`
2. Consolidate multi-line formatting client-side (compose full text string with `\n`) instead of positional line writes.
3. Replace `any_button_pressed()` (unsupported) with event-driven pattern:
   - Subscribe: `sub_id = api.event_bus.subscribe("button_pressed", handler)`
   - Filter inside handler by `event.get("button")`.
   - Unsubscribe on teardown.
4. Enforce LED/Button Parity Rule:
   - LEDs ON exactly for buttons the app is currently willing to accept.
   - Ignore presses for LEDs that are OFF (framework should enforce; app must set LEDs correctly & not rely on ignored events).
   - Always clear (all OFF) in `finally`.
5. Use `stop_event` cooperatively: loops must check at least every 0.5s (target ≤0.2s for responsive exit). Replace long sleeps with `stop_event.wait(interval)`.
6. Log meaningful errors via `api.log_error` instead of silent failures.
7. Validate required secrets via manifest (`required_env`) — already enforced by AppManager; ensure manifests are updated if new env vars introduced.
8. After all apps migrated, remove legacy compatibility methods from `AppScreenAPI` and add a CI grep guard.

## Quick Classification (current scan)
Modern (already using `display_text` only):
- admin_boss_admin
- admin_shutdown
- admin_startup
- admin_wifi_configuration
- app_jokes
- current_weather
- hello_world
- list_all_apps

Legacy (uses at least one deprecated screen method):
- bird_sightings_near_me
- breaking_news
- color_of_the_day
- constellation_of_the_night
- dad_joke_generator
- flight_status_favorite_airline
- flights_leaving_heathrow
- internet_speed_check
- joke_of_the_moment (also uses unsupported `any_button_pressed`)
- local_tide_times
- moon_phase
- name_that_animal
- on_this_day
- public_domain_book_snippet
- quote_of_the_day
- random_emoji_combo
- random_local_place_name
- random_useless_fact
- space_update
- tiny_poem
- today_in_music
- top_trending_search
- word_of_the_day

## Per-App Task Checklist
(Feel free to annotate with PR numbers / dates.)

### Already Modern (Validation Pass)
| App | Validate LED Parity | Validate stop_event cadence | Confirm no legacy calls | Notes | Status |
|-----|--------------------|-----------------------------|-------------------------|-------|--------|
| admin_boss_admin | [ ] | [ ] | [ ] | Complex loop; ensure event unsubscribes | [ ] |
| admin_shutdown | [ ] | [ ] | [ ] | Confirmation flow only | [ ] |
| admin_startup | [ ] | [ ] | [ ] | Short-lived splash | [ ] |
| admin_wifi_configuration | [ ] | [ ] | [ ] | Long polling (1.0s wait) might be tightened | [ ] |
| app_jokes | [ ] | [ ] | [ ] | Timer loop 0.5s wait okay | [ ] |
| current_weather | [ ] | [ ] | [ ] | Loop wait 0.5s; ensure LED cleanup (if any) | [ ] |
| hello_world | [ ] | [ ] | [ ] | Several waits (0.2–5.0s) — shorten 5s span | [ ] |
| list_all_apps | [ ] | [ ] | [ ] | Scroll/paging? ensure responsiveness | [ ] |

### Legacy Apps Requiring Refactor
For each: (A) Replace legacy screen writes with single `display_text` call (optionally multi-phase), (B) Introduce LED pattern if user interaction expected (else explicitly none), (C) Ensure stop_event-friendly loop, (D) Add button event subscriptions if interactive, (E) Remove any polling for button states, (F) Update manifest if new env vars.

| App | Legacy Methods Present | Interaction? | External API(s) | Special Notes | Status |
|-----|------------------------|--------------|-----------------|--------------|--------|
| bird_sightings_near_me | write_line, write_wrapped, clear_body | No (display only) | eBird | Format species list via joined lines | [ ] |
| breaking_news | write_line, write_wrapped, clear_body | No | (News API?) none listed yet | Headlines list join; ellipsize | [ ] |
| color_of_the_day | write_line, write_wrapped, clear_body | No | (Color API?) | Keep hex + name styling | [ ] |
| constellation_of_the_night | write_line, write_wrapped | No | (Astronomy?) | Single message only — trivial | [ ] |
| dad_joke_generator | write_line, write_wrapped, clear_body | No | Joke API (icanhazdad?) | Multi-line joke; fallback text | [ ] |
| flight_status_favorite_airline | write_line, write_wrapped, clear_body | No | aviationstack | Table-like layout; use \n lines | [ ] |
| flights_leaving_heathrow | write_line, write_wrapped, clear_body | No | aviationstack | Same pattern as above | [ ] |
| internet_speed_check | write_line, clear_body | No | Speed test (internal) | Replace multi-line metrics | [ ] |
| joke_of_the_moment | write_line, write_wrapped, clear_body, any_button_pressed | Potential (button to reveal punchline) | Joke API(s) | Must replace button logic with events; show setup then subscribe | [ ] |
| local_tide_times | write_line, write_wrapped, clear_body | No | (Tide API) | Multi-line schedule | [ ] |
| moon_phase | write_line, write_wrapped, clear_body | No | ipgeolocation (moon) | Could consolidate metrics | [ ] |
| name_that_animal | write_line, write_wrapped, clear_body | No | (Animal API) | Manage wrapping of diet info | [ ] |
| on_this_day | write_line, write_wrapped, clear_body | No | (History API) | List of events; maybe limit lines | [ ] |
| public_domain_book_snippet | write_line, clear_body | No | (Book/Gutenberg) | Multi-line snippet; preserve indentation? | [ ] |
| quote_of_the_day | write_line, write_wrapped, clear_body | No | (Quote API) | Author on last line prefixed dash | [ ] |
| random_emoji_combo | write_line, clear_body | No | (Local/random) | Centered emoji string | [ ] |
| random_local_place_name | write_line, clear_body | No | (Local dataset) | Possibly uppercase styling | [ ] |
| random_useless_fact | write_line, write_wrapped, clear_body | No | (Fact API) | Might need wrapping | [ ] |
| space_update | write_line, write_wrapped, clear_body | No | NASA | Potential long text; ensure truncation | [ ] |
| tiny_poem | write_line, write_wrapped, clear_body | No | (Poem API) | Title + poem + author signature; spacing | [ ] |
| today_in_music | write_line, write_wrapped, clear_body | No | (Music chart API) | Headline + item lines | [ ] |
| top_trending_search | write_line, write_wrapped, clear_body | No | (Trends API) | Single trend line possibly | [ ] |
| word_of_the_day | write_line, write_wrapped, clear_body | No | (Dictionary API) | Word + defs + example lines | [ ] |

## Suggested Refactor Order (Batching)
1. Critical (blocking removal): `joke_of_the_moment` (unsupported button logic).
2. High Fan-out Patterns (define formatting conventions): `word_of_the_day`, `quote_of_the_day`, `space_update`, `tiny_poem`.
3. List/Table Layout Group: flight apps, breaking_news, on_this_day, today_in_music, bird_sightings_near_me.
4. Simple Single/Short Text: constellation_of_the_night, random_* apps, color_of_the_day.
5. Remaining data/metric apps: internet_speed_check, moon_phase, local_tide_times, name_that_animal.

## Formatting Conventions Proposal
- Title + blank line + body (preferred)
- Use automatic wrapping inside `display_text`; manually insert line breaks only for semantic separation.
- Keep total payload under ~800 characters; truncate and append '…' if longer.

## Definition of Done Per App
- No legacy screen API references (grep returns zero).
- All screen updates performed with 1–2 `display_text` calls per refresh cycle.
- (If interactive) Button events subscribed/unsubscribed properly; LED parity enforced.
- Loop respects `stop_event` with max 0.5s responsiveness (target 0.2s).
- Manifest accurately declares `required_env` and `external_apis` (if any).
- App logs at least one startup info line and error lines for failures.

## Post-Migration Cleanup
- Remove legacy methods from `AppScreenAPI` implementation.
- Add test/CI grep ensuring forbidden identifiers absent in `boss/apps/**/main.py`:
  - `write_line(`, `write_wrapped(`, `clear_body(`, `any_button_pressed(`
- Update documentation to mark migration complete.

## Open Questions / Follow-Ups
- Do any mini-apps need image support soon (prototype `display_image` example)?
- Central utility for truncating multi-line text? (Potential helper in shared utils.)
- Consider adding a per-app `render()` abstraction to consolidate formatting logic for easier testing.

---
(Autogenerated initial version; update statuses as work progresses.)
