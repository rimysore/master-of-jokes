import functools, re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        nickname = request.form['nickname']
        password = request.form['password']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        elif not nickname:
            error = 'Nickname is required.'
        elif not password:
            error = 'Password is required.'


        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            error = "Email Address format is incorrect."

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (email, nickname, password) VALUES (?, ?, ?)",
                    (email, nickname, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"The choosen nickname is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = "Email or Nickname is required."
        elif not password:
            error = "Password is required."

        user = db.execute(
            'SELECT * FROM user WHERE email = ?', (username,)
        ).fetchone()

        if user is None:
            user = db.execute(
                'SELECT * FROM user WHERE nickname = ?', (username,)
            ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['jokesVisited'] = []
            return redirect(url_for('joke.create'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    db = get_db()
    
    db.execute(f"UPDATE user SET joke_balance = {session['jokeBalance']} WHERE id = {session['user_id']}")
    db.commit()

    session.clear()
    return redirect(url_for('auth.login'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view