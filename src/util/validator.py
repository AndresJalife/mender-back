from datetime import datetime
import re
from firebase_admin import auth

from src.config.database import get_context_db
from src.models import User
from src.service.Logger import logger
