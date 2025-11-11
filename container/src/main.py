import logging
from http import HTTPStatus

from connector import TelegramConnector
from telegram import get_telegram_client
from timescale import get_timescale_client
from flask import Flask, jsonify


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

telegram = None
timescale = None


def _ensure_clients():
    """Initialize clients if not already created"""
    global telegram, timescale

    if telegram is None:
        logger.info("Initializing Telegram client...")
        telegram = get_telegram_client()
        logger.info("Telegram client initialized")

    if timescale is None:
        logger.info("Initializing Timescale client...")
        timescale = get_timescale_client()
        logger.info("Timescale client initialized")


@app.route("/")
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "message": "Container is running"}), HTTPStatus.OK


@app.route("/connector")
def run_connector():
    logger.info("Connector endpoint called")

    try:
        _ensure_clients()

        logger.info("Creating TelegramConnector instance")
        connector = TelegramConnector(timescale, telegram)
        logger.info("TelegramConnector instance created")

        logger.info("Starting connector...")
        connector.start()
        logger.info("Connector finished successfully")

        return jsonify({"status": "Connector finished"}), HTTPStatus.OK

    except Exception as e:
        logger.error(f"Error in run_connector: {e}", exc_info=True)
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
