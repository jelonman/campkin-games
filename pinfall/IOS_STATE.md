# iOS pipeline — exactly where it stands, 2026-08-01

## Working

- The game builds and runs. Renders in `art/shots/` are the real thing on a real GPU.
- The repo lane exists: `jelonman/campkin-games`, workflow `pinfall-ios.yml`, macOS runner,
  bounded steps, full diagnostics.
- Godot 4.6.3 and the iOS export templates install correctly on the runner — `ios.zip`,
  202 MB, in the right directory. Verified in the log, not assumed.
- Asset import passes on the runner.
- App Store Connect API works from this box: 2 apps, 4 distribution certificates, 3 bundle ids,
  3 active profiles. Team ID **4X59743R44**, read out of a live provisioning profile.
- Bundle ids for all three games created by API today: `com.piotraiventures.untangle`,
  `.gaterush`, `.pinrescue` (9Q7MLAR6QK / 28LFH2ZD66 / 9HA7CD6M6R).

## Blocked, and precisely on what

`--export-debug "iOS"` refuses with **`Cannot export project with preset "iOS" due to
configuration errors:`** followed by an **empty reason**, identically on Linux and on the macOS
runner. Five materially different attempts, none of which moved it:

1. Six-way bisect of every option I had set (export method, team id, device family, min iOS
   version, icons removed) — all still refused, so it is not a wrong value.
2. A minimal empty project with a two-key preset — same refusal, so it is not this game.
3. Installed the 1.2 GB export templates locally so iteration costs nothing — no change.
4. Ran the editor headless over Xvfb to normalise the preset — it does not rewrite a preset it
   did not author, and will not create one without the GUI dialog.
5. Added the keys a hand-written preset lacks: `custom_template/debug|release`,
   `export_project_only`, the storyboard set, the four signing fields — no change.

**The remaining candidate is the one thing I cannot fill in:** `provisioning_profile_uuid_debug`
and `code_sign_identity_debug` are empty strings. Godot's iOS exporter validates signing before
it will emit an Xcode project, and its objection here has no message text — which is consistent
with everything observed. A real UUID and identity require a provisioning profile bound to
`com.piotraiventures.pinfall`, and a profile requires an **App Store Connect app record**.

## Why that is genuinely the owner's, and not an excuse

Apple does not allow app-record creation over the API at all: `POST /v1/apps` returns
`FORBIDDEN_ERROR — The resource 'apps' does not allow 'CREATE'. Allowed operations are:
GET_COLLECTION, GET_INSTANCE, UPDATE`. It is a web-UI-only action, and the web session needs a
sign-in with 2FA. That is identity.

Note this would have blocked release regardless of the export bug, so finishing the export today
would not have shipped anything.

## The exact click

1. appstoreconnect.apple.com → sign in
2. **Apps → + → New App**
3. Platform **iOS**, name **Pinfall**, primary language English (U.S.),
   Bundle ID **com.piotraiventures.pinfall** (already exists in the dropdown), SKU `pinfall2026`
4. Create. Nothing else — no pricing, no screenshots, no submission.

Then this box takes it from there: create the provisioning profile over the API, fill the two
signing fields, export, sign, and upload to TestFlight. All of that is API and CI work.

## Runner spend

Four runs, one of which hung 32 minutes before the deadline existed. macOS bills at 10x, so
further runs are paused until there is a signing identity to test — iterating on an empty error
message across a billed runner is the thing to stop doing, not repeat.
