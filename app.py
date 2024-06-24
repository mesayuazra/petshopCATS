from flask import Flask, render_template, session,send_from_directory, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
import re
import os
from werkzeug.utils import secure_filename 
from datetime import datetime
from collections import defaultdict

password = 'sparta'
cxn_str = f'mongodb://test:{password}@ac-6skehua-shard-00-00.eqimsea.mongodb.net:27017,ac-6skehua-shard-00-01.eqimsea.mongodb.net:27017,ac-6skehua-shard-00-02.eqimsea.mongodb.net:27017/?ssl=true&replicaSet=atlas-dad2x6-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0 '
client = MongoClient(cxn_str)
db = client.dbsparta_latihan

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)
app.secret_key = 'sparta'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

accessories = []  # Initialize accessories globally as an empty list

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_logged_in():
    return 'logged_in' in session and session['logged_in']

@app.route('/')
def index():
    return render_template('index.html', accessories=accessories, food=[])

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/food', methods=['GET'])
def food():
    food_list = list(db.food.find({}))
    return render_template('food.html', food=food_list)

@app.route('/accessories', methods=['GET'])
def accessories():
    accessories = list(db.accessories.find({}))
    return render_template('accessories.html', accessories=accessories)

@app.route('/grooming', methods=['GET'])
def grooming():
    return render_template('grooming.html')

@app.route('/ClinicHome', methods=['GET'])
def clinicHome():
    return render_template('clinicHome.html')

@app.route('/HealthCareServices', methods=['GET'])
def HCServices():
    return render_template('HCServices.html')

@app.route('/BookingHealthcareServices', methods=['GET'])
def bookHCServices():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    # Mengambil username dari session jika pengguna sudah login
    username = session.get('username', 'User')  # 'User' digunakan sebagai default jika session tidak memiliki username
    
    return render_template('BookHCServices.html', username=username)


@app.route('/bookingHCS', methods=['GET'])
def booking_hcs():
    bookHCS = list(db.bookingHCS.find({}))
    return render_template('adminBookHCS.html', bookHCS=bookHCS)

@app.route('/bookingHCS', methods=['POST'])
def add_booking_hcs():
    try:
        name = request.form['bookingName']
        services = request.form['bookingServices']
        waktu = request.form['bookingTime']
        tanggal = request.form['bookingDate']
        antar_jemput = request.form['antar_jemput']
        status = request.form['status']

        new_reservation = {
            "name": name,
            "services": services,
            "waktu": waktu,
            "tanggal": tanggal,
            "antar_jemput": antar_jemput,
            "status": status
        }
        # Insert the new reservation into the database
        db.bookingHCS.insert_one(new_reservation)

        return jsonify({'result': 'success', 'msg': 'Booking Layanan Klinik berhasil disimpan'})
    
    except Exception as e:
        print(e)  # Debug statement to print the error
        return jsonify({"result": "error", "message": str(e)}), 400


@app.route('/edit_bookingHCS/<booking_id>', methods=['GET', 'POST'])
def edit_booking_hcs(booking_id):
    if request.method == 'GET':
        bookHCS = db.bookingHCS.find_one({'_id': ObjectId(booking_id)})
        if not bookHCS:
            return jsonify({'error': 'Booking not found'}), 404
        bookHCS['_id'] = str(bookHCS['_id'])
        return jsonify(bookHCS)
    elif request.method == 'POST':
        try:
            booking_name = request.form['bookingName']
            booking_services = request.form['bookingServices']
            booking_time = request.form['bookingTime']
            booking_date = request.form['bookingDate']
            antar_jemput = request.form['antar_jemput']
            status = request.form['status']

            update_data = {
                'name': booking_name,
                'services': booking_services,
                'waktu': booking_time,
                'tanggal': booking_date,
                'antar_jemput': antar_jemput,
                'status': status,
            }

            result = db.bookingHCS.update_one({'_id': ObjectId(booking_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return jsonify({'result': 'success', 'msg': 'Booking berhasil diperbarui'})
            return jsonify({'result': 'gagal', 'msg': 'Booking tidak ditemukan atau gagal diperbarui'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})


@app.route('/bookingHCS/<id>', methods=['DELETE'])
def delete_booking(id):
    db.bookingHCS.delete_one({'_id': ObjectId(id)})
    return jsonify({'status': 'Booking deleted successfully'})

@app.route('/check_login_status', methods=['GET'])
def check_login_status():
    logged_in = session.get('logged_in', False)
    if logged_in:
        username = session.get('username', 'User')
        return jsonify({'logged_in': True, 'username': username})
    return jsonify({'logged_in': False})

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username_give']
        password = request.form['password_give']
        user = db.users.find_one({'email': username})
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            return jsonify({'result': 'success', 'msg': 'success'})
        return jsonify({'result': 'failure', 'msg': 'Email atau password salah'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pet_name = request.form['pet_name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        email_regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(email_regex, email):
            return jsonify({'result': 'failure', 'msg': 'Format email tidak valid'})
        if password != confirm_password:
            return jsonify({'result': 'failure', 'msg': 'Password salah'})
        hashed_password = generate_password_hash(password)
        if db.users.find_one({'email': email}):
            return jsonify({'result': 'failure', 'msg': 'Email sudah terdaftar'})
        
        registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.users.insert_one({
            'pet_name': pet_name,
            'address': address,
            'phone': phone,
            'email': email,
            'password': hashed_password,
            'registration_date': registration_date
        })
        return jsonify({'result': 'success'})
    return render_template('register.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    users = list(db.users.find({}, {'_id': 0, 'email': 1, 'pet_name': 1, 'registration_date': 1}))
    
    food_list = list(db.food.find({}))
    food_counts = defaultdict(int)
    for food in food_list:
        food_counts[food['name']] += 1
        
    accessories_list = list(db.accessories.find({}))
    acc_counts = defaultdict(int)
    for accessory in accessories_list:
        acc_counts[accessory['name']] += 1
        
    grooming_list = list(db.reservasi_grooming.find({}))
    groomres_counts = defaultdict(int)
    for grooming in grooming_list:
        groomres_counts[grooming['name']] += 1
    return render_template('dashboard.html', users=users, accessories_list=accessories_list, acc_counts=acc_counts, food_list=food_list, 
                           food_counts=food_counts, groomres_counts=groomres_counts, grooming_list=grooming_list)

@app.route('/get_user_data', methods=['GET'])
def get_user_data():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'result': 'failure', 'msg': 'User not logged in'}), 401
    username = session['username']
    user = db.users.find_one({'email': username}, {'_id': 0, 'pet_id': 1, 'pet_name': 1, 'address': 1, 'phone': 1, 'email': 1, 'profile_photo': 1})
    if user:
        return jsonify(user), 200
    return jsonify({'result': 'failure', 'msg': 'User tidak ditemukan'}), 404

@app.route('/profile', methods=['GET'])
def profile():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    username = session['username']
    user = db.users.find_one({'email': username})
    if not user:
        return jsonify({'result': 'failure', 'msg': 'User tidak ditemukan'})
    profile_photo_url = user.get('profile_photo', None)
    return render_template('profile.html', user=user, profile_photo_url=profile_photo_url)

@app.route('/save_profile_photo', methods=['POST'])
def save_profile_photo():
    if 'profile_photo' not in request.files:
        return jsonify({'result': 'failure', 'msg': 'No file part'}), 400
    file = request.files['profile_photo']
    if file.filename == '':
        return jsonify({'result': 'failure', 'msg': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        username = session['username']
        db.users.update_one({'email': username}, {'$set': {'profile_photo': filename}})
        return jsonify({'result': 'success', 'file_path': file_path}), 200
    return jsonify({'result': 'failure', 'msg': 'Tipe file tidak diperbolehkan'}), 400

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'result': 'failure', 'msg': 'User belum log in'}), 401
    data = request.json
    username = session['username']
    update_data = {
        'pet_name': data.get('pet_name'),
        'address': data.get('address'),
        'phone': data.get('phone'),
        'email': data.get('email')
    }
    db.users.update_one({'email': username}, {'$set': update_data})
    return jsonify({'result': 'success'}), 200

@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/aturProduk', methods=['GET'])
def aturProduk():
    accessories_list = list(db.accessories.find({}))
    food_list = list(db.food.find({}))
    return render_template('manageProd.html', accessories=accessories_list, food=food_list)

@app.route('/api/add-accessory', methods=['POST'])
def add_accessory():
    if request.method == 'POST':
        try:
            name = request.form['productName']
            type = request.form['productType']
            category = request.form['productCategory']
            quantity = int(request.form['productQuantity'])
            price = float(request.form['productPrice'])

            # Handling file upload
            if 'productImage' in request.files:
                file = request.files['productImage']
                if file.filename == '':
                    filename = None
                elif file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    raise Exception('Invalid file type')
            else:
                filename = None

            # Add new accessory to the database
            new_accessory = {
                "name": name,
                "type": type,
                "category": category,
                "quantity": quantity,
                "price": price,
                "image": filename
            }
            # Assuming db is your MongoDB client and accessories is your collection
            db.accessories.insert_one(new_accessory)

            # Optionally, refresh accessories list from database
            # global accessories  # Remove global variable usage if not needed
            # accessories = list(db.accessories.find({}))

            return jsonify({"result": "success"})
        
        except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging

@app.route('/api/add-food', methods=['POST'])
def add_food():
    try:
        name = request.form['productName']
        type = request.form['productType']
        category = request.form['productCategory']
        quantity = int(request.form['productQuantity'])
        price = float(request.form['productPrice'])

        # Handling file upload
        if 'productImage' in request.files:
            file = request.files['productImage']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                filename = None
        else:
            filename = None

        # Add new food to the database
        new_food = {
            "name": name,
            "type": type,
            "category": category,
            "quantity": quantity,
            "price": price,
            "image": filename
        }
        # Assuming db is your MongoDB client and foods is your collection
        db.food.insert_one(new_food)

        return jsonify({"result": "success"})
    
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400


@app.route('/edit-product/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if request.method == 'GET':
        accessory = db.accessories.find_one({'_id': ObjectId(product_id)})
        if not accessory:
            accessory = db.food.find_one({'_id': ObjectId(product_id)})
            if not accessory:
                return 'Product not found', 404
        return render_template('editProduct.html', product=accessory)
    elif request.method == 'POST':
        try:
            product_name = request.form['productName']
            product_type = request.form['productType']
            product_category = request.form['productCategory']
            product_quantity = int(request.form['productQuantity'])
            product_price = float(request.form['productPrice'])

            update_data = {
                'name': product_name,
                'type': product_type,
                'category': product_category,
                'quantity': product_quantity,
                'price': product_price
            }

            if 'productImage' in request.files:
                file = request.files['productImage']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    update_data['image'] = filename

            result = db.accessories.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})
            if result.modified_count == 0:
                result = db.food.update_one({'_id': ObjectId(product_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return jsonify({'result': 'success', 'msg': 'Produk berhasil diupdate'})
            return jsonify({'result': 'failure', 'msg': 'Produk tidak ditemukan atau update tidak berhasil'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/api/delete-product/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        result = db.accessories.delete_one({'_id': ObjectId(product_id)})
        if result.deleted_count == 0:
            result = db.food.delete_one({'_id': ObjectId(product_id)})
            if result.deleted_count == 0:
                return jsonify({'result': 'failure', 'msg': 'Produk tidak ditemukan'})
        return jsonify({'result': 'success', 'msg': 'Produk berhasil terhapus'})
    except Exception as e:
        return jsonify({'result': 'failure', 'msg': str(e)})

@app.route('/manageuser', methods=['GET', 'POST'])
def manageuser():
    users = list(db.users.find({}, {'_id': 0, 'email': 1, 'pet_name': 1, 'registration_date': 1, 'phone': 1, 'address': 1, 'profile_photo': 1}))
    return render_template('usManage.html', users=users)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    email = request.json.get('email')
    if email:
        result = db.users.delete_one({'email': email})
        if result.deleted_count == 1:
            return jsonify({'success': True, 'message': 'User sukses terhapus'}), 200
        else:
            return jsonify({'success': False, 'message': 'Penghapusan user gagal'}), 404
    else:
        return jsonify({'success': False, 'message': 'Email parameter tidak ada'}), 400

@app.route('/Groomingreserve', methods=['GET'])
def Bookgrooming():
    grooming_list = list(db.reservasi_grooming.find({}))
    return render_template('groomReserve.html', grooming=grooming_list)

@app.route('/api/add-groomingReserve', methods=['POST'])
def add_GReserve():
    if request.method == 'POST':
        try:
            name = request.form['groomingName']
            type = request.form['groomingType']
            services = request.form['groomingServices']
            waktu = request.form['groomingSchedule']
            antar_jemput = request.form['antar_jemput']

            new_reservation = {
                "name": name,
                "type": type,
                "services": services,
                "waktu": waktu,
                "antar_jemput": antar_jemput
            }
            # Assuming db is your MongoDB client and accessories is your collection
            db.reservasi_grooming.insert_one(new_reservation)

            return jsonify({'result': 'success', 'msg': 'Reservasi Grooming berhasil disimpan'})
        
        except Exception as e:
            return jsonify({"result": "error", "message": str(e)}), 400  # Return error message and HTTP status 400 (Bad Request) for client-side debugging


#@app.route('/api/edit-jadwal/<groom_id>', methods=['POST'])
#def edit_jadwal(groom_id):

#        try:
#            grooming_name = request.form['groomingName']
#            grooming_type = request.form['groomingType']
#            grooming_services = request.form['groomingServices']
#            grooming_schedule = request.form['groomingSchedule']
#            antar_jemput = request.form['antar_jemput']


#            update_data = {
#                'name': grooming_name,
#                'type': grooming_type,
#                'services': grooming_services,
#                'waktu': grooming_schedule,
#                'antar_jemput' : antar_jemput
#            }

#            result = db.reservasi_grooming.update_one({'_id': ObjectId(groom_id)}, {'$set': update_data})

#            if result.modified_count == 1:
#                return jsonify({'result': 'success', 'msg': 'Produk sukses diupdate'})
#            return jsonify({'result': 'failure', 'msg': 'Produk tidak ditemukan atau update tidak berhasil'})
#        except Exception as e:
#            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/edit-grooming-reservation/<groom_id>', methods=['GET', 'POST'])
def edit_grooming_reservation(groom_id):
    if request.method == 'GET':
        # Retrieve the grooming reservation details
        reservation = db.reservasi_grooming.find_one({'_id': ObjectId(groom_id)})
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        reservation['_id'] = str(reservation['_id'])
        return jsonify(reservation)
    elif request.method == 'POST':
        try:
            grooming_name = request.form['groomingName']
            grooming_type = request.form['groomingType']
            grooming_services = request.form['groomingServices']
            grooming_schedule = request.form['groomingSchedule']
            antar_jemput = request.form['antar_jemput']

            update_data = {
                'name': grooming_name,
                'type': grooming_type,
                'services': grooming_services,
                'waktu': grooming_schedule,
                'antar_jemput': antar_jemput
            }

            result = db.reservasi_grooming.update_one({'_id': ObjectId(groom_id)}, {'$set': update_data})

            if result.modified_count == 1:
                return redirect(url_for('Bookgrooming'))
            return jsonify({'result': 'gagal', 'msg': 'Reservasi tidak ditemukan atau gagal'})
        except Exception as e:
            return jsonify({'result': 'failure', 'msg': str(e)})
        
@app.route('/api/delete-jadwal/<groom_id>', methods=['DELETE'])
def delete_jadwal(groom_id):
    try:
        result = db.reservasi_grooming.delete_one({'_id': ObjectId(groom_id)})
        if result.deleted_count == 1:
            return jsonify({'result': 'success', 'msg': 'Reservasi berhasil terhapus'})
    except Exception as e:
        return jsonify({'result': 'failure', 'msg': str(e)})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
