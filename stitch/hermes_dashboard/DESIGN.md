---
name: Hermes Dashboard
colors:
  surface: '#faf9fc'
  surface-dim: '#dad9dd'
  surface-bright: '#faf9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f6'
  surface-container: '#eeedf1'
  surface-container-high: '#e9e8eb'
  surface-container-highest: '#e3e2e5'
  on-surface: '#1a1c1e'
  on-surface-variant: '#43474e'
  inverse-surface: '#2f3033'
  inverse-on-surface: '#f1f0f3'
  outline: '#73777f'
  outline-variant: '#c3c6cf'
  surface-tint: '#446083'
  primary: '#000e20'
  on-primary: '#ffffff'
  primary-container: '#002444'
  on-primary-container: '#708cb2'
  inverse-primary: '#acc9f1'
  secondary: '#a93800'
  on-secondary: '#ffffff'
  secondary-container: '#fe753f'
  on-secondary-container: '#631d00'
  tertiary: '#0d0d0d'
  on-tertiary: '#ffffff'
  tertiary-container: '#232323'
  on-tertiary-container: '#8b8a89'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d2e4ff'
  primary-fixed-dim: '#acc9f1'
  on-primary-fixed: '#001c37'
  on-primary-fixed-variant: '#2c486a'
  secondary-fixed: '#ffdbcf'
  secondary-fixed-dim: '#ffb59b'
  on-secondary-fixed: '#380d00'
  on-secondary-fixed-variant: '#812900'
  tertiary-fixed: '#e4e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1b1c1b'
  on-tertiary-fixed-variant: '#474746'
  background: '#faf9fc'
  on-background: '#1a1c1e'
  surface-variant: '#e3e2e5'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  mono-label:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  gutter: 16px
  component-gap: 8px
  stack-tight: 4px
  max-width: 1440px
---

## Brand & Style

The design system is engineered for high-stakes technical environments where precision and reliability are paramount. It adopts a **Corporate / Modern** aesthetic with a heavy lean toward **Engineering Minimalism**. The visual language evokes a "Control Room" atmosphere—functional, dense, and authoritative. 

The strategy prioritizes clarity over decoration. It eschews modern trends like glassmorphism or vibrant gradients in favor of a structured, monochromatic foundation punctuated by high-intent technical accents. The emotional goal is to provide a sense of absolute control and calm efficiency, ensuring that engineers can parse complex datasets without cognitive fatigue.

## Colors

The palette is anchored by **Primary Navy (#002444)**, representing stability and depth. **Accent Orange (#a93800)** is reserved strictly for high-priority actions, critical status updates, and interactive focal points.

**Light Mode:** Uses **Warm White (#fcf9f8)** as the primary surface to reduce eye strain compared to pure white. Borders and dividers utilize low-opacity navy to maintain structure without creating visual noise.

**Dark Mode:** Built on a **Deep Charcoal/Navy** foundation (Neutral Base). It avoids pure black (#000000) to prevent high-contrast "blooming" of text. Surface elevations are indicated by subtle shifts in navy saturation rather than gray scales, maintaining the brand's cool-toned professional identity.

## Typography

This design system utilizes a dual-font approach to separate narrative content from technical data. 

**Inter** serves as the primary typeface for all interface elements, navigation, and headings. It provides excellent legibility at small sizes and a neutral, professional tone. 

**JetBrains Mono** is employed for technical stat cards, logs, code blocks, and any data point where character alignment is critical for scanning. This distinction helps users instantly differentiate between "system talk" and "data talk."

On mobile devices, `headline-lg` should scale down to 24px (headline-md) to ensure readability within constrained horizontal widths.

## Layout & Spacing

The system follows a strict **8px Grid** to ensure mathematical consistency across all layouts.

**Grid System:** 
- **Desktop:** A 12-column fluid grid with 16px gutters. For data-heavy views, use a "sidebar-main" layout where the sidebar is fixed at 256px and the main content area expands.
- **Tablet:** 8-column grid with 16px margins.
- **Mobile:** 4-column grid with 16px margins.

**Density:**
The design system favors high data density. Vertical spacing between table rows and list items is minimized to 8px or 12px to maximize the information visible above the fold. Consistent padding (e.g., 16px or 24px) is used within cards to provide "visual breathing room" around high-density data clusters.

## Elevation & Depth

This design system uses **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows to define hierarchy.

- **Level 0 (Background):** Primary surface color (Warm White or Deep Navy).
- **Level 1 (Cards/Panels):** Defined by a 1px solid border (#002444 at 10% opacity in light mode). No shadow.
- **Level 2 (Popovers/Dropdowns):** Subtle ambient shadow (4px blur, 0.05 opacity) to provide a soft lift from the base layer.
- **Level 3 (Modals):** High-contrast 1px border and a medium-diffused shadow (12px blur) to focus user attention.

In Dark Mode, depth is achieved by lightening the surface fill color slightly as the element moves "closer" to the user, mimicking physical light sources.

## Shapes

The shape language is "Soft" and disciplined. 
- **Small Components:** (Buttons, inputs, chips) use a **4px (0.25rem)** corner radius.
- **Large Components:** (Cards, modals) use an **8px (0.5rem)** corner radius.

This subtle rounding prevents the UI from feeling aggressive while maintaining a precise, technical edge. Elements that are purely functional—like status indicators or progress bar fills—should remain sharp (0px) to emphasize their "system-generated" nature.

## Components

### Buttons
- **Primary:** Solid Navy (#002444) with white text. 4px radius. 
- **Secondary:** 1px Navy border, transparent background. 
- **Technical/Action:** Solid Orange (#a93800) for destructive or high-alert actions only.

### Status Indicators
Do not rely on color alone. Use a combination of color and icon (e.g., a green dot for 'Active', a yellow triangle for 'Warning', and a red square for 'Critical').

### Data Tables
Dense rows (32px-40px height). Header cells use `label-caps` typography with a subtle background tint. Use a 1px divider between rows; do not use alternating row colors (zebra striping) to avoid visual clutter.

### Stat Cards
A top-aligned `body-sm` label, followed by a large `mono-data` value. Include a small sparkline (linear trend) at the bottom if applicable.

### Skeleton Loaders
Use a "shimmer" effect that transitions between two shades of the primary surface color. Avoid high-contrast greys; keep the motion slow and rhythmic (1.5s duration) to maintain the "premium" feel.

### Input Fields
1px border with a subtle inset shadow on focus. Labels use `body-sm` and are positioned above the field. Validation errors must use the Accent Orange for visibility.