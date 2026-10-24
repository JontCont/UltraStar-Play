---
name: ultrastar-play-unity-upgrade
description: "Use when upgrading UltraStar Play Unity Editor versions, resolving package or API migration failures, validating engine compatibility, or aligning build and test versions. 適用於 Unity 升級、匯入編譯與相容性驗證。"
---

# Unity upgrade architecture and validation

## Context

Read the [shared instructions](../../README.md), [architecture](../../../spec/architecture.md), and [opening guide](../../../spec/getting-started.md). Load the architecture and development skills before application changes.

The user approved upgrading the Windows main game from `6000.5.6f1` to installed Editor `6000.6.7f1`, then explicitly approved the same Editor upgrade and Built-In to URP migration for Companion. No runnable 6.5 baseline was captured, so failures cannot automatically be attributed to the upgrade. Approval does not cover UI redesign or network/audio changes.

## Boundaries

- The main-game Editor owns project-settings and serialized-asset migrations.
- The package manifest and lockfile own package versions; prefer existing pins unless an actual migration failure requires a compatible replacement.
- Shared packages have both main-game and Companion consumers. Do not silently assume Companion compatibility from a main-game compile.
- Verify the configured render-pipeline asset and all quality overrides, not merely an installed URP dependency. The main game already uses URP. Companion was Built-In before the separately approved migration; create project-local renderer/pipeline assets with Unity APIs, assign the Graphics default, and check every quality level. Do not borrow the desktop asset or change desktop settings.
- Keep scoring, chart semantics, microphone calibration, data persistence, and network protocols unchanged.
- Nuke restore success is not Unity compilation, and batch compilation is not an interactive singing or player smoke test.

## Procedure

1. Verify the exact installed Editor executable, current branch, dirty files, original version, and whether another Editor holds this project open. Preserve existing work.
2. Record the approved target and validation limits before migration. Do not install, downgrade, accept licensing terms, or change versions without approval.
3. Use the installed Editor to import the project with an explicit project path and dedicated log. Run only one Editor on the project at a time; bound automated runs and inspect exit status.
4. If licensing, package resolution, or compilation fails, inspect the first actionable error and relevant source. Never hide errors or repeatedly restore unrelated dependencies.
5. Make only demonstrated compatibility changes. Preserve Unity-generated metadata and inspect affected migration hunks rather than manually rewriting serialized assets.
6. After a successful import, run focused existing EditMode tests for affected UI, parsing, timing, or scoring surfaces, then a Windows build when feasible.
7. Align each approved project's CI Editor version with its migrated ProjectVersion; do not claim unexecuted mobile or CI builds pass.
8. Verify interactive main scene, audio/video, microphone calibration, and scoring separately. Check materials, shaders, particles, and background effects in the active pipeline; configuring URP alone does not prove every asset renders correctly. Keep those checks pending when hardware or user interaction is unavailable.
9. Update the opening guide, task evidence, and skills with exact outcomes. Do not describe an installed version as a successfully upgraded project.

## Failure handling

An unavailable license or inaccessible package registry is a blocker, not evidence of code incompatibility. If blocked, preserve the exact stage reached and the user's next action. Do not force a newer project open in an older Editor as rollback.

### VS Code project discovery

When the repository root contains both Unity projects, C# Dev Kit may synthesize a workspace solution that includes `Library/PackageCache`, Hot Reload project copies and built Mod templates. Memory Profiler's package-internal projects use `Unity.Sdk` without a public SDK version; ordinary `dotnet` evaluation reports `MSB4236` and restore skips them with `NU1503`. These are not the Unity-generated IDE projects.

The root [workspace settings](../../../.vscode/settings.json) select `UltraStar Play/UltraStar Play.slnx` explicitly. Use `.NET: Open Solution` to switch to Companion's generated solution. After changing the setting, reload the VS Code window; regenerate projects through Unity's External Tools if the solution or referenced projects are missing. Validate `dotnet restore` on each generated solution, not package-internal projects. Do not patch PackageCache, install an arbitrary `Unity.Sdk`, disable restore, or add warning suppression/global SDK pins to hide incorrect discovery.

The original optional `com.unity.build-report-inspector` `0.3.0-preview` fails 6.6 compilation with `UAC0023` for `BinaryFormatter`; no newer registry release was available during migration. It has no project C# or assembly-definition consumers. Remove this Editor-only preview dependency rather than disabling diagnostics or patching PackageCache; acknowledge that its report-inspection menu is no longer available.

Unity 6.6 reported UXML float conversion errors for `scroll-deceleration-rate="0,135"` and `elasticity="0,1"`. Normalize these scalar attributes to invariant decimals (`0.135` and `0.1`) in approved projects and shared layouts. Preserve list/vector separators, layout behavior, file encoding, and unrelated attributes.

## Companion migration boundary

- The approved Companion migration owns its manifest/lockfile, ProjectSettings, project-local URP renderer/assets, camera prefab and two affected UXML layouts.
- Its UI is screen-space UI Toolkit: `CompanionAppPanelSettings` has no target texture, and `CommonSceneObjects` supplies a single orthographic camera. No project-local material/shader or rendering callbacks were found before migration.
- Keep the existing UI, color space, frame-rate control, transport DTOs and microphone pipeline. Use a lightweight forward URP renderer without added post-processing, depth/opaque textures or shadows for this UI-only project.
- Restore missing LeanTween, UniRx and Companion NuGet dependencies through `RestoreCompanionAppDependencies`. This target also restores main-game/shared NuGet plugins; run with both Editors closed.
- The rendering smoke test uses actual camera/panel/UXML assets without application controllers, profile loading or discovery. For a future full-scene check, isolate settings through `ApplicationManager.simulatedCommandLineArguments` in Editor, not process CLI arguments. Do not overwrite a real Companion profile.
- Add focused tests for the effective pipeline at every quality, renderer/camera configuration and the affected UXML. Mobile packaging, microphone permissions, touch rendering and main-game pairing remain separate checks; only Windows/WebGL Editor modules are currently installed.

## Current validation

- Main-game import/compilation and Windows64 builds succeeded on `6000.6.7f1` with URP `17.6.0`.
- Focused chart-format, timing, and theme tests: 38 passed, one pre-existing Ignore, zero failures.
- `CoreGameLoopTest` still times out waiting to enter SingScene, including after UXML normalization. This remains a blocker for certifying end-to-end singing, not a passing or skipped test.
- Unity 6.6 logs successful builds as `Build Finished, Result: Success.`; verify the actual report and output, not a hardcoded older log phrase.
- Count individual test cases and failures: this runner emitted root status `Skipped:Ignored` despite 38 passes and one expected ignored case.
- Companion import/compilation, five pipeline/camera/UXML EditMode cases, one isolated rendering PlayMode case and a Windows smoke build passed. The main game's focused 38-pass/one-Ignore result was preserved after restoring shared dependencies.
- Batch-mode PlayMode tests do not automatically render a Game view. Use `RenderPipeline.SubmitRenderRequest` with a URP `SingleCameraRequest` and a real target texture to exercise the renderer; do not merely wait for `currentPipeline` to become non-null.
- Runtime initialization logs an existing shared `ApplicationUtils` error because Companion lacks `StreamingAssets/ffmpeg-supported-common-file-extensions.txt`. It occurs before the isolated test and does not fail that case; do not describe the entire runtime log as error-free or silently suppress it. No FFmpeg/media behavior was changed in this migration.
- Android/iOS build modules are not installed. Neither a Windows smoke build nor an isolated render test certifies mobile rendering, microphone permissions, battery use or pairing.
