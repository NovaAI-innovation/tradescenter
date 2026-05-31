# TradesCenter Website Implementation Plan

## Target Result

Build the full TradesCenter website around the current direction: a dark industrial contractor marketplace with safety-orange accents, strong project-proof imagery, clear homeowner workflows, and standard, reliable UI patterns. The finished site should feel credible for trades, easy for homeowners to scan, and polished enough to support contractor discovery, project inspiration, quote requests, and social proof.

## Skill Groups

### Product and Scope

- `requirements-clarity`: Lock sitemap, audience, conversion goals, and feature scope before detailed design starts.

### Data and Domain Architecture

- `database-schema-designer`: Model the core marketplace entities, relationships, constraints, and access patterns that the website and dashboards depend on.
- `api-design-principles`: Use when turning the data model into frontend-facing API contracts for search, profiles, quote requests, messaging, and dashboards.

### Visual and UX Design

- `frontend-design`: Establish the bold visual direction and page-level composition.
- `ui-ux-pro-max`: Critique each section, remove weak elements, and enforce visual hierarchy.
- `imagegen`: Produce custom hero, project-proof, category, and placeholder imagery where real assets are missing.

### Design System and UI Components

- `design-system-starter`: Convert the direction into tokens, components, layout rules, and accessibility standards.
- `mui`: Implement production UI with MUI patterns, theme tokens, responsive layouts, and component variants.
- `dashboard-creator`: Shape KPI, proof, contractor ranking, quote status, and homeowner workspace views.

### Frontend Engineering

- `react-dev`: Build typed React components, data-driven page sections, hooks, and reusable UI.
- `react-useeffect`: Keep effects limited to real synchronization, avoiding unnecessary state/effect complexity.
- `nextjs-app-router-patterns`: Use if the frontend is Next.js; structure routes, layouts, metadata, loading states, and server/client boundaries.

### Content and Messaging

- `writing-clearly-and-concisely`: Tighten all UI copy, CTAs, empty states, trust messaging, and contractor proof language.

### QA and Release Validation

- `qa-test-planner`: Define smoke, regression, visual, responsive, and accessibility test coverage.

## Recommended Skill Sequence

1. Product and scope
2. Data and domain architecture
3. Visual and UX design
4. Design system and UI components
5. Frontend engineering
6. Content and messaging
7. QA and release validation

## Phase 1: Scope and Product Architecture

**Goal:** Decide what the whole website must include before designing more screens.

**Pages:**
- Home
- Get Inspired
- Contractor Directory
- Contractor Profile
- Project Proof Detail
- Quote Request Flow
- Homeowner Dashboard
- Contractor Dashboard
- Messages / Quote Inbox
- About / Trust & Verification
- Contact / Emergency Service CTA

**Key decisions:**
- Primary visitor: homeowner needing trusted local trades.
- Primary conversion: request a quote.
- Secondary conversions: browse verified work, save contractor, contact contractor, follow project proof.
- Trust model: license, insurance, reviews, completed projects, response time, service area.

**Deliverables:**
- Sitemap: see `website-sitemap-and-conversions.md`
- User journey map: see `website-sitemap-and-conversions.md`
- Content inventory: see `website-sitemap-and-conversions.md`
- Conversion goals per page: see `website-sitemap-and-conversions.md`
- Out-of-scope list for v1: see `website-sitemap-and-conversions.md`

**Exit criteria:**
- Every page has a purpose, primary CTA, and minimum required content.

## Phase 2: Data Model and Domain Architecture

**Goal:** Define the domain model before building UI screens so the website maps to real marketplace data instead of static page assumptions.

