import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import log_info, log_error

class EmbeddingStore:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.index_path = os.path.join(base_dir, "vector_store.index")
        self.metadata_path = os.path.join(base_dir, "metadata.json")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.metadata = []
        self.load_store()

    def load_store(self):
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                log_info("Loaded existing FAISS index and metadata.")
            except Exception as e:
                log_error(f"Failed to load existing FAISS index and metadata: {e}")
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                log_info("Initialized new FAISS index.")
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            log_info("Initialized new FAISS index.")

    def save_store(self):
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f)
            log_info("Saved FAISS index and metadata.")
        except Exception as e:
            log_error(f"Failed to save FAISS index and metadata: {e}")

    def add_documents(self, documents, source_files):
        embeddings = self.get_embeddings(documents)
        if embeddings is not None:
            embeddings_np = np.array(embeddings).astype('float32')
            self.index.add(embeddings_np)
            self.metadata.extend(source_files)
            log_info(f"Added {len(documents)} documents to the index.")
            self.save_store()
        else:
            log_error("Failed to obtain embeddings for the documents.")

    def get_embeddings(self, texts):
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
            return embeddings.tolist()
        except Exception as e:
            log_error(f"Error obtaining embeddings: {e}")
            return None

    def search(self, query, top_k=3):
        embedding = self.get_embeddings([query])
        if embedding is not None:
            embedding_np = np.array(embedding).astype('float32')
            distances, indices = self.index.search(embedding_np, top_k)
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.metadata):
                    source = self.metadata[idx]
                    similarity = 1 / (1 + distance)
                    results.append((source, similarity))
            return results
        else:
            log_error("Failed to obtain embedding for the query.")
            return []

def build_embedding_store(scraped_data_folder, embedding_store, max_chunk_size=500):
    documents = []
    sources = []
    for txt_file in os.listdir(scraped_data_folder):
        if txt_file.endswith('.txt'):
            file_path = os.path.join(scraped_data_folder, txt_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n', 2)
                if len(lines) >= 3:
                    source_url = lines[0].strip()
                    text_to_embed = ''.join(lines[2:]).strip()
                else:
                    source_url = "Unknown Source"
                    text_to_embed = ''.join(lines[1:]).strip() if len(lines) > 1 else ''.join(lines).strip()
                
                words = text_to_embed.split()
                for i in range(0, len(words), max_chunk_size):
                    chunk = ' '.join(words[i:i + max_chunk_size])
                    documents.append(chunk)
                    sources.append(txt_file)
    embedding_store.add_documents(documents, sources)
