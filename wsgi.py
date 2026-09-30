from web import app
from bot import main
import threading
import os

def run_bot():
    main()

# inicia el bot en un hilo aparte
threading.Thread(target=run_bot, daemon=True).start()

# Render busca la variable 'app'
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
