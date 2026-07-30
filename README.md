# Camp & Kin games — iOS build harness

Three Capacitor-wrapped HTML5 games. This repo exists for one reason: `npx cap add ios`
needs macOS, and the machine these are built on is Linux. The workflow in
`.github/workflows/ios-build.yml` runs that step on a GitHub macOS runner and uploads the
generated `ios/` project as an artifact.

Signing and App Store upload are deliberately NOT in the workflow — those need Apple
certificates tied to a real identity.
