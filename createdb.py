from tortoise import Tortoise, fields
from tortoise.models import Model
from datetime import date, datetime
import uuid
import hashlib
from peewee import IntegrityError
from tortoise.exceptions import DBConnectionError


# class Content(Model):
#     id = fields.IntField(pk=True)
#     idblock = fields.CharField(max_length=255)
#     short_title = fields.CharField(max_length=255)
#     img = fields.CharField(max_length=255)
#     altimg = fields.CharField(max_length=255)
#     title = fields.CharField(max_length=255)
#     contenttext = fields.CharField(max_length=255)
#     author = fields.CharField(max_length=255)
#     timestampdata = fields.DateField(default=datetime.date(datetime.now()))


class Users(Model):
    id = fields.IntField(pk=True)
    user_mail = fields.CharField(max_length=255)
    company_name = fields.CharField(max_length=200)
    phone_number = fields.CharField(max_length=12)
    contract_number = fields.CharField(max_length=6)
    password = fields.CharField(max_length=255)


async def create_models():
    try:
        await Tortoise.generate_schemas()
    except Exception as exc:
        raise Exception(f'Ошибка создания модели БД: {exc}')

async def connect():
    try:
        await Tortoise.init(
            db_url="sqlite://flask_database.db",
            modules={"models": ["createdb"]},
        )
    except DBConnectionError as exc:
        raise DBConnectionError(f'Ошибка подключения к БД: {exc}')


async def create_user(user, password):
    try:
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        check_user = await Users.filter(username=user).exists()
        # check_user_2 = await Users.filter(username=user).first()
        if check_user:
            return False
        await Users.create(
            username=user,
            password=hashed_password
        )
        return True
    except IntegrityError as exc:
        raise IntegrityError(f'Ошибка: {exc} \n При попытке создания пользователя {user}')


async def check_user(user_mail, hashed_password):
    check_user = await Users.filter(user_mail=user_mail).first()
    if check_user:
        db_password = check_user.password
        if hashed_password == db_password:
            return check_user
        else:
            return False
    else:
        return False

# async def get_content():
#     content_data = await Content.all()
#     json_data = {}
#     print(content_data)
#     for row in content_data:
#         if row.idblock not in json_data:
#             json_data[row.idblock] = []
#
#         json_data[row.idblock].append({
#             'id': row.id,
#             'short_title': row.short_title,
#             'img': row.img,
#             'altimg': row.altimg,
#             'title': row.title,
#             'contenttext': row.contenttext,
#             'author': row.author,
#             'timestampdata': row.timestampdata
#         })
#     return json_data

async def get_user(user_id):
    try:
        user_row = await Users.filter(id=user_id)
        return user_row[0]
    except Exception as exc:
        return False

# async def db_update_content(form_dict):
#     if await Content.filter(id=form_dict['id']):
#         try:
#             content = await Content.get(id=form_dict['id'])
#             await content.update_from_dict(form_dict)
#             await content.save()
#         except Exception as exc:
#             raise f'Error  : {exc}'
#         return True
#     return False

