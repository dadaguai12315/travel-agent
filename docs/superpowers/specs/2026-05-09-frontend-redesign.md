# Frontend Redesign Spec: Travel Advisor

**Date**: 2026-05-09  
**Status**: Approved

## Overview

Rebuild the Travel Advisor frontend with a premium, clean, and low-barrier user experience. The redesign introduces a dual-mode input system while maintaining the existing SSE-streaming chat architecture.

## Visual Design

**Style**: Minimalist White — black/white/gray palette, generous whitespace, no colorful gradients.

| Element | Value |
|---------|-------|
| Primary | `#111` (near-black, for emphasis) |
| Background | `#fff` |
| Surface | `#f9fafb`, `#f3f4f6` |
| Border | `#e5e7eb`, `#d1d5db` |
| Text primary | `#111` |
| Text secondary | `#6b7280` |
| Text placeholder | `#9ca3af`, `#d1d5db` |
| Font | System sans-serif stack (same as current) |
| Radius | 8px cards, 20px buttons/inputs |
| Shadow | Minimal, only for active states |

**No colorful gradients**. The current purple gradient header is replaced with a clean white header with a subtle bottom border.

## Interaction Design

### Dual-Mode Home Screen

The welcome page has a **tab switch** at the top allowing users to toggle between two input modes:

**Mode 1: Free Input** (default)
- Hero text: "发现你的完美旅行" with globe icon
- Subtitle: "智能推荐，一步到位"
- 4 quick-prompt cards (full-width, rounded, one per row) replacing the current horizontal pill layout
- Bottom input bar: rounded text input + black send button
- Quick prompts are tappable — populate input and auto-send, same as current behavior

**Mode 2: Guided Selection** (switch via tab)
- 3-step progress indicator (numbered circles connected by lines)
- Step 1: Destination type — 2×2 grid of icon+label cards (海滩度假, 文化古城, 自然风光, 都市探索)
- Step 2: Budget & season — selectable chips (经济实惠, 舒适中等, 奢华高端) plus season (春季, 夏季, 秋季, 冬季)
- Step 3: Travel vibe — optional extras (家庭亲子, 浪漫蜜月, 冒险探索, 美食之旅, 休闲放松)
- Back/Next buttons at bottom

### Chat Interface

After submission from either mode, the UI transitions to a chat view:
- Message list (same streaming approach)
- User messages: black background `#111`, white text, right-aligned
- Assistant messages: light gray `#f3f4f6`, dark text, left-aligned
- Streaming cursor: subtle pulsing block cursor
- Tool progress: subtle indicator pill above messages
- Input bar persists at bottom for follow-up questions

### Mode Switching

- Tab switch is always visible at the top of the home screen
- After entering chat mode, a "新对话" button in the header allows returning to home
- Session memory preserved (same sessionStorage mechanism)

## Architecture

No structural changes to the backend or build system:

- **index.html**: Vue 3 CDN template, all HTML markup with `v-if`/`v-for` directives
- **style.css**: All styles, mobile-responsive at 600px breakpoint
- **chat.js**: Vue 3 Composition API setup — state, mode switching, guided steps, SSE streaming (unchanged logic)

Keep Vue 3 via CDN (`unpkg.com/vue@3`). No build step.

## Data Flow (unchanged from current)

1. User submits input → `POST /api/chat/stream` with `{ message, session_id }`
2. SSE stream returns `content`, `tool_call`, `tool_result`, `done` events
3. Frontend renders streaming response into assistant message
4. `X-Session-Id` header persists session across requests

## Responsive Behavior (600px breakpoint, same as current)

- Narrower padding on mobile
- Quick-prompt cards remain single-column (already full-width)
- Grid cards in guided mode stay 2-column
- Slightly smaller font sizes

## Migration Notes

- Rewrite all three static files (index.html, style.css, chat.js) from scratch
- Remove purple gradient, keep structure minimal
- Backend unchanged (main.py, routes/chat.py, agent/ remain as-is)
- Remove emoji-heavy welcome icon, use single globe 🌍 only
