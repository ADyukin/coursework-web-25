from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import random
from flask import session
from .repositories import GameRepository, ReviewRepository
from . import db
from .forms import GameForm
from .auth import role_required
import re

bp = Blueprint('games', __name__, url_prefix='/games')
game_repository = GameRepository(db)
review_repository = ReviewRepository(db)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'games')
IMAGE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'images')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'zip', 'rar', '7z'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def get_game_word(count):
    """Возвращает правильное склонение слова 'игра' в зависимости от числа"""
    if count % 10 == 1 and count % 100 != 11:
        return 'игра'
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return 'игры'
    else:
        return 'игр'

@bp.route('/')
def index():
    """Показывает список всех игр"""
    # Получаем параметры фильтрации из запроса
    selected_genres = request.args.getlist('genres', type=int)
    selected_authors = request.args.getlist('authors', type=int)
    min_rating = request.args.get('rating', type=int)
    search_query = request.args.get('search', '').strip()
    
    # Получаем или создаем случайную игру для баннера в сессии
    if 'banner_game_id' not in session or not request.args:  # Обновляем только при полной перезагрузке
        banner_game_id = game_repository.get_banner_game()
        if banner_game_id:
            session['banner_game_id'] = banner_game_id
    
    # Получаем данные игры для баннера
    banner_game = None
    if 'banner_game_id' in session and not search_query:  # Не показываем баннер при поиске
        banner_game = game_repository.get_by_id(session['banner_game_id'])
        if banner_game:
            rating_info = review_repository.get_game_rating(banner_game['id'])
            banner_game.update(rating_info)
    
    # Получаем популярные и бесплатные игры
    popular_games = []
    free_games = []
    if not search_query and not selected_genres and not selected_authors and not min_rating:
        popular_games = game_repository.get_popular_games()
        free_games = game_repository.get_free_games()
    
    # Получаем отфильтрованные игры
    games = game_repository.get_filtered_games(
        search_query=search_query,
        selected_genres=selected_genres,
        selected_authors=selected_authors,
        min_rating=min_rating
    )
    
    # Добавляем рейтинг для каждой игры
    for game in games:
        rating_info = review_repository.get_game_rating(game['id'])
        game.update(rating_info)
    
    # Получаем жанры и авторов
    genres = game_repository.get_genres_with_count()
    authors = game_repository.get_authors()

    return render_template('games/index.html', 
                         games=games,
                         popular_games=popular_games,
                         free_games=free_games,
                         genres=genres,
                         authors=authors,
                         selected_genres=selected_genres,
                         selected_authors=selected_authors,
                         min_rating=min_rating,
                         banner_game=banner_game,
                         search_query=search_query.strip('%'),
                         get_game_word=get_game_word)

@bp.route('/all')
@login_required
@role_required(['admin'])
def all_games():
    """Показывает все игры (для администратора)"""
    games = game_repository.get_all_games()
    return render_template('games/all.html', games=games)

@bp.route('/my-games')
@login_required
@role_required(['author'])
def my_games():
    """Показывает игры автора"""
    games = game_repository.get_author_games(current_user.id)
    return render_template('games/my_games.html', games=games)

@bp.route('/purchased')
@login_required
@role_required(['buyer'])
def purchased_games():
    """Показывает купленные игры"""
    games = game_repository.get_purchased_games(current_user.id)
    return render_template('games/purchased.html', games=games)

@bp.route('/moderate')
@login_required
@role_required(['admin'])
def moderate():
    """Показывает игры на модерацию"""
    games = game_repository.get_pending_games()
    return render_template('games/moderate.html', games=games)

