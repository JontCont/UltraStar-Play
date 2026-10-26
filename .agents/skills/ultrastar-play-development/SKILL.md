---
name: ultrastar-play-development
description: "Use when implementing, refreshing, fixing, testing, or packaging UltraStar Play desktop features, Unity C# code, UI Toolkit screens, or Companion integration. 適用於桌機翻新、功能修改、測試與發行。"
---

# UltraStar Play development

## Required context

Read the [shared instructions](../../README.md), [scope](../../../spec/README.md), [plan](../../../spec/plan.md), and [tasks](../../../spec/tasks.md).

Load the [architecture skill](../ultrastar-play-architecture/SKILL.md) before application-code changes.

## Imported baseline

Source is present at the workspace root on branch `refactor/desktop-refresh`, based on commit `a4aaa0b31327062a92d12b5e4cab4d80777f2a3f`. The main Unity project is `UltraStar Play`; Companion is `UltraStar Play Companion`.

The original upstream editor version was `6000.5.6f1`; both the main game and Companion have been migrated to installed Editor `6000.6.7f1` and URP `17.6.0`. Each project owns separate rendering assets. `NukeBuild/NukeBuild.csproj` targets `net8.0`.

The root `build.ps1` can bootstrap .NET and restore packages. Do not run even its help path as a supposedly read-only check. Review its effects and the selected restore target before executing it.

The main-game Nuke restore, Unity import/compilation, focused EditMode tests, and Windows builds have succeeded. The core-game-loop PlayMode test still times out before SingScene; do not treat a produced EXE as a verified singing session. Use the [upgrade skill](../ultrastar-play-unity-upgrade/SKILL.md) and [opening guide](../../../spec/getting-started.md) for exact evidence. Do not repeat dependency restoration unless required.

Windows LAN-test Setup.exe files for both projects can be reproduced with `tools/windows-installer/Build-Installers.ps1` using Inno Setup 6 and existing Mono Windows64 players. Companion now has `CompanionAppBuildTools.BuildWindows64` and Nuke `BuildCompanionAppWindows64`; its app version remains `1.3.4`, distinct from the main game's `1.7.1-beta1`. Installers add canonical license texts and Companion's missing media-extension catalogue, without changing application protocols. Installed-player loopback handshake, permissions/MicProfile exchange, HTTP hello, payload hashes and reinstall/uninstall passed; two-PC networking, microphone and full singing remain unverified. Startup TMP default-font exceptions were observed and are not fixed by packaging. The opening guide records steps, boundaries and evidence.

## Procedure

1. Select a task whose prerequisites are complete. If the baseline or visual direction needed by that task is not approved, ask rather than guessing.
2. Confirm whether upstream source is present. If it is not, stop implementation at the source-import prerequisite; do not scaffold an unrelated application or install Unity speculatively.
3. Read the selected checkout's contribution guide, package manifest, editor-version file, and relevant code. Confirm the actual build and test entrypoints before running them.
4. Establish the existing behavior for the affected screen or workflow. Inspect shared controls and styles before adding new ones.
5. Follow the architecture skill. Capture verified architectural knowledge before implementing changes, and document intentional behavior shifts for approval.
6. Implement the smallest complete change. Reuse existing C# controllers, UI Toolkit layouts, localization, theme facilities, and error-reporting patterns.
7. Validate the exact requirement with focused tests and, for UI changes, the running desktop player. Check navigation, focus, layout, localization, and error states as applicable.
8. Update the task entry with checks performed and evidence. Distinguish a Unity Editor check from a packaged Windows-player check.
9. Update affected skills and architecture notes before considering the work complete.

## Behavior preservation

- A visual refresh must not alter scoring rules, microphone calibration, chart interpretation, playback synchronization, or saved data.
- Use temporary local profiles or copies of user data for testing. Do not overwrite an existing song library.
- Do not add a website or backend for local-only features.
- Treat Companion functionality as a separate integration boundary, not a prerequisite for single-player desktop singing.
- Companion's isolated rendering test intentionally loads only camera/panel/UXML assets, not application controllers, settings or networking. Its passing result is not evidence of mobile permissions, pairing, or end-to-end microphone transport.

## Completion

- The task's acceptance criteria are demonstrated, not inferred from compilation.
- Required tests passed, or the task remains blocked with a specific reason.
- Architecture knowledge and task status match the implementation.
- No unrelated code, generated caches, credentials, or unlicensed song content is included.
