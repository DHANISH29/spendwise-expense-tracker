import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import date
import plotly.graph_objects as go

DB_FILE = "spendwise.db"

CATEGORY_META = {
    "food":      {"icon": "🍔", "color": "#E3A857"},
    "transport": {"icon": "🚗", "color": "#4C8577"},
    "rent":      {"icon": "🏠", "color": "#1B4D3E"},
    "shopping":  {"icon": "🛍️", "color": "#C97B5E"},
    "health":    {"icon": "💊", "color": "#7A9E7E"},
    "other":     {"icon": "✨", "color": "#A3A3A3"},
}

# ---------- Database layer ----------


def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # username already exists
    finally:
        conn.close()


def authenticate(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False
    return row[0] == hash_password(password)


def add_expense(username, amount, category, note):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO expenses (username, date, amount, category, note) VALUES (?, ?, ?, ?, ?)",
              (username, str(date.today()), amount, category, note))
    conn.commit()
    conn.close()


def load_expenses(username):
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM expenses WHERE username = ?", conn, params=(username,))
    conn.close()
    return df


init_db()

# ---------- Page config ----------
st.set_page_config(page_title="Spendwise", page_icon="💸", layout="wide")

# ---------- CSS (same design system as before) ----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F2F7F4; }
    h1, h2, h3 { font-family: 'Sora', sans-serif !important; color: #1B4D3E; }
    .app-title {
        font-family: 'Sora', sans-serif; font-weight: 800; font-size: 2.4rem;
        color: #1B4D3E; margin-bottom: 0;
    }
    .app-subtitle {
        font-family: 'Inter', sans-serif; color: #6B8F82; font-size: 1rem;
        margin-top: 0.2rem; margin-bottom: 1.8rem;
    }
    .stat-card {
        background: white; border-radius: 16px; padding: 1.3rem 1.5rem;
        box-shadow: 0 2px 10px rgba(27, 77, 62, 0.08); border-left: 5px solid #1B4D3E;
    }
    .stat-label { font-size: 0.8rem; color: #6B8F82; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
    .stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.9rem; font-weight: 700; color: #1B4D3E; margin-top: 0.2rem; }
    .card { background: white; border-radius: 16px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(27, 77, 62, 0.08); }
    .txn-row { display: flex; justify-content: space-between; align-items: center; padding: 0.7rem 0; border-bottom: 1px solid #EAF0ED; }
    .txn-row:last-child { border-bottom: none; }
    .txn-left { display: flex; align-items: center; gap: 0.7rem; }
    .txn-icon { background: #F2F7F4; border-radius: 10px; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
    .txn-note { font-weight: 600; color: #1A1A1A; font-size: 0.92rem; }
    .txn-meta { font-size: 0.78rem; color: #6B8F82; }
    .txn-amount { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #1B4D3E; }
    .pill { display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; color: white; }
    div[data-testid="stForm"] { background: white; border-radius: 16px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(27, 77, 62, 0.08); border: none; }
    .stButton button { background-color: #1B4D3E; color: white; border-radius: 10px; font-weight: 600; border: none; padding: 0.5rem 1.5rem; }
    .stButton button:hover { background-color: #16382C; color: white; }
</style>
""", unsafe_allow_html=True)

# ---------- Auth state ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

# ---------- Login / Signup screen ----------
if not st.session_state.logged_in:
    st.markdown('<div class="app-title">💸 Spendwise</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Track where your money actually goes.</div>',
                unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
            if submitted:
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

    with tab_signup:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input(
                "Confirm password", type="password")
            submitted = st.form_submit_button("Create account")
            if submitted:
                if not new_username or not new_password:
                    st.error("Username and password can't be empty.")
                elif new_password != confirm_password:
                    st.error("Passwords don't match.")
                elif create_user(new_username, new_password):
                    st.success(
                        "Account created! Go to the Log in tab to sign in.")
                else:
                    st.error("That username is already taken.")

    st.stop()

# ---------- Logged-in dashboard ----------
top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown('<div class="app-title">💸 Spendwise</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div class="app-subtitle">Welcome back, {st.session_state.username}.</div>', unsafe_allow_html=True)
with top_right:
    st.write("")
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

df = load_expenses(st.session_state.username)

col1, col2, col3 = st.columns(3)
total_spent = df["amount"].sum() if not df.empty else 0
this_month = 0
top_category = "—"

if not df.empty:
    df["date"] = pd.to_datetime(df["date"])
    current_month = pd.Timestamp.now().month
    this_month = df[df["date"].dt.month == current_month]["amount"].sum()
    top_category = df.groupby("category")["amount"].sum().idxmax()

with col1:
    st.markdown(f"""<div class="stat-card"><div class="stat-label">Total Spent</div>
    <div class="stat-value">₹{total_spent:,.0f}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="stat-card"><div class="stat-label">This Month</div>
    <div class="stat-value">₹{this_month:,.0f}</div></div>""", unsafe_allow_html=True)
with col3:
    icon = CATEGORY_META.get(top_category, {}).get("icon", "—")
    st.markdown(f"""<div class="stat-card"><div class="stat-label">Top Category</div>
    <div class="stat-value">{icon} {top_category.title() if top_category != "—" else "—"}</div></div>""", unsafe_allow_html=True)

st.write("")
st.write("")

left, right = st.columns([1, 1.2])

with left:
    st.markdown("#### Add an expense")
    with st.form("add_expense_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        category = st.selectbox("Category", list(CATEGORY_META.keys()))
        note = st.text_input("Note", placeholder="e.g. lunch with team")
        submitted = st.form_submit_button("Add expense")
        if submitted and amount > 0:
            add_expense(st.session_state.username, amount, category, note)
            st.success("Added!")
            st.rerun()

with right:
    st.markdown("#### Spending by category")
    if not df.empty:
        by_cat = df.groupby("category")["amount"].sum().reset_index()
        colors = [CATEGORY_META.get(c, {}).get("color", "#A3A3A3")
                  for c in by_cat["category"]]
        fig = go.Figure(data=[go.Pie(
            labels=[c.title() for c in by_cat["category"]],
            values=by_cat["amount"], hole=0.6,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            textinfo="percent", textfont=dict(family="Inter", size=13),
        )])
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", y=-0.15,
                        font=dict(family="Inter", size=12)),
            margin=dict(t=10, b=10, l=10, r=10), height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"₹{total_spent:,.0f}", x=0.5, y=0.5,
                              font=dict(family="JetBrains Mono",
                                        size=18, color="#1B4D3E"),
                              showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add your first expense to see the breakdown.")

st.write("")
st.markdown("#### Recent transactions")
if not df.empty:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    recent = df.sort_values("date", ascending=False).head(8)
    for _, row in recent.iterrows():
        meta = CATEGORY_META.get(
            row["category"], {"icon": "✨", "color": "#A3A3A3"})
        note_display = row["note"] if row["note"] else row["category"].title()
        st.markdown(f"""
        <div class="txn-row">
            <div class="txn-left">
                <div class="txn-icon">{meta['icon']}</div>
                <div>
                    <div class="txn-note">{note_display}</div>
                    <div class="txn-meta">{row['date'].strftime('%d %b %Y')}
                        <span class="pill" style="background-color:{meta['color']}">{row['category'].title()}</span>
                    </div>
                </div>
            </div>
            <div class="txn-amount">₹{row['amount']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No transactions yet — add one on the left.")
