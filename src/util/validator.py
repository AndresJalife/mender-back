from datetime import datetime
import re
from firebase_admin import auth

from src.config.database import get_context_db
from src.models import User
from src.service.Logger import logger


def validate_entity_id(entity_id):
    if not entity_id:
        logger.error("Entity id is required")
        raise ValueError("Entity id is required")
    if not isinstance(entity_id, int):
        logger.error("Entity id must be an integer")
        raise ValueError("Entity id must be an integer")
    return True


def validate_date_format(date):
    try:
        return datetime.strptime(date, "%d/%m/%Y")
    except ValueError:
        logger.error(f"Invalid date format: {date}. Must be: %d/%m/%Y")
        raise ValueError(f"Invalid date format: {date}. Must be: %d/%m/%Y")


def validate_client(client):
    if not client.active:
        logger.error(f"Client is not active: {client.client_id}")
        raise ValueError(f"Client is not active: {client.client_id}")
    if not client.cuit or len(client.cuit) < 11:
        logger.error(f"Client has no cuit: {client.client_id}")
        raise ValueError(f"Client has no cuit: {client.client_id}")
    return True


def validate_dates(start_date, end_date):
    start = validate_date_format(start_date)
    end = validate_date_format(end_date)
    if start > end:
        logger.error("Start date is greater than end date")
        raise ValueError("Start date is greater than end date")


def validate_user_admin(decoded_token):
    if decoded_token['admin'] is not True:
        raise Exception('Not an admin')


def validate_user_active(uid):
    user_record = auth.get_user(uid)
    if user_record.disabled:
        raise Exception('User is disabled')


def validate_emails(emails):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    for email in emails:
        if not email.email:
            logger.error("Email is required")
            raise ValueError("Email is required")
        if not re.match(email_regex, email.email):
            logger.error("Invalid email format")
            raise ValueError("Invalid email format")
        if not email.type:
            logger.error("Email type is required")
            raise ValueError("Email type is required")
    return None


def validate_user_views(views, url, decoded_token):
    if decoded_token['admin'] is True:
        return
    if "/monotribute" in url and "monotribute" not in views:
        raise Exception('User has no access to monotribute')
    if "/event" in url and "planification" not in views:
        raise Exception('User has no access to planification')
    if "/debt" in url and "debt" not in views:
        raise Exception('User has no access to debt')
    if "/document" in url and "documents" not in views:
        raise Exception('User has no access to documents')

