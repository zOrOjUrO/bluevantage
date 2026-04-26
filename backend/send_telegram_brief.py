import os
import httpx
from supabase import create_client

# Telegram bot credentials
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_api_base = f"https://api.telegram.org/bot{telegram_bot_token}"

# Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
)

def send_daily_brief(fisher_id):
    # Get fisher profile
    fisher = supabase.table('fisher_profiles').select('*').eq('id', fisher_id).single().execute()
    
    if not fisher.data['telegram_enabled']:
        return

    if not fisher.data.get("phone"):
        print(f"⚠ Skipping {fisher.data.get('name', fisher_id)}: no Telegram chat id configured")
        return
    
    # Get top 3 zones for their target species and home port
    zones = supabase.table('zones')\
        .select('*')\
        .eq('port_id', fisher.data['home_port_id'])\
        .order('zonescore', desc=True)\
        .limit(3)\
        .execute()
    
    # Format message
    message = f"🎣 BlueVantage Daily Brief for {fisher.data['name']}\n\n"
    message += f"Top 3 zones for {', '.join(fisher.data['target_species'])}:\n\n"
    
    for i, zone in enumerate(zones.data, 1):
        top_species = "N/A"
        species = zone.get("species") or []
        if isinstance(species, list) and len(species) > 0 and isinstance(species[0], dict):
            top_species = species[0].get("name", "N/A")

        slots_total = zone.get("slotstotal", zone.get("slots_total", 0)) or 0
        slots_filled = zone.get("slotsfilled", zone.get("slots_filled", 0)) or 0
        slots_available = max(slots_total - slots_filled, 0)
        hex_id = zone.get("hexid") or zone.get("hex_id") or "unknown"
        zone_score = zone.get("zonescore", zone.get("zone_score", 0))
        distance_km = zone.get("distancekm", zone.get("distance_km", 0))
        message += f"{i}. Zone {str(hex_id)[:8]} (Score: {zone_score})\n"
        message += f"   • Top species: {top_species}\n"
        message += f"   • {distance_km:.1f} km from port\n"
        message += f"   • {slots_available} slots available\n\n"
    
    message += "View full map: https://bluevantage.vercel.app"
    
    # Send via Telegram Bot API.
    # Current profile mapping:
    # - fisher_profiles.phone is treated as Telegram chat_id
    # - fisher_profiles.telegram_enabled is treated as notification opt-in
    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{telegram_api_base}/sendMessage",
            json={
                "chat_id": fisher.data["phone"],
                "text": message
            },
        )
        response.raise_for_status()
    
    print(f"✓ Sent Telegram brief to {fisher.data['name']}")

# Schedule this to run daily at 6 AM
if __name__ == "__main__":
    if not telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    # Get all fishers with notifications enabled
    fishers = supabase.table('fisher_profiles')\
        .select('id')\
        .eq('telegram_enabled', True)\
        .execute()
    
    for fisher in fishers.data:
        send_daily_brief(fisher['id'])
