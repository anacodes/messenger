from flask import Flask, render_template, redirect, url_for, flash, request
from wtforms import Form, PasswordField, StringField, validators
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'messenger'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MySQL
mysql = MySQL(app)


@app.route('/home')
def home():
    return render_template('home.html')

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
      
@app.route('/login')
def login():
    return render_template('login.html')
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)