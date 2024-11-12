from api.embedding import EmbeddingStore, build_embedding_store

scraped_data_folder = "ScrapedData"
embedding_store = EmbeddingStore()
build_embedding_store(scraped_data_folder, embedding_store)
