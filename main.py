import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
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

# Constants
MAX_TOKENS_PER_REQUEST = 4096
CURRENT_CONTEXT_FILE = "current_relevant_context.txt"

# Initialize FastAPI app
app = FastAPI()

# Conversation histories stored per user
conversation_histories = {}

class Message(BaseModel):
    message: str

def initialize_conversation(conversation_history):
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

                    if total_length + chunk_length > MAX_TOKENS_PER_REQUEST * 4:
                        break

                    context += chunk_with_citation
                    total_length += chunk_length

    with open(CURRENT_CONTEXT_FILE, 'w', encoding='utf-8') as ctx_file:
        ctx_file.write(context)
    log_info(f"Updated {CURRENT_CONTEXT_FILE} with the latest context.")

    return context

def summarize_text(text, max_length=500):
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length] + "..."

def manage_conversation_history(conversation_history, new_message, max_history=10):
    conversation_history.append(new_message)
    if len(conversation_history) > max_history + 1:
        conversation_history.pop(1)

def get_groq_response(user_input, conversation_history):
    if not conversation_history:
        initialize_conversation(conversation_history)

    context = get_relevant_context(user_input)

    if context:
        system_context_message = {'role': 'system', 'content': context}
        manage_conversation_history(conversation_history, system_context_message)

    user_message = {'role': 'user', 'content': user_input}
    manage_conversation_history(conversation_history, user_message)

    try:
        response = groq_client.chat.completions.create(
            messages=conversation_history,
            model='llama3-70b-8192'
        )
        bot_response = response.choices[0].message.content.strip()
        bot_response = strip_markdown(bot_response)
        assistant_message = {'role': 'assistant', 'content': bot_response}
        manage_conversation_history(conversation_history, assistant_message)
        return bot_response
    except Exception as ex:
        log_error(f"An error occurred: {ex}")
        return "Error: Unable to retrieve response."

@app.post("/chat")
async def chat_endpoint(message: Message, request: Request):
    user_input = message.message
    user_id = request.client.host

    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_history = conversation_histories[user_id]

    try:
        bot_response = get_groq_response(user_input, conversation_history)
        return {"reply": bot_response}
    except Exception as ex:
        log_error(f"An error occurred: {ex}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")
