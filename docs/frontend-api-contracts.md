# TradesCenter Frontend API Contracts

## API Style

Use REST v1 resources with JSON payloads. Keep resources plural, use HTTP methods normally, paginate collections, and return stable DTOs that do not mirror raw database tables.

Base path:

```text
/api/v1
```

Standard list envelope:

```json
{
  "items": [],
  "pageInfo": {
    "limit": 24,
    "cursor": "next-cursor",
    "hasNextPage": true
  }
}
```

Standard error:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Trade is required.",
    "fieldErrors": {
      "tradeId": "Choose a trade."
    }
  }
}
```

## Shared DTOs

### TradeSummary

```ts
type TradeSummary = {
  id: string;
  slug: string;
  name: string;
  iconName?: string;
};
```

### ServiceAreaSummary

```ts
type ServiceAreaSummary = {
  id: string;
  name: string;
  province?: string;
  countryCode: string;
};
```

### GraphTrustSummary

```ts
type GraphTrustSummary = {
  localTrustScore: number;
  proofStrengthScore: number;
  recommendationScore: number;
  responseQualityScore: number;
  profileCompletenessScore: number;
  networkProximityScore: number;
  overallRankScore: number;
  signals: string[];
};
```

### ReactionSummary

```ts
type ReactionSummary = {
  trust: number;
  helpful: number;
  save: number;
  recommend: number;
  like: number;
  currentUserReactionTypes: string[];
};
```

## Contractor Search

```http
GET /api/v1/contractors?trade=plumbing&serviceArea=calgary&verified=true&sort=trust&cursor=...
```

Response:

```ts
type ContractorSearchResult = {
  id: string;
  slug: string;
  companyName: string;
  logoUrl?: string;
  coverImageUrl?: string;
  trades: TradeSummary[];
  serviceAreas: ServiceAreaSummary[];
  verificationStatus: "unverified" | "pending" | "verified" | "suspended" | "expired";
  averageRating: number;
  reviewCount: number;
  responseTimeMinutes?: number;
  proofPostCount: number;
  recentProofImageUrl?: string;
  trust: GraphTrustSummary;
  mutualSignals: string[];
};
```

## Contractor Profile

```http
GET /api/v1/contractors/{slug}
```

Response:

```ts
type ContractorProfile = ContractorSearchResult & {
  bio?: string;
  websiteUrl?: string;
  yearsInBusiness?: number;
  verificationRecords: VerificationRecordSummary[];
  proofPosts: ProjectProofCard[];
  reviews: ReviewSummary[];
  recommendations: RecommendationSummary[];
};

type VerificationRecordSummary = {
  id: string;
  recordType: "identity" | "license" | "insurance" | "business" | "project_proof";
  status: "pending" | "approved" | "rejected" | "expired";
  label: string;
  expiresAt?: string;
};
```

## Project Proof Feed

```http
GET /api/v1/proof-posts?trade=roofing&serviceArea=calgary&sort=local_trust&cursor=...
```

Response item:

```ts
type ProjectProofCard = {
  id: string;
  projectId: string;
  title: string;
  description?: string;
  contractor: {
    id: string;
    slug: string;
    companyName: string;
    logoUrl?: string;
    verificationStatus: string;
  };
  trade?: TradeSummary;
  serviceArea?: ServiceAreaSummary;
  media: ProjectMedia[];
  proofItems: ProofItemSummary[];
  reactions: ReactionSummary;
  commentCount: number;
  createdAt: string;
};

type ProjectMedia = {
  id: string;
  url: string;
  type: "image" | "video" | "document";
  phase?: "before" | "after" | "during" | "document";
  caption?: string;
  altText?: string;
};

type ProofItemSummary = {
  id: string;
  proofType: "license" | "insurance" | "inspection" | "review" | "timeline" | "photo" | "client_confirmation";
  status: "pending" | "approved" | "rejected" | "expired";
  label: string;
};
```

## Project Proof Detail

```http
GET /api/v1/proof-posts/{id}
```

Response:

```ts
type ProjectProofDetail = ProjectProofCard & {
  timeline: {
    label: string;
    date?: string;
    status: "completed" | "pending";
  }[];
  comments: CommentThread;
  relatedContractors: ContractorSearchResult[];
  relatedProofPosts: ProjectProofCard[];
};
```

## Social Feed

```http
GET /api/v1/social-feed?surface=home&trade=plumbing&serviceArea=calgary&sort=rank&cursor=...
```

Response item:

```ts
type SocialFeedItem = {
  id: string;
  actor: {
    id: string;
    type: "user" | "contractor";
    displayName: string;
    avatarUrl?: string;
  };
  verb:
    | "contractor_verified"
    | "project_proof_posted"
    | "homeowner_saved_contractor"
    | "homeowner_trusted_review"
    | "homeowner_recommended_contractor"
    | "contractor_replied_to_quote"
    | "review_published"
    | "comment_added"
    | "reaction_added"
    | "service_area_followed";
  objectType: string;
  objectId: string;
  targetType?: string;
  targetId?: string;
  trade?: TradeSummary;
  serviceArea?: ServiceAreaSummary;
  visibility: "public" | "local" | "followers" | "participant" | "admin";
  rankScore: number;
  card:
    | { type: "projectProof"; data: ProjectProofCard }
    | { type: "contractor"; data: ContractorSearchResult }
    | { type: "review"; data: ReviewSummary }
    | { type: "recommendation"; data: RecommendationSummary };
  createdAt: string;
};
```

## Comments

```http
GET /api/v1/comments?targetType=proof_post&targetId={id}
POST /api/v1/comments
```

Create payload:

```ts
type CreateCommentPayload = {
  targetType: "proof_post" | "review" | "recommendation";
  targetId: string;
  parentCommentId?: string;
  body: string;
};
```

Response:

```ts
type CommentThread = {
  items: CommentSummary[];
};

