import customtkinter as ct
import os
import threading
import time
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, Match, FieldCondition, MatchValue, BoolOperation
from sentence_transformers import SentenceTransformer
from groq import Groq  # Ensure this library exists or replace with appropriate client
import json

# Load environment variables from .env file
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')  # Groq API key

# Initialize the GROQ client
groq_client = Groq(api_key=groq_api_key)

# Initialize Qdrant client
qdrant_client = QdrantClient(host='localhost', port=6333)  # Adjust if using cloud
COLLECTION_NAME = 'hawaii_concierge'

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize the conversation history
conversation_history = []

def strip_markdown(text):
    """
    Removes Markdown formatting from the given text.

    Args:
        text (str): The text containing Markdown syntax.

    Returns:
        str: The plain text without Markdown.
    """
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

class TypingIndicator:
    def __init__(self, parent_frame, main_window):
        """
        Initializes the typing indicator.

        Args:
            parent_frame (CTkScrollableFrame): The frame where the typing indicator will be displayed.
            main_window (CTk): The main application window used to schedule updates.
        """
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.bubble_frame = ct.CTkFrame(parent_frame, fg_color="#E5E5EA", corner_radius=15)
        self.bubble_frame.pack(anchor="w", pady=5, padx=10)

        self.label = ct.CTkLabel(
            self.bubble_frame,
            text="Bot is typing.",
            text_color="#000000",
            wraplength=300,  # Increased from 250 to 300
            justify="left"
        )
        self.label.pack(pady=5, padx=10)

        self.dots = 1
        self.after_id = None
        self.start_time = time.time()  # Record the start time
        self.start_animation()

    def start_animation(self):
        """Starts the typing animation by scheduling the first update."""
        self.update_text()

    def update_text(self):
        """Updates the label text to simulate typing by cycling dots."""
        self.label.configure(text="Bot is typing" + "." * self.dots)
        self.dots = (self.dots % 3) + 1  # Cycle dots between 1 and 3
        # Schedule the next update after 500 milliseconds using the main window
        self.after_id = self.main_window.after(500, self.update_text)

    def get_elapsed_time(self):
        """Returns the elapsed time since the typing indicator was shown."""
        return time.time() - self.start_time

    def stop(self):
        """Stops the typing animation and removes the typing indicator from the UI."""
        if self.after_id:
            self.main_window.after_cancel(self.after_id)
        self.bubble_frame.destroy()

# Global variable to keep track of the typing indicator
typing_indicator = None

def search_vector_database(query, top_k=5):
    """
    Searches the Qdrant vector database for the top_k most similar documents to the query.

    Args:
        query (str): The user's query.
        top_k (int): Number of top results to return.

    Returns:
        list: List of matching documents with metadata.
    """
    embedding = embedding_model.encode(query).tolist()
    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=top_k
    )
    results = []
    for res in search_result:
        payload = res.payload
        results.append({
            'url': payload['url'],
            'title': payload['title'],
            'content': payload['content'],
            'subdomain': payload['subdomain'],
            'score': res.score
        })
    return results

def get_groq_response(user_input, context):
    """
    Sends the user's input along with context to the Groq API and retrieves the bot's response.

    Args:
        user_input (str): The message input by the user.
        context (str): Contextual information from the vector database.

    Returns:
        str: The response from the bot or an error message.
    """
    conversation_history.append({'role': 'user', 'content': user_input})
    try:
        prompt = f"Context: {context}\n\nUser: {user_input}\nBot:"
        response = groq_client.chat.completions.create(
            messages=conversation_history,
            prompt=prompt,
            model='gpt-3.5-turbo',  # Replace with the model version you’re using
            max_tokens=150
        )
        bot_response = response.choices[0].message.content.strip()
        # Strip Markdown from the bot's response
        bot_response = strip_markdown(bot_response)
        conversation_history.append({'role': 'assistant', 'content': bot_response})
        return bot_response
    except Exception as ex:
        print(f"An error occurred: {ex}")
        return "Error: Unable to retrieve response."

