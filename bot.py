import os
import json
import asyncio
import aiohttp
from datetime import datetime, timezone
import config

API_KEY = config.API_KEY
WEBHOOK = config.WEBHOOK
COLLECTIONS = config.COLLECTIONS
CHECK_INTERVAL = config.CHECK_INTERVAL
STATE_FILE = config.STATE_FILE

HEADERS = {
    "accept": "application/json",
    "x-api-key": API_KEY
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


state = load_state()


def format_address(addr):
    if not addr or str(addr).lower() == "unknown":
        return "Unknown"
    addr_str = str(addr)
    if addr_str.startswith("0x") and len(addr_str) == 42:
        return f"[{addr_str[:6]}...{addr_str[-4:]}](https://opensea.io/{addr_str})"
    return addr_str


def get_event_identifier(event):
    asset = event.get("asset") or event.get("nft") or {}
    return str(asset.get("identifier") or "")


async def send_discord(session, slug, event):

    asset = event.get("asset") or event.get("nft") or {}

    title = asset.get("name") or f"#{asset.get('identifier','Unknown')}"

    image = (
        asset.get("display_image_url")
        or asset.get("image_url")
        or asset.get("original_image_url")
    )

    url = asset.get("opensea_url")

    # Parse payment/price information
    payment = event.get("payment", {})
    price_value = payment.get("value") or payment.get("quantity")
    price_decimals = payment.get("decimals", 18)
    price_symbol = payment.get("symbol", "ETH")

    if price_value is not None:
        try:
            price = float(price_value) / (10 ** int(price_decimals))
            price_str = f"**{price:.4f} {price_symbol}**"
        except Exception:
            price_str = "Unknown"
    else:
        price_str = "Unknown"

    seller = format_address(event.get("maker") or event.get("seller"))
    buyer = format_address(event.get("taker") or event.get("recipient") or event.get("buyer"))

    embed = {
        "title": "💰 New Sale Detected",
        "color": 0x3498DB,
        "url": url,
        "thumbnail": {
            "url": image
        } if image else {},
        "image": {
            "url": image
        } if image else {},
        "fields": [
            {
                "name": "Collection",
                "value": slug,
                "inline": True
            },
            {
                "name": "NFT",
                "value": title,
                "inline": True
            },
            {
                "name": "Price",
                "value": price_str,
                "inline": True
            },
            {
                "name": "Seller",
                "value": seller,
                "inline": True
            },
            {
                "name": "Buyer",
                "value": buyer,
                "inline": True
            },
            {
                "name": "Chain",
                "value": event.get("chain", "Unknown").capitalize(),
                "inline": True
            },
            {
                "name": "Transaction",
                "value": f"[View Transaction](https://polygonscan.com//tx/{event.get('transaction')})" if event.get("transaction") and str(event.get("transaction")).startswith("0x") else str(event.get("transaction", "Unknown")),
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "embeds": [embed]
    }

    async with session.post(WEBHOOK, json=payload) as r:
        if r.status not in (200, 204):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Discord webhook error: HTTP {r.status} - {await r.text()}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Discord alert sent successfully.")


async def check_collection(session, slug):
    after_timestamp = None
    last_seen_id = ""

    last_seen_state = state.get(slug)
    if isinstance(last_seen_state, dict):
        last_seen_id = last_seen_state.get("id", "")
        after_timestamp = last_seen_state.get("timestamp")
    else:
        last_seen_id = last_seen_state or ""

    if not after_timestamp and config.START_TIME:
        after_timestamp = config.START_TIME

    url = (
        f"https://api.opensea.io/api/v2/events/collection/{slug}"
        "?event_type=sale"
        "&limit=20"
    )
    if after_timestamp:
        # Subtract 1 to safely capture events that occurred in the same block/second
        url += f"&after={after_timestamp - 1}"

    try:
        async with session.get(url, headers=HEADERS) as r:
            if r.status != 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching {slug}: HTTP {r.status} - {await r.text()}")
                return
            data = await r.json()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Network error querying {slug}: {e}")
        return

    events = data.get("asset_events", [])
    if not events:
        return

    events.reverse()  # Process oldest to newest (chronological order)

    # Filter out already processed events up to and including last_seen_id
    event_ids = [
        event.get("transaction", "")
        + "_"
        + get_event_identifier(event)
        for event in events
    ]

    if last_seen_id and last_seen_id in event_ids:
        idx = event_ids.index(last_seen_id)
        events = events[idx + 1:]

    if not events:
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(events)} new sale(s) for collection '{slug}'!")

    newest_id = last_seen_id
    newest_timestamp = after_timestamp

    for event in events:
        unique = (
            event.get("transaction", "")
            + "_"
            + get_event_identifier(event)
        )

        event_time = event.get("event_timestamp")
        if event_time is not None:
            try:
                event_time = int(event_time)
            except (ValueError, TypeError):
                event_time = None

        if event_time is None:
            event_time = int(datetime.utcnow().timestamp())

        newest_id = unique
        newest_timestamp = event_time

        asset = event.get("asset") or event.get("nft") or {}
        identifier = asset.get("identifier", "Unknown")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending Discord alert for {slug} #{identifier}...")
        await send_discord(session, slug, event)

    if newest_id != last_seen_id:
        state[slug] = {
            "id": newest_id,
            "timestamp": newest_timestamp
        }
        save_state(state)


async def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting ArtNovaBot...")
    print(f"Monitored collections: {', '.join(COLLECTIONS)}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    if config.START_TIME:
        print(f"Start time filter: {datetime.fromtimestamp(config.START_TIME).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        print("Start time filter: None (latest 20 events)")
    print("-" * 65)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking collections for new sales...")
                tasks = [
                    check_collection(session, slug)
                    for slug in COLLECTIONS
                ]
                await asyncio.gather(*tasks)
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error in main loop: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())