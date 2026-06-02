from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'nexus-media-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

db = SQLAlchemy(app)

# ─── Models ──────────────────────────────────────────────


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(200), default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    downloads = db.relationship('Download', backref='user', lazy=True)


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    genre = db.Column(db.String(100))
    year = db.Column(db.Integer)
    duration = db.Column(db.String(20))
    file_path = db.Column(db.String(500))
    thumbnail = db.Column(db.String(500))
    description = db.Column(db.Text)
    plays = db.Column(db.Integer, default=0)
    downloads_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=4.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.String(500))


class Download(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Admin Helpers ────────────────────────────────────────
ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
ALLOWED_VIDEO = {'mp4', 'mkv', 'avi', 'mov', 'webm'}
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'webp', 'gif'}


def allowed_file(filename, exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in exts


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        u = User.query.get(session['user_id'])
        if not u or not u.is_admin:
            return render_template('403.html'), 403
        return f(*args, **kwargs)
    return decorated

# ─── Public Routes ────────────────────────────────────────


@app.route('/')
def index():
    featured = Media.query.order_by(Media.plays.desc()).limit(6).all()
    songs = Media.query.filter_by(media_type='song').order_by(
        Media.created_at.desc()).limit(8).all()
    movies = Media.query.filter_by(media_type='movie').order_by(
        Media.created_at.desc()).limit(8).all()
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('index.html', featured=featured, songs=songs, movies=movies, user=user)


@app.route('/browse')
def browse():
    media_type = request.args.get('type', 'all')
    genre = request.args.get('genre', '')
    search = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = 12
    query = Media.query
    if media_type != 'all':
        query = query.filter_by(media_type=media_type)
    if genre:
        query = query.filter(Media.genre.ilike(f'%{genre}%'))
    if search:
        query = query.filter((Media.title.ilike(f'%{search}%')) | (
            Media.artist.ilike(f'%{search}%')))
    total = query.count()
    items = query.order_by(Media.plays.desc()).offset(
        (page-1)*per_page).limit(per_page).all()
    user = User.query.get(session['user_id']) if 'user_id' in session else None
    return render_template('browse.html', items=items, total=total, page=page,
                           per_page=per_page, media_type=media_type, genre=genre,
                           search=search, user=user)


@app.route('/media/<int:media_id>')
def media_detail(media_id):
    item = Media.query.get_or_404(media_id)

    # --- DELETE THESE TWO LINES ---
    # item.plays += 1
    # db.session.commit()
    # ------------------------------

    related = Media.query.filter_by(media_type=item.media_type).filter(
        Media.id != item.id).limit(6).all()
    user = User.query.get(session['user_id']) if 'user_id' in session else None

    return render_template('details.html', item=item, related=related, user=user)


@app.route('/api/media')
def api_media():
    media_type = request.args.get('type', 'all')
    search = request.args.get('q', '')
    query = Media.query
    if media_type != 'all':
        query = query.filter_by(media_type=media_type)
    if search:
        query = query.filter((Media.title.ilike(f'%{search}%')) | (
            Media.artist.ilike(f'%{search}%')))
    items = query.order_by(Media.plays.desc()).all()
    return jsonify([{
        'id': m.id, 'title': m.title, 'artist': m.artist,
        'type': m.media_type, 'genre': m.genre, 'year': m.year,
        'duration': m.duration, 'thumbnail': m.thumbnail,
        'plays': m.plays, 'rating': m.rating, 'description': m.description
    } for m in items])


@app.route('/download/<int:media_id>')
def download_media(media_id):
    # 1. Security Check
    if 'user_id' not in session:
        return jsonify({'error': 'Login required', 'redirect': '/login'}), 401

    # 2. Get the media item
    item = Media.query.get_or_404(media_id)

    # 3. Update download stats
    dl = Download(user_id=session['user_id'], media_id=media_id)
    item.downloads_count += 1
    db.session.add(dl)
    db.session.commit()

    # 4. Extract the filename from the path
    # Since your item.file_path is stored as 'uploads/songs/filename.mp3'
    # we need to split it so send_from_directory looks in the right place
    if item.file_path:
        # Example: if file_path is 'uploads/songs/song.mp3'
        # base = 'static/uploads' and filename = 'songs/song.mp3'
        directory = os.path.join(app.root_path, 'static', 'uploads')

        # We need the relative path starting after 'uploads/'
        filename = item.file_path.replace('uploads/', '')

        return send_from_directory(directory, filename, as_attachment=True)

    return jsonify({'error': 'File not found'}), 404


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return render_template('auth.html', mode='register')
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('auth.html', mode='register')
        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return render_template('auth.html', mode='register')

        user = User(username=username, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('index'))

    return render_template('auth.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password')
            return render_template('auth.html', mode='login')

        session['user_id'] = user.id
        session['username'] = user.username

        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))

    return render_template('auth.html', mode='login')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    downloads = Download.query.filter_by(user_id=user.id).order_by(
        Download.downloaded_at.desc()).limit(20).all()
    dl_media = [Media.query.get(d.media_id)
                for d in downloads if Media.query.get(d.media_id)]
    return render_template('profile.html', user=user, downloads=dl_media)


@app.route('/api/play/<int:media_id>', methods=['POST'])
def play_media(media_id):
    item = Media.query.get_or_404(media_id)
    item.plays += 1
    db.session.commit()
    return jsonify({'plays': item.plays})

# ─── Admin Routes ─────────────────────────────────────────


