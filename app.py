from flask import Flask, render_template, redirect, url_for, flash, request, session, logging   
from wtforms import Form, PasswordField, StringField, validators
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'messenger'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MySQL
mysql = MySQL(app)

#checks whether the user is logged in or not
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please log in', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', user=session['username'])

class RegisterForm(Form):
    firstname = StringField('First Name', [validators.Length(min=1, max=30), validators.DataRequired()])
    lastname = StringField('Last Name', [validators.Length(min=1, max=30), validators.DataRequired()])
    email = StringField('Email', [validators.Email(message="Check your email again."), validators.DataRequired()])
    username = StringField('Username', [validators.Length(min=3, max=30), validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired(), validators.equal_to('confirm', message="Password does not match")])
    confirm =  PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        firstname = form.firstname.data
        lastname = form.lastname.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(firstname, lastname, email, username, password) VALUES(%s, %s, %s, %s, %s)", (firstname, lastname, email, username, password))
        mysql.connection.commit()
        cur.close()

        flash('You are now registered and can log in', 'success') 

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=30, message="Check yoyr username once again.")])
    password = PasswordField('Password', [validators.DataRequired(message="Enter password")])
      
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        candidate_password = form.password.data

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username= %s", [username])
        if result>0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(candidate_password, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('home'))
            else:
                error = "Password is wrong"
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = "Username not found. Enter correct username or register"
            return render_template('login.html', error=error)
    return render_template('login.html', form=form)

class MessageForm(Form):
    msgg = StringField('', [validators.Length(min=1, max=300, message="Message must be of length 1 to 300.")])

@app.route('/messages/<string:sender>/<string:receiver>/', methods=['GET', 'POST'])
@is_logged_in
def messages(sender,receiver):
    if session['username'] == sender and (sender != receiver):
        form = MessageForm(request.form)
        friend = receiver
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM  users WHERE username = %s", [sender])
        sen = cur.fetchone()
        #sender's id
        sen_id = sen['id']
        cur.execute("SELECT * FROM  users WHERE username = %s", [receiver])
        rec = cur.fetchone()
        #receiver's id
        rec_id = rec['id']
        mysql.connection.commit()
        cur.close()
        if request.method == 'POST' and form.validate():
            msgg = form.msgg.data

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO messages(senderid, receiverid, message) VALUES(%s, %s, %s)",(sen_id, rec_id, msgg))
            mysql.connection.commit()
            cur.close()

            return redirect(url_for('messages', sender=sender, receiver=receiver))

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM messages WHERE (senderid = %s AND receiverid = %s) OR (senderid = %s AND receiverid = %s) ORDER BY message_time ASC", [sen_id, rec_id, rec_id, sen_id])
        msgs = cur.fetchall()

        if result>0:
            return render_template('messages.html', msgs=msgs, friend=friend, sen_id=sen_id, rec_id=rec_id, form=form, user = session['username'])
        else:
            flash('Start a new conversation.', 'info')
            return render_template('messages.html', friend=friend, form=form, user = session['username'])
        cur.close()
    else:
        err = "You can't access this page."
        return render_template('messages.html', error=err, user = session['username'])

@app.route('/messages/<string:sender>/')
@is_logged_in
def allchats(sender):
    if session['username'] == sender:
        chats = []

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [sender])
        unique = cur.fetchone()
        uniqueid = unique['id']
        #creating list of all ids of chats
        cur.execute("SELECT * FROM messages WHERE senderid = %s", [uniqueid])
        chatsa = cur.fetchall()
        for x in chatsa:
            chats.append(x['receiverid'])
        cur.execute("SELECT * FROM messages WHERE receiverid = %s", [uniqueid])
        chatsb = cur.fetchall()
        for x in chatsb:
            chats.append(x['senderid'])
        chats = list(set(chats))
        #creating a list of all usernames of chats
        names= []
        for chat in chats:
            cur.execute("SELECT * FROM users WHERE id = %s", [chat])
            name_a = cur.fetchone()
            name_b = name_a['username']
            names.append(name_b)
        names.sort()
        l = len(names)
        if l>0:
            return render_template('allchats.html', names = names, user = session['username'])
        flash('You have no chats. Start a new one here.', 'info')
        return render_template('allchats.html', user = session['username'])#test
    else:
        err = "You can't access this page."
        return render_template('allchats.html', error=err, user = session['username'])


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)