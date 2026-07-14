# `scientific-system-renderer` Skill

[中文说明](README.md)

An agent-operated skill for Codex, Claude Code, and other coding agents that uses evidence, interfaces, and physical constraints to create and audit Blender/SVG system architectures, physical setups, and component figures.

## What It Is For

- Create system architectures, real equipment connections, experimental setups, component sheets, and mechanism insets.
- Turn product photos, datasheets, CAD, sketches, and technical constraints into reproducible Blender scenes.
- Combine high-resolution no-text 3D renders with editable SVG annotation.
- Check optical paths, cables, fluid routes, thermal paths, wireless fields, mechanical contacts, motion envelopes, and supports.
- Repair intersections, floating parts, wrong ports or orientations, misleading scale, and temporal states drawn as duplicated hardware.

## Typical Requests

- "Use these product photos and manuals to build a physical setup figure and deliver `.blend`, transparent PNG, and annotated SVG files."
- "Separate this electronic, fluidic, and mechanical system into architecture and physical-setup panels."
- "Audit this Blender scene for impossible routes, floating supports, and incorrect interfaces, then repair it."
- "Create an orthographic component sheet showing the active area, ports, and mounting interface."

## What You Provide

- The system claim and intended audience.
- Available photographs, manuals, datasheets, CAD, sketches, dimensions, or interface definitions.
- Which details must be faithful and which may be explicitly schematic.
- Output size, background, view, file formats, and editability requirements.

## Outputs

- Reproducible Blender construction scripts and `.blend` projects.
- High-resolution transparent no-text PNGs and white-background inspection composites.
- Editable annotated SVGs and raster previews.
- A `scene_manifest.json`, source ledger, QA log, and regeneration command.
- Physical, visual, and delivery risk findings for existing figures.

## Agent Integration

Keep the complete skill directory, not only `SKILL.md`, because the workflow depends on `manifest.yaml`, `static/`, `references/`, `scripts/`, and `assets/`.

For Codex, link a stable checkout into the skills directory:

```bash
ln -s /absolute/path/scientific-system-renderer \
  ~/.codex/skills/scientific-system-renderer
```

Start a new Codex session, then describe the task naturally or explicitly request `$scientific-system-renderer`.

For Claude Code, keep a stable checkout and create a thin wrapper at `~/.claude/agents/scientific-system-renderer.md`:

```markdown
---
name: scientific-system-renderer
description: Build and audit evidence-grounded scientific system renders.
---
Read `/absolute/path/scientific-system-renderer/SKILL.md` first and follow it.
Load supporting files from that skill directory only when needed.
Do not replace its truth-model and visual-QA workflow with a generic response.
```

Other agents can use a custom prompt, subagent, or command wrapper that points to the real `SKILL.md`, provided they can read local files and execute tools.

## Boundaries

- Generated images and look-alike product photos are not treated as hardware evidence.
- Synthetic regression tests validate rules, not a project's design.
- Missing critical interfaces, dimensions, or boundary behavior must be recorded as assumptions or block detailed modeling.
- Safety, medical, regulatory, and manufacturing acceptance still require qualified expert review.

## Open-Source and Data Boundary

The repository contains only skill instructions, original code, generic templates, and original synthetic tests. It contains no paper PDFs, paper figures, paper-by-paper summaries, DOI or bibliographic corpus, manufacturer imagery, user project assets, or private paths. Project-specific references should not be committed unless their licenses explicitly permit redistribution.

Code and documentation are licensed under Apache-2.0. Third-party inputs remain subject to their own licenses and terms.
