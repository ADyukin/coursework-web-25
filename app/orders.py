from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_login import login_required, current_user
from .repositories import OrderRepository
from . import db

bp = Blueprint('orders', __name__, url_prefix='/orders')
order_repository = OrderRepository(db)

@bp.route('/')
@login_required
def list():
    """Показывает список заказов пользователя"""
    orders = order_repository.get_user_orders(current_user.id)
    return render_template('orders/list.html', orders=orders)

@bp.route('/<int:order_id>')
@login_required
def view(order_id):
    """Показывает информацию о конкретном заказе"""
    order = order_repository.get_order_by_id(order_id)
    if not order:
        flash('Заказ не найден', 'danger')
        return redirect(url_for('orders.list'))
    
    # Проверяем, принадлежит ли заказ текущему пользователю
    if order['buyer_id'] != current_user.id and current_user.role != 'admin':
        flash('У вас нет доступа к этому заказу', 'danger')
        return redirect(url_for('orders.list'))
    
    return render_template('orders/view.html', order=order) 