# Intended Frontend Design (Archived Before Deletion)

## Creative Direction
- Mission-control visual language for a contractor marketplace.
- Dark-first interface with atmospheric depth, grid texture, and subtle grain.
- One dominant warm accent (orange) supported by cool cyan highlights.

## Design System Intent
- Token-driven spacing and typography scale.
- Distinct font roles:
  - Display: bold editorial headlines.
  - Heading: geometric modern hierarchy.
  - Body: high-legibility sans.
  - Mono: telemetry labels and data readouts.
- Core component usage through shared primitives (`Button`, `Badge`, `Card`) instead of ad hoc controls.

## Page Architecture
- Cinematic hero with strong three-line value proposition.
- Right-side live signal/status panel.
- KPI ribbon for top-level metrics.
- Bento-style command grid for system capabilities.
- Step-based workflow timeline.
- Proof/outcomes card section.
- Final deployment CTA block.

## Motion + Interaction
- Entrance motion with restrained easing and stagger.
- Ambient pulse bars for live-system feel.
- Reduced-motion compliance through media-query overrides.

## Responsiveness
- Desktop: asymmetric hero + structured multi-column grids.
- Tablet/mobile: single-column collapse with preserved hierarchy and CTA priority.

This note captures the intended frontend direction immediately before full frontend deletion.
