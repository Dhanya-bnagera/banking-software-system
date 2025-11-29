# app.py - main Flask application
from flask import Flask, render_template_string, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import init_db, get_session, User, Transaction
from forms import RegisterForm, LoginForm, TransferForm, DepositForm, WithdrawForm
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_to_a_random_secret'  # change for production

# Initialize DB
init_db()

# Simple templates as strings (so you can paste only files)
BASE_HTML = """
<!doctype html>
<title>Banking System</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/mini.css/3.0.1/mini-default.min.css">
<nav>
  <a href="{{ url_for('index') }}">Home</a>
  {% if user %}<a href="{{ url_for('dashboard') }}">Dashboard</a><a href="{{ url_for('logout') }}">Logout</a>{% else %}<a href="{{ url_for('login') }}">Login</a><a href="{{ url_for('register') }}">Register</a>{% endif %}
</nav>
<main class="container">
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <section>
        {% for m in messages %}
          <div class="card">{{ m }}</div>
        {% endfor %}
      </section>
    {% endif %}
  {% endwith %}
  {{ body }}
</main>
"""

INDEX = """
{% extends "base" %}
{% block body %}
  <h2>Welcome to the Banking Software System</h2>
  <p>This is a demo app for the SDLC assignment.</p>
  <p><strong>Features:</strong> register/login, view balance, deposit, withdraw, transfer, transaction history.</p>
{% endblock %}
"""

# helpers
def current_user():
    sid = session.get('user_id')
    if not sid:
        return None
    db = get_session()
    return db.query(User).filter_by(id=sid).first()

