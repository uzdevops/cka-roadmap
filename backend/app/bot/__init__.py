"""The Telegram bot: a separate process, the same code.

It runs from the backend image (`python -m app.bot`), so the models, settings
and database session are the ones the API already uses. A second Dockerfile
would mean two definitions of the same things drifting apart.

There is no HTTP between the bot and the API - both talk to the database
through the same service layer, so there is one implementation of what "today"
means and one of how progress is computed.
"""
