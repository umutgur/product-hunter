# Product Hunter

This Flask application periodically searches the web (via DuckDuckGo)
for Reddit posts containing phrases like "is there a tool that" or
"is there an app that".  The discovered snippets are treated as product
ideas.  Each idea is analysed with the OpenAI API in Turkish and scored
for profitability, competition and supply.

Results are stored in a database so previously seen ideas are not
repeated.  A small dashboard displays the analysis in a table and shows
a bar chart of the overall scores.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Export your OpenAI API key (optional, needed for real analysis):
   ```bash
   export OPENAI_API_KEY=your-key
   ```

3. (Optional) specify a different database, e.g. Postgres:
   ```bash
   export DATABASE_URL=postgresql://user:pass@localhost/dbname
   ```

4. Run the application:
   ```bash
   python app.py
   ```

The app will be available at `http://localhost:5000`.

If no `OPENAI_API_KEY` is configured the analysis columns contain
placeholders.  Any OpenAI API error is displayed in the output so you
can verify requests are executed.
