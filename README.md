# Ewa-Beach-Coders

## Koa - Hawaiʻi Government Assistant

Aloha! Welcome to Koa, an AI-powered assistant designed to provide accurate and helpful information exclusively from credible Hawaiʻi government websites. Koa scrapes content from official government domains, processes and indexes the data, and uses it to answer user queries through a user-friendly chat interface.

## Features

- **Accurate Information**: Provides information strictly from trusted Hawaiʻi government sources
- **User-Friendly Interface**: Interactive GUI built with customtkinter
- **Web Scraping**: Scrapes text and PDF content from specified Hawaiʻi government websites
- **Embeddings and Search**: Uses Sentence Transformers and FAISS for efficient retrieval of relevant information
- **Chatbot Integration**: Integrates with a language model via Groq's API to generate responses

## Prerequisites

- Python 3.7 or higher
- Groq API Key: You must have a valid Groq API key to use the chatbot functionality. This API key is free to obtain from https://console.groq.com/keys

## Installation

Please open Visual Studio Code and follow these installation instructions:

### 1. Clone the Repository
```bash
git clone https://github.com/HACC2024/Ewa-Beach-Coders.git
cd Ewa-Beach-Coders
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Prepare Data
Your project should have the Scraped Data folder which contains all of the scraped file content. If you would like the most up to date website data, you may delete that folder and run:
```bash
python src/scraper.py
```

### 5. Build Embeddings
```bash
python src/build_embeddings.py
```

### 6. Launch the Application
```bash
python src/gui.py
```

A GUI window will open, allowing you to interact with Koa:
- Type your queries into the input box at the bottom of the window
- Koa will provide responses based on information from the scraped Hawaiʻi government websites

---

## How It Works

### Web Scraping
**Script**: `src/scraper.py`

**Process**:
- Reads subdomains from CSV files in the `domains/` folder
- Visits each subdomain to scrape text content and download linked PDFs
- Extracts text from PDFs
- Saves all content into text files in the `Scraped Data/` folder

### Building the Embedding Store
**Script**: `src/embedding.py`

**Process**:
- Reads text files from the `Scraped Data/` folder
- Splits text into chunks (e.g., 500 words)
- Converts text chunks into embeddings using sentence-transformers (all-MiniLM-L6-v2 model)
- Stores embeddings in a FAISS index for efficient similarity search
- Saves metadata about each embedding's source in `metadata.json`

### Chatbot Interaction
**Script**: `src/chat.py`

**Process**:
- Uses the EmbeddingStore to find relevant text chunks based on the user's query
- Sends the relevant context and user query to the language model via the Groq API
- Receives and displays the assistant's response
- Maintains conversation history for context

### GUI Interface
**Script**: `src/gui.py`

**Process**:
- Creates a user-friendly chat interface using customtkinter
- Displays the conversation between you and Koa
- Features typing indicators and clickable links
- Allows for smooth scrolling and user interaction
