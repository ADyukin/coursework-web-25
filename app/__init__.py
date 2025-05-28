import os
from flask import Flask, redirect, url_for, render_template, request
from flask_login import LoginManager, current_user
from .db import db
from .auth import login_manager, bp as auth_bp
from .users import bp as users_bp
from .repositories import user_repository
from .games import bp as games_bp
from .cart import bp as cart_bp
from . import orders
from .config import Config

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.from_mapping(test_config)

    # Настройка кодировки для Flask
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'
    login_manager.login_message_category = 'info'

    from .cli import init_db_command
    app.cli.add_command(init_db_command)

    from . import auth
    app.register_blueprint(auth.bp)
    auth.login_manager.init_app(app)

    from . import users
    app.register_blueprint(users.bp)
    
    from . import games
    app.register_blueprint(games.bp)

    from . import cart
    app.register_blueprint(cart.bp)

    from . import orders
    app.register_blueprint(orders.bp)

    @app.errorhandler(403)
    def forbidden_error(error):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return render_template('errors/403.html'), 403

    @app.route('/')
    def index():
        return redirect(url_for('games.index'))

    return app 