# Telegram Cloudflare Connector

This service runs on Cloudflare Workers with containers. It periodically retrieves new messages from Telegram and stores them in a Timescale database. Consecutive messages from the same author within the same channel are merged into a single message by concatenating their text and retaining the metadata of the last message.

## Local Development

### Quick Start

1. **Copy local environment template:**

   ```bash
   cp .env.local.example .env.local
   ```

2. **Configure credentials** in `.env.local`:
   - Set your Telegram API credentials (see [Obtaining Telegram Credentials for testing](#obtaining-telegram-credentials-for-testing))
   - Database connection string is automatically configured by docker-compose

3. **Start local services:**

   ```bash
   docker-compose up -d
   ```

   This starts:
   - TimescaleDB on `localhost:5432`
   - Flask connector service on `localhost:8080`

4. **Trigger the connector:**

   ```bash
   curl http://localhost:8080/
   ```

5. **View logs:**

   ```bash
   docker-compose logs -f connector
   ```

6. **Stop services:**

   ```bash
   docker-compose down
   ```

## Production Setup (Cloudflare)

### Timescale Setup

[Create](https://console.cloud.timescale.com/signup) a Timescale database with their 30 days free trial. You will need to add connection string to `TIMESCALE_CONNECTION` secret.

Use queries below to set up schema.

```sql
CREATE TABLE IF NOT EXISTS "message_feed" (
	"id" integer GENERATED ALWAYS AS IDENTITY (sequence name "message_feed_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START WITH 1 CACHE 1),
	"timestamp" timestamp with time zone DEFAULT now() NOT NULL,
	"platform_name" text NOT NULL,
	"platform_user_id" text NOT NULL,
	"platform_user_name" text NOT NULL,
	"platform_message_id" text NOT NULL,
	"platform_message_url" text,
	"source_account_id" text NOT NULL,
	"source_channel_name" text,
	"source_channel_id" text,
	"platform_specific" jsonb,
	"message_id" integer NOT NULL,
	CONSTRAINT "message_feed_id_timestamp_pk" PRIMARY KEY("id","timestamp"),
	CONSTRAINT "message_feed_timestamp_platform_name_platform_message_id_unique" UNIQUE("timestamp","platform_name","platform_message_id")
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "unique_messages" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "unique_messages_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START WITH 1 CACHE 1),
	"content" text NOT NULL,
	"embedding" text DEFAULT null,
	CONSTRAINT "unique_messages_content_unique" UNIQUE("content")
);
--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "message_feed" ADD CONSTRAINT "message_feed_message_id_unique_messages_id_fk" FOREIGN KEY ("message_id") REFERENCES "public"."unique_messages"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
```

## Obtaining Telegram Credentials for testing

### 1. Get Telegram API Credentials

Use a dedicated account for testing. Follow [this guide](https://docs.telethon.dev/en/stable/basic/signing-in.html#signing-in) to register a Telegram application and obtain your `api_id` and `api_hash`.

### 2. Add API Credentials to `.env.local`

Add your Telegram API credentials to `.env.local`:

```bash
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
```

### 3. Generate Session String

Run the session string generator script using docker-compose:

```bash
docker-compose run --rm scripts ./scripts/generate_session_str.py
```

The script will:

- Automatically load your API credentials from `.env.local`
- Prompt for your phone number
- Send a verification code to your phone
- Output the session string as JSON

### 4. Add Session String to `.env.local`

Copy the `session_str` value from the script output and add it to `.env.local`:

```bash
TELEGRAM_SESSION_STR=your_session_string_here
```

### 5. Restart Services

After updating `.env.local`, restart the services to load the new credentials:

```bash
docker-compose restart
```

### 6. Deploy to Cloudflare

Add these three values as Cloudflare Secrets:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_STR`

## Useful Resources

- [Deploying Cloudflare Worker with container](https://developers.cloudflare.com/containers/get-started/)
- [Telethon Documentation](https://docs.telethon.dev/en/stable/)
