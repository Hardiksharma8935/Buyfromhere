# Premium Telegram Payment Bot

## Railway Deployment
1. Connect your GitHub repository to Railway.
2. Add a **PostgreSQL** plugin in Railway.
3. Add the environment variables from `.env.example` to your Railway Project Variables. (Make sure `DATABASE_URL` starts with `postgresql+asyncpg://`).

## Database Migrations
This bot uses **Zero-Touch Introspection Migrations**. When the bot boots up on Railway, it automatically checks the PostgreSQL schema and safely applies `ALTER TABLE` commands for any missing columns without deleting existing user data. No CLI required.

## Admin Features
Send `/admin` to the bot to access the control panel to add Groups, Demos, and update Settings on the fly.
Ensure the bot is added as an **Administrator** with "Invite Users via Link" permissions in your private groups for automatic invite delivery to function.
