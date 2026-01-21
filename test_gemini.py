# import os
# from google import genai

# # Load API Key
# api_key = os.getenv("GEMINI_API_KEY")
# print(f"API Key Loaded: {bool(api_key)}")

# if not api_key:
#     print("Error: GEMINI_API_KEY not found. Run 'export GEMINI_API_KEY=your_key'")
#     exit()

# # Initialize Client
# client = genai.Client(api_key=api_key)

# try:
#     # Using 'gemini-2.0-flash' which is the newest and most stable for this SDK
#     # If you prefer 1.5, use 'gemini-1.5-flash' (ensure no 'models/' prefix)
#     response = client.models.generate_content(
#         model="gemini-2.0-flash", 
#         contents="Rewrite this professionally: i am good at coding"
#     )

#     print("\nGemini Response:")
#     if response.text:
#         print(response.text)
#     else:
#         # Some responses might be blocked or empty; this helps debug
#         print("Response received but no text found.")
#         print(response)

# except Exception as e:
   
#     print(f"\nAn error occurred: {e}")