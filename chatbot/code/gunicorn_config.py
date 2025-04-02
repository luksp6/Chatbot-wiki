import os
import multiprocessing

from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"), override=True)
CHATBOT_PORT = int(os.getenv('CHATBOT_PORT', "6000"))

bind = f'127.0.0.1:{CHATBOT_PORT}'
backlog = 512
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'async'
timeout = 60
preload = True