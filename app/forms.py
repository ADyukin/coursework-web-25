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
    game_id = None  # Обычная переменная для ID игры
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    system_requirements = TextAreaField('Системные требования')
    price = DecimalField('Цена', default=0, validators=[NumberRange(min=0)])
    genre_id = SelectField('Жанр', coerce=int, validators=[DataRequired()])
    game_file = FileField('Файл игры', validators=[Optional()])
    image_file = FileField('Изображение', validators=[Optional()])
    image_url = StringField('URL изображения', validators=[Optional()]) 
    submit = SubmitField('Сохранить')

    def validate_title(self, field):
        game_repository = GameRepository(db)
        if game_repository.game_exists_by_title(field.data, exclude_id=self.game_id):
            raise ValidationError('Игра с таким названием уже существует')