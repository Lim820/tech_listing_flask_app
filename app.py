import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import re
from werkzeug.utils import secure_filename
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_PATH = 'users.db'

malaysia_states = [
    'Johor', 'Kedah', 'Kelantan', 'Malacca', 'Negeri Sembilan', 'Pahang',
    'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak', 'Selangor',
    'Terengganu', 'Kuala Lumpur', 'Putrajaya', 'Labuan'
]

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        if not email or not password:
            flash("Email and password are required.")
            return redirect("/")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            flash("This email is not registered.")
            return redirect("/")

        # user[2] is the hashed password
        if not check_password_hash(user[2], password):
            flash("Incorrect password.")
            return redirect("/")

        session["user_id"] = user[0]
        session["email"] = user[1].strip().lower()
        # Increment login_count
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET login_count = COALESCE(login_count, 0) + 1 WHERE id = ?", (user[0],))
        conn.commit()
        conn.close()
        return redirect("/home")  # 登录成功后跳转到主页

    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    email = request.form["email"].strip()
    password = request.form["password"].strip()

    if not email or not password:
        flash("Email and password are required for registration.")
        return redirect("/")

    if "@" not in email or "." not in email:
        flash("Please enter a valid email address.")
        return redirect("/")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash("This email is already registered.")
        conn.close()
        return redirect("/")

    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
    conn.commit()
    conn.close()
    flash("Registration successful. Please log in.")
    return redirect("/")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties ORDER BY id DESC")
    properties = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', states=malaysia_states, properties=properties)

@app.route('/post_property', methods=['GET', 'POST'])
def post_property():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect('/')

    if request.method == 'POST':
        listing_type = request.form['listing_type'].upper()
        state = request.form['state']
        title = request.form['title']
        price = float(request.form['price'])
        ptype = request.form['type'].upper()
        area = request.form['area']
        address = request.form['address']
        description = request.form['description']
        photos = request.files.getlist('photos')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        terrace_house_subtype = request.form.get('terrace_house_subtype')
        semi_d_subtype = request.form.get('semi_d_subtype')
        bangalow_subtype = request.form.get('bangalow_subtype')
        land_subtype = request.form.get('land_subtype')
        high_rise_subtype = request.form.get('high_rise_subtype')
        residential_subtype = request.form.get('residential_subtype')
        commercial_subtype = request.form.get('commercial_subtype')
        factory_subtype = request.form.get('factory_subtype')
        factory_building_type = request.form.get('factory_building_type')
        size_unit = request.form.get('size_unit', 'SQFT').upper()
        if terrace_house_subtype: terrace_house_subtype = terrace_house_subtype.upper()
        if semi_d_subtype: semi_d_subtype = semi_d_subtype.upper()
        if bangalow_subtype: bangalow_subtype = bangalow_subtype.upper()
        if land_subtype: land_subtype = land_subtype.upper()
        if high_rise_subtype: high_rise_subtype = high_rise_subtype.upper()
        if residential_subtype: residential_subtype = residential_subtype.upper()
        if commercial_subtype: commercial_subtype = commercial_subtype.upper()
        if factory_subtype: factory_subtype = factory_subtype.upper()
        if factory_building_type: factory_building_type = factory_building_type.upper()
        created_at = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO properties (listing_type, state, title, price, type, area, size_unit, address, description, created_by, terrace_house_subtype, semi_d_subtype, bangalow_subtype, land_subtype, high_rise_subtype, residential_subtype, commercial_subtype, factory_subtype, factory_building_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (listing_type, state, title, price, ptype, area, size_unit, address, description, session['user_id'], terrace_house_subtype, semi_d_subtype, bangalow_subtype, land_subtype, high_rise_subtype, residential_subtype, commercial_subtype, factory_subtype, factory_building_type, created_at))
        property_id = cursor.lastrowid
        for photo in photos:
            if photo and photo.filename and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute('INSERT INTO property_images (property_id, filename) VALUES (?, ?)', (property_id, filename))
        conn.commit()
        conn.close()
        flash('Property posted successfully.')
        return redirect(url_for('home'))

    # GET request: render the post property form
    return render_template('post_property.html', states=malaysia_states, email=session.get('email'))

