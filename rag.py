import os
import faiss
from sentence_transformers import SentenceTransformer

class RAGEngine:
    def __init__(self):
        # This model converts text → vectors
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.text_chunks = []
        self.index = None

    def load_data(self, data_dir="data"):
        chunks = []

        for file in os.listdir(data_dir):
            path = os.path.join(data_dir, file)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        chunks.append(line)

        self.text_chunks = chunks
        print(f"Loaded {len(chunks)} knowledge chunks.")

    def build_index(self):
        embeddings = self.model.encode(self.text_chunks)
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        print("FAISS index built successfully.")

    def search(self, query, k=5):
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            results.append({
                "text": self.text_chunks[idx],
                "score": float(dist)
            })

        return results