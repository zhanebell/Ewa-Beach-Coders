import re
import logging

# Configure logging
logging.basicConfig(
    filename='langchainscrape.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def strip_markdown(text):
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`.*?`', '', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'(\*\*|\*|__|_)', '', text)
    text = re.sub(r'^#+\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-\*\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[<>]', '', text)
    return text.strip()

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)