@app.route('/properties/<state>')
def view_state_properties(state):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.email as posted_by
        FROM properties p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.state = ?
        ORDER BY p.id DESC
    ''', (state,))
    properties = [dict(row) for row in cursor.fetchall()]
    for prop in properties:
        cursor.execute("SELECT filename FROM property_images WHERE property_id = ?", (prop['id'],))
        prop['images'] = [row['filename'] for row in cursor.fetchall()]
    conn.close()
    return render_template('state_properties.html', properties=properties, state=state)

ADMIN_EMAILS = [
    'user@example.com',
    'admin@yourdomain.com',
    'janelee.techiph@gmail.com'
]
ADMIN_EMAILS = [e.strip().lower() for e in ADMIN_EMAILS]

# Helper function for admin check
def is_admin():
    return session.get('email', '').strip().lower() in ADMIN_EMAILS

@app.route('/delete_property/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    if not is_admin():
        flash('Only admin can delete properties.')
        return redirect(url_for('home'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM properties WHERE id = ?', (property_id,))
    conn.commit()
    conn.close()
    flash('Property deleted successfully.')
    return redirect(url_for('home'))

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect('/')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        SELECT p.*, u.email as posted_by
        FROM properties p
        LEFT JOIN users u ON p.created_by = u.id
        WHERE p.id = ?
    ''', (property_id,))
    property = cur.fetchone()
    if not property:
        conn.close()
        flash('Property not found.')
        return redirect('/home')
    property = dict(property)
    cur.execute('SELECT filename FROM property_images WHERE property_id = ?', (property_id,))
    property['images'] = [row['filename'] for row in cur.fetchall()]
    conn.close()
    return render_template('property_detail.html', property=property)

@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    try:
        if 'user_id' not in session:
            flash('Please log in first.')
            return redirect('/')
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('''
            SELECT p.*, u.email as posted_by
            FROM properties p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.id = ?
        ''', (property_id,))
        property = cur.fetchone()
        if not property:
            conn.close()
            flash('Property not found.')
            return redirect('/home')
        # Only allow owner or admin
        if not is_admin() and str(property['created_by']) != str(session['user_id']):
            conn.close()
            flash('You do not have permission to edit this property.')
            return redirect('/home')
        if request.method == 'POST':
            listing_type = request.form['listing_type'].upper()
            state = request.form['state']
            title = request.form['title']
            price = float(request.form['price'])
            ptype = request.form['type'].upper()
            area = request.form['area']
            address = request.form['address']
            description = request.form['description']
            terrace_house_subtype = request.form.get('terrace_house_subtype')
            semi_d_subtype = request.form.get('semi_d_subtype')
            bangalow_subtype = request.form.get('bangalow_subtype')
            land_subtype = request.form.get('land_subtype')
            high_rise_subtype = request.form.get('high_rise_subtype')
            residential_subtype = request.form.get('residential_subtype')
            commercial_subtype = request.form.get('commercial_subtype')
            factory_subtype = request.form.get('factory_subtype')
            factory_building_type = request.form.get('factory_building_type')
            size_unit = request.form.get('size_unit', 'SQFT').upper()
            if terrace_house_subtype: terrace_house_subtype = terrace_house_subtype.upper()
            if semi_d_subtype: semi_d_subtype = semi_d_subtype.upper()
            if bangalow_subtype: bangalow_subtype = bangalow_subtype.upper()
            if land_subtype: land_subtype = land_subtype.upper()
            if high_rise_subtype: high_rise_subtype = high_rise_subtype.upper()
            if residential_subtype: residential_subtype = residential_subtype.upper()
            if commercial_subtype: commercial_subtype = commercial_subtype.upper()
            if factory_subtype: factory_subtype = factory_subtype.upper()
            if factory_building_type: factory_building_type = factory_building_type.upper()
            cur.execute('''
                UPDATE properties SET listing_type=?, state=?, title=?, price=?, type=?, area=?, size_unit=?, address=?, description=?, terrace_house_subtype=?, semi_d_subtype=?, bangalow_subtype=?, land_subtype=?, high_rise_subtype=?, residential_subtype=?, commercial_subtype=?, factory_subtype=?, factory_building_type=? WHERE id=?
            ''', (listing_type, state, title, price, ptype, area, size_unit, address, description, terrace_house_subtype, semi_d_subtype, bangalow_subtype, land_subtype, high_rise_subtype, residential_subtype, commercial_subtype, factory_subtype, factory_building_type, property_id))
            # Handle new photo uploads
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and photo.filename and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    cur.execute('INSERT INTO property_images (property_id, filename) VALUES (?, ?)', (property_id, filename))
            conn.commit()
            conn.close()
            flash('Property updated successfully.')
            return redirect('/home')
        # GET: show form
        states = [
            "Johor", "Kedah", "Kelantan", "Malacca", "Negeri Sembilan", "Pahang",
            "Penang", "Perak", "Perlis", "Sabah", "Sarawak", "Selangor",
            "Terengganu", "Kuala Lumpur", "Putrajaya", "Labuan"
        ]
        # Fetch images for display
        cur.execute('SELECT filename FROM property_images WHERE property_id = ?', (property_id,))
        images = [row['filename'] for row in cur.fetchall()]
        property = dict(property)
        property['images'] = images
        conn.close()
        return render_template('edit_property.html', property=property, states=states)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(f'An error occurred while editing the property: {e}')
        return redirect('/home')

