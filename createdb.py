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
    company_tin = fields.CharField(max_length=200)
    phone_number = fields.CharField(max_length=12)
    contract_number = fields.CharField(max_length=6)
    password = fields.CharField(max_length=255)

class UserTickets(Model):
    id = fields.IntField(pk=True)
    ticket_type = fields.CharField(max_length=255)
    ticket_status = fields.CharField(max_length=20)
    ticket_title = fields.CharField(max_length=100)
    ticket_description = fields.CharField(max_length=4096)
    software_name = fields.CharField(max_length=50)
    software_version = fields.FloatField()
    firmware_version = fields.FloatField()
    system_software_version = fields.FloatField()
    ticket_logs_id = fields.ForeignKeyField("models.UserLog",
                                            source_field="log_file")

class UserLog(Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    ticket_log_file_name = fields.CharField(max_length=2048)
    ticket_log_file_path = fields.CharField(max_length=4096)
    ticket_log_file_size = fields.IntField()
    ticket_last_update = fields.DateField(default=date.today())


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



async def check_user_password(user_mail, hashed_password):
    user_data = await get_user_by(user_mail)
    if user_data:
        db_password = user_data.password
        if hashed_password == db_password:
            return user_data
        else:
            return False
    else:
        return False

async def get_user_by(user_mail):
    user_data = await Users.filter(user_mail=user_mail).first()
    return user_data

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

async def checking_user_presence(user_mail):
    try:
        user_row = await Users.filter(user_mail=user_mail).exists()
        print('user_row:', user_row)
        if not user_row:
            return False
        else:
            return True
    except Exception as exc:
        return False

async def create_user(user_data):
    try:
        hashed_password = hashlib.sha256(user_data['password'].encode('utf-8')).hexdigest()
        user = await Users.create(
            user_mail=user_data['user_mail'],
            company_tin=user_data['company_tin'],
            phone_number=user_data['phone_number'],
            contract_number=user_data['contract_number'],
            password=hashed_password
        )
        return user
    except IntegrityError as exc:
        raise IntegrityError(f'Ошибка: {exc} \n При попытке создания пользователя {user}')

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

