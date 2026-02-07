from rag import RAGEngine

rag = RAGEngine()
rag.load_data()
rag.build_index()

query = "How can I make my resume more ATS friendly?"

results = rag.search(query, k=5)

print("\nTop relevant rules:\n")
for i, r in enumerate(results, 1):
    print(f"{i}. {r}")