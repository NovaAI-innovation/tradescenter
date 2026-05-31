import os

def get_stripe_client():
    import stripe

    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    stripe.api_key = secret_key
    return stripe


def stripe_enabled() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY"))
