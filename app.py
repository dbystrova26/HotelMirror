"""
Hotel Mirror — Flask server
Serves hotel_mirror.html with ANTHROPIC_API_KEY injected as a JS variable.
Key never appears in source code — read from environment / .env at runtime.
"""

import os
from flask import Flask, render_template_string

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

@app.route("/")
def index():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    with open("hotel_mirror.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Inject the key as the first JS variable — replaces the runtime check
    injection = f'<script>const ANTHROPIC_API_KEY = "{api_key}";</script>'
    html = html.replace("<script>", injection + "\n<script>", 1)
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