**Core entities:**
- `users`: shared account identity for homeowners, contractors, admins, and support.
- `homeowner_profiles`: homeowner display profile, location, saved contractors, and project preferences.
- `contractor_profiles`: company identity, bio, verification summary, service radius, rating, response metrics, and public profile settings.
- `trades`: trade categories such as plumbing, HVAC, roofing, electrical, cabinetry, landscaping.
- `service_areas`: cities, postal regions, radius rules, and geocoded coverage.
- `contractor_trades`: many-to-many mapping between contractors and trades.
- `contractor_service_areas`: many-to-many mapping between contractors and service areas.
- `projects`: completed or requested project records.
- `project_media`: before/after images, documents, thumbnails, ordering, captions, and alt text.
- `project_proof_items`: license checks, insurance checks, inspection documents, client reviews, completion timeline, and proof status.
- `quote_requests`: homeowner project requests, selected trade, location, timeline, description, budget range, status.
- `quote_request_media`: photos or attachments uploaded by homeowners.
- `quote_responses`: contractor responses to quote requests, proposed next step, estimate range, status, and timestamps.
- `messages`: conversation records tied to quote requests or contractor inquiries.
- `reviews`: homeowner ratings, written feedback, project reference, moderation status.
- `verification_records`: license, insurance, identity, admin review, expiry dates, and verification status.
- `saved_contractors`: homeowner saved/favorite contractors.
- `activity_events`: feed/dashboard events such as project posted, quote submitted, response received, review added.
- `social_follows`: directed follow edges between homeowners, contractors, projects, trades, or service areas.
- `trust_edges`: explicit trust signals such as homeowner trusts contractor, homeowner trusts review, contractor endorsed by another contractor, or admin verified proof.
- `post_comments`: comments on project proof posts, quote inspiration posts, and contractor updates.
- `post_reactions`: lightweight reactions such as trust, helpful, save, recommend, and like.
- `shares`: share events for project proof posts, contractor profiles, or inspiration collections.
- `recommendations`: structured recommendations from one user to another for a contractor, trade, or project type.
- `social_feed_items`: denormalized feed records generated from posts, proof events, recommendations, reviews, and follows.
- `graph_scores`: derived social/proof ranking metrics such as local trust score, proof strength, recommendation count, and network proximity.

**Primary relationships:**
- One user can have one homeowner profile, contractor profile, or both.
- One contractor can serve many trades and many service areas.
- One project belongs to a contractor and may optionally link to a homeowner/review.
- One project can have many media assets and many proof items.
- One quote request belongs to one homeowner and one trade.
- One quote request can receive many contractor responses.
- One quote request can have one or more message threads.
- One review links a homeowner, contractor, and optionally a completed project.
- One user can follow many users, contractors, trades, projects, or service areas.
- One project proof post can have many comments, reactions, saves, and shares.
- One recommendation links a recommending user, a recipient or audience, and a recommended contractor/trade/project.
- One contractor can accumulate many trust edges from reviews, follows, proof interactions, verification records, and recommendations.
- One social feed item references the source entity that created it, such as a project, review, recommendation, quote milestone, or contractor update.

**Frontend access patterns to optimize for:**
- Search contractors by trade, location, verification status, rating, response time.
- Load contractor profile with services, proof posts, reviews, and quote CTA.
- Load project proof feed by location/trade/date.
- Load personalized social proof feed from followed trades, contractors, service areas, and homeowner network activity.
- Load homeowner dashboard counts: active quotes, saved contractors, unread messages, recent proof.
- Load contractor dashboard counts: new quote requests, response rate, verification health, proof posts.
- Filter inspiration gallery by trade, room/project type, budget range, and location.
- Rank contractors by local trust graph, recent verified work, proximity, response quality, and social recommendations.
- Show mutual proof signals such as "3 homeowners near you saved this contractor" or "Recommended by a verified reviewer."

**Schema rules:**
- Use UUID primary keys if the system is distributed or Supabase/Postgres-based.
- Add foreign keys for all relationships.
- Index all foreign keys.
- Index common filters: `trade_id`, `service_area_id`, `contractor_id`, `homeowner_id`, `status`, `created_at`, `verification_status`.
- Store money/ranges with decimal or integer cents, never float.
- Store timestamps in UTC.
- Keep media metadata separate from project records.
- Keep verification records separate from contractor profiles so expiry/history is auditable.
- Store social graph edges as explicit rows with `source_type`, `source_id`, `target_type`, `target_id`, `edge_type`, and timestamps if polymorphic relationships are needed.
- Use stricter typed join tables where integrity matters most, such as user-to-user follows or homeowner-to-contractor saves.
- Denormalize social feed items and graph scores for read performance; keep canonical events in normalized source tables.
- Add uniqueness constraints to prevent duplicate follows, saves, reactions, and recommendations from the same actor to the same target.
- Add moderation status to comments, reviews, shares, and recommendations.

**API contract outputs needed for frontend:**
- Contractor search result DTO.
- Contractor profile DTO.
- Project proof card DTO.
- Social feed item DTO.
- Comment thread DTO.
- Reaction summary DTO.
- Recommendation DTO.
- Graph trust summary DTO.
- Quote request detail DTO.
- Quote request creation payload.
- Dashboard summary DTOs for homeowner and contractor.
- Message thread DTO.
- Review summary DTO.

