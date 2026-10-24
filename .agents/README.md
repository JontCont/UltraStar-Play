# Shared AI instructions

This directory is the single source of truth for project-specific AI guidance. Do not maintain parallel copies under tool-specific directories.

## Project direction

- Refresh UltraStar Play as a Unity desktop application, initially targeting Windows.
- Keep music, charts, settings, and results local. A website, NAS deployment, and a new backend are not required.
- Preserve the existing singing engine and intended behavior. UI refresh does not authorize scoring, chart-format, audio, or protocol changes.
- Upstream source is imported at commit `a4aaa0b31327062a92d12b5e4cab4d80777f2a3f` in the workspace root on branch `refactor/desktop-refresh`. Git remote `origin` points to `https://github.com/JontCont/UltraStar-Play.git`; `upstream` retains the official source repository. Do not push without user authorization.
- The main game now uses Unity `6000.6.7f1` and URP `17.6.0`. Import, compilation, 38 focused EditMode tests, and Windows64 builds passed; one existing test is ignored. The core-game-loop PlayMode test still times out entering SingScene, so runtime singing is not verified. Follow the [opening guide](../spec/getting-started.md) and do not claim the upgrade is fully validated.
- The user subsequently approved Companion's Unity 6.6 and Built-In to URP migration. Its project-local pipeline/camera, five EditMode checks, isolated rendering PlayMode check and Windows smoke build passed. Android/iOS packaging, touch, microphone permissions and main-game pairing remain unverified; do not conflate the rendering check with a connected app test.

## Required workflow

1. Read the [scope](../spec/README.md), [plan](../spec/plan.md), and relevant entries in the [task list](../spec/tasks.md).
2. For development, load [ultrastar-play-development](skills/ultrastar-play-development/SKILL.md) and [ultrastar-play-architecture](skills/ultrastar-play-architecture/SKILL.md) before editing application code.
   For Editor or package migration, also load [ultrastar-play-unity-upgrade](skills/ultrastar-play-unity-upgrade/SKILL.md).
3. Inspect the actual checkout and identify affected components, callers, shared UI, and tests. Treat the [architecture baseline](../spec/architecture.md) as research evidence, not proof about unimported code.
4. Before implementing an architectural change, create or update the relevant architecture skill and baseline with verified facts, boundaries, and validation steps. Mark proposals as proposed until implemented and verified.
5. Reuse an existing skill when it covers the work. Create a focused skill only for a new architectural responsibility or repeatable workflow that is not covered. Do not create one skill per ticket.
6. Make bounded changes, run the smallest relevant existing checks, and record actual results or blockers in the task list.
7. Before closing implementation work, reconcile skills and architecture documentation with the delivered code. Never mark an untested requirement complete.

## Guardrails

- Do not introduce Web frameworks, desktop Web wrappers, cloud services, or a new server merely to refresh the UI.
- Do not replace the singing engine, change scores or timing tolerance, or redesign the Companion protocol without explicit approval.
- Ask before source-baseline selection, major dependency upgrades, new product features, or approval of a visual direction. Documentation may record these as pending without resolving them.
- Preserve dirty work, upstream license notices, localization keys, keyboard/controller navigation, and supported existing workflows.
- Surface errors using existing project conventions; do not hide failures behind success-shaped fallbacks.
- Restore dependencies only when the approved setup requires it or validation reports missing dependencies. Use the Unity version and build commands verified in the selected checkout.
- Use Traditional Chinese for user-facing planning documents. Follow upstream conventions for application code.

## Skill conventions

- Store all project skills at `.agents/skills/<skill-name>/SKILL.md`.
- Include YAML frontmatter with `name` matching the folder and a meaningful `description` containing task triggers.
- Each skill must describe when to use it, the procedure, architectural constraints, and validation or completion criteria.
- Reference canonical specifications instead of duplicating them. Record unknowns explicitly.
- Keep instructions vendor-neutral. The root [AGENTS.md](../AGENTS.md) is only a discovery pointer.

## Discovery limits

`.agents/skills/` is a shared convention, not a guarantee that every AI product loads it automatically. Tools that support root `AGENTS.md` can follow the pointer; otherwise configure the tool to read this directory or load the instructions manually. Do not create divergent copies as a workaround.

## Upstream guidance

The imported main-game `AGENTS.md` is a discovery pointer to this directory. Its [original contents](references/upstream-main-game-guidelines.md) are preserved as a historical reference only; do not apply its outdated version, platform, or test-policy claims as current project rules.