@app.route('/add_property_photo/<int:property_id>', methods=['POST'])
def add_property_photo(property_id):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect('/')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM properties WHERE id=?', (property_id,))
    property = cur.fetchone()
    if not property:
        conn.close()
        flash('Property not found.')
        return redirect('/home')
    if not is_admin() and str(property['created_by']) != str(session['user_id']):
        conn.close()
        flash('You do not have permission to add photos to this property.')
        return redirect(f'/edit_property/{property_id}')
    photos = request.files.getlist('photos')
    added = 0
    for photo in photos:
        if photo and photo.filename and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute('INSERT INTO property_images (property_id, filename) VALUES (?, ?)', (property_id, filename))
            added += 1
    conn.commit()
    if added:
        flash(f'{added} photo(s) added successfully.')
    else:
        flash('No valid photo files uploaded.')
    conn.close()
    return redirect(f'/edit_property/{property_id}')

@app.route('/delete_property_photo/<int:property_id>/<filename>', methods=['POST'])
def delete_property_photo(property_id, filename):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect('/')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM properties WHERE id=?', (property_id,))
    property = cur.fetchone()
    if not property:
        conn.close()
        flash('Property not found.')
        return redirect('/home')
    if not is_admin() and str(property['created_by']) != str(session['user_id']):
        conn.close()
        flash('You do not have permission to delete photos from this property.')
        return redirect(f'/edit_property/{property_id}')
    # Remove the image record for this property
    cur.execute('DELETE FROM property_images WHERE property_id=? AND filename=?', (property_id, filename))
    conn.commit()
    # Check if any other property uses this image
    cur.execute('SELECT COUNT(*) as cnt FROM property_images WHERE filename=?', (filename,))
    count = cur.fetchone()['cnt']
    if count == 0:
        # Only delete the file if no other property uses it
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    conn.close()
    flash('Photo deleted successfully.')
    return redirect(f'/edit_property/{property_id}')

