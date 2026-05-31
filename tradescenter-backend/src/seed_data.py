from src.supabase_client import get_supabase_client
from uuid import uuid4


def upsert_seed_data():
    supabase = get_supabase_client()

    users = [
        {
            "email": "owner1@tradescenter.ca",
            "first_name": "Maya",
            "last_name": "Singh",
            "user_type": "homeowner",
            "location": "Calgary",
        },
        {
            "email": "contractor1@tradescenter.ca",
            "first_name": "Luca",
            "last_name": "Bennett",
            "user_type": "contractor",
            "location": "Calgary",
        },
    ]
    supabase.table("users").upsert(users, on_conflict="email").execute()

    homeowner = (
        supabase.table("users")
        .select("id")
        .eq("email", "owner1@tradescenter.ca")
        .limit(1)
        .execute()
        .data[0]
    )
    contractor_user = (
        supabase.table("users")
        .select("id")
        .eq("email", "contractor1@tradescenter.ca")
        .limit(1)
        .execute()
        .data[0]
    )

    contractor = (
        supabase.table("contractors")
        .upsert(
            {
                "user_id": contractor_user["id"],
                "business_name": "North Star Renovations",
                "description": "Residential renovation and finishing specialists.",
                "service_areas": ["Calgary", "Airdrie"],
                "specialties": ["Kitchen", "Basement", "Flooring"],
                "verified": True,
                "rating": 4.8,
                "total_reviews": 12,
            },
            on_conflict="user_id",
        )
        .execute()
        .data[0]
    )

    project_payload = {
        "client_id": homeowner["id"],
        "contractor_id": contractor["id"],
        "title": "Main floor kitchen remodel",
        "description": "Full redesign with cabinetry and electrical updates.",
        "category": "Kitchen",
        "location": "Calgary",
        "budget_min": 30000,
        "budget_max": 50000,
        "status": "in_progress",
        "priority": "high",
    }
    project = supabase.table("projects").insert(project_payload).execute().data[0]

    supabase.table("project_milestones").insert(
        [
            {
                "project_id": project["id"],
                "title": "Design sign-off",
                "status": "completed",
                "order_index": 1,
            },
            {
                "project_id": project["id"],
                "title": "Cabinet installation",
                "status": "in_progress",
                "order_index": 2,
            },
        ]
    ).execute()

    supabase.table("reviews").upsert(
        {
            "project_id": project["id"],
            "contractor_id": contractor["id"],
            "client_id": homeowner["id"],
            "rating": 5,
            "title": "Strong communication and quality",
            "comment": "Everything has been on schedule and very transparent.",
            "quality_rating": 5,
            "communication_rating": 5,
            "timeliness_rating": 4,
            "professionalism_rating": 5,
            "value_rating": 4,
            "verified_project": True,
        },
        on_conflict="project_id",
    ).execute()

    profile_rows = [
        {
            "auth_user_id": str(uuid4()),
            "email": "inspire-owner@tradescenter.ca",
            "display_name": "Maya Homeowner",
            "role": "user",
            "tier_status": "active",
        },
        {
            "auth_user_id": str(uuid4()),
            "email": "inspire-pro@tradescenter.ca",
            "display_name": "Luca Pro Build",
            "role": "contractor",
            "contractor_tier": "pro",
            "tier_status": "active",
        },
        {
            "auth_user_id": str(uuid4()),
            "email": "inspire-platinum@tradescenter.ca",
            "display_name": "Nova Platinum Studio",
            "role": "contractor",
            "contractor_tier": "platinum",
            "tier_status": "active",
        },
        {
            "auth_user_id": str(uuid4()),
            "email": "admin@tradescenter.ca",
            "display_name": "Admin Control",
            "role": "admin",
            "tier_status": "active",
        },
    ]
    profiles = supabase.table("profiles").insert(profile_rows).execute().data or []

    if profiles:
        pro_profile = next((p for p in profiles if p["display_name"] == "Luca Pro Build"), None)
        plat_profile = next((p for p in profiles if p["display_name"] == "Nova Platinum Studio"), None)
        user_profile = next((p for p in profiles if p["display_name"] == "Maya Homeowner"), None)

        post_rows = []
        if pro_profile:
            post_rows.append(
                {
                    "author_profile_id": pro_profile["id"],
                    "caption": "A bright kitchen refresh with warm oak tones and matte black fixtures.",
                    "category": "Kitchen",
                    "promoted": True,
                    "visibility": "public",
                }
            )
        if plat_profile:
            post_rows.append(
                {
                    "author_profile_id": plat_profile["id"],
                    "caption": "Backyard transformation with cedar pergola, gas fireplace, and lounge zone.",
                    "category": "Exterior",
                    "promoted": True,
                    "visibility": "public",
                }
            )
        if user_profile:
            post_rows.append(
                {
                    "author_profile_id": user_profile["id"],
                    "caption": "Looking for ideas to modernize our basement media room.",
                    "category": "Basement",
                    "promoted": False,
                    "visibility": "public",
                }
            )

        inserted_posts = supabase.table("posts").insert(post_rows).execute().data or []
        media_rows = []
        for index, post in enumerate(inserted_posts):
            media_rows.append(
                {
                    "post_id": post["id"],
                    "media_url": f"https://images.unsplash.com/photo-1600566752355-35792bedcfea?auto=format&fit=crop&w=1200&q=80&sig={index}",
                    "media_type": "image",
                    "order_index": 0,
                }
            )
        if media_rows:
            supabase.table("post_media").insert(media_rows).execute()

    print("Supabase seed data inserted successfully.")


if __name__ == "__main__":
    upsert_seed_data()
