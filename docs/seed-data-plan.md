# TradesCenter Seed Data Plan

## Purpose

Seed data should support design, local development, QA, and demos. It must make the social proof model visible: contractors should have verified work, homeowners should have quote activity, and the feed should show graph-driven trust signals.

## Trade Categories

Seed at least these trades:

- Plumbing
- HVAC
- Electrical
- Roofing
- Cabinetry
- Basement Development
- Kitchen Renovation
- Bathroom Renovation
- Landscaping
- Painting

## Service Areas

Seed at least these areas:

- Calgary, AB
- Airdrie, AB
- Cochrane, AB
- Chestermere, AB
- Okotoks, AB
- Edmonton, AB
- Red Deer, AB

## Users

| Persona | Role | Purpose |
| --- | --- | --- |
| Casey Homeowner | homeowner | Primary demo homeowner dashboard and saved contractors |
| Maria J. | homeowner | Recommendation and basement request examples |
| Devon K. | homeowner | Review/comment/reaction examples |
| Arrow Plumbing Admin | contractor | Verified contractor with proof posts and quote responses |
| Northline Cabinetry Admin | contractor | Top-ranked proof-heavy contractor |
| CR Roofing Admin | contractor | Partially verified/reviewing contractor |
| A5 Development Admin | contractor | Basement development contractor |
| TradesCenter Admin | admin | Moderation and verification queue examples |

## Contractor Profiles

### Arrow Plumbing & HVAC

- Trades: Plumbing, HVAC
- Areas: Calgary, Airdrie, Chestermere
- Verification: license approved, insurance approved, project proof approved
- Proof posts: water heater replacement, emergency shutoff cleanup, furnace replacement
- Graph signals: trusted by 18 local homeowners, 42 proof projects, average response 2.6h

### Northline Cabinetry

- Trades: Cabinetry, Kitchen Renovation
- Areas: Calgary, Cochrane
- Verification: fully verified
- Proof posts: custom kitchen cabinetry, built-in mudroom storage, walnut vanity
- Graph signals: 18 verified projects, strong saves/recommendations

### CR Roofing

- Trades: Roofing
- Areas: Calgary, Okotoks, Airdrie
- Verification: insurance approved, license pending renewal
- Proof posts: hail damage replacement, flat roof repair
- Graph signals: 11 reviewed jobs, moderation/verification edge case

### A5 Development

- Trades: Basement Development, Electrical, Painting
- Areas: Calgary, Airdrie
- Verification: pending project proof
- Proof posts: basement framing and finish, legal suite rough-in
- Graph signals: quote-heavy contractor with lower proof completeness

## Project Proof Posts

Each proof post should include:

- Contractor
- Trade
- Service area
- Title
- Short description
- Before image
- After image
- Proof items
- Reactions
- Comments
- Graph signals

Minimum seed posts:

| Title | Contractor | Trade | Area | Proof Items |
| --- | --- | --- | --- | --- |
| Emergency Water Heater Replacement | Arrow Plumbing & HVAC | Plumbing | Airdrie | License, insurance, 2-day turnaround, client reviewed |
| Custom Oak Kitchen Cabinetry | Northline Cabinetry | Cabinetry | Calgary | Insurance, material invoice, client reviewed |
| Hail Damage Roof Replacement | CR Roofing | Roofing | Okotoks | Insurance, inspection, review pending |
| Basement Development Rough-In | A5 Development | Basement Development | Calgary | Timeline, inspection pending |
| Furnace Replacement Before Winter | Arrow Plumbing & HVAC | HVAC | Calgary | License, insurance, client confirmed |
| Built-In Mudroom Storage | Northline Cabinetry | Cabinetry | Cochrane | Client reviewed, after photos |

## Quote Requests

Seed at least:

- Open quote request: basement development, Calgary, spring timeline.
- Open quote request: roofing repair, Airdrie, urgent timeline.
- Matched quote request: water heater replacement, Airdrie.
- Closed quote request: cabinetry project, Calgary.

Each quote request needs:

- Homeowner
- Trade
- Service area
- Description
- Timeline
- Optional budget range
- Media placeholders
- Responses from 1-3 contractors
- Conversation thread

## Social Graph Events

Seed graph activity to populate social proof modules:

- Casey follows Plumbing and Calgary service area.
- Casey saves Arrow Plumbing & HVAC.
- Maria recommends A5 Development for basement work.
- Devon trusts Arrow Plumbing's water heater proof post.
- Northline posts a verified cabinetry project.
- TradesCenter Admin verifies Arrow Plumbing insurance.
- CR Roofing license record expires soon.
- Casey comments on a proof post.
- Maria shares a proof post internally.

## Feed Ranking Examples

Use these expected rank outcomes for QA:

1. A fully verified contractor with recent local proof outranks an older saved contractor.
2. A contractor recommended by a trusted local homeowner outranks a contractor with only generic likes.
3. A proof post with before/after media outranks a text-only post.
4. A contractor with expired verification is demoted even if they have many reactions.
5. Quote participant activity is hidden from public feeds unless converted into approved proof.

## Dashboard Seed Metrics

### Homeowner Dashboard

- Active quote requests: 3
- Saved contractors: 5
- Unread messages: 4
- Recent proof viewed: 8
- Recommended contractors: 3

### Contractor Dashboard

- New quote requests: 6
- Response rate: 91%
- Average response: 2.6h
- Proof post count: 42
- Verification health: 94%

## Moderation Queue

Seed:

- Pending comment with normal content.
- Flagged recommendation with promotional language.
- Pending project proof item.
- Expiring license verification record.
- Hidden review with disputed content.

## Asset Requirements

For each seeded proof post:

- `before` image
- `after` image
- thumbnail image
- alt text

If real images are unavailable, use generated dark industrial or renovation imagery with clear labels in the seed metadata so the assets can be replaced later.
