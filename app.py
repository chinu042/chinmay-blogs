from flask import Flask, render_template,request,redirect,session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import psycopg2
import os
from urllib.parse import urlparse
database_url = os.environ.get('DATABASE_URL')
url_parts = urlparse(database_url)

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.session_cookie_name = 'session'
Session(app)

# Connect to PostgreSQL database
conn = psycopg2.connect(
    database=url_parts.path[1:],
    user=url_parts.username,
    password=url_parts.password,
    host=url_parts.hostname,
)

# Index route
@app.route('/')
def index():
    cur = conn.cursor()
    cur.execute('''SELECT b.blog_id, b.blog_title,b.blog_content,b.blog_date, u.user_name
FROM blogs b
INNER JOIN users u ON b.user_id = u.user_id;''')
    data = cur.fetchall()
    result = []
    for i in data:
        temp = {}
        temp['blog_id'] = i[0]
        temp['blog_title'] = i[1]
        temp['blog_content'] = i[2]
        temp['blog_date'] = i[3]
        temp['user_name'] = i[4]
        result.append(temp)
    return render_template('index.html',data=result)

# Login route
@app.route('/login')
def login():
    if session.get('user_name'):
        return redirect('/')
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def loggin():
    email = request.form['email']
    password = request.form['password']

    # Check if email and password are valid in the database
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_email = %s', (email,))
    user = cur.fetchone()

    if user:
        if check_password_hash(user[3], password):
            session['user_name'] = user[1];
            # Redirect to index page if login is successful
            return redirect('/')
        # Redirect to login page with error message if login fails
        return render_template('login.html', message={'error':'Invalid email or password'})
    else:
        # Redirect to login page with error message if login fails
        return render_template('login.html', message={'error':'Invalid email or password'})

@app.route('/logout',methods=['GET'])
def logout():
    session['user_name'] = None
    return redirect('/')

# Register route
@app.route('/register',methods=['GET'])
def register():
    return render_template('signup.html')

@app.route('/register',methods=['POST'])
def add_user():
    user_name = request.form['user_name']
    user_email = request.form['user_email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_email = %s', (user_email,))
    user = cur.fetchone()
    if user:
        # Redirect to register page with error message if email already exists
        return render_template('signup.html', message={'error':'Email already exists'})
    elif password != confirm_password:
        # Redirect to register page with error message if password and confirm_password don't match
        return render_template('signup.html', message={'error':'Password not matched'}) 
     # Add new user to the database
    hashed =  generate_password_hash(password)
    cur.execute('INSERT INTO users (user_name, user_email, user_password) VALUES (%s, %s, %s)', (user_name,user_email,hashed))
    conn.commit()
    return redirect('/')    

# View blog route
@app.route('/view_blog/<int:id>')
def view_blog(id):
    cur = conn.cursor()
    cur.execute('SELECT b.blog_id,b.blog_title,b.blog_content,b.blog_date,u.user_name FROM blogs as b,users as u WHERE b.blog_id = %s and b.user_id = u.user_id', (id,))
    blog = cur.fetchone()
    result = {}
    result['blog_id'] = blog[0]
    result['blog_title'] = blog[1]
    result['blog_content'] = blog[2]
    result['blog_date'] = blog[3]
    result['blog_user'] = blog[4]
    cur.execute('SELECT c.comment_id,c.comment_content,c.comment_date,u.user_name FROM comments as c,users as u WHERE blog_id = %s and c.user_id = u.user_id', (id,))
    comments = cur.fetchall()
    comment_data = []
    for i in comments:
        temp = {}
        temp['comment_id'] = i[0]
        temp['comment_content'] = i[1]
        temp['comment_date'] = i[2]
        temp['comment_user'] = i[3]
        comment_data.append(temp)
    return render_template('view_blog.html',data={'result':result,'comment_data':comment_data})

# Create blog route
@app.route('/create_blog')
def create_blog():
    if not session.get("user_name"):
        return redirect('/')
    return render_template('create_blog.html')

@app.route('/create_blog',methods=['POST'])
def add_blog():
    title = request.form['title']
    content = request.form['content']
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_name = %s', (session['user_name'],))
    user = cur.fetchone()
    user_id = user[0]
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    cur = conn.cursor()
    cur.execute('INSERT INTO blogs (blog_title,blog_content,blog_date,user_id) VALUES (%s, %s, %s, %s)', (title,content,date_string,user_id))
    conn.commit()
    return redirect('/')

@app.route('/update_blog/<int:id>',methods=['GET'])
def update_blog(id):
    if not session.get('user_name'):
        return redirect('/')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_name = %s', (session['user_name'],))
    user = cur.fetchone()
    cur.execute('SELECT * FROM blogs WHERE blog_id = %s', (id,))
    blog = cur.fetchone()
    if not blog:
        return redirect('/')
    if(user[0] != blog[4]):
        return redirect('/')
    return render_template('update_blog.html',data=blog)

@app.route('/update_blog/<int:id>',methods=['POST'])
def update(id):
    if not session.get('user_name'):
        return redirect('/')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_name = %s', (session['user_name'],))
    user = cur.fetchone()
    cur.execute('SELECT * FROM blogs WHERE blog_id = %s', (id,))
    blog = cur.fetchone()
    if not blog:
        return redirect('/')
    if(user[0] != blog[4]):
        return redirect('/')
    cur.execute('update blogs set blog_title = %s,blog_content = %s where blog_id = %s', (request.form['title'],request.form['content'],id))
    conn.commit()
    return redirect('/')

@app.route('/delete/<int:id>',methods=['GET'])
def delete_blog(id):
    if not session.get('user_name'):
        return redirect('/')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_name = %s', (session['user_name'],))
    user = cur.fetchone()
    cur.execute('SELECT * FROM blogs WHERE blog_id = %s', (id,))
    blog = cur.fetchone()
    if(user[0] != blog[4]):
        return redirect('/')
    cur.execute('delete from blogs where blog_id = %s',(id,))
    conn.commit()
    return redirect('/')

@app.route('/add_comment',methods=['POST'])
def add_comment():
    id = request.form['blog_id']
    if not session.get('user_name'):
        return redirect('/')
    comment_content = request.form['comment']
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d')
    
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_name = %s', (session['user_name'],))
    user = cur.fetchone()
    cur.execute('insert into comments(comment_content,comment_date,user_id,blog_id) values(%s,%s,%s,%s)', (comment_content,date_string,user[0],id))
    conn.commit()
    return redirect(f'/view_blog/{id}')
    

if __name__ == '__main__':
    app.run(port=4000)
