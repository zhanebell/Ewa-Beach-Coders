import json
import os
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def load_scraped_data():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    with open(os.path.join(data_dir, 'scraped_data.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def generate_embeddings(data, model_name='all-MiniLM-L6-v2'):
    model = SentenceTransformer(model_name)
    texts = [item['content'] for item in data]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def save_embeddings(data, embeddings):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    with open(os.path.join(data_dir, 'embeddings.json'), 'w', encoding='utf-8') as f:
        json.dump([{
            'url': item['url'],
            'title': item['title'],
            'content': item['content'],
            'subdomain': item['subdomain'],
            'embedding': embedding.tolist()
        } for item, embedding in zip(data, embeddings)], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("Loading scraped data...")
    scraped_data = load_scraped_data()
    print(f"Loaded {len(scraped_data)} records.")

    print("Generating embeddings...")
    embeddings = generate_embeddings(scraped_data)

    print("Saving embeddings...")
    save_embeddings(scraped_data, embeddings)

    print("Embeddings generation completed.")
