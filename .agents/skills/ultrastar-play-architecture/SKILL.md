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

## When to add another architecture skill

Add one only when a domain needs independently useful, verified procedures, such as audio calibration, shared UI controls, or Companion synchronization.

The new skill must include its owning components, dependency boundaries, change procedure, compatibility obligations, and focused validation. Add a discovery link from the shared instructions, and keep general rules here rather than copying them.

## Completion

Every affected boundary is accounted for, compatibility has been checked, and documentation describes verified facts. Source import alone is not architectural validation.
