from datetime import datetime
import click
import re
from flask_login import current_user,LoginManager
from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin,AdminIndexView
from flask_admin.contrib.sqla import ModelView
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin.form import ImageUploadField
from werkzeug.utils import secure_filename
from flask_admin import AdminIndexView, expose
from flask_admin.menu import MenuLink
app = Flask(__name__)
app.secret_key = 'calkjdfjejazxcb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/Bookworm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/'

db = SQLAlchemy(app)

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('admin_login'))
        return redirect(url_for('book.index_view'))
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))
    def is_visible(self):
        return False


admin = Admin(name="Bookworm",template_mode = 'bootstrap3')
migrate = Migrate(app, db)
admin.init_app(app, index_view=MyAdminIndexView(url='/admin'))
admin.index_view = MyAdminIndexView(url='/admin')
logout_link = MenuLink('Logout', endpoint='admin_logout')
admin.add_link(logout_link)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin-login'

@app.cli.command("create-admin")
@click.argument('username')
@click.argument('password')
def create_admin(username, password):
    """Create an admin user from the command line."""
    hashed_password = generate_password_hash(password)
    new_admin = AdminUser(username=username, password=hashed_password, is_admin=True)
    db.session.add(new_admin)
    db.session.commit()
    print('Admin user created successfully!')

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False) 
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return self.name

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    pay_method = db.Column(db.String(100), unique=True, nullable=False)

   
    orders = db.relationship('BookOrder', back_populates='payment_method')

    def __repr__(self):
        return f'<PaymentMethod {self.pay_method}>'

order_items = db.Table('order_items',
    db.Column('book_order_id', db.Integer, db.ForeignKey('book_orders.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
)

class BookOrder(db.Model):
    __tablename__ = 'book_orders'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)

    
    books = db.relationship('Book', secondary=order_items, back_populates='orders')    
    payment_method = db.relationship('PaymentMethod', back_populates='orders')

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('books', lazy=True))
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    
    orders = db.relationship('BookOrder', secondary=order_items, back_populates='books')
    def __repr__(self):
        return f'{self.name}'
    
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref='cart_items')
    book = db.relationship('Book', backref='cart_items')

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin-login'))

class UserAdmin(MyModelView):
    column_exclude_list = ['password']
    form_excluded_columns = ['password']
    column_searchable_list = ['user_name']
    can_create = False  
    can_edit = False  
    can_delete = False

def _list_thumbnail(view, context, model, name):
    if not model.image_path:
        return ''
    return Markup(f'<img src="{url_for('static', filename="images/" + model.image_path)}" style="height:100px; ">')
    
    
class BookOrderAdmin(MyModelView):
    column_list = ('id', 'user_name', 'email', 'address', 'payment_method', 'order_date', 'total_price')
    column_searchable_list = ('user_name', 'email', 'address')
    column_filters = ('user_name', 'email', 'address', 'payment_method.pay_method', 'order_date')
    can_create = False  
    can_edit = False  
    can_delete = True

    column_formatters = {
        'payment_method': lambda view, context, model, name: 
            Markup(f'<a href="{url_for("paymentmethod.details_view", id=model.payment_method_id)}">{model.payment_method.pay_method}</a>')
    }
    
class BookAdmin(MyModelView):
    
    column_searchable_list = ['name', 'author']
    form_columns = ['name', 'author', 'category', 'description', 'price', 'image_path']
    can_view_details = True
    form_overrides = {
        'image_path': ImageUploadField
    }
    form_args = {
        'image_path': {
            'label': 'Book Image',
            'base_path': app.config['UPLOAD_FOLDER'],
            'allow_overwrite': False,
            'namegen': lambda obj, file_data: secure_filename(file_data.filename)
        }
    }
    column_formatters = {
        'image_path': _list_thumbnail
    }
    
class ReportModelView(MyModelView):
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    column_searchable_list = ['name', 'email']
    column_filters = ['email', 'date_posted']
    form_excluded_columns = ['date_posted'] 


