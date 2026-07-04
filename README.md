# ArtNovaBot 🚀

ArtNovaBot is an asynchronous Python bot designed to monitor OpenSea NFT collections for new sale events and send real-time alerts to a Discord channel via webhooks.

---

## Features

- **Multi-Collection Monitoring**: Tracks multiple OpenSea collections concurrently using `asyncio` and `aiohttp`.
- **Discord Notifications**: Sends beautifully formatted rich embed messages to a Discord channel with NFT thumbnails, price details, buyer/seller addresses, and transaction links.
- **State Management**: Keeps track of the last processed sale in `state.json` to prevent duplicate notifications upon restarts.
- **Highly Configurable**: Easily configure settings (API key, tracking interval, collections) via environment variables.

---

## File Structure

```text
artnovabot/
├── .env.example       # Example configuration file
├── bot.py             # Main entry point and bot logic
├── config.py          # Configuration loader
├── README.md          # Setup and usage guide
├── requirements.txt   # Python dependencies
└── state.json         # State file to prevent duplicate alerts
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher installed on your system.
- An OpenSea API Key (optional but recommended for high rate limits or v2 endpoints access). Get one from the [OpenSea Developer Portal](https://opensea.io/developer-portal).
- A Discord server where you have permission to manage webhooks.

### 2. Installation

Clone the repository or navigate to your project directory, then install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configuration

1. Copy `.env.example` to a new file named `.env`:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` in a text editor and fill in your details:
   - `OPENSEA_API_KEY`: Your OpenSea API key.
   - `DISCORD_WEBHOOK`: The webhook URL for your Discord channel.
   - `COLLECTIONS`: A comma-separated list of collection slugs you want to track (e.g., `boredapeyachtclub,mutant-ape-yacht-club`).
   - `CHECK_INTERVAL`: The check interval in seconds (default is `15`).
   - `START_TIME`: The starting point for queries when no previous state exists. Options include `today` (starts from 00:00 UTC of today), `yesterday` (starts from 00:00 UTC of yesterday), `now` or `latest` (sales happening after bot starts), a Unix timestamp (e.g. `1715000000`), or an ISO timestamp (e.g. `2026-07-04T12:00:00Z`). Leave empty to retrieve OpenSea's latest 20 events.

### 4. Running the Bot

Run the bot using the following command:

```bash
python bot.py
```

### 5. Running in Production with PM2 (Linux)

You can manage the bot on a Linux server 24/7 using the [PM2](https://pm2.keymetrics.io/) process manager. An `ecosystem.config.js` file is provided for this purpose.

1. Ensure NodeJS and PM2 are installed on the server:
   ```bash
   npm install pm2 -g
   ```
2. Start the bot using the ecosystem configuration:
   ```bash
   pm2 start ecosystem.config.js
   ```
3. Use standard PM2 commands to manage the process:
   - View logs: `pm2 logs artnovabot`
   - Check status: `pm2 status`
   - Restart the bot: `pm2 restart artnovabot`
   - Stop the bot: `pm2 stop artnovabot`

---

## State Retention

The bot automatically creates and updates `state.json` to remember which sales have already been processed. If you want to force-reprocess or reset the state, simply empty the JSON object in `state.json` back to `{}`.
