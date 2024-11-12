# api/utils.py

import re

def strip_markdown(text):
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r'`.*?`', '', text)
    # Remove images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Remove links but keep the link text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold and italics
    text = re.sub(r'(\*\*|\*|__|_)', '', text)
    # Remove headers
    text = re.sub(r'^#+\s', '', text, flags=re.MULTILINE)
    # Remove blockquotes
    text = re.sub(r'^>\s', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^---$', '', text, flags=re.MULTILINE)
    # Remove unordered list markers
    text = re.sub(r'^[-\*\+]\s+', '', text, flags=re.MULTILINE)
    # Remove ordered list numbers
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove remaining Markdown symbols
    text = re.sub(r'[<>]', '', text)
    return text.strip()

def log_info(message):
    print(f"INFO: {message}")

def log_error(message):
    print(f"ERROR: {message}")
