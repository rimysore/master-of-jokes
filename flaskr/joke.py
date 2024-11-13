from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('joke', __name__, url_prefix='/joke')

@bp.route('/create', methods=["GET", "POST"])
@login_required
def create():
    db = get_db()

    jokesOfCurrentUser = db.execute(f"SELECT * FROM joke WHERE author_id = {g.user['id']}").fetchall()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if len(title.split(' ')) >= 11:
            error = 'Title contains more than 10 words.'

        if not title:
            error = 'Title is required.'

        for joke in jokesOfCurrentUser:
            if joke['title'] == title:
                error = 'Title of Joke must be unique.'
                break

        if error is not None:
            flash(error)
        else:
            db.execute(
                'INSERT INTO joke (title, body, author_id, author_nickname)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], g.user['nickname'])
            )
            db.commit()
            if session["jokeBalance"] == -1:
                session["jokeBalance"] += 1
            session["jokeBalance"] += 1
            return redirect(url_for('joke.create'))

    if "jokeBalance" not in session:
        session["jokeBalance"] = g.user["joke_balance"]

    return render_template('joke/create.html', jokeBalance=session["jokeBalance"])

@bp.route("/my_jokes", methods=["GET"])
@login_required
def my_jokes():
    if "joke_id" in session:
        del session["joke_id"]

    db = get_db()

    jokes = db.execute(f"SELECT * FROM joke WHERE author_id = {g.user['id']}").fetchall()

    return render_template('joke/my_jokes.html', jokes=jokes, jokeCount=session["jokeBalance"])

@bp.route("/update", methods=["GET", "POST"])
@login_required
def update():
    db = get_db()

    if request.method == "POST":
        body = request.form['body']

        db.execute(
            f"UPDATE joke SET body='{body}' WHERE author_id = {g.user['id']} AND id = '{session['joke_id']}'"
        )
        db.commit()
        del session["joke_id"]
        return redirect(url_for('joke.my_jokes'))

    jokes = db.execute(f"SELECT * FROM joke WHERE author_id = {g.user['id']} AND id = '{request.args.get('joke_id')}'").fetchall()
    session['joke_id'] = request.args.get("joke_id")

    return render_template('joke/update.html', jokes=jokes)

@bp.route("/take", methods=["GET"])
@login_required
def take():
    if session["jokeBalance"] == 0 and not session["jokesVisited"]:
        flash('You need to first leave a joke.')
        return render_template('joke/create.html', jokeBalance=session["jokeBalance"])

    db = get_db()

    jokes = db.execute(f"SELECT * FROM joke WHERE author_id != {g.user['id']}").fetchall()

    return render_template('joke/take.html', jokes=jokes)

@bp.route("/view", methods=["GET", "POST"])
@login_required
def view():
    if session["jokeBalance"] == -1:
        flash('Your joke balance reached to 0. Please leave joke in order to view jokes.')
        return render_template('joke/create.html', jokeBalance=session["jokeBalance"])

    db = get_db()

    jokeId = request.args.get("joke_id")

    if jokeId not in session["jokesVisited"]:
        session["jokesVisited"].append(jokeId)
        session["jokeBalance"] -= 1
    
    jokes = db.execute(f"SELECT * FROM joke WHERE id = {jokeId}").fetchall()

    return render_template('joke/view.html', jokes=jokes)

@bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    db = get_db()

    if request.method == 'POST':
        db.execute(
            f"DELETE FROM joke WHERE id = '{session['joke_id']}'"
        )
        db.commit()
        del session["joke_id"]
        return redirect(url_for('joke.my_jokes'))

    jokeId = request.args.get("joke_id")

    session['joke_id'] = jokeId

    jokes = db.execute(f"SELECT * FROM joke WHERE id = {jokeId}").fetchall()

    return render_template('joke/delete.html', jokes=jokes)

@bp.route("/rate", methods=["POST"])
@login_required
def rate():
    if request.method == "POST":
        ratings = float(request.form["ratings"])
        jokeId = request.form["id"]

        db = get_db()

        joke = db.execute(f"SELECT * FROM joke WHERE id = {jokeId}").fetchone()

        newRating = round((((joke["ratings"] * joke["number_of_rating"]) + round(ratings, 2)) / (joke["number_of_rating"] + 1)), 2)

        db.execute(
            f"UPDATE joke SET ratings='{newRating}', number_of_rating='{joke['number_of_rating'] + 1}' WHERE id = '{jokeId}'"
        )
        db.commit()

        return redirect(url_for('joke.view', joke_id=jokeId))










