#!/usr/bin/env python3

import os, sys, time, io
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import db
import bcrypt
import re

#nice path trick for bottle. thanks niles!
#sys.path.insert(0, ".");
#sys.path.remove(".")
#root = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
app.secret_key = os.urandom(12).hex()
CORS(app)


db.init()

email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

def user_from_id(uid):
    q = db.query("select * from users where user_id=?", str(uid));
    return q[0];

def verify_session():
    if not 'logged_in' in session or not 'username' in session or not 'password' in session:
        return False

    if session['logged_in'] == False:
        return False

    pw = session['password'] 
    un = session['username']

    q = db.query("""select * from users where username == ?""", un)
    if len(q) == 0:
        return False
    
    q = db.query("""select password from users where username == ?""", un)
    if q[0]['password'] != pw:
        return False

    return True

@app.route("/index")
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/workout", methods=['GET'])
def workout():
    if not verify_session():
        return redirect(url_for('login'))

    if request.method == 'GET':
        wid = request.args.get('id')
        if wid == None:
            return browse()
        wout = db.query("select * from workouts where workout_id=?", str(wid))[0];
        u = user_from_id(wout['user_id']);

        if u != None:
            uname = u['username'];
        else:
            return browse()

        r = db.query("select * from reviews where workout_id=?", str(wid))
        if len(r) < 1:
            revs = -1
        else:
            revs = jsonify(r)

        return render_template("workout.html", workout=wout, username=uname, reviews=revs)
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
    if not verify_session():
        return redirect(url_for('login'))

    return render_template("create_workout.html")

@app.route("/workout_created", methods=['POST'])
def workout_created():
    if not verify_session():
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title').strip()
        content = data.get('content').strip()
        freq = data.get('frequency')
        tags = data.get('tags')

        errors = []
        can_create = True

        tq = db.query("""select * from workouts where title == ?""", title)
        if len(tq) > 0:
            errors.append("Title already in use")

        if len(errors) > 0:
            return jsonify({'success': 0, 'redirect': '', 'errors': errors})

        uid = db.query("""select user_id from users where username == ?""", session['username'])[0]['user_id']

        db.execute("""
            insert into workouts (
                user_id, title, content, frequency, tags
            ) values (
                ?, ?, ?, ?, ?
            )""", 
            uid, title, content, str(freq), str(tags)
        )

        wid = db.query("""
            select workout_id, max(created_date) from workouts 
            group by workout_id
        """)[0]['workout_id']

        return jsonify({'success': 1, 'redirect': url_for('browse', id=wid), 'errors': []})
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
        pass_plain = data.get('pass_plain')
        pass_conf = data.get('pass_conf')
      
        errors = []      
        can_create = True

        if len(username) < 4 or " " in username:
            errors.append("Username must be at least four characters long and cannot include spaces")
        
        if len(pass_plain) < 8 or " " in pass_plain:
            errors.append("Password must be at least eight characters long and cannot include spaces")
        
        if pass_plain != pass_conf:
            errors.append("Passwords must match");

        if not re.search(email_regex, email):
            errors.append("Email must be valid")

        unq = db.query("""select * from users where username == ?""", username)
        if len(unq) > 0:
            errors.append("Username already in use")

        emq = db.query("""select * from users where email == ?""", email)
        if len(emq) > 0:
            errors.append("Email already in use")

        if len(errors) > 0:
            can_create = False
        

        if not can_create:
            return jsonify({'success': 0, 'redirect': '', 'errors': errors});

        password = bcrypt.hashpw(pass_plain.encode(), bcrypt.gensalt())
        db.execute("""
            insert into users (
                username, password, email
            ) values (
                ?, ?, ?
            )""",
            username, password, email
        )
        session['logged_in'] = True 
        session['password'] = password
        session['username'] = username

        return jsonify({'success': 1, 'redirect': url_for('browse'), 'errors': []});
    return render_template("signup.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/attempt_login', methods=['POST'])
def attempt_login(): 
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        pass_plain = data.get('pass_plain')
      
        errors = []      
        can_create = True

        pw = ''

        if len(username) < 4 or " " in username:
            errors.append("Username must be at least four characters long and cannot include spaces")
        
        if len(pass_plain) < 8 or " " in pass_plain:
            errors.append("Password must be at least eight characters long and cannot include spaces")
        
        unq = db.query("""select * from users where username == ?""", username)
        if len(unq) < 1:
            errors.append("Username not found")
        else:
            pw = db.query("""select password from users where username == ?""", username)[0]['password']
            if not bcrypt.checkpw(pass_plain.encode('utf-8'), pw):
                errors.append("Incorrect password")

        if len(errors) > 0:
            can_create = False
        
        if not can_create:
            return jsonify({'success': 0, 'redirect': '', 'errors': errors}) 

        session['logged_in'] = True
        session['password'] = pw
        session['username'] = username

        return jsonify({'success': 1, 'redirect': url_for('browse'), 'errors': []})
    return render_template("signup.html")

@app.route("/logout")
def logout():
    if verify_session():
        session['logged_in'] = False
        session['username'] = ''
        session['password'] = ''
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login_status', methods=['POST'])
def login_status():
    if verify_session():
        return jsonify({'status': 1})
    else:
        return jsonify({'status': 0})

@app.route('/get_reviews', methods=['POST'])
def get_reviews():
    if request.method == 'POST':
        data = request.get_json()
        wid = data.get('wid')

        q = db.query("select * from reviews where workout_id == ?", wid)
        return jsonify(q) 

app.run(port=8080, debug=True)
session.clear()
