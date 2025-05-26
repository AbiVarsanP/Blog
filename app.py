from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database setup
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
        c.execute('''CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, media TEXT, created_at TEXT)''')
        c.execute('''CREATE TABLE comments (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, content TEXT, created_at TEXT)''')
        conn.commit()
        conn.close()

# Home route - Display posts
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT posts.id, posts.content, posts.media, posts.created_at, users.username FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.created_at DESC')
    posts = c.fetchall()
    post_comments = {}
    for post in posts:
        c.execute('SELECT comments.content, comments.created_at, users.username FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id = ?', (post[0],))
        post_comments[post[0]] = c.fetchall()
    conn.close()
    return render_template('index.html', posts=posts, post_comments=post_comments)

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# Create Post
@app.route('/post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        flash('Please log in to create a post.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        content = request.form['content']
        media = request.form.get('media', '')
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO posts (user_id, content, media, created_at) VALUES (?, ?, ?, ?)',
                  (session['user_id'], content, media, created_at))
        conn.commit()
        conn.close()
        flash('Post created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('post.html')

# Edit Post
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        flash('Please log in to edit a post.', 'error')
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM posts WHERE id = ? AND user_id = ?', (post_id, session['user_id']))
    post = c.fetchone()
    if not post:
        conn.close()
        flash('Post not found or you do not have permission to edit it.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        content = request.form['content']
        media = request.form.get('media', '')
        c.execute('UPDATE posts SET content = ?, media = ? WHERE id = ?', (content, media, post_id))
        conn.commit()
        conn.close()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', post=post)

# Delete Post
@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    if 'user_id' not in session:
        flash('Please log in to delete a post.', 'error')
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM posts WHERE id = ? AND user_id = ?', (post_id, session['user_id']))
    c.execute('DELETE FROM comments WHERE post_id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('index'))

# Add Comment
@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        flash('Please log in to comment.', 'error')
        return redirect(url_for('login'))
    content = request.form['content']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO comments (post_id, user_id, content, created_at) VALUES (?, ?, ?, ?)',
              (post_id, session['user_id'], content, created_at))
    conn.commit()
    conn.close()
    flash('Comment added successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
