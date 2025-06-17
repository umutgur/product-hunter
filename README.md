# Product Hunter

This simple Flask web application searches Google for Reddit posts
containing phrases like "is there a tool that" or "is there an app that".
The returned snippets represent potential product ideas. Each snippet is
then evaluated using the OpenAI API to judge whether it might be a
profitable idea.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Export your OpenAI API key (optional, needed for real analysis):
   ```bash
   export OPENAI_API_KEY=your-key
   ```

3. Run the application:
   ```bash
   python app.py
   ```

The app will be available at `http://localhost:5000`.

If no `OPENAI_API_KEY` is configured, placeholder text is shown instead
of real evaluations.