admin.add_view(UserAdmin(User, db.session))
admin.add_view(BookAdmin(Book, db.session, name='Books'))
admin.add_view(ModelView(PaymentMethod, db.session, name='Payment Method'))
admin.add_view(BookOrderAdmin(BookOrder, db.session, name='Book Orders'))
admin.add_view(ReportModelView(Report, db.session))

 
@login_manager.user_loader
def load_user(id):
    return AdminUser.query.get(int(id))

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    message = ""
    alert_type=""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            if user.is_admin:
                login_user(user)
                return redirect(url_for('admin.index'))
            else:
                message = 'You do not have the required permissions'
                alert_type="danger"
                return render_template('admin/login.html',message=message,alert_type=alert_type)
            

        else:
            
            message = 'Invalid username or password'
            alert_type="danger"
            return render_template('admin/login.html',message=message,alert_type=alert_type)


    return render_template('admin/login.html')

@app.route('/admin-logout')
def admin_logout():
    logout_user()  
    
    return redirect(url_for('admin_login'))    
    
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    alert_type = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        entered_password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, entered_password):
            session['loggedin'] = True
            session['userid'] = user.user_id
            session['name'] = user.user_name
            session['email'] = user.email
            message = 'Logged in successfully'
            alert_type = "success"
            return redirect(url_for('home'))
        else:
            message = 'Invalid email or password'
            alert_type = "danger"

    return render_template('login.html', message=message, alert_type=alert_type)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    alert_type = ''
    if request.method == 'POST' and all(k in request.form for k in ['name', 'email', 'phone', 'password']):
        userName = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        account = User.query.filter_by(email=email).first()

        if account:
            message = 'Account Already Exists'
            alert_type = "danger"
        elif not userName or not password or not email:
            message = 'Please Fill Out the Form'
            alert_type = "danger"
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid Email Address'
            alert_type = "danger"
        else:
    
            password_hash = generate_password_hash(password)
            new_user = User(user_name=userName, email=email, phone=phone, password=password_hash)
            db.session.add(new_user)
            db.session.commit()
            message = 'Registration Completed Successfully'
            alert_type = "success"
            return render_template('login.html', message=message, alert_type=alert_type)
    return render_template('register.html', message=message, alert_type=alert_type)



@app.route('/home')
def home():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/book')
def book():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    books = Book.query.all()
    return render_template('book.html', books=books)


@app.route('/aboutus')
def about():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    return render_template('aboutus.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    try:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message_content = request.form['message']  
        new_message = Report(name=name, email=email, phone=phone, message=message_content)
        db.session.add(new_message)
        db.session.commit()
        message = 'Your Report Submitted Successfully'
        return render_template('contact.html', message=message)
    except Exception as e:
        message = 'Error occurred: ' + str(e)
        return render_template('contact.html', message=message)

@app.route('/contact')
def contact():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    return render_template('contact.html')

def get_book_by_id(book_id):
    book = Book.query.get(book_id)
    return book


@app.route('/item/<int:book_id>')
def item(book_id):
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    book = get_book_by_id(book_id)
    return render_template('itemdetail.html', book = book)


@app.route('/add-to-cart/<int:book_id>', methods=['POST'])
def add_to_cart(book_id):
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))  

    user_id = session['userid'] 
    quantity = int(request.form.get('quantity', 1))  

    cart_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()

    if cart_item:
        cart_item.quantity += quantity 
    else:
        new_cart_item = CartItem(user_id=user_id, book_id=book_id, quantity=quantity)
        db.session.add(new_cart_item)

    db.session.commit()
    return redirect(url_for('book'))


@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity_str = request.form.get('quantity')
    print(f"Received quantity string: {quantity_str}")  

    try:
        new_quantity = int(quantity_str)
    except (TypeError, ValueError) as e:
        print(f"Error converting quantity to int: {e}")  

    cart_item = CartItem.query.get(item_id)

    if cart_item:
        if new_quantity > 0:
            cart_item.quantity = new_quantity
        else:
            db.session.delete(cart_item)
        db.session.commit()

    return redirect(url_for('view_cart'))


