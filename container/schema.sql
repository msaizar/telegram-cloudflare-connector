-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Table for storing unique message content (deduplication)
CREATE TABLE IF NOT EXISTS "unique_messages" (
	"id" integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY (sequence name "unique_messages_id_seq" INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START WITH 1 CACHE 1),
	"content" text NOT NULL,
	"embedding" text DEFAULT null,
	CONSTRAINT "unique_messages_content_unique" UNIQUE("content")
);

-- Table for storing message feed entries
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

-- Add foreign key constraint
DO $$ BEGIN
 ALTER TABLE "message_feed" ADD CONSTRAINT "message_feed_message_id_unique_messages_id_fk" FOREIGN KEY ("message_id") REFERENCES "public"."unique_messages"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;

-- Convert message_feed to hypertable (TimescaleDB feature)
SELECT create_hypertable('message_feed', 'timestamp', if_not_exists => TRUE);
