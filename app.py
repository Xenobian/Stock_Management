from flask import Flask, render_template,request, flash, redirect,url_for, session, logging
from scrapper_company_list import scrap_call
from scrapper_stock import stock_data
from flask_mysqldb import MySQL
from wtforms import Form , StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


stock_list = scrap_call()
stocks = {}
username=""

app = Flask(__name__)
app.debug = True
app.secret_key='secret123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'dbms'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Close connection
            cur.close()
            # inserting into the log
            cur = mysql.connection.cursor()
            cur.execute("INSERT into log(username) values (%s)", [username])
            mysql.connection.commit()
            cur.close()

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('portfolio'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route("/portfolio",methods=['POST','GET'])
@is_logged_in
def portfolio():
    # Create cursor
    cur = mysql.connection.cursor()
    # getting user stocks information
    cur.execute("select * from stocks where USERNAME = %s",[session['username']])

    # converting into 2D Array
    n = cur.rowcount
    table_data = []
    for i in range(n):
        row=[]
        for j in range(5):
            row.append(0)
        table_data.append(row)   
    pl = []
    tpl = 0.0
    for i in range(n):
            data = cur.fetchone()
            table_data[i][0] = (data['STOCK_SYMBOL'])
            table_data[i][1] = (data['BUY_PRICE'])
            table_data[i][2] = (data['QUANTITY'])
            table_data[i][3] = (data['total_value'])
            table_data[i][4] = (stock_data(data['STOCK_SYMBOL'])['stock_price'] - (data['BUY_PRICE']))*(data['QUANTITY'])
            pl.append(table_data[i][4])
            pl.append(data['STOCK_SYMBOL'])
            tpl = tpl + float(table_data[i][4])
    # Close connection
    cur.close()
    #new
    cur = mysql.connection.cursor()
    for i in range(0,2*n-1,2):
        cur.execute("UPDATE stocks set pl =%s where USERNAME = %s and STOCK_SYMBOL= %s",(pl[i],session['username'],pl[i+1]))
        mysql.connection.commit()
    cur.close()   
    #pl
    cur = mysql.connection.cursor()
    try:
        cur.execute("insert into pl values(%s,%s)",(session['username'],tpl))
    except:
        cur.execute("update pl set profit = %s where username = %s",(tpl,session['username']))    
    mysql.connection.commit()
    cur.close() 
    if request.method ==  'POST':
        global stocks
        stocks = stock_data(request.form['stock'])
        global stock_symbol
        stock_symbol = request.form['stock']
        return redirect(url_for('stock'))
    return render_template("portfolio.html",stock_list=stock_list,row=table_data,n=n,tpl=tpl)

@app.route("/stock" , methods=['POST','GET'])    
@is_logged_in
def stock():
    if request.method == 'POST':
      
        # Create cursor
        cur = mysql.connection.cursor()
        
        #inserting into stocks table

        cur.execute("INSERT INTO stocks(USERNAME, STOCK_SYMBOL, BUY_PRICE, QUANTITY) VALUES(%s, %s, %s, %s)", (session['username'], stock_symbol, stocks['stock_price'], request.form['quantity']))
        
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('stock successfully bought', 'success')

        return redirect(url_for('portfolio'))
    return render_template("stock.html",stock=stocks)

@app.route('/log')
@is_logged_in
def log():
    # Create cursor
    cur = mysql.connection.cursor()

    # getting user stocks information
    cur.execute("select * from log where USERNAME = %s",[session['username']])

    # converting into 2D Array
    n = cur.rowcount
    table_data = []
    for i in range(n):
        row=[]
        for j in range(2):
            row.append(0)
        table_data.append(row)   

    for i in range(n):
            data = cur.fetchone()
            table_data[i][0] = (data['SID'])
            table_data[i][1] = (data['START_TIME'])

    # Close connection
    cur.close()

    return render_template("log.html",row=table_data,n=n)