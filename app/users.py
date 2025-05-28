from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .repositories import UserRepository
from . import db
from .forms import UserForm
from .auth import role_required
import hashlib

user_repository = UserRepository(db)

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/')
@login_required
@role_required(['admin'])
def index():
    users = user_repository.all()
    return render_template('users/index.html', users=users)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def create():
    form = UserForm()
    if form.validate_on_submit():
        password_hash = hashlib.sha256(form.password.data.encode()).hexdigest()
        user_repository.create(
            name=form.name.data,
            email=form.email.data,
            password_hash=password_hash,
            role=form.role.data
        )
        flash('Пользователь успешно создан', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/form.html', form=form, title='Создание пользователя')

@bp.route('/<int:user_id>')
@login_required
@role_required(['admin'])
def view(user_id):
    user = user_repository.get_by_id(user_id)
    if user is None:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('users.index'))
    return render_template('users/view.html', user=user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UserForm()
    # Скрываем поле пароля при редактировании
    del form.password

    if form.validate_on_submit():
        # Для обычных пользователей сохраняем текущую роль
        role = form.role.data if current_user.role == 'admin' else current_user.role
        
        # Получаем текущего пользователя из базы данных
        user = user_repository.get_by_id(current_user.id)
        if user is None:
            flash('Ошибка при обновлении профиля', 'danger')
            return redirect(url_for('users.edit_profile'))
        
        # Обновляем данные
        user_repository.update(
            user_id=current_user.id,
            name=form.name.data,
            email=form.email.data,
            role=role
        )
        
        # Обновляем данные в current_user
        current_user.name = form.name.data
        current_user.email = form.email.data
        
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('users.edit_profile'))

    # При GET запросе заполняем форму текущими данными
    form.name.data = current_user.name
    form.email.data = current_user.email
    form.role.data = current_user.role
    
    return render_template('users/form.html', 
                         form=form, 
                         title='Редактирование профиля',
                         is_admin=(current_user.role == 'admin'))

@bp.route('/profile')
@login_required
def view_profile():
    return render_template('users/profile.html')

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit(user_id):
    user = user_repository.get_by_id(user_id)
    if user is None:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('users.index'))

    form = UserForm()
    # Скрываем поле пароля при редактировании
    del form.password

    if form.validate_on_submit():
        user_repository.update(
            user_id=user_id,
            name=form.name.data,
            email=form.email.data,
            role=form.role.data
        )
        flash('Пользователь успешно обновлен', 'success')
        return redirect(url_for('users.edit', user_id=user_id))

    form.name.data = user['name']
    form.email.data = user['email']
    form.role.data = user['role']
    return render_template('users/form.html', form=form, title='Редактирование пользователя')

@bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete(user_id):
    user = user_repository.get_by_id(user_id)
    if user is None:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('users.index'))

    if user_repository.delete(user_id):
        flash('Пользователь успешно удален', 'success')
    else:
        flash('Ошибка при удалении пользователя', 'danger')
    return redirect(url_for('users.index'))
