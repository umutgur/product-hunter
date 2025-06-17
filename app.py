import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///ideas.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, unique=True, nullable=False)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    competition = db.Column(db.Integer)
    profit = db.Column(db.Integer)
    supply = db.Column(db.Integer)
    score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    """Return structured analysis dict about the idea."""
    if openai is None or not os.getenv("OPENAI_API_KEY"):
        return {
            "pros": "-",
            "cons": "-",
            "competition": 0,
            "profit": 0,
            "supply": 0,
        }
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Bir girişim danışmanı olarak konuşuyorsun. Cevabın Türkçe JSON olsun. "
                    "Alanlar: pros, cons, competition(0-10), profit(0-10), supply(0-10)."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
        )
        import json
        text = response.choices[0].message.content.strip()
        try:
            return json.loads(text)
        except Exception:
            return {}
    except Exception as exc:  # pragma: no cover - network failures
        return {
            "pros": f"OpenAI error: {exc}",
            "cons": "",
            "competition": 0,
            "profit": 0,
            "supply": 0,
        }

def compute_score(item):
    return round(
        (
            item.get("profit", 0)
            + (10 - item.get("competition", 0))
            + (10 - item.get("supply", 0))
        )
        / 3,
        1,
    )

def fetch_and_store():
    queries = [
        'site:reddit.com "is there a tool that"',
        'site:reddit.com "is there an app that"',
    ]
    for q in queries:
        for idea in google_search(q, num=10):
            if not Idea.query.filter_by(text=idea).first():
                data = evaluate_with_openai(
                    f"Bu fikir karlı bir ürün olabilir mi? Lütfen değerlendir: {idea}"
                )
                score = compute_score(data)
                entry = Idea(
                    text=idea,
                    pros=data.get("pros", ""),
                    cons=data.get("cons", ""),
                    competition=int(data.get("competition", 0)),
                    profit=int(data.get("profit", 0)),
                    supply=int(data.get("supply", 0)),
                    score=score,
                )
                db.session.add(entry)
    db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store, "interval", hours=1, next_run_time=datetime.utcnow())
scheduler.start()

@app.route("/")
def index():
    ideas = Idea.query.order_by(Idea.created_at.desc()).all()
    template = """
    <!DOCTYPE html>
    <html lang='tr'>
    <head>
        <meta charset='utf-8'>
        <title>Ürün Avcısı</title>
        <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    </head>
    <body>
    <h1>Keşfedilen Fikirler</h1>
    <table border='1' cellpadding='5' cellspacing='0'>
        <tr>
            <th>Fikir</th>
            <th>Artılar</th>
            <th>Eksiler</th>
            <th>Rekabet</th>
            <th>Kazanç</th>
            <th>Arz</th>
            <th>Skor</th>
        </tr>
        {% for item in ideas %}
        <tr>
            <td>{{ item.text }}</td>
            <td>{{ item.pros }}</td>
            <td>{{ item.cons }}</td>
            <td>{{ item.competition }}</td>
            <td>{{ item.profit }}</td>
            <td>{{ item.supply }}</td>
            <td>{{ item.score }}</td>
        </tr>
        {% endfor %}
    </table>

    <canvas id='chart' width='400' height='200'></canvas>
    <script>
    const scores = {{ ideas|map(attribute='score')|list|tojson }};
    const labels = [...Array(scores.length).keys()].map(n => n+1);
    new Chart(document.getElementById('chart'), {
        type: 'bar',
        data: {labels, datasets:[{label:'Genel Skor', data:scores}]},
    });
    </script>
    </body>
    </html>
    """
    return render_template_string(template, ideas=ideas)

if __name__ == "__main__":  # pragma: no cover
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
