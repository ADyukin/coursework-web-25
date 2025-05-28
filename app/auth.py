from functools import wraps
from flask import Blueprint, request, render_template, url_for, flash, redirect, current_app, abort
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from .repositories import UserRepository
from . import db
import hashlib

user_repository = UserRepository(db)

bp = Blueprint('auth', __name__, url_prefix='/auth')

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Авторизуйтесь для доступа к этому ресурсу.'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_id, name, email, role=None, created_at=None):
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.created_at = created_at

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@login_manager.user_loader
def load_user(user_id):
    user = user_repository.get_by_id(user_id)
    if user is not None:
        return User(user['id'], user['name'], user['email'], user['role'], user['created_at'])
    return None

@bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        remember_me = request.form.get('remember_me') == 'on'

        # Хешируем пароль
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user = user_repository.get_by_name_and_password(name, password_hash)

        if user is not None:
            flash('Авторизация прошла успешно', 'success')
            login_user(User(user['id'], user['name'], user['email'], user['role'], user['created_at']), remember=remember_me)
            next_url = request.args.get('next', url_for('games.index'))
            return redirect(next_url)

        flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('games.index'))