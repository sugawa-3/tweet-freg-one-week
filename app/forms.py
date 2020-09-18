from flask_wtf import FlaskForm
from wtforms import Form, StringField, ValidationError, validators
from wtforms.validators import Required


class SearchForm(FlaskForm):
    search_word = StringField('検索ワード', validators=[validators.Length(max=15, message='は15文字以下で入力して下さい')])

class DownloadForm(FlaskForm):
    search_word = StringField('検索ワード', validators=[validators.Required(message='')])
    total = StringField('ツイート総数', validators=[validators.Required(message='')])
    oneweek = StringField('1週間', validators=[validators.Required(message='')])
    counts = StringField('ツイート数', validators=[validators.Required(message='')])