**Deliverables:**
- Entity relationship diagram.
- SQL schema or ORM schema: see `tradescenter-domain-schema.sql`.
- Index strategy: see `tradescenter-domain-schema.sql`.
- Migration plan.
- Frontend DTO/API contract document: see `frontend-api-contracts.md`.
- Seed/demo data matching the website pages: see `seed-data-plan.md`.
- Social graph event taxonomy.
- Feed ranking rules.
- Moderation and privacy rules for graph interactions.

**Exit criteria:**
- Every UI section has a known data source or documented static/content source.

### Social Graph Model Detail

**Graph node types:**
- `user`
- `homeowner_profile`
- `contractor_profile`
- `trade`
- `service_area`
- `project`
- `project_proof_post`
- `review`
- `quote_request`
- `recommendation`

**Graph edge types:**
- `follows`: user follows contractor, user, trade, service area, or project.
- `saved`: homeowner saves contractor, project proof, or inspiration post.
- `trusted`: user marks contractor, review, proof post, or recommendation as trusted.
- `recommended`: user recommends contractor or project proof to another user/audience.
- `reviewed`: homeowner reviews contractor/project.
- `commented`: user comments on proof post or recommendation.
- `reacted`: user reacts to post, comment, review, or recommendation.
- `shared`: user shares project proof, contractor profile, or inspiration collection.
- `verified`: admin/system verifies contractor, license, insurance, project proof, or review.
- `served`: contractor serves trade or service area.
- `completed`: contractor completed project.

**Canonical graph event examples:**
- `contractor_verified`
- `project_proof_posted`
- `homeowner_saved_contractor`
- `homeowner_trusted_review`
- `homeowner_recommended_contractor`
- `contractor_replied_to_quote`
- `review_published`
- `comment_added`
- `reaction_added`
- `service_area_followed`

**Feed item fields:**
- `id`
- `actor_type`
- `actor_id`
- `verb`
- `object_type`
- `object_id`
- `target_type`
- `target_id`
- `service_area_id`
- `trade_id`
- `visibility`
- `rank_score`
- `created_at`
- `metadata`

**Visibility rules:**
- `public`: visible to all users and anonymous visitors where appropriate.
- `local`: visible to users in matching service areas.
- `followers`: visible to followers or saved-contractor relationships.
- `participant`: visible only to quote/message participants.
- `admin`: visible only to admins/moderators.

**Moderation rules:**
- Comments, reviews, and recommendations require `moderation_status`.
- Possible statuses: `pending`, `approved`, `rejected`, `hidden`, `flagged`.
- Public feeds show only approved public/local content.
- Contractor profile pages show approved proof, approved reviews, and verified records.
- Quote request activity is never public unless converted into an approved project proof post.

**Ranking inputs:**
- Verification strength: license active, insurance active, admin proof approval.
- Social proximity: followed by users near me, saved by users near me, recommended by trusted profiles.
- Recency: new completed work and recent responses rank higher.
- Project relevance: trade, service area, project type, budget range.
- Quality: review score, detailed reviews, proof completeness, before/after media presence.
- Responsiveness: quote response time and reply completion rate.
- Negative signals: hidden content, rejected proof, stale verification, unresolved complaints.

**Graph score outputs:**
- `local_trust_score`
- `proof_strength_score`
- `recommendation_score`
- `response_quality_score`
- `profile_completeness_score`
- `network_proximity_score`
- `overall_rank_score`

**Graph-specific UI surfaces:**
- Personalized verified feed.
- "Recommended near you" contractor module.
- Mutual proof indicators on contractor cards.
- Trust graph panel on contractor profiles.
- Proof graph visualization on project detail pages.
- Activity timeline in homeowner dashboard.
- Contractor proof performance panel.
- Review/recommendation context blocks.

**Graph implementation caution:**
- Start with relational tables and denormalized feed/score tables.
- Do not introduce a graph database in v1 unless query complexity proves relational modeling insufficient.
- Keep raw events append-only where possible.
- Rebuild derived feed and score records from canonical events when ranking rules change.

## Phase 3: Visual Direction and Design Principles

**Goal:** Turn the current prototype into a durable visual language.

**Direction:**
- Dark industrial foundation: black, charcoal, tool steel.
- Orange as a functional signal: CTAs, active states, rank markers, proof highlights.
- Image-first hero and proof sections.
- Cards stay practical and scan-friendly, not decorative.
- Each section gets one visual priority, with supporting elements reduced.

**Design principles:**
- Proof beats claims.
- One dominant action per section.
- Contractor credibility should be visible before users click.
- Homeowners should understand the next step in under 3 seconds on mobile.
- Avoid generic SaaS visuals, purple gradients, floating blobs, and equal-weight card grids.

