# Build state — 2026-08-01

## Both platforms build. The blocker was one project setting.

`textures/vram_compression/import_etc2_astc=true`

Mobile GPUs cannot sample the desktop texture formats Godot imports by default, so **iOS and
Android both refuse to export** until the project re-imports every texture in a mobile format.
Godot's headless exporter prints `Cannot export project with preset "X" due to configuration
errors:` and then **an empty body**. The editor's export dialog prints the actual line:

> *Target platform requires 'ETC2/ASTC' texture compression. Enable 'Import ETC2 ASTC' to fix.*

Six runner builds, a six-way preset bisect, a minimal-project repro, a local 1.2 GB template
install, a JDK downgrade and a full Android SDK install all failed to surface it, because none
of them could see a message that was never printed. Running the editor GUI on a virtual display
and reading the dialog took four minutes and answered it outright.

**The lesson, and it is the general one:** when a headless tool reports an error with no text,
run its GUI on Xvfb and look at the screen. The information exists; the CLI just is not printing
it.

## Android — done

    export/PinfallFoundry.apk        75 MB, signed, installable

    package        com.piotraiventures.pinfall
    label          Pinfall Foundry
    versionName    1.0.0   versionCode 1
    minSdk         24      compileSdk 36
    signer         CN=Android Debug (debug keystore, for sideload/testing)
    verified with  apksigner verify --print-certs

## iOS — Xcode project generates, on Linux

    P.xcodeproj + project.pbxproj
    P.xcframework, MoltenVK.xcframework, P.pck (47 MB), PrivacyInfo.xcprivacy
    485 MB total

Compiling and signing it still needs macOS, which is what the runner lane is for. The App Store
Connect side is already done: app **Pinfall Foundry** (6797051442), bundle
`com.piotraiventures.pinfall`, profile `Pinfall_AppStore` ACTIVE, team 4X59743R44.

## Toolchain installed on this box today

- Godot export templates 4.6.3.stable (1.2 GB) — iOS and Android
- Android SDK: cmdline-tools, platform-tools, build-tools 34.0.0, platforms android-34
- JDK 17 at `~/jdk17` (Godot's Android export wants 17, the box had 21)
- Debug keystore at `~/.android/debug.keystore`
- Godot editor settings point at all of the above

A second game now costs an export command, not a day.
