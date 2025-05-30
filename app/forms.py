from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DecimalField, IntegerField, BooleanField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from .repositories import UserRepository, GameRepository
from . import db

class UserForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Роль', coerce=str)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.role.choices = UserRepository(None).get_all_roles()

class GameForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    system_requirements = TextAreaField('Системные требования')
    price = DecimalField('Цена', validators=[DataRequired(), NumberRange(min=0)], places=2)
    genre_id = SelectField('Жанр', coerce=int, validators=[DataRequired()])
    game_file = FileField('Файл игры', validators=[Optional()])
    image_file = FileField('Изображение', validators=[Optional()])
    image_url = StringField('URL изображения', validators=[Optional()])
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        self.game_id = kwargs.pop('game_id', None)  # Получаем ID игры, если он есть
        super(GameForm, self).__init__(*args, **kwargs)
        self.game_repository = GameRepository(db)

    def validate_title(self, field):
        # Проверяем уникальность только при создании новой игры
        if not self.game_id and self.game_repository.game_exists_by_title(field.data):
            raise ValidationError('Игра с таким названием уже существует')