@bp.route('/<int:game_id>/approve', methods=['POST'])
@login_required
@role_required(['admin'])
def approve(game_id):
    """Одобряет игру"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'danger')
        return redirect(url_for('games.moderate'))
    
    game_repository.update_status(game_id, 'approved')
    flash('Игра успешно одобрена', 'success')
    return redirect(url_for('games.moderate'))

@bp.route('/<int:game_id>/reject', methods=['POST'])
@login_required
@role_required(['admin'])
def reject(game_id):
    """Отклоняет игру"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'danger')
        return redirect(url_for('games.moderate'))
    
    # Удаляем файлы игры и запись из базы данных
    game_repository.delete(game_id)
    flash('Игра отклонена и удалена', 'success')
    return redirect(url_for('games.moderate'))

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required(['author', 'admin'])
def create():
    """Создает новую игру"""
    form = GameForm()
    form.genre_id.choices = [(g['id'], g['name']) for g in game_repository.get_all_genres()]

    if form.validate_on_submit():
        file_path = None
        image_path = None

        if form.game_file.data:
            file = form.game_file.data
            if file and allowed_file(file.filename):
                filename = generate_safe_filename(form.title.data, file.filename)
                file_path = filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))

        if form.image_file.data:
            image = form.image_file.data
            if image and allowed_image(image.filename):
                filename = generate_safe_filename(form.title.data, image.filename)
                image_path = filename
                image.save(os.path.join(IMAGE_FOLDER, filename))

        game_repository.create(
            title=form.title.data,
            description=form.description.data,
            system_requirements=form.system_requirements.data,
            price=form.price.data,
            genre_id=form.genre_id.data,
            author_id=current_user.id,
            file_path=file_path,
            image_url=image_path or form.image_url.data,
            status='approved' if current_user.role == 'admin' else 'pending'
        )
        
        flash('Игра успешно создана' + (' и ожидает модерации' if current_user.role != 'admin' else ''), 'success')
        return redirect(url_for('games.index'))

    return render_template('games/form.html', form=form, title='Создание игры')

@bp.route('/<int:game_id>/download')
def download(game_id):
    """Скачивает игру"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'danger')
        return redirect(url_for('games.index'))
    
    # Если игра платная, проверяем права на скачивание
    if game['price'] > 0:
        if not current_user.is_authenticated:
            flash('Для скачивания платной игры необходимо авторизоваться', 'warning')
            return redirect(url_for('auth.login', next=url_for('games.view', game_id=game_id)))
        
        if current_user.role == 'author' and current_user.id != game['author_id']:
            abort(403)
        elif current_user.role == 'buyer' and not game_repository.is_game_purchased(game_id, current_user.id):
            flash('Для скачивания необходимо приобрести игру', 'warning')
            return redirect(url_for('games.view', game_id=game_id))
    
    if not game['file_path']:
        flash('Файл игры не найден', 'danger')
        return redirect(url_for('games.view', game_id=game_id))
    
    return send_from_directory(UPLOAD_FOLDER, game['file_path'], as_attachment=True)

@bp.route('/<int:game_id>')
def view(game_id):
    """Показывает информацию об игре"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'error')
        return redirect(url_for('games.index'))
    
    # Добавляем информацию о рейтинге
    rating_info = review_repository.get_game_rating(game_id)
    game.update(rating_info)

    # Получаем похожие игры
    similar_games = game_repository.get_filtered_games(selected_genres=[game['genre_id']])
    similar_games = [g for g in similar_games if g['id'] != game_id][:3]
    
    # Добавляем рейтинг для похожих игр
    for similar_game in similar_games:
        rating_info = review_repository.get_game_rating(similar_game['id'])
        similar_game.update(rating_info)

    # Получаем отзывы
    reviews = review_repository.get_game_reviews(game_id)

    # Проверяем, купил ли пользователь игру и оставил ли отзыв
    has_purchased = False
    has_reviewed = False
    if current_user.is_authenticated:
        has_purchased = game_repository.is_game_purchased(game_id, current_user.id)
        has_reviewed = review_repository.has_user_reviewed(current_user.id, game_id)

    return render_template('games/view.html',
                         game=game,
                         reviews=reviews,
                         similar_games=similar_games,
                         has_purchased=has_purchased,
                         has_reviewed=has_reviewed)

