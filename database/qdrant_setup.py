import json
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
import tqdm

def load_embeddings():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    with open(os.path.join(data_dir, 'embeddings.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def setup_qdrant(collection_name='hawaii_concierge'):
    client = QdrantClient(host='localhost', port=6333)  # Adjust if using cloud

    # Create collection with appropriate vector size and distance metric
    sample_embedding = load_embeddings()[0]['embedding']
    vector_size = len(sample_embedding)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )

    # Load data and upload to Qdrant
    data = load_embeddings()
    points = [
        PointStruct(
            id=i,
            vector=record['embedding'],
            payload={
                'url': record['url'],
                'title': record['title'],
                'content': record['content'],
                'subdomain': record['subdomain']
            }
        )
        for i, record in enumerate(data)
    ]

    batch_size = 100
    for i in tqdm(range(0, len(points), batch_size), desc="Uploading to Qdrant"):
        client.upsert(
            collection_name=collection_name,
            points=points[i:i+batch_size]
        )

    print("Qdrant setup and data upload completed.")

if __name__ == "__main__":
    setup_qdrant()
