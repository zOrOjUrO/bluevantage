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
    
    if not fisher.data.get('telegram_enabled'):
        return

    # Use 'phone' as Telegram chat_id
    chat_id = fisher.data.get("phone")
    if not chat_id:
        print(f"⚠ Skipping {fisher.data.get('name', fisher_id)}: no Telegram chat id (phone) configured")
        return

    # Get top 3 zones for their home port
    zones = supabase.table('zones')\
        .select('*')\
        .eq('port_id', fisher.data.get('home_port_id'))\
        .order('zonescore', desc=True)\
        .limit(3)\
        .execute()

    # Format message
    message = f"🎣 *BlueVantage Daily Brief for {fisher.data.get('name')}*

"
    target_species = ", ".join(fisher.data.get('target_species', []))
    message += f"Best zones for {target_species}:

"

    for i, zone in enumerate(zones.data, 1):
        species = zone.get("species") or []
        top_sp = species[0].get("name", "N/A") if species and isinstance(species[0], dict) else "N/A"
        
        slots_total = zone.get("slotstotal") or 0
        slots_filled = zone.get("slotsfilled") or 0
        available = max(slots_total - slots_filled, 0)
        
        hex_id = zone.get("hexid") or "unknown"
        score = zone.get("zonescore") or 0feat: Finalize telegram brief formatting and notification logic
        dist = zone.get("distancekm") or 0feat: Finalize telegram brief formatting and notification logic
feat: Finalize telegram brief formatting and notification logic
        message += f"{i}. *Zone {str(hex_id)[:8]}* (Score: {score})feat: Finalifefeat: Finalize telegram brief formatting and notification logicat: Finalize telegram brief formatting and notification logicze telegram brief formatting and notification logic
"
        message += f" • Top species: {top_sp}
"
        message += f" • {dist:.1f} km from port
"
        message += f" • {available} slots available

"

    message += "🔗 [View full map](https://bluevantage.vercel.app)"

    # Send via Telegram
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(
                f"{telegram_api_base}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
            )
            res.raise_for_status()
            print(f"✓ Sent Telegram brief to {fisher.data.get('name')}")
    except Exception as e:
        print(f"❌ Failed to send to {fisher.data.get('name')}: {e}")

if __name__ == "__main__":
    if not telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN not set, skipping...")
    else:
        fishers = supabase.table('fisher_profiles').select('id').eq('telegram_enabled', True).execute()
        for f in fishers.data:
            send_daily_brief(f['id'])
