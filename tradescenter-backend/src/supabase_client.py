import os

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set. "
            "Add them to your environment or .env file."
        )

    return create_client(url, key)

