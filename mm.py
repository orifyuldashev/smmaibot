from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

print("BOT:", os.getenv("BOT_TOKEN"))
print("OPENAI:", os.getenv("OPENAI_API_KEY"))
print("ADMIN:", os.getenv("ADMIN_ID"))