# Spendwise — Multi-User Expense Tracker

## Problem
The original version stored everyone's expenses in one shared file. This version adds real accounts — each user signs up, logs in, and only ever sees their own data.

## How it works
Streamlit app backed by SQLite (`spendwise.db`, created automatically on first run). Two tables: `users` (username + SHA-256 hashed password) and `expenses` (each row tagged with a username). Every query is scoped to `st.session_state.username`, so data never crosses between accounts. UI unchanged from the earlier version — same design system, now behind a login/signup screen.

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Opens at `http://localhost:8501`. First run creates `spendwise.db` in the same folder — sign up with any username/password to get started.

## Deploy it live (for your LinkedIn post)
1. Push this folder to GitHub.
2. Go to https://streamlit.io/cloud, connect your GitHub, point it at `app.py`.
3. You get a public URL in ~2 minutes.

Note: Streamlit Community Cloud's free tier doesn't guarantee persistent disk storage across restarts — `spendwise.db` may reset occasionally. Fine for a portfolio demo; call this out as a known limitation if asked.

## What I'd improve
- Move to a hosted database (e.g. Postgres on Supabase/Railway) for real persistence.
- Add password reset and stronger password rules.
- Rate-limit login attempts to prevent brute-forcing.
- Session tokens instead of relying purely on Streamlit's session state.