**Deliverables:**
- Moodboard references
- Final color palette
- Typography scale
- Image style guide
- Motion rules

**Exit criteria:**
- The current `design-preview.html` direction is translated into a repeatable system.

## Phase 4: Design System Foundation

**Goal:** Create reusable tokens and components before building pages.

**Tokens:**
- Color: background, surface, surface-raised, line, text, muted, orange, orange-hover, success, warning, error.
- Spacing: 4px/8px-based scale.
- Radius: 8px default, full radius only for avatars/chips.
- Typography: display, section heading, card heading, body, caption, metric.
- Shadow: restrained dark-surface elevation.
- Breakpoints: mobile, tablet, desktop, wide desktop.

**Core components:**
- AppHeader
- UtilityBar
- Sidebar / RailNav
- Button
- IconButton
- Card
- Badge / VerificationBadge
- Avatar
- ContractorCard
- ProjectProofCard
- QuoteRequestCard
- KPIStat
- ProgressMetric
- DataTable
- EmptyState
- Modal/Dialog
- FormField

**MUI implementation notes:**
- Use theme tokens rather than one-off colors.
- Prefer `sx` objects for component-level styling.
- Use `slots` / `slotProps` for MUI v7 customization.
- Keep cards at 8px radius unless the design system says otherwise.
- Use MUI layout primitives where they reduce custom CSS.

**Deliverables:**
- Theme file
- Component inventory
- Component prop contracts
- Accessibility notes per component
- Story/demo page if the project supports it

**Exit criteria:**
- Pages can be built from shared components instead of ad hoc markup.

## Phase 5: Asset and Image System

**Goal:** Replace weak placeholders with credible visual assets.

**Asset sets:**
- Hero background images
- Trade category images
- Before/after project proof images
- Contractor profile cover images
- Avatar and company logo placeholders
- Trust/verification visuals

**Image rules:**
- Use real or generated raster images, not abstract SVG decoration.
- Keep left-side negative space for hero copy.
- Use dark overlays only when needed for contrast.
- Avoid stock-like smiling portraits unless actual contractor/team content exists.
- Optimize files for web delivery.

**Deliverables:**
- `/assets/hero/`
- `/assets/categories/`
- `/assets/project-proof/`
- Image naming convention
- Alt text guidance

**Exit criteria:**
- No critical page depends on low-quality placeholder art.

## Phase 6: Public Marketing Pages

**Goal:** Build the public website experience.

**Home page sections:**
- Header and emergency utility bar
- Image-led hero with quote CTA
- Verified project proof feed preview
- Trade categories
- How proof works
- Top verified contractors near you
- Homeowner quote workflow
- Trust and verification explanation
- Final quote CTA
- Footer

**Get Inspired:**
- Project gallery
- Trade/category filters
- Before/after cards
- Save and request quote actions

**Contractor Directory:**
- Search and filters
- Contractor cards with proof counts
- Trade, service area, verification, rating, response time

**Contractor Profile:**
- Cover image
- Verification summary
- Services
- Completed proof posts
- Reviews
- Quote CTA

**About / Trust:**
- Marketplace model
- Verification process
- Homeowner safety guidance
- Contractor onboarding CTA

**Exit criteria:**
- A homeowner can land, understand the offer, browse proof, and start a quote request.

## Phase 7: Quote Request and Forms

**Goal:** Make conversion flows usable and trustworthy.

**Quote request steps:**
- Trade/category
- Location/service area
- Project description
- Timeline
- Budget range if needed
- Photo upload placeholder
- Preferred contact method
- Review and submit

**Form rules:**
- One clear step at a time.
- Required fields are explicit.
- Error messages are specific.
- Mobile form controls are large enough.
- Confirmation page explains what happens next.

**Deliverables:**
- Quote request flow
- Validation states
- Confirmation state
- Error and empty states

**Exit criteria:**
- Users can complete the quote request on mobile without layout issues.

## Phase 8: Dashboard and Workspace Views

**Goal:** Build authenticated-style operational screens with dashboard patterns.

**Homeowner dashboard:**
- Active quote requests
- Saved contractors
- Recent proof viewed
- Messages
- Recommended contractors
- Project timeline/status

**Contractor dashboard:**
- New quote requests
- Response rate
- Proof posts
- Verification status
- Reviews
- Service areas

**Dashboard components:**
- KPI cards
- Status chips
- Progress indicators
- Tables
- Activity feed
- Empty states
- Action menus

