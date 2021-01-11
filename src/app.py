#!/usr/bin/env python3

import os, sys, time, io
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import db
import bcrypt

#nice path trick for bottle. thanks niles!
#sys.path.insert(0, ".");
#sys.path.remove(".")
#root = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
CORS(app)

db.init()

def user_from_id(uid):
    q = db.query("select * from users where user_id=?", str(uid));
    return q[0];

@app.route("/index")
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/workout", methods=['GET'])
def workout():
    if request.method == 'GET':
        wid = request.args.get('id')
        if wid == None:
            return browse()
        wout = db.query("select * from workouts where workout_id=?", str(wid))[0];
        u = user_from_id(wout['user_id']);
        print(u)
        if u != None:
            uname = u['username'];
        else:
            return browse()
        return render_template("workout.html", workout=wout, username=uname)
    else:
        return browse()

@app.route("/browse")
def browse():
    wouts = db.query("select * from workouts");
    unames = []
    for wout in wouts:
        unames.append(user_from_id(wout['user_id'])['username'])
    items = zip(unames, wouts)    
    return render_template("browse.html", workouts=items);

@app.route("/create_workout")
def create_workout():
    return render_template("create_workout.html")

@app.route("/workout_created", methods=['POST'])
def workout_created():
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        freq = data.get('frequency')
        tags = data.get('tags')

        db.execute("""
            insert into workouts (
                user_id, title, content, frequency, tags
            ) values (
                1, ?, ?, ?, ?
            )""", 
            title, content, str(freq), str(tags)
        )

        wid = db.query("""
            select workout_id, max(created_date) from workouts 
            group by workout_id
        """)[0]['workout_id']

        return redirect(url_for('workout', id=wid))
    return browse()

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/user_created", methods=['POST'])
def user_created():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        pass_plain = data.get('password');
       
      

        password = bcrypt.hashpw(pass_plain.encode(), bcrypt.gensalt())
        db.execute("""
            insert into users (
                username, password, email
            ) values (
                ?, ?, ?
            )""",
            username, password, email
        )

        return redirect(url_for('browse'))
    return signup()

app.run(port=8080, debug=True)