# Routes
@app.route('/')
def index():
    return render_template_string(BASE_HTML, user=current_user(), body=render_template_string(INDEX))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db = get_session()
        if db.query(User).filter_by(username=form.username.data).first():
            flash("Username already exists")
            return redirect(url_for('register'))
        pwd = generate_password_hash(form.password.data)
        u = User(username=form.username.data, password_hash=pwd, full_name=form.full_name.data or None, balance=0.0)
        db.add(u); db.commit()
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))
    body = """
    <h3>Register</h3>
    <form method="post">
      {{ form.hidden_tag() }}
      <label>Username</label>{{ form.username() }}
      <label>Password</label>{{ form.password() }}
      <label>Confirm</label>{{ form.confirm() }}
      <label>Full name</label>{{ form.full_name() }}
      <br>{{ form.submit(class_="primary") }}
    </form>
    """
    return render_template_string(BASE_HTML, user=current_user(), body=render_template_string(body, form=form))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = get_session()
        u = db.query(User).filter_by(username=form.username.data).first()
        if not u or not check_password_hash(u.password_hash, form.password.data):
            flash("Invalid credentials")
            return redirect(url_for('login'))
        session['user_id'] = u.id
        flash("Logged in successfully")
        return redirect(url_for('dashboard'))
    body = """
    <h3>Login</h3>
    <form method="post">
      {{ form.hidden_tag() }}
      <label>Username</label>{{ form.username() }}
      <label>Password</label>{{ form.password() }}
      <br>{{ form.submit(class_="primary") }}
    </form>
    """
    return render_template_string(BASE_HTML, user=current_user(), body=render_template_string(body, form=form))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    u = current_user()
    if not u:
        return redirect(url_for('login'))
    db = get_session()
    db.refresh(u)
    body = f"""
    <h3>Welcome, {u.username}!</h3>
    <p>Balance: ₹{u.balance:.2f}</p>
    <p><a href="{url_for('deposit')}">Deposit</a> | <a href="{url_for('withdraw')}">Withdraw</a> | <a href="{url_for('transfer')}">Transfer</a> | <a href="{url_for('transactions')}">Transaction History</a></p>
    """
    return render_template_string(BASE_HTML, user=u, body=body)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    u = current_user()
    if not u:
        return redirect(url_for('login'))
    form = DepositForm()
    if form.validate_on_submit():
        db = get_session()
        db.refresh(u)
        amt = float(form.amount.data)
        u.balance += amt
        txn = Transaction(user=u, type='deposit', amount=amt, note='Deposit via web')
        db.add(txn); db.commit()
        flash(f"Deposited ₹{amt:.2f}")
        return redirect(url_for('dashboard'))
    body = """
    <h3>Deposit</h3>
    <form method="post">
      {{ form.hidden_tag() }}
      <label>Amount</label>{{ form.amount() }}<br>
      {{ form.submit(class_="primary") }}
    </form>
    """
    return render_template_string(BASE_HTML, user=u, body=render_template_string(body, form=form))

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    u = current_user()
    if not u:
        return redirect(url_for('login'))
    form = WithdrawForm()
    if form.validate_on_submit():
        db = get_session()
        db.refresh(u)
        amt = float(form.amount.data)
        if amt > u.balance:
            flash("Insufficient funds")
            return redirect(url_for('withdraw'))
        u.balance -= amt
        txn = Transaction(user=u, type='withdraw', amount=amt, note='Withdraw via web')
        db.add(txn); db.commit()
        flash(f"Withdrew ₹{amt:.2f}")
        return redirect(url_for('dashboard'))
    body = """
    <h3>Withdraw</h3>
    <form method="post">
      {{ form.hidden_tag() }}
      <label>Amount</label>{{ form.amount() }}<br>
      {{ form.submit(class_="primary") }}
    </form>
    """
    return render_template_string(BASE_HTML, user=u, body=render_template_string(body, form=form))

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    u = current_user()
    if not u:
        return redirect(url_for('login'))
    form = TransferForm()
    if form.validate_on_submit():
        db = get_session()
        db.refresh(u)
        to_user = db.query(User).filter_by(username=form.to_username.data).first()
        amt = float(form.amount.data)
        if not to_user:
            flash("Recipient not found")
            return redirect(url_for('transfer'))
        if to_user.id == u.id:
            flash("Cannot transfer to self")
            return redirect(url_for('transfer'))
        if amt > u.balance:
            flash("Insufficient funds")
            return redirect(url_for('transfer'))
        # do transfer
        u.balance -= amt
        to_user.balance += amt
        txn_out = Transaction(user=u, type='transfer_out', amount=amt, note=f"To {to_user.username}")
        txn_in = Transaction(user=to_user, type='transfer_in', amount=amt, note=f"From {u.username}")
        db.add_all([txn_out, txn_in])
        db.commit()
        flash(f"Transferred ₹{amt:.2f} to {to_user.username}")
        return redirect(url_for('dashboard'))
    body = """
    <h3>Transfer</h3>
    <form method="post">
      {{ form.hidden_tag() }}
      <label>To (username)</label>{{ form.to_username() }}
      <label>Amount</label>{{ form.amount() }}<br>
      {{ form.submit(class_="primary") }}
    </form>
    """
    return render_template_string(BASE_HTML, user=u, body=render_template_string(body, form=form))

@app.route('/transactions')
def transactions():
    u = current_user()
    if not u:
        return redirect(url_for('login'))
    db = get_session()
    txns = db.query(Transaction).filter_by(user_id=u.id).order_by(Transaction.timestamp.desc()).all()
    rows = "".join(f"<li>{t.timestamp.strftime('%Y-%m-%d %H:%M:%S')} — {t.type} — ₹{t.amount:.2f} — {t.note or ''}</li>" for t in txns)
    body = f"""
    <h3>Transaction History</h3>
    <ul>{rows or '<li>No transactions yet</li>'}</ul>
    <p><a href="{url_for('dashboard')}">Back</a></p>
    """
    return render_template_string(BASE_HTML, user=u, body=body)

# Add a small helper route to create a demo user (for quick testing)
@app.route('/setup-demo')
def setup_demo():
    db = get_session()
    if db.query(User).filter_by(username='alice').first():
        flash("Demo users already created")
        return redirect(url_for('index'))
    u1 = User(username='alice', password_hash=generate_password_hash('alice123'), full_name='Alice', balance=1000.0)
    u2 = User(username='bob', password_hash=generate_password_hash('bob123'), full_name='Bob', balance=500.0)
    db.add_all([u1, u2]); db.commit()
    flash("Demo users created: alice/bob (passwords: alice123, bob123)")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
