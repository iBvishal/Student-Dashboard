from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import time
import datetime

app = Flask(__name__)
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'gupta@123'
#Change Password Accordingly
app.config['MYSQL_DB'] = 'results'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('home.html')

# Register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    roll_number = StringField('Roll Number', [validators.Length(min=5, max=15)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# USer Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        roll_number = form.roll_number.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO user(name, email, roll_number, password) VALUES(%s, %s, %s, %s)", (name, email, roll_number, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        roll_number = request.form['roll_number']

        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by roll_number
        result = cur.execute("SELECT * FROM user WHERE roll_number = %s", [roll_number])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password'] 

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # passed
                app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['roll_number'] = roll_number

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            cur.close
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Decorator: Checks if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

def run_sql_file(filename):
    '''
    The function takes a filename and a connection as input
    and will run the SQL query on the given connection  
    '''
    cur = mysql.connection.cursor()
    start = time.time()
    
    file = open(filename, 'r')
    sql = s = " ".join(file.readlines())
    print("Start executing: " + filename + " at " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + "\n" + sql) 
    cur.execute(sql) 
    # mysql.connection.commit() 
    end = time.time()
    print("Time elapsed to run the query:")
    print(str((end - start)*1000) + ' ms')

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get user by roll_number
    # run_sql_file('data')
    student_sem_data = []
    cur.execute("SELECT * FROM semesters WHERE roll_no  = '{}'" .format(session['roll_number']))
    data = cur.fetchall()
    print(data)
    student_sem_cgpi = []
    student_sem_sgpi = []
    for dict_sem in data:
        student_sem_cgpi.append(dict_sem['cgpi'])
        student_sem_sgpi.append(dict_sem['sgpi'])
    print(student_sem_cgpi)
    print(student_sem_sgpi)

    # student_sem_data[0] = CGPI
    # student_sem_data[1] = SGPI
    student_sem_data.append(student_sem_cgpi)
    student_sem_data.append(student_sem_sgpi)

    cur.execute("SELECT * FROM students WHERE roll_no  = '{}'" .format(session['roll_number']))
    student_data = cur.fetchall()
    student_data_list = []
    student_data_list.append(student_data[0]['roll_no'])
    student_data_list.append(student_data[0]['name'])
    student_data_list.append(student_data[0]['cgpi'])
    student_data_list.append(student_data[0]['year_rank'])
    student_data_list.append(student_data[0]['college_rank'])
    print(student_data)

    # student_sem_data[2] = student details
    student_sem_data.append(student_data_list)

    cur.execute("SELECT * FROM subjects WHERE roll_no  = '{}'" .format(session['roll_number']))
    student_subjects = cur.fetchall()
    student_subjects_list = []
    for i in student_subjects:
        stu_sub_list = []
        stu_sub_list.append(i['subject_name'])
        stu_sub_list.append(i['ObtainCR'])
        stu_sub_list.append(i['TotalCR'])
        stu_sub_list.append(int(i['semester_no']) % 10)
        student_subjects_list.append(stu_sub_list)
        # print(i)
    print(student_subjects_list)

    # student_sem_data[3] = subject wise details of student
    student_sem_data.append(student_subjects_list)

    return render_template('dashboard.html' , data=student_sem_data)

if __name__ == '__main__':
    app.secret_key='secret123'
app.run(debug=True)