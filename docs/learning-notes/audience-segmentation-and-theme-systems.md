# Learning Note: Audience Segmentation and Theme Token Architecture

## Context

CareerLens serves two primary user archetypes with fundamentally different objectives:
1. **Students and Early-Career Freshers**:
   - Focus: Transitioning from academic coursework and personal projects to commercial readiness.
   - Core Needs: Translating GitHub repositories into production skill signals, closing foundational tooling gaps (Docker, Git workflows, unit testing), discovering internships/entry-level roles, and preparing for initial CS and STAR behavioral interview rounds.
2. **Working Professionals and Career Switchers**:
   - Focus: Maximizing commercial seniority, lateral technology transitions, and leadership leveling.
   - Core Needs: Quantifying business impact (latency, throughput, revenue outcomes), bridging architectural skill deltas (Kafka, distributed caching, vector databases), discovering mid/senior/staff positions, and practicing high-scale system design loops.

## Organization of the Overview Workspace

Rather than overwhelming users with an undifferentiated, cluttered dashboard, the Overview Page implements a **Persona Lens Architecture**:
- **Interactive Persona Filter**: A segmented control allows immediate switching between `Students & Freshers`, `Working Professionals`, and `Unified Dual View`.
- **Targeted KPIs**: Dynamically updates readiness scores, matching opportunity counts, and prioritized skill deltas based on the chosen lens.
- **Actionable Blueprints**: Displays step-by-step pathways showing how to move from resume upload to mock interview practice for the candidate's exact stage.
- **Direct Workspace Launchpad**: Quick-launch buttons directly trigger `onNavigate('Resume')`, `onNavigate('Jobs')`, `onNavigate('Roadmap')`, and `onNavigate('Interviews')`.

## Theme Token and Contrast Correction

When supporting dual light and dark modes in modular frontends, several design pitfalls frequently occur:
1. **Hardcoded Color Stops in Gradients**: Using CSS like `bg-[linear-gradient(145deg,var(--cl-surface),#0f1722)]` works in dark mode but produces an ugly, muddy black stop in light mode. Switching to `bg-[linear-gradient(145deg,var(--cl-surface),var(--cl-surface-muted))]` ensures natural elevation in both themes.
2. **Button Text Contrast**: Light mode accents (such as amber `#d97706`) require white text (`#ffffff`), while dark mode accents (such as gold `#f59e0b`) require dark text (`#090d14`). Introducing `--cl-accent-contrast` solves text illegibility across button hover and active states.
3. **Hardcoded Pastel Tailwind Utilities**: Classes like `text-red-100` or `text-emerald-100` were originally chosen for dark backgrounds, but render as illegible washed-out pastels on white light backgrounds. Using `--cl-danger`, `--cl-success`, and `--cl-warning` semantic variables guarantees minimum 4.5:1 WCAG AA contrast.
