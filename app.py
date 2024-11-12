# app.py

import os
import sys
from dotenv import load_dotenv
from shiny import App, render_text, ui
from embedding import EmbeddingStore
from utils import strip_markdown, log_info, log_error
from groq import Groq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Initialize embedding store
embedding_store = EmbeddingStore()

# Initialize Shiny app
app_ui = ui.page_fluid(
    ui.h2("Koa - Hawaii Government Information Assistant"),
    ui.input_text("user_input", "Enter your query:", placeholder="Ask me anything about Hawaii government..."),
    ui.button("submit", "Submit"),
    ui.output_text_verbatim("bot_response")
)

def server(input, output, session):
    conversation_history = []

    @output
    @render_text
    def bot_response():
        if input.submit > 0:
            user_query = input.user_input()
            if not user_query:
                return "Please enter a valid query."

            # Initialize conversation with system message if empty
            if not conversation_history:
                system_message = {
                    'role': 'system',
                    'content': (
                        "You are a helpful assistant designed to provide information exclusively from credible "
                        "Hawaii government websites. Your responses should be accurate, concise, and strictly focused "
                        "on topics related to Hawaii government information. Do not provide information outside this scope. "
                        "Your name is Koa and you are designed to be as helpful as possible."
                    )
                }
                conversation_history.append(system_message)
                log_info("Initialized conversation with system message.")

            # Get relevant context
            context = get_relevant_context(user_query)

            if context:
                system_context_message = {'role': 'system', 'content': context}
                manage_conversation_history(conversation_history, system_context_message)

            # Add user message to history
            user_message = {'role': 'user', 'content': user_query}
            manage_conversation_history(conversation_history, user_message)

            try:
                response = groq_client.chat.completions.create(
                    messages=conversation_history,
                    model='llama3-70b-8192'
                )
                bot_reply = response.choices[0].message.content.strip()
                bot_reply = strip_markdown(bot_reply)
                assistant_message = {'role': 'assistant', 'content': bot_reply}
                manage_conversation_history(conversation_history, assistant_message)
                return bot_reply
            except Exception as ex:
                log_error(f"An error occurred: {ex}")
                return "Error: Unable to retrieve response."

def get_relevant_context(user_query, top_k=3, max_chunk_size=500):
    results = embedding_store.search(user_query, top_k)
    context = ""
    total_length = 0

    for source, similarity in results:
        file_path = os.path.join("ScrapedData", source)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    source_url = lines[0].strip()
                    content = ''.join(lines[2:]).strip()
                else:
                    source_url = "Unknown Source"
                    content = ''.join(lines[1:]).strip() if len(lines) > 1 else ''.join(lines).strip()

                words = content.split()
                for i in range(0, len(words), max_chunk_size):
                    chunk = ' '.join(words[i:i + max_chunk_size])
                    summarized_chunk = summarize_text(chunk)
                    chunk_with_citation = f"From {source} ({source_url}):\n{summarized_chunk}\n\n"
                    chunk_length = len(chunk_with_citation)

                    if total_length + chunk_length > 4096 * 4:
                        break

                    context += chunk_with_citation
                    total_length += chunk_length
    return context

def summarize_text(text, max_length=500):
    return text[:max_length] + "..." if len(text) > max_length else text

def manage_conversation_history(conversation_history, new_message, max_history=10):
    conversation_history.append(new_message)
    if len(conversation_history) > max_history + 1:
        conversation_history.pop(1)

app = App(app_ui, server)

# app.py (Add at the end of the file)

if __name__ == "__main__":
    import shiny
    shiny.App(app_ui, server).run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

