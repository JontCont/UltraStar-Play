---
name: ultrastar-play-architecture
description: "Use before changing UltraStar Play architecture or application code, including Unity scenes, UXML/USS, shared packages, microphone and scoring flows, persistence, build dependencies, and Companion networking. 適用於架構確認、架構變更與建立或維護架構 skills。"
---

# UltraStar Play architecture

## Required context

Read the [architecture baseline](../../../spec/architecture.md) and [shared instructions](../../README.md).

The baseline separates upstream research from local validation. The imported source is based on commit `a4aaa0b31327062a92d12b5e4cab4d80777f2a3f`; main-game Unity 6.6 compilation, focused EditMode checks, and Windows builds have passed. The core singing PlayMode check remains failing, and interactive behavior is not yet validated.

The user subsequently approved a Windows main-game migration to installed Unity `6000.6.7f1` without first running 6.5. Follow the [Unity upgrade skill](../ultrastar-play-unity-upgrade/SKILL.md); installation and migration approval alone do not prove compatibility.

The user also approved Companion's Unity 6.6 and Built-In to URP migration. Keep its renderer assets project-local and its UI Toolkit, microphone and networking behavior unchanged; validate the effective pipeline for every quality level and isolate settings in runtime checks. Mobile builds and pairing require separate evidence.

## Procedure before implementation

1. Identify the imported revision and affected responsibility: screen UI, shared UI, singing pipeline, song library, persistence, Companion, or build.
2. Trace the affected behavior through actual callers and existing tests. Identify the owner, inputs, outputs, persistence effects, and other consumers.
3. Compare findings with the baseline. Correct outdated claims and distinguish:
   - verified current behavior;
   - proposed changes requiring approval;
   - implemented and validated behavior.
4. Before making an architectural change, update the baseline and this skill, or create a focused architecture skill if the new responsibility needs its own reusable workflow. Describe boundaries, compatibility risks, and validation steps.
5. Keep presentation changes inside the relevant scene or shared UI layer. Shared changes require checking both the main game and Companion when both consume them.
6. Implement only the approved change. Keep network, audio, scoring, and data migrations explicit rather than hiding them inside a UI refactor.
7. After validation, reconcile the documentation with what actually shipped and record the evidence in the task list.

## Architectural constraints

- Keep the existing Unity desktop architecture unless a separate architecture decision is approved.
- Do not treat UXML as browser HTML or USS as fully compatible CSS.
- Keep real-time microphone analysis separate from offline AI chart generation.
- Keep chart parsing and timing semantics stable during visual work.
- Keep local singing usable without a NAS, external server, or network connection.
- Preserve Companion message compatibility unless a coordinated protocol change is approved.
- Do not move scene-specific behavior into shared packages without an actual shared consumer.
- Do not invent classes, services, commands, or supported platforms absent from the selected checkout.

## Localization boundary