@app.route('/admin')
@admin_required
def admin_dashboard():
    user = User.query.get(session['user_id'])
    all_items = Media.query.order_by(Media.created_at.desc()).all()
    return render_template('admin/admin_dashboard.html',
                           user=user,
                           items=all_items,
                           total_songs=Media.query.filter_by(
                               media_type='song').count(),
                           total_movies=Media.query.filter_by(
                               media_type='movie').count(),
                           total_users=User.query.count(),
                           total_downloads=Download.query.count())


@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        media_type = request.form.get('media_type', 'song')
        title = request.form.get('title', '').strip()
        artist = request.form.get('artist', '').strip()
        genre = request.form.get('genre', '').strip()
        year = request.form.get('year', '')
        duration = request.form.get('duration', '').strip()
        description = request.form.get('description', '').strip()
        tags = request.form.get('tags', '').strip()
        rating = float(request.form.get('rating', 4.5))

        if not title or not artist:
            return jsonify({'error': 'Title and artist are required'}), 400

        file_path = None
        mf = request.files.get('media_file')
        if mf and mf.filename:
            allowed = ALLOWED_AUDIO if media_type == 'song' else ALLOWED_VIDEO
            if not allowed_file(mf.filename, allowed):
                return jsonify({'error': f'Invalid file type for {media_type}'}), 400
            sub = 'songs' if media_type == 'song' else 'movies'
            dest = os.path.join(app.config['UPLOAD_FOLDER'], sub)
            os.makedirs(dest, exist_ok=True)
            fname = secure_filename(mf.filename)
            mf.save(os.path.join(dest, fname))

            file_path = f'uploads/{sub}/{fname}'

        thumbnail = request.form.get('thumbnail_url', '').strip()
        tf = request.files.get('thumbnail_file')
        if tf and tf.filename and allowed_file(tf.filename, ALLOWED_IMAGE):
            dest = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
            os.makedirs(dest, exist_ok=True)
            tname = secure_filename(tf.filename)
            tf.save(os.path.join(dest, tname))
            thumbnail = url_for(
                'static', filename=f'uploads/thumbnails/{tname}')

        if not thumbnail:
            seed = title.replace(' ', '')
            thumbnail = f'https://picsum.photos/seed/{seed}/400/{"400" if media_type == "song" else "600"}'

        item = Media(title=title, artist=artist, media_type=media_type, genre=genre,
                     year=int(year) if year.isdigit() else None, duration=duration,
                     description=description, tags=tags, rating=rating,
                     file_path=file_path, thumbnail=thumbnail)

        db.session.add(item)
        db.session.commit()

        # ─── 🔥 FIXED JSON RETURN ARRAY ───
        # Your custom javascript intercepts the response object to find the streaming media paths.
        # Returning 'file_url' down the network adapter pipe lets the client play the track smoothly!
        return jsonify({
            'success': True,
            'id': item.id,
            'title': item.title,
            'file_url': url_for('static', filename=item.file_path) if item.file_path else ''
        })

    return render_template('admin/upload.html', user=user)


@app.route('/admin/media')
@admin_required
def admin_media_list():
    user = User.query.get(session['user_id'])
    media_type = request.args.get('type', 'all')
    query = Media.query
    if media_type != 'all':
        query = query.filter_by(media_type=media_type)
    items = query.order_by(Media.created_at.desc()).all()
    return render_template('admin/media.html', user=user, items=items, media_type=media_type)


@app.route('/admin/media/delete/<int:media_id>', methods=['POST'])
@admin_required
def admin_delete_media(media_id):
    item = Media.query.get_or_404(media_id)
    if item.file_path:
        full = os.path.join(app.root_path, 'static', item.file_path)
        if os.path.exists(full):
            os.remove(full)
    Download.query.filter_by(media_id=media_id).delete()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/media/<int:media_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_media(media_id):
    user = User.query.get(session['user_id'])
    item = Media.query.get_or_404(media_id)
    if request.method == 'POST':
        item.title = request.form.get('title', item.title).strip()
        item.artist = request.form.get('artist', item.artist).strip()
        item.genre = request.form.get('genre', item.genre or '').strip()
        item.description = request.form.get(
            'description', item.description or '').strip()
        item.tags = request.form.get('tags', item.tags or '').strip()
        item.duration = request.form.get(
            'duration', item.duration or '').strip()
        yr = request.form.get('year', '')
        if yr.isdigit():
            item.year = int(yr)
        item.rating = float(request.form.get('rating', item.rating))
        thumb_url = request.form.get('thumbnail_url', '').strip()
        if thumb_url:
            item.thumbnail = thumb_url
        tf = request.files.get('thumbnail_file')
        if tf and tf.filename and allowed_file(tf.filename, ALLOWED_IMAGE):
            dest = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
            os.makedirs(dest, exist_ok=True)
            tname = secure_filename(tf.filename)
            tf.save(os.path.join(dest, tname))
            item.thumbnail = url_for(
                'static', filename=f'uploads/thumbnails/{tname}')
        db.session.commit()
        return jsonify({'success': True})

    return render_template('admin/edit.html', user=user, item=item)


@app.route('/admin/users')
@admin_required
def admin_users():
    user = User.query.get(session['user_id'])
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', user=user, users=users)


def create_admin():
    """Create default admin account if none exists."""
    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            username='admin',
            email='admin@nexus.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created — email: admin@nexus.com  password: admin123")


with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