@app.route("/home")
def home():
    print('DEBUG: session email:', repr(session.get('email')))
    print('DEBUG: ADMIN_EMAILS:', ADMIN_EMAILS)
    print('DEBUG: is_admin:', is_admin())
    if "user_id" not in session:
        flash("Please log in first.")
        return redirect("/")

    filter_email = request.args.get('filter_email')
    search = request.args.get('search')
    filter_type = request.args.get('filter_type')
    filter_residential_subtype = request.args.get('filter_residential_subtype')
    filter_terrace_house_subtype = request.args.get('filter_terrace_house_subtype')
    filter_semi_d_subtype = request.args.get('filter_semi_d_subtype')
    filter_bangalow_subtype = request.args.get('filter_bangalow_subtype')
    filter_land_subtype = request.args.get('filter_land_subtype')
    filter_high_rise_subtype = request.args.get('filter_high_rise_subtype')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT p.*, u.email as posted_by
        FROM properties p
        LEFT JOIN users u ON p.created_by = u.id
    """
    params = []
    where_clauses = []
    if filter_email:
        where_clauses.append("u.email = ?")
        params.append(filter_email)
    if search:
        where_clauses.append("(p.state LIKE ? OR p.address LIKE ? OR p.area LIKE ? OR p.type LIKE ? OR p.title LIKE ?)")
        params.extend([f"%{search}%"] * 5)
    if filter_type:
        where_clauses.append("p.type = ?")
        params.append(filter_type)
    if filter_type == 'Residential' and filter_residential_subtype:
        where_clauses.append("p.residential_subtype = ?")
        params.append(filter_residential_subtype)
        if filter_residential_subtype == 'Terrace House' and filter_terrace_house_subtype:
            where_clauses.append("p.terrace_house_subtype = ?")
            params.append(filter_terrace_house_subtype)
        if filter_residential_subtype == 'Semi D' and filter_semi_d_subtype:
            where_clauses.append("p.semi_d_subtype = ?")
            params.append(filter_semi_d_subtype)
        if filter_residential_subtype == 'Bangalow' and filter_bangalow_subtype:
            where_clauses.append("p.bangalow_subtype = ?")
            params.append(filter_bangalow_subtype)
    if filter_type == 'Land' and filter_land_subtype:
        where_clauses.append("p.land_subtype = ?")
        params.append(filter_land_subtype)
    if filter_type == 'High Rise' and filter_high_rise_subtype:
        where_clauses.append("p.high_rise_subtype = ?")
        params.append(filter_high_rise_subtype)
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY p.id DESC"
    cur.execute(query, params)
    properties = [dict(row) for row in cur.fetchall()]

    # Fetch images for each property and calculate days_ago
    for prop in properties:
        cur.execute("SELECT filename FROM property_images WHERE property_id = ?", (prop['id'],))
        prop['images'] = [row['filename'] for row in cur.fetchall()]
        # Calculate days_ago
        if prop.get('created_at'):
            try:
                created_date = datetime.datetime.fromisoformat(prop['created_at'])
                prop['days_ago'] = (datetime.datetime.now() - created_date).days
            except Exception:
                prop['days_ago'] = None
        else:
            prop['days_ago'] = None

    # Fetch all users for filter
    cur.execute("SELECT email FROM users")
    all_users = [row['email'] for row in cur.fetchall()]

    # For filter dropdowns
    cur.execute("SELECT DISTINCT type FROM properties")
    all_types = [row['type'] for row in cur.fetchall()]
    residential_subtypes = []
    terrace_house_subtypes = []
    semi_d_subtypes = []
    bangalow_subtypes = []
    land_subtypes = []
    high_rise_subtypes = []
    if filter_type == 'Residential':
        cur.execute("SELECT DISTINCT residential_subtype FROM properties WHERE residential_subtype IS NOT NULL AND residential_subtype != ''")
        residential_subtypes = [row['residential_subtype'] for row in cur.fetchall()]
        if filter_residential_subtype == 'Terrace House':
            cur.execute("SELECT DISTINCT terrace_house_subtype FROM properties WHERE terrace_house_subtype IS NOT NULL AND terrace_house_subtype != ''")
            terrace_house_subtypes = [row['terrace_house_subtype'] for row in cur.fetchall()]
        if filter_residential_subtype == 'Semi D':
            cur.execute("SELECT DISTINCT semi_d_subtype FROM properties WHERE semi_d_subtype IS NOT NULL AND semi_d_subtype != ''")
            semi_d_subtypes = [row['semi_d_subtype'] for row in cur.fetchall()]
        if filter_residential_subtype == 'Bangalow':
            cur.execute("SELECT DISTINCT bangalow_subtype FROM properties WHERE bangalow_subtype IS NOT NULL AND bangalow_subtype != ''")
            bangalow_subtypes = [row['bangalow_subtype'] for row in cur.fetchall()]
    if filter_type == 'Land':
        cur.execute("SELECT DISTINCT land_subtype FROM properties WHERE land_subtype IS NOT NULL AND land_subtype != ''")
        land_subtypes = [row['land_subtype'] for row in cur.fetchall()]
    if filter_type == 'High Rise':
        cur.execute("SELECT DISTINCT high_rise_subtype FROM properties WHERE high_rise_subtype IS NOT NULL AND high_rise_subtype != ''")
        high_rise_subtypes = [row['high_rise_subtype'] for row in cur.fetchall()]

    # Counts (flat for now, can be nested if needed)
    cur.execute("SELECT type, COUNT(*) as count FROM properties GROUP BY type")
    type_counts = {row['type']: row['count'] for row in cur.fetchall()}

    states = [
        "Johor", "Kedah", "Kelantan", "Malacca", "Negeri Sembilan", "Pahang",
        "Penang", "Perak", "Perlis", "Sabah", "Sarawak", "Selangor",
        "Terengganu", "Kuala Lumpur", "Putrajaya", "Labuan"
    ]

    conn.close()

    return render_template(
        "home.html",
        email=session.get("email"),
        properties=properties,
        states=states,
        all_users=all_users,
        type_counts=type_counts,
        all_types=all_types,
        residential_subtypes=residential_subtypes,
        terrace_house_subtypes=terrace_house_subtypes,
        semi_d_subtypes=semi_d_subtypes,
        bangalow_subtypes=bangalow_subtypes,
        land_subtypes=land_subtypes,
        high_rise_subtypes=high_rise_subtypes,
        filter_type=filter_type,
        filter_residential_subtype=filter_residential_subtype,
        filter_terrace_house_subtype=filter_terrace_house_subtype,
        filter_semi_d_subtype=filter_semi_d_subtype,
        filter_bangalow_subtype=filter_bangalow_subtype,
        filter_land_subtype=filter_land_subtype,
        filter_high_rise_subtype=filter_high_rise_subtype,
        is_admin=is_admin()
    )

@app.route('/admin/logins')
def admin_logins():
    print('DEBUG: session email:', repr(session.get('email')))
    print('DEBUG: ADMIN_EMAILS:', ADMIN_EMAILS)
    print('DEBUG: is_admin:', is_admin())
    if not is_admin():
        flash('Admin access only.')
        return redirect('/home')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT email, login_count FROM users ORDER BY login_count DESC, email ASC')
    users = cur.fetchall()
    conn.close()
    return render_template('admin_logins.html', users=users)

import sqlite3
from werkzeug.security import generate_password_hash

db = sqlite3.connect('users.db')
c = db.cursor()
new_password = '345678'  # Set your new password here
hashed = generate_password_hash(new_password)
c.execute("UPDATE users SET password=? WHERE email=?", (hashed, 'hello@gmail.com'))
db.commit()
db.close()
print("Password for hello@gmail.com updated!")