def display_message(sender, message):
    """
    Displays a message in the chat frame.

    Args:
        sender (str): The sender of the message ("user" or "assistant").
        message (str): The message content.
    """
    bubble_color = "#e5e3d9" if sender == "user" else "#E5E5EA"
    text_color = "#000000"
    alignment = "e" if sender == "user" else "w"

    # Message bubble frame
    bubble_frame = ct.CTkFrame(chat_frame, fg_color=bubble_color, corner_radius=15)
    bubble_frame.pack(anchor=alignment, pady=5, padx=10)

    # Message text label
    label = ct.CTkLabel(
        bubble_frame,
        text=message,
        text_color=text_color,
        wraplength=600,  # Increased from 250 to 300
        justify="left"
    )
    label.pack(pady=5, padx=10)

def process_input():
    """
    Processes the user's input by displaying it and fetching the bot's response.
    """
    global typing_indicator
    user_input = user_entry.get().strip()
    if user_input:
        display_message("user", user_input)
        user_entry.delete(0, ct.END)

        # Display the typing indicator
        typing_indicator = TypingIndicator(chat_frame, window)

        # Fetch and display the bot response in a separate thread to avoid freezing the GUI
        def fetch_and_display_response():
            # Determine if the input is a question
            is_question = user_input.endswith('?')
            if is_question:
                # Search the vector database for context
                search_results = search_vector_database(user_input)
                context = "\n".join([f"{res['title']}: {res['content']}" for res in search_results])
                response = get_groq_response(user_input, context)
            else:
                # Non-related message handling
                response = "I'm sorry, I can only assist with information related to Hawai'i. How can I help you today?"

            if typing_indicator:
                elapsed_time = typing_indicator.get_elapsed_time()
                minimum_duration = 1.0  # Minimum duration in seconds (changed from 2.0 to 1.0)
                remaining_time = minimum_duration - elapsed_time
                if remaining_time > 0:
                    # Schedule display_bot_response after the remaining time
                    window.after(int(remaining_time * 1000), lambda: display_bot_response(response))
                else:
                    # Schedule display_bot_response immediately
                    window.after(0, lambda: display_bot_response(response))

        threading.Thread(target=fetch_and_display_response, daemon=True).start()

def display_bot_response(response):
    """
    Displays the bot's response and removes the typing indicator.

    Args:
        response (str): The bot's response message.
    """
    global typing_indicator
    if typing_indicator:
        typing_indicator.stop()
        typing_indicator = None
    display_message("assistant", response)
    # Optionally, scroll to the bottom to show the latest message
    chat_frame.yview_moveto(1)

# GUI Setup
ct.set_appearance_mode("Light")  # or "Dark" for dark mode
ct.set_default_color_theme("blue")  # "blue" is the default theme

# Main window setup
window = ct.CTk()
window.geometry("360x640")
window.title("Hawai'i AI Concierge Bot")

# Chat display frame
chat_frame = ct.CTkScrollableFrame(window, fg_color="#FFFFFF")
chat_frame.pack(pady=10, padx=10, fill="both", expand=True)

# User input frame at the bottom
input_frame = ct.CTkFrame(window)
input_frame.pack(fill="x", pady=10, padx=10)

user_entry = ct.CTkEntry(input_frame, placeholder_text="Type a message...", width=240)
user_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

# Updated Send Button with matching color
send_button = ct.CTkButton(
    input_frame,
    text="Send",
    command=process_input,
    fg_color="#e5e3d9",        # Set to match user message bubble color
    hover_color="#d4d1c6",      # Optional: a slightly darker shade on hover
    text_color="#000000",       # Ensure text is readable on light background
    corner_radius=15            # Match the corner radius of message bubbles
)
send_button.pack(side="right")

# Bind the Enter key to send message
def on_enter_press(event):
    process_input()

user_entry.bind("<Return>", on_enter_press)

# Run the app
window.mainloop()