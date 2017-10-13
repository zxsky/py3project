from flask import Flask, request, render_template, redirect, url_for, flash, g, session

import pymysql
from config import db_config

from app import webapp
from app.userforms import login_required, logout
from app.userforms import verify


from wand.image import Image
from werkzeug.utils import secure_filename

import os

'''
photos = UploadSet('photos', IMAGES)
configure_uploads(webapp, photos)
patch_request_class(webapp)
'''

ALLOWED_EXTENSIONS = (['png', 'jpg', 'jpeg', 'gif'])

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
'''
@webapp.teardown_appcontext
def close_DB(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
'''

def savefile(imagefile, username):
    """Upload Procedure:"""
    cnx = connect_DB()
    cursor = cnx.cursor()
    
    filename = secure_filename(imagefile.filename)
    filename = username + filename
    imagefile.save(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
    # with open(os.path.join(webapp.config['UPLOAD_FOLDER'], filename)) as f:
    #     image_binary = f.read()
    # with Image(filename='./images_uploaded/'+filename) as img:
    # with Image(blob=image_binary) as img:
    fname = os.path.join(webapp.config['UPLOAD_FOLDER'], filename)
    img = Image(filename=fname)
    # with open(fname, "rb") as image0:
    with img.clone() as flipped:
        flipped.flip()
        newname1 = os.path.join(webapp.config['UPLOAD_FOLDER'], 'trans_1_' + filename)
        # flipped.save(os.path.join(webapp.config['UPLOAD_FOLDER'], newname1))
        flipped.save(filename=newname1)
    with img.clone() as cropped:
        frequency = 3
        phase_shift = -90
        amplitude = 0.2
        bias = 0.7
        cropped.function('sinusoid', [frequency, phase_shift, amplitude, bias])
        cropped.save(filename=os.path.join(webapp.config['UPLOAD_FOLDER'], "trans_2_" + filename))
    with img.clone() as colored:
        colored.evaluate(operator='rightshift', value=1, channel='blue')
        colored.evaluate(operator='leftshift', value=1, channel='red')
        colored.save(filename=os.path.join(webapp.config['UPLOAD_FOLDER'], "trans_3_" + filename))
    query = '''INSERT INTO images (username, image0, image1, image2, image3) VALUES (%s,%s,%s,%s, %s)'''
    # username = session['username']
    cursor.execute(query, (username, filename, 'trans_1_' + filename, 'trans_2_' + filename, 'trans_3_' + filename))
    cnx.commit()
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        # flash('File Uploaded Successfully!','warning')
        # return render_template("/user_profile.html", username=username)


@webapp.route('/userpage/<username>', methods=['GET'])
@login_required
def profile(username):
    if session['username'] != username:
        logout()
        flash("You are not allowed to log into different accounts without logging out fist!",'warning')
        return redirect(url_for('login'))
    return render_template("/user_profile.html", username=username)


@webapp.route('/fileupload/form',methods=['GET'])
@login_required
def upload_image():
    return render_template("/imageupload_form.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@webapp.route('/fileupload',methods=['GET','POST'])
@login_required
def upload():
    
    if 'image_file' not in request.files:
        # return "Missing uploaded file"
        flash('Missing uploaded file', 'warning')
        return render_template("/imageupload_form.html")
    imagefile = request.files['image_file']

    if imagefile.filename == '':
        # return 'Missing file name'
        flash("There is no file name", 'warning')
        return render_template("/imageupload_form.html")

    if imagefile and allowed_file(imagefile.filename):
        username = session['username']
        savefile(imagefile, username)
    else:
        flash('Upload Failed!')
        return redirect(url_for('profile', username=session['username']))
    flash('File Uploaded Successfully!', 'success')
    
    #Close database here
    # return render_template("/user_profile.html", username=session['username'])
    return redirect(url_for('profile', username=session['username']))


# To facilitate testing
@webapp.route('/test/FileUpload/form', methods=['GET'])
def upload_image_test():
    return render_template("/imageupload_testform.html")
    
    
def allowed_file_test(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@webapp.route('/test/FileUpload', methods=['GET', 'POST'])
def upload_test():
    username = request.form["userID"]
    password = request.form["password"]
    result = verify(username, password)
    if result == 0: #user verified
        if 'uploadedfile' not in request.files:
            # return "Missing uploaded file"
            flash('Missing uploaded file', 'warning')
            return render_template("/imageupload_testform.html")
        
        uploadedfile = request.files['uploadedfile']
    
        if uploadedfile.filename == '':
            # return 'Missing file name'
            flash("There is no file name selected", 'warning')
            return render_template("/imageupload_testform.html")
        
        if uploadedfile and allowed_file(uploadedfile.filename):
            savefile(uploadedfile, username)
            flash('File Uploaded Successfully!', 'success')
            return redirect('/test/FileUpload/form')

    flash("Unrecognized User", 'warning')
    return render_template("/imageupload_testform.html")




# To display image:
@webapp.route('/imagelist/<username>', methods=['GET'])
@login_required
def image_list(username):
    if username == session['username']:
        cnx = connect_DB()
        cursor = cnx.cursor()
        query = '''SELECT username, imageid, image0  FROM images WHERE username= %s'''
        cursor.execute(query,(username,))
        userimagelist = []
        for row in cursor:
            userimagelist.append(row)
        return render_template("imagelist.html", cursor=userimagelist)
    return"error!"


@webapp.route('/imageview/<username>/<imageid>', methods=['GET'])
@login_required
def imageview(username,imageid):
    if username == session['username']:
        cnx = connect_DB()
        cursor = cnx.cursor()
        query = '''SELECT image0, image1, image2, image3  FROM images WHERE username= %s and imageid = %s'''
        cursor.execute(query,(username,imageid))
        imagelist = cursor.fetchone()
        # for row in cursor:
        #     imagelist.append(row)

        return render_template("imageview.html", cursor=imagelist)
    return "error!"