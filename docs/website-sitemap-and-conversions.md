# TradesCenter Sitemap and Conversion Map

## Primary Audiences

- Homeowner: wants a trustworthy local contractor and proof of recent work.
- Contractor: wants qualified quote requests, stronger local visibility, and proof-based reputation.
- Admin/moderator: verifies contractors, reviews proof, resolves reports, and protects trust quality.

## Public Pages

| Page | Purpose | Primary CTA | Secondary CTA | Data Needed |
| --- | --- | --- | --- | --- |
| Home | Explain TradesCenter and route users into proof, contractors, or quote flow. | Request a quote | Browse verified work | Featured proof posts, top contractors, trade categories, trust stats |
| Get Inspired | Let homeowners browse project proof and save ideas. | Save project | Request similar quote | Project proof posts, trades, service areas, media, reactions |
| Contractor Directory | Search and compare local contractors. | Request quote | Save contractor | Contractors, trades, service areas, graph scores, verification status |
| Contractor Profile | Prove contractor credibility and start contact. | Request quote | Follow / save | Contractor profile, proof posts, reviews, verification records, trust graph |
| Project Proof Detail | Show completed work, media, proof items, and social context. | Request similar quote | Save / share | Project, media, proof items, comments, reactions, recommendations |
| About / Trust | Explain verification and marketplace trust model. | Browse contractors | Contractor signup | Verification process content, trust metrics |
| Contact / Emergency | Give direct contact path and urgent-service route. | Call / request emergency quote | Send message | Contact settings, trade/service area options |

## Authenticated Homeowner Pages

| Page | Purpose | Primary Action | Data Needed |
| --- | --- | --- | --- |
| Homeowner Dashboard | Summarize quote, saved, and social proof activity. | Review active quotes | Quote requests, saved contractors, unread messages, activity feed |
| Quote Request Flow | Collect a project request and route it to contractors. | Submit request | Trades, service areas, project types, uploaded media |
| Quote Detail | Track responses and messages for a request. | Reply to contractor | Quote request, quote responses, conversation, media |
| Saved Contractors | Compare saved contractors and proof. | Request quote | Saved contractors, graph scores, latest proof |
| Messages | Centralized quote and contractor conversations. | Reply | Conversations, participants, unread counts |
| Profile / Preferences | Manage homeowner profile and location. | Save preferences | Profile, service area, notification settings |

## Authenticated Contractor Pages

| Page | Purpose | Primary Action | Data Needed |
| --- | --- | --- | --- |
| Contractor Dashboard | Show leads, proof performance, and verification health. | Respond to quote | Quote inbox, proof stats, graph scores, verification records |
| Quote Inbox | Manage inbound homeowner requests. | Reply / accept lead | Quote requests, homeowner profile summary, project media |
| Proof Studio | Create and manage proof posts. | Publish proof | Projects, media, proof items, trades, service areas |
| Contractor Profile Editor | Maintain public contractor profile. | Save profile | Company info, trades, service areas, media, verification status |
| Reviews | Review feedback and recommendation activity. | Reply / report | Reviews, recommendations, moderation status |
| Subscription / Visibility | Manage paid visibility tiers if retained. | Upgrade / manage plan | Billing status, plan features, promotion metrics |

## Admin Pages

| Page | Purpose | Primary Action | Data Needed |
| --- | --- | --- | --- |
| Moderation Queue | Review comments, proof, reviews, recommendations, reports. | Approve / reject | Moderation items, reporter context, target content |
| Verification Queue | Validate contractor identity, license, insurance, and proof. | Verify / reject | Verification records, attachments, contractor profile |
| Graph Health | Detect abuse, spam, duplicate reactions, suspicious recommendations. | Investigate | Trust edges, graph scores, reports, activity events |

## Conversion Goals

| Funnel | Step 1 | Step 2 | Step 3 | Success Event |
| --- | --- | --- | --- | --- |
| Homeowner quote | Home or contractor page | Quote request flow | Submit request | `quote_request_submitted` |
| Contractor discovery | Directory | Contractor profile | Save/follow/request quote | `contractor_saved` or `quote_request_started` |
| Inspiration to quote | Get Inspired | Project proof detail | Request similar quote | `similar_quote_requested` |
| Contractor proof | Contractor dashboard | Proof Studio | Publish proof post | `project_proof_posted` |
| Social trust | Feed/profile | Trust/recommend/save | Graph score updates | `trust_edge_created` |

## V1 Out of Scope

- Native mobile apps.
- Real-time bid marketplace.
- Payment escrow.
- Full graph database.
- Public quote pricing guarantees.
- Automated license verification integrations unless already available.
