import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

app = Flask(__name__)

def google_search(query, num=5):
    """Return a list of search result snippets using DuckDuckGo."""
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for a in soup.select("a.result__a"):
        results.append(a.get_text(" ", strip=True))
        if len(results) >= num:
            break
    return results

def evaluate_with_openai(prompt):
    """Return OpenAI completion for the idea, or a placeholder if not configured."""
    if openai is None or not os.getenv("OPENAI_API_KEY"):
        return "[OpenAI API key not configured]"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You analyze if an idea could be profitable.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover - network failures
        return f"[OpenAI error: {exc}]"

@app.route("/")
def index():
    queries = [
        'site:reddit.com "is there a tool that"',
        'site:reddit.com "is there an app that"',
    ]
    ideas = []
    for q in queries:
        snippets = google_search(q)
        ideas.extend(snippets)

    evaluated = [
        {
            "idea": idea,
            "analysis": evaluate_with_openai(
                f"Is the following idea potentially profitable as a SaaS or product? {idea}"
            ),
        }
        for idea in ideas
    ]

    template = """
    <html>
    <head><title>Product Hunter</title></head>
    <body>
    <h1>Discovered Ideas</h1>
    {% for item in evaluated %}
    <div style='margin-bottom:20px;'>
        <strong>Idea:</strong> {{ item.idea }}<br>
        <strong>Analysis:</strong> {{ item.analysis }}
    </div>
    {% endfor %}
    </body>
    </html>
    """
    return render_template_string(template, evaluated=evaluated)

if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True, host="0.0.0.0", port=5000)
