import logging
import os
from datetime import date

class Logger:
    def __init__(self):
        base_path = os.environ.get('LOG_BASE_PATH')
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[
                                logging.FileHandler(base_path + f"/log-{date.today()}.log"),  # Log to a file
                                logging.StreamHandler()                 # Log to the terminal
                            ])

    def info(self, message):
        logging.info(message)

    def error(self, message):
        logging.error(message)


logger = Logger()
