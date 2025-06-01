# Bookworm 📚

A modern e-commerce web application for book lovers, built with Flask and MySQL. Bookworm provides a seamless experience for browsing, purchasing books, and managing orders with a robust admin interface.

## 🌟 Features

### Customer Features
- 📖 Browse extensive book catalog with detailed descriptions
- 🛒 Shopping cart functionality
- 👤 User authentication and registration
- 💳 Multiple payment method support
- 📦 digital voucher management
- 📝 Contact form for customer support

### Admin Features
- 📊 Comprehensive admin dashboard
- 📚 Book inventory management
- 🏷️ Category management
- 👥 User management
- 💳 Payment management
- 📨 Customer message handling

## 🔧 Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **Frontend**: HTML, CSS, Bootstrap 3
- **Template Engine**: Jinja2
- **Authentication**: Flask-Login
- **Admin Panel**: Flask-Admin

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bookworm.git
cd bookworm
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Configure MySQL:
- Create a MySQL database named 'Bookworm'
- Update the database URI in `app.py` if needed:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/Bookworm'
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Create an admin user:
```bash
flask create-admin <username> <password>
```

7. Run the application:
```bash
flask run
```

## 📁 Project Structure

```
bookworm/
├── app.py              # Main application file
├── static/            
│   ├── images/        # Book images and other static files
│   └── css/          # Stylesheet files
├── templates/          # HTML templates
│   ├── admin/         # Admin interface templates
│   └── *.html         # User interface templates
├── migrations/         # Database migrations
└── requirements.txt    # Project dependencies
```

## 💻 Usage

1. Access the application at `http://localhost:5000`
2. Admin interface is available at `http://localhost:5000/admin`
3. Register a new user account or log in with existing credentials
4. Browse books, add to cart, and complete purchases
5. Admins can manage inventory, orders, and users through the admin interface



## 👥 Author

- Toe Aung Linn - [toeaunglynn@gmail.com]

## 🙏 Acknowledgments

- Flask documentation and community
- Bootstrap team
