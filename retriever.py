from rag import RAGEngine

_rag = None

def _get_rag() -> RAGEngine:
    global _rag
    if _rag is not None:
        return _rag

    rag = RAGEngine()
    rag.load_data()
    rag.build_index()
    _rag = rag
    return _rag

def retrieve_context(text, k=5):
    """
    Given resume text or a query, returns top-k relevant rules.
    """
    return _get_rag().search(text, k=k)