- Both projects load `playshared/Runtime/Resources/Translations/messages*.properties` through the shared `Translation` wrapper and ProTrans `ResourcesFolderPropertiesFileProvider`. Add locales there, not separate project copies.
- ProTrans uses two-letter language/region suffixes: `messages_zh_TW.properties` maps to `CultureInfo("zh-TW")`. Existing `messages_zh.properties` remains Simplified Chinese; do not replace it or use unsupported script suffixes such as `zh_Hant`.
- `LanguageChooserControl` discovers available cultures and labels them using the default English catalogue's `language<suffix>` key. Add `language_zh_tw` to the default catalogue and localized catalogue. Existing controllers persist `CultureInfoName`, with no new schema.
- Preserve every default key, placeholder name, escaped newline, rich-text tag and URL when translating. Check the raw files for duplicate keys as ProTrans otherwise overwrites duplicates.
- Shared `UltraStarPlayTextSettings` already includes dynamic Noto Sans TC as a fallback. Verify glyph coverage before adding font downloads or changing fallback order.
- Test culture discovery, the real chooser, representative desktop/Companion strings, formatted values, full key/placeholder/markup/URL parity and settings serialization. Tests should use Resources directly and restore global configuration to avoid reading custom user overrides.
- Shared locale tests live in the nested `playsharedui.Translations.Editor.Tests` assembly. Both manifests explicitly list `playsharedui` in `testables`, otherwise Companion's local package dependency does not discover its tests. Verify actual fixture counts, not merely runner exit code.
- Font coverage tests load the existing source font through `FontEngine.TryGetGlyphWithUnicodeValue` rather than adding glyphs to serialized dynamic atlases. Avoid `TextAsset` ambiguity with TextCore's type.
- Source glyph coverage alone is not a rendering test: CJK fallback assets use 1024x1024 dynamic atlases and now enable multi-atlas support and clear dynamic data on build. Adding more translated screens exhausted their previous single atlas even when the source contained every glyph. `CjkFontAtlasTest` exercises `TryAddCharacters` on temporary font assets with production packing settings, including regular/bold faces and every CJK fallback reachable before TC. Preserve fallback order and additional atlas pages instead of hiding missing characters or enlarging controls.
- Test atlas capacity without mutating serialized fonts: create a temporary `FontAsset` from the production source and packing settings and destroy its generated textures/material after testing. Verify game and recording settings in a rebuilt player, not just the main menu.
- Unity's clear-on-build option can rewrite checked-in font texture/glyph caches and move serialized fields. Keep the authored change to the two scalar settings; preserve original cache data only in assets known to have been clean before your build, without reverting user edits. Test runners should not produce serialized atlas changes.
- Main-game settings apply the saved culture at startup. Companion currently saves `CultureInfoName` but does not apply it on startup; document that pre-existing limitation rather than claiming a restart test passed. Keep fixing that behavior separate from adding a catalogue.

## Song archive import

- `DownloadSongArchiveUiControl` reports errors and registers the extracted folder only after `DownloadAndExtractSongArchiveControl` finishes download and extraction. Preserve that ordering and the original archive on failure.
- `ExtractArchiveControl` owns background extraction and progress. ZIP import must use `System.IO.Compression.ZipArchive`, not SharpZipLib: compilation can resolve the shared NuGet 0.85 or Sherpa 1.4 DLL while the .NET Framework-profile Windows player ships Unity Mono's 4.84 assembly with incompatible methods. Editor-only tests cannot prove packaged compatibility.
- Preserve the existing Windows short temporary-path staging and target-folder copy behavior. Create parent directories for file entries even when the archive omits directory records, keep UTF-8 names and empty directories, reject destinations outside the extraction root, count all processed entries, and clean owned staging directories on both success and failure.
- TAR extraction, Android StreamingAssets and build-output compression still use their existing SharpZipLib paths; this ZIP-import change does not certify those other consumers. Do not edit PackageCache or Unity's installed framework DLLs.
- Validate tiny generated archives, invalid/missing archives, Unicode and nested paths, progress and traversal rejection. Then test the actual downloaded archive and the native packaged player; do not mark the fix complete from compilation or an Editor-only check.
- Validated on Windows: 10 focused Editor PlayMode cases passed; the regular rebuilt player imported the cached official archive through its download UI over loopback, registered its folder, and produced 217 files matching the archive by SHA-256. The standalone test runner itself is blocked by existing PlayMode tests referencing unavailable `VisualElementTestUtils`; use the regular player for packaged evidence rather than hiding those compilation errors.

## When to add another architecture skill
Add one only when a domain needs independently useful, verified procedures, such as audio calibration, shared UI controls, or Companion synchronization.

The new skill must include its owning components, dependency boundaries, change procedure, compatibility obligations, and focused validation. Add a discovery link from the shared instructions, and keep general rules here rather than copying them.

## Completion

Every affected boundary is accounted for, compatibility has been checked, and documentation describes verified facts. Source import alone is not architectural validation.