@bp.route('/<int:game_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['author', 'admin'])
def edit(game_id):
    """Редактирует игру"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'error')
        return redirect(url_for('games.index'))
    
    # Проверяем права доступа
    if current_user.role != 'admin' and game['author_id'] != current_user.id:
        flash('У вас нет прав для редактирования этой игры', 'error')
        return redirect(url_for('games.index'))
    
    form = GameForm()
    form.game_id = game_id  # Устанавливаем ID игры как обычную переменную
    form.genre_id.choices = [(g['id'], g['name']) for g in game_repository.get_all_genres()]
    
    if request.method == 'GET':
        form.title.data = game['title']
        form.description.data = game['description']
        form.system_requirements.data = game['system_requirements']
        form.price.data = game['price']
        form.genre_id.data = game['genre_id']
        form.image_url.data = game['image_url']
    
    if form.validate_on_submit():
        file_path = game['file_path']
        image_path = game['image_url']

        if form.game_file.data:
            file = form.game_file.data
            if file and allowed_file(file.filename):
                # Удаляем старый файл
                if file_path:
                    old_file_path = os.path.join(UPLOAD_FOLDER, file_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                filename = generate_safe_filename(form.title.data, file.filename)
                file_path = filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))

        if form.image_file.data:
            image = form.image_file.data
            if image and allowed_image(image.filename):
                # Удаляем старое изображение
                if image_path and image_path.startswith('images/'):
                    old_image_path = os.path.join(IMAGE_FOLDER, image_path.split('/')[-1])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = generate_safe_filename(form.title.data, image.filename)
                image_path = f'images/{filename}'
                image.save(os.path.join(IMAGE_FOLDER, filename))

        game_repository.update(
            game_id=game_id,
            title=form.title.data,
            description=form.description.data,
            system_requirements=form.system_requirements.data,
            price=form.price.data,
            genre_id=form.genre_id.data,
            file_path=file_path,
            image_url=image_path or form.image_url.data
        )
        
        flash('Игра успешно обновлена', 'success')
        return redirect(url_for('games.view', game_id=game_id))

    return render_template('games/form.html', form=form, title='Редактирование игры')

@bp.route('/<int:game_id>/delete', methods=['POST'])
@login_required
@role_required(['author', 'admin'])
def delete(game_id):
    """Удаляет игру"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'danger')
        return redirect(url_for('games.index'))

    # Проверяем права на удаление
    if current_user.role != 'admin' and current_user.id != game['author_id']:
        abort(403)

    if game_repository.delete(game_id):
        flash('Игра успешно удалена', 'success')
    else:
        flash('Ошибка при удалении игры', 'danger')
    return redirect(url_for('games.index')) 

@bp.route('/<int:game_id>/review', methods=['POST'])
@login_required
def add_review(game_id):
    """Добавляет отзыв к игре"""
    game = game_repository.get_by_id(game_id)
    if game is None:
        flash('Игра не найдена', 'danger')
        return redirect(url_for('games.index'))
    
    # Проверяем, купил ли пользователь игру
    if not game_repository.is_game_purchased(game_id, current_user.id):
        flash('Вы можете оставить отзыв только после покупки игры', 'warning')
        return redirect(url_for('games.view', game_id=game_id))
    
    # Проверяем, не оставил ли пользователь уже отзыв
    if review_repository.has_user_reviewed(current_user.id, game_id):
        flash('Вы уже оставили отзыв на эту игру', 'warning')
        return redirect(url_for('games.view', game_id=game_id))
    
    rating = int(request.form.get('rating', 0))
    comment = request.form.get('comment', '').strip()

    if not rating or not comment:
        flash('Пожалуйста, заполните все поля', 'warning')
        return redirect(url_for('games.view', game_id=game_id))

    review_repository.create_review(current_user.id, game_id, rating, comment)
    flash('Отзыв успешно добавлен', 'success')
    return redirect(url_for('games.view', game_id=game_id))

@bp.route('/images/<filename>')
def serve_image(filename):
    """Отдает изображение игры"""
    # Заменяем обратные слеши на прямые
    filename = filename.replace('\\', '/')
    if filename.startswith('images/'):
        filename = filename.split('/')[-1]
    return send_from_directory(IMAGE_FOLDER, filename)

def generate_safe_filename(title, original_filename):
    """Генерирует безопасное имя файла на основе названия игры"""
    # Получаем расширение файла
    _, ext = os.path.splitext(original_filename)
    
    # Очищаем название игры от специальных символов
    safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title)
    safe_title = re.sub(r'\s+', '-', safe_title).lower()
    
    return f"{safe_title}{ext}"

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = GameForm()
    form.genre_id.choices = [(g['id'], g['name']) for g in game_repository.get_all_genres()]

    if form.validate_on_submit():
        filename = None
        image_filename = None
        
        # Обработка файла игры
        if form.game_file.data:
            game_file = form.game_file.data
            if game_file.filename:
                filename = generate_safe_filename(form.title.data, game_file.filename)
                game_file.save(os.path.join(UPLOAD_FOLDER, filename))
        
        # Обработка изображения
        if form.image_file.data:
            image = form.image_file.data
            if image.filename:
                image_filename = generate_safe_filename(form.title.data, image.filename)
                image.save(os.path.join(IMAGE_FOLDER, image_filename))
        
        # Создание игры
        game_repository.create(
            title=form.title.data,
            description=form.description.data,
            system_requirements=form.system_requirements.data,
            price=form.price.data,
            genre_id=form.genre_id.data,
            author_id=current_user.id,
            file_path=filename,
            image_url=image_filename
        )
        
        flash('Игра успешно добавлена', 'success')
        return redirect(url_for('games.index'))
    
    return render_template('games/add.html', form=form) 