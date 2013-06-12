# app.py
# James Wang, 8 Jun 2013

"""Runs HackerSchooler Faces Web Interface"""

from flask import Flask, render_template, redirect, request, url_for, \
    abort, flash
from parser.crawler import run_crawler, HackerSchoolerSpider, BatchSpider, \
    LoginFailedException
import random

app = Flask(__name__)
app.secret_key = "dsAQkfj#$(Snc!@"
app.vars = {}
app.vars['difficulty'] = "medium"  # hardcoded difficulty for now


@app.route('/', methods=['GET', 'POST'])
def index():
    # Present description and login page
    if request.method == 'GET':
        return render_template("index.html")
    else:
        app.vars['email'] = request.form['inputEmail']
        app.vars['password'] = request.form['inputPassword']
        return redirect(url_for('choose_batch'))


@app.route('/choose_batch', methods=['GET', 'POST'])
def choose_batch():
    if request.method == 'GET':
        if not allin(app.vars, 'email', 'password'):
            return redirect(url_for('index'))  # redirect no-logins
        try:
            items = run_crawler(BatchSpider, username=app.vars['email'],
                                password=app.vars['password'])
        except LoginFailedException:  # login rejected
            flash("Invalid login. Please check your email or password.")
            return redirect(url_for('index'))
        else:
            return render_template("choose_batch.html",
                                   batches=items)
    else:
        app.vars['batch'] = request.form['batch']
        return redirect(url_for('game'))


@app.route('/difficulty')
def difficulty():
    # easy (3 choices), medium (6 choices), hard (freeform)
    abort(404)  # not implemented


@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == "GET":
        if not allin(app.vars, 'email', 'password', 'batch'):
            return redirect(url_for('index'))  # redirect no-logins
        else:
            schoolers = run_crawler(HackerSchoolerSpider,
                                    username=app.vars['email'],
                                    password=app.vars['password'],
                                    batch=app.vars['batch'])
            the_chosen_one = random.choice(schoolers)
            app.vars['chosen'] = the_chosen_one
            name, pic, skills = the_chosen_one  # deconstruct tuple
            the_names = present_choices(the_chosen_one, schoolers,
                                        app.vars['difficulty'])
            return render_template("game.html",
                                   answer=False,
                                   correct=False,
                                   name=name, pic=pic,
                                   names=the_names)
    if request.method == "POST":
        user_answer = request.form['name_choice']
        name, pic, skills = app.vars['chosen']
        answer = True
        if user_answer == name:
            correct = True
        else:
            correct = False
        return render_template("game.html",
                               answer=answer,
                               correct=correct,
                               name=name, pic=pic,
                               skills=skills)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")


def present_choices(chosen, schooler3Tuples, difficulty):
    """Takes a chosen HackerSchooler to be displayed, HackerSchooler
    tuple of 3 (name, picture, skills) returned by
    HackerSchoolerSpider, and game difficulty. Returns shuffled list
    of name choices (NAME ONLY), the number of which will be based on
    the difficulty of the game.

    """
    difficulties = {"easy": 3, "medium": 6, "hard": 12}
    # x - 1 because the right choice is added in later
    num_choices = difficulties[difficulty] - 1

    schooler3Tuples.remove(chosen)  # mutation... pain in the ass...
    wrong_schoolers = random.sample(schooler3Tuples, num_choices)
    wrong_schoolers.append(chosen)
    all_names = [schooler[0] for schooler in wrong_schoolers]
    random.shuffle(all_names)
    return all_names  # again, mutation, pain in the ass...


def allin(the_dict, *args):
    """Function that takes a dict and any number of keys, and tests if
    all of them are in the dict. Returns True if so, False otherwise.

    """
    return all(a_key in the_dict for a_key in args)


if __name__ == '__main__':
    app.run(debug=True)
