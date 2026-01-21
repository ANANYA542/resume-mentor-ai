from rag import RAGEngine

rag = RAGEngine()
rag.load_data()
rag.build_index()

def retrieve_context(text, k=5):
    """
    Given resume text or a query, returns top-k relevant rules.
    """
    return rag.search(text, k=k)