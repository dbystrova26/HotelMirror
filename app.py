"""
Hotel Mirror — Flask server
Serves hotel_mirror.html with ANTHROPIC_API_KEY and OPENAI_API_KEY
injected as JS variables. Keys never appear in source code —
read from environment / .env at runtime.
"""

import os
from flask import Flask

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)


@app.route("/debug")
def debug():
    a = os.environ.get("ANTHROPIC_API_KEY", "")
    o = os.environ.get("OPENAI_API_KEY", "")
    return (
        f"Anthropic: {'SET (' + a[:12] + '...)' if a else 'MISSING'}<br>"
        f"OpenAI: {'SET (' + o[:8] + '...)' if o else 'MISSING'}"
    )


@app.route("/")
def index():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    with open("hotel_mirror.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Inject both keys as JS variables — first <script> tag in the page
    injection = (
        f"<script>"
        f'const ANTHROPIC_API_KEY = "{anthropic_key}";'
        f'const OPENAI_API_KEY = "{openai_key}";'
        f"</script>"
    )
    html = html.replace("<script>", injection + "\n<script>", 1)
    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