type CommentSummary = {
  id: string;
  author: {
    id: string;
    displayName: string;
    avatarUrl?: string;
    role: string;
  };
  body: string;
  moderationStatus: "pending" | "approved" | "rejected" | "hidden" | "flagged";
  reactions: ReactionSummary;
  replies: CommentSummary[];
  createdAt: string;
};
```

## Reactions and Saves

```http
POST /api/v1/reactions
DELETE /api/v1/reactions?targetType=proof_post&targetId={id}&reactionType=trust
POST /api/v1/saved-contractors
DELETE /api/v1/saved-contractors/{contractorId}
```

Reaction payload:

```ts
type CreateReactionPayload = {
  targetType: "proof_post" | "comment" | "review" | "recommendation" | "contractor";
  targetId: string;
  reactionType: "trust" | "helpful" | "save" | "recommend" | "like";
};
```

## Recommendations

```http
GET /api/v1/recommendations?contractorId={id}
POST /api/v1/recommendations
```

Payload:

```ts
type CreateRecommendationPayload = {
  contractorId?: string;
  tradeId?: string;
  projectId?: string;
  recipientUserId?: string;
  serviceAreaId?: string;
  body: string;
  visibility: "public" | "local" | "followers";
};
```

Response item:

```ts
type RecommendationSummary = {
  id: string;
  recommender: {
    id: string;
    displayName: string;
    avatarUrl?: string;
  };
  contractor?: ContractorSearchResult;
  trade?: TradeSummary;
  project?: ProjectProofCard;
  body: string;
  visibility: string;
  moderationStatus: string;
  reactions: ReactionSummary;
  createdAt: string;
};
```

## Quote Requests

```http
POST /api/v1/quote-requests
GET /api/v1/quote-requests
GET /api/v1/quote-requests/{id}
```

Create payload:

```ts
type CreateQuoteRequestPayload = {
  tradeId: string;
  serviceAreaId: string;
  title: string;
  description: string;
  timeline?: string;
  budgetMinCents?: number;
  budgetMaxCents?: number;
  preferredContact?: "email" | "phone" | "sms" | "message";
  media?: {
    url: string;
    type: "image" | "video" | "document";
    caption?: string;
  }[];
};
```

Response:

```ts
type QuoteRequestDetail = {
  id: string;
  homeowner: {
    id: string;
    displayName: string;
    serviceArea?: ServiceAreaSummary;
  };
  trade?: TradeSummary;
  serviceArea?: ServiceAreaSummary;
  title: string;
  description: string;
  timeline?: string;
  budgetMinCents?: number;
  budgetMaxCents?: number;
  preferredContact?: string;
  status: "draft" | "open" | "matched" | "closed" | "cancelled";
  media: ProjectMedia[];
  responses: QuoteResponseSummary[];
  createdAt: string;
};

type QuoteResponseSummary = {
  id: string;
  contractor: ContractorSearchResult;
  message: string;
  estimateMinCents?: number;
  estimateMaxCents?: number;
  status: "sent" | "viewed" | "shortlisted" | "accepted" | "declined" | "withdrawn";
  createdAt: string;
};
```

## Dashboards

```http
GET /api/v1/dashboard/homeowner
GET /api/v1/dashboard/contractor
```

Homeowner dashboard:

```ts
type HomeownerDashboard = {
  metrics: {
    activeQuoteRequests: number;
    unreadMessages: number;
    savedContractors: number;
    recentProofViewed: number;
  };
  activeQuotes: QuoteRequestDetail[];
  savedContractors: ContractorSearchResult[];
  recommendedContractors: ContractorSearchResult[];
  activity: SocialFeedItem[];
};
```

Contractor dashboard:

```ts
type ContractorDashboard = {
  metrics: {
    newQuoteRequests: number;
    responseRate: number;
    proofPostCount: number;
    averageRating: number;
  };
  verification: VerificationRecordSummary[];
  quoteInbox: QuoteRequestDetail[];
  proofPerformance: ProjectProofCard[];
  graphTrust: GraphTrustSummary;
  activity: SocialFeedItem[];
};
```

## Messages

```http
GET /api/v1/conversations
POST /api/v1/conversations
GET /api/v1/conversations/{id}/messages
POST /api/v1/conversations/{id}/messages
```

Conversation:

```ts
type ConversationSummary = {
  id: string;
  subject?: string;
  quoteRequestId?: string;
  participants: {
    id: string;
    displayName: string;
    role: string;
    avatarUrl?: string;
  }[];
  lastMessage?: {
    body: string;
    senderId: string;
    createdAt: string;
  };
  unreadCount: number;
  updatedAt: string;
};
```

## Moderation

```http
GET /api/v1/admin/moderation?status=pending
POST /api/v1/admin/moderation/{itemId}/action
```

Action payload:

```ts
type ModerationActionPayload = {
  action: "approve" | "reject" | "hide" | "flag";
  reason?: string;
};
```
