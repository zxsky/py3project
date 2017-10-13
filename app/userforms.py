from flask import Flask, request, render_template, redirect, url_for, flash, g, session

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo

#from werkzeug.security import generate_password_hash,check_password_hash

#from flask_sqlalchemy import SQLAlchemy

from app import webapp
from app import bcrypt

from functools import wraps

import pymysql
from config import db_config

#create two forms object
# bcrypt = Bcrypt(webapp)

class RegisterForm(FlaskForm):
    username = StringField(u'Username',
                validators=[DataRequired(message= u'Username can not be empty.'), Length(4, 16)])
    password = PasswordField('Enter Your Password',
                validators=[DataRequired(message= u'Password can not be empty.'),
                EqualTo('confirm', message='Passwords does not match')])
    confirm = PasswordField('Repeat the Password')
    submit = SubmitField(u'Register')


class LoginForm(FlaskForm):
    username = StringField(u'Username', validators=[
               DataRequired(message=u'Username can not be empty.'), Length(4, 16)])
    password = PasswordField(u'Password',
                validators=[DataRequired(message=u'Password can not be empty.')])
    submit = SubmitField(u'Login')


#database related functions

def setup_DB():
    return pymysql.connect(host=db_config['host'],
               port=3306,
               user=db_config['user'],
               password=db_config['password'],
               db=db_config['database'])

def connect_DB():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = setup_DB()
    return db


#close the database when the website is closed
@webapp.teardown_appcontext
def close_DB(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def login_required(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return func(*args, **kwargs)
        else:
            flash("You need to log in first!",'warning')
            return redirect(url_for('login'))
    return wrap

# def enPassWord(password):
#     return generate_password_hash(password)
#
# def checkPassWord(enpassword,password):
#     return check_password_hash(enpassword,password)

# class USER(object):
#     def __init__(self,username, password):
#         self.username = username
#         self.set_password(password)
#     def set_password(self,password):
#         self.pw_hash=generate_password_hash(password)
#     def check_passwprd(self,password):
#         return check_password_hash(self.pw_hash,password)


# Verify Identity
def verify(username, password):
    cnx = connect_DB()
    cursor = cnx.cursor()
    query = '''SELECT * FROM user WHERE username = %s'''
    cursor.execute(query, (username,))
    if cursor.fetchone() is None:
        return -1 #User does not exist
    else:
        #
        query = '''SELECT password FROM user WHERE username = %s'''
        cursor.execute(query, (username,))
        myenPassWord = cursor.fetchone()
        if not bcrypt.check_password_hash(myenPassWord[0], password):
            
            # query = '''SELECT * FROM user WHERE username = %s AND password = %s'''
            # cursor.execute(query, (username, password))
            # if cursor.fetchone() is None:
            
            return 1 # Password doesn't match
        else:
            return 0


@webapp.route('/logout')
@login_required
def logout():
    session.clear()
    flash("You are logged out!",'warning')
    return render_template("/main.html")


@webapp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        result = verify(username, password)
        if result == -1: #User does not exist
            flash("The username does not exist", 'warning')
            return render_template("/login_form.html", form=form)
        if result == 1: # password does not match
            flash("The password is wrong!", 'warning')
            return render_template("/login_form.html", form=form)
            
        if result == 0:
            flash("Login Success!", 'success')
            session['logged_in']= True
            session['username']= username
            return redirect(url_for('profile', username=username))
    return render_template("/login_form.html", form=form)


@webapp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = request.form.get('username')
        password = request.form.get('password')
        cnx = connect_DB()
        cursor = cnx.cursor()
        query = '''SELECT * FROM user WHERE username = %s'''
        cursor.execute(query, (username,))
        if cursor.fetchone() is not None:
            flash("The username has been used already", 'warning')
            return render_template("/register_form.html", form=form)
        else:
            query = '''Insert into user (username,password) values (%s, %s)'''
            cursor.execute(query, (username, bcrypt.generate_password_hash(password)))
            cnx.commit()
            flash("Register Success!", 'success')
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('profile', username=username))
    return render_template("/register_form.html", form=form)

@webapp.errorhandler(404)
def page_not_found(e):
    return render_template("404_error.html")