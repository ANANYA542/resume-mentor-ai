import os

class RAGEngine:
    def __init__(self):
        # Lazy-loaded to keep the core app usable even if
        # local embedding/native deps (faiss/torch) are unavailable.
        self._model = None
        self._model_name = "all-MiniLM-L6-v2"
        self.text_chunks = []
        self._index = None
        self.index = None

    def _get_model(self):
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer  # local import

        self._model = SentenceTransformer(self._model_name)
        return self._model

    def _faiss(self):
        import faiss  # local import

        return faiss

    def load_data(self, data_dir="data"):
        chunks = []

        for file in os.listdir(data_dir):
            if not file.lower().endswith(".txt"):
                continue
            path = os.path.join(data_dir, file)
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        chunks.append(line)

        self.text_chunks = chunks
        return len(chunks)

    def build_index(self):
        if not self.text_chunks:
            raise RuntimeError("No data loaded. Call load_data() first.")

        # Use cosine similarity via inner product by normalizing embeddings.
        model = self._get_model()
        embeddings = model.encode(self.text_chunks, normalize_embeddings=True)
        dimension = embeddings.shape[1]

        faiss = self._faiss()
        self._index = faiss.IndexFlatIP(dimension)
        self.index = self._index
        self._index.add(embeddings)
        return self._index.ntotal

    def search(self, query, k=5):
        if not query or not str(query).strip():
            return []
        if self._index is None:
            raise RuntimeError("Index not built. Call build_index() first.")

        model = self._get_model()
        query_embedding = model.encode([query], normalize_embeddings=True)
        distances, indices = self._index.search(query_embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            results.append({
                "text": self.text_chunks[idx],
                # Cosine similarity in [-1, 1]; higher is better.
                "score": float(dist)
            })

        return results