**Exit criteria:**
- Dashboard pages feel quieter, denser, and more utilitarian than the marketing pages.

## Phase 9: Responsive and Interaction Pass

**Goal:** Make the site feel intentional across mobile, tablet, and desktop.

**Breakpoints to verify:**
- 320px
- 390px
- 768px
- 1024px
- 1280px
- 1440px

**Checks:**
- No horizontal overflow.
- Header behavior is clear.
- Hero copy remains readable.
- Cards do not collapse awkwardly.
- Buttons fit text.
- Tables have mobile-safe patterns.
- Sticky rails do not trap content.

**Motion rules:**
- Use restrained entrance motion.
- Avoid constant pulsing.
- Respect reduced motion.
- Use hover states for clarity, not spectacle.

**Exit criteria:**
- Core pages pass responsive screenshot review.

## Phase 10: Accessibility and Content Quality

**Goal:** Make the site usable and credible.

**Accessibility checks:**
- Semantic landmarks.
- Keyboard navigation.
- Visible focus states.
- Contrast meets WCAG AA.
- Buttons and links have accessible names.
- Forms announce errors.
- Images have useful alt text or are marked decorative.

**Copy checks:**
- CTAs use concrete verbs.
- Trust claims are specific.
- Empty states tell users what to do next.
- Contractor proof language is consistent.
- Emergency/contact copy is not overused.

**Exit criteria:**
- No known accessibility blockers.
- UI copy is short and action-oriented.

## Phase 11: Implementation Hardening

**Goal:** Prepare the website for real use.

**Technical checks:**
- Build passes.
- Typecheck passes.
- Lint passes.
- No console errors.
- No missing image assets.
- Page metadata is set.
- Images are optimized.
- Loading states exist where data is async.
- Error boundaries or fallback states exist where needed.

**Performance checks:**
- Compress images.
- Lazy load below-the-fold media.
- Avoid unnecessary client-side JavaScript.
- Keep animations CSS-first where possible.

**Exit criteria:**
- Website is stable under local production build.

## Phase 12: QA and Release Validation

**Goal:** Prove the site is ready rather than assuming it is.

**Smoke tests:**
- Home page loads.
- Navigation works.
- Quote CTA opens the right flow.
- Contractor cards link to profile pages.
- Filters do not break layout.
- Forms validate and submit or mock-submit.

**Visual regression checks:**
- Home desktop/mobile.
- Get Inspired desktop/mobile.
- Contractor directory desktop/mobile.
- Contractor profile desktop/mobile.
- Quote flow desktop/mobile.
- Dashboard desktop/mobile.

**Browser targets:**
- Chrome
- Edge
- Firefox
- Safari if available

**Exit criteria:**
- No P0/P1 UI, navigation, responsiveness, or form blockers remain.

## Phase 13: Launch Package

**Goal:** Leave the project maintainable after the first full website pass.

**Deliverables:**
- Final sitemap
- Component inventory
- Design token documentation
- Asset inventory
- QA checklist
- Known limitations
- Follow-up backlog

**Recommended v2 backlog:**
- Real contractor onboarding flow
- Real project media upload
- Geolocation/service-area matching
- Review moderation
- Saved project boards
- SEO landing pages by trade and city
- Analytics events for quote funnel

## Build Order Summary

1. Lock sitemap and conversion goals.
2. Define data model, relationships, and frontend API contracts.
3. Define social graph events, edges, feed generation, visibility, and ranking rules.
4. Finalize dark/orange visual system.
5. Build design tokens and MUI theme.
6. Create core shared components.
7. Build public home page.
8. Build Get Inspired and contractor directory.
9. Build contractor profile and proof detail pages.
10. Build personalized proof feed and graph-driven contractor modules.
11. Build quote request flow.
12. Build homeowner and contractor dashboards.
13. Replace placeholder imagery.
14. Run responsive, accessibility, and visual QA.
15. Harden build and document launch package.

## Definition of Done

The website is complete when a homeowner can:
- Understand TradesCenter from the home page.
- Browse verified local project proof.
- See social proof from local activity, recommendations, saves, reviews, and trusted profiles.
- Compare contractors.
- Open a contractor profile.
- Start and complete a quote request.
- View quote/request activity in a dashboard-style workspace.

The implementation is complete when:
- Shared components and tokens drive the UI.
- All target pages are responsive.
- No browser console errors remain.
- Accessibility and contrast issues are resolved.
- Build, lint, typecheck, and smoke tests pass.
