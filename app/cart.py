from flask import Blueprint, session, redirect, url_for, flash, render_template, request
from flask_login import current_user
from .repositories import CartRepository
from . import db

bp = Blueprint('cart', __name__, url_prefix='/cart')
cart_repository = CartRepository(db)

def get_cart():
    """Получает содержимое корзины из сессии"""
    return session.get('cart', [])

def add_to_cart(game_id):
    """Добавляет игру в корзину"""
    cart = get_cart()
    if game_id not in cart:
        cart.append(game_id)
        session['cart'] = cart
        return True
    return False

def remove_from_cart(game_id):
    """Удаляет игру из корзины"""
    cart = get_cart()
    if game_id in cart:
        cart.remove(game_id)
        session['cart'] = cart
        return True
    return False

def clear_cart():
    """Очищает корзину"""
    session.pop('cart', None)

@bp.route('/')
def view():
    """Показывает содержимое корзины"""
    cart_items, total = cart_repository.get_cart_items(get_cart())
    return render_template('cart/view.html', 
                         cart_items=cart_items,
                         total=total)

@bp.route('/add/<int:game_id>')
def add(game_id):
    """Добавляет игру в корзину"""
    if add_to_cart(game_id):
        return '', 204  # Возвращаем пустой ответ с кодом 204 (No Content)
    return '', 400  # Возвращаем ошибку, если игра уже в корзине

@bp.route('/remove/<int:game_id>')
def remove(game_id):
    """Удаляет игру из корзины"""
    remove_from_cart(game_id)
    return '', 204  # Возвращаем пустой ответ с кодом 204 (No Content)

@bp.route('/checkout', methods=['POST'])
def checkout():
    """Обрабатывает оформление заказа"""
    if not current_user.is_authenticated:
        flash('Для оформления заказа необходимо авторизоваться', 'warning')
        return redirect(url_for('auth.login'))

    cart_items = get_cart()
    if not cart_items:
        return redirect(url_for('cart.view'))

    cart_items, total = cart_repository.get_cart_items(cart_items)
    if not cart_items:
        flash('Ошибка при получении информации о товарах', 'danger')
        return redirect(url_for('cart.view'))
        
        # Создаем заказ
    order_id = cart_repository.create_order(current_user.id, total, [item['id'] for item in cart_items])
    
    # Очищаем корзину
    clear_cart()
    
    flash('Заказ успешно оформлен! Скоро вы получите игру на указанный email', 'success')
    return redirect(url_for('games.index')) 