@app.route('/remove_cart_item/<int:item_id>', methods=['POST'])
def remove_cart_item(item_id):
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))  

    cart_item = CartItem.query.get(item_id)
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
    else:
        pass
        
    return redirect(url_for('view_cart'))


@app.context_processor
def inject_cart_details():
    if 'loggedin' in session and session['loggedin']:
        user_id = session['userid']
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        total_items = sum(item.quantity for item in cart_items) 
    else:
        total_items = 0  

    return {'total_items': total_items}


@app.route('/view-cart')
def view_cart():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))  

    user_id = session['userid'] 
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    subtotal = sum(item.book.price * item.quantity for item in cart_items)
    return render_template('add-to-cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/check_out')
def check_out():
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    user_id = session['userid']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    items_with_subtotals = [
        {
            'name': item.book.name,
            'price': item.book.price,
            'quantity': item.quantity,
            'subtotal': item.book.price * item.quantity
        }
        for item in cart_items
    ]
    total = sum(item['subtotal'] for item in items_with_subtotals)
    payment_methods = PaymentMethod.query.all()
    return render_template('checkout.html', items_with_subtotals=items_with_subtotals, total=total,payment_methods=payment_methods)


def prepare_order_confirmation(user_id):
    """Prepare order details to be used in the order confirmation."""
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    items_with_subtotals = [{
        'book_id': item.book.id,
        'name': item.book.name,
        'author': item.book.author,
        'price': item.book.price,
        'quantity': item.quantity,
        'subtotal': item.book.price * item.quantity,
        'image': item.book.image_path if item.book.image_path else 'default.jpg'
    } for item in cart_items]
    total_price = sum(item['subtotal'] for item in items_with_subtotals)
    shipping_fee = 22  
    grand_total = total_price + shipping_fee

    session['order_details'] = {
        'items_with_subtotals': items_with_subtotals,
        'total_price': total_price,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total
    }

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'loggedin' not in session or not session['loggedin']:
        session['message'] = "You need to log in to place an order."
        session['alert_type'] = "danger"
        return redirect(url_for('login'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    address = request.form.get('address')
    payment_method_id = request.form.get('payment_method_id')
    
    if not all([username, email, address, payment_method_id]):
        session['message'] = "Please complete all fields."
        session['alert_type'] = "danger"
        return redirect(url_for('check_out'))
    
    user_id = session['userid']
    prepare_order_confirmation(user_id) 

    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        session['message'] = "Your cart is empty."
        session['alert_type'] = "danger"
        return redirect(url_for('check_out'))

    total_price = sum(item.book.price * item.quantity for item in cart_items)
    new_order = BookOrder(
        user_name=username,
        email=email,
        address=address,
        payment_method_id=payment_method_id,
        order_date=datetime.utcnow(),
        total_price=total_price
    )

    db.session.add(new_order)
    try:
        db.session.commit()
        for item in cart_items:
            db.session.delete(item)
        db.session.commit()
        session['message'] = "Your Previous order has been successfully placed."
        session['alert_type'] = "success"
    except Exception as e:
        db.session.rollback()
        session['message'] = f"An error occurred while placing your order: {str(e)}"
        session['alert_type'] = "danger"

    return redirect(url_for('order_confirm', order_id=new_order.id))


@app.route('/order_confirm/<int:order_id>')
def order_confirm(order_id):
    if 'loggedin' not in session or not session['loggedin']:
        return redirect(url_for('login'))
    order = BookOrder.query.get(order_id)
    if not order:
        return redirect(url_for('home', message="Order not found.", alert_type="danger"))
    order_details = session.pop('order_details', None)
    if not order_details:
        return redirect(url_for('home', message="Error retrieving order details.", alert_type="danger"))
    return render_template('receipt.html', order=order, order_date=order.order_date.strftime("%d %b, %Y"),
                           items_with_subtotals=order_details['items_with_subtotals'],
                           total_price=order_details['total_price'],
                           shipping_fee=order_details['shipping_fee'],
                           grand_total=order_details['grand_total'])


if __name__ == "__main__":
    app.run(debug=True)
    
    