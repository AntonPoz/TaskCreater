from quart import Quart, render_template, redirect, url_for, request, session
import asyncio
import hashlib
from createdb import (connect, close_connection, create_models,
                      check_user_password, Tortoise,
                      checking_user_presence, create_user, get_user_by_id)
from werkzeug.exceptions import InternalServerError
import logging
import random
import json
from external_services import check_user_data, check_user_email, check_company_name


app = Quart(__name__)
app.secret_key = 'Just hash. All day, all night'
app.logger.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,  # (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

@app.before_serving
async def startup():
    """Выполняется при запуске приложения"""
    try:
        await connect()
        await create_models()
    except Exception as exc:
        raise f'Ошибка: {exc}'

@app.after_serving
async def shutdown():
    """Выполняется при завершении работы"""
    await close_connection()

@app.route('/')
async def main():
    return await render_template('base_content.html')


@app.route('/home')
async def home():
    return await render_template('home.html')


@app.route('/about')
async def about():
    return await render_template('about.html')

@app.route('/sign_in', methods=['GET', 'POST'])
async def sign_in():
    try:
        error = None
        app.logger.info(f"In func")
        if request.method == 'POST':
            form = await request.form
            user_mail = form['user_mail']
            password = form['password']
            if user_mail == '' or password == '':
                error = 'Заполните все поля!'
            else:
                hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
                check_user_result = await check_user_password(user_mail, hashed_password)
                if check_user_result:
                    session['user_id'] = check_user_result.id
                    return redirect(url_for('ticket_history'))
                else:
                    # TO DO
                    # Сделать страницу с информацией об отказе для пользователя.
                    # Добавить кнопку возврата на предыдущую страницу.
                    error = 'Неправильное имя пользователя или пароль!'
        return await render_template('sign_in.html', error=error)
    except Exception as e:
        app.logger.error(f"Sign in error: {str(e)}", exc_info=True)
        return await render_template('sign_in.html',
                                     error='Внутренняя ошибка сервера'), 500


@app.route('/sign_up', methods=['GET', 'POST'])
async def sign_up():
    try:
        error = None
        # app.logger.info(f"In func")
        if request.method == 'POST':
            form = await request.form
            if form['user_mail'] == '' or form['company_tin'] == ''\
                    or form['phone_number'] == '' or form['phone_number'] == ''\
                    or form['password'] == '':
                error = 'Заполните все поля!'
                return await render_template('sign_up.html', error=error)
            user_data = {
                'user_mail': form['user_mail'],
                'company_tin': form['company_tin'],
                'phone_number': form['phone_number'],
                'contract_number': form['contract_number'],
                'password': form['password']
            }
            session['user_data'] = user_data
            check_company_name_result = await check_company_name(user_data['company_tin'])
            if check_company_name_result:
                return redirect(url_for('sign_up_confirm'))
            else:
                error = 'Данные компании - не корректны!'
                return await render_template('sign_up.html', error=error)
        return await render_template('sign_up.html', error=error)
    except Exception as e:
        app.logger.error(f"Sign in error: {str(e)}", exc_info=True)
        return await render_template('sign_up.html',
                                     error='Внутренняя ошибка сервера'), 500


@app.route('/sign_up_confirm', methods=['GET', 'POST'])
async def sign_up_confirm():
    user_data = session.get('user_data')
    if not user_data:
        return "Доступ запрещён, сначала необходимо пройти регистрацию", 403
    user_email = user_data['user_mail']
    if request.method=='POST':
        form = await request.form
        app.logger.info(f"Проверка кода one-time_code: {session['one-time_code']}")
        app.logger.info(f"Проверка кода verification_code: {form['verification_code']}")
        if session['one-time_code'] == int(form['verification_code']):
            if not await checking_user_presence(user_email):
                create_user_result = await create_user(user_data)
                app.logger.info(f"Верификация прошла, создаём пользователя: {user_data}")
                session['user_id'] = create_user_result.id
                print('User:', create_user_result)
                if create_user_result:
                    return redirect(url_for('ticket_history'))
            else:
                # TO DO
                # Сделать страницу с информацией об отказе для пользователя.
                # Добавить кнопку возврата на предыдущую страницу.
                return 'Пользователь с такой почтой уже существует'

    random_code = random.randrange(100000, 999999)
    app.logger.info(f"Generated random_code: {random_code} (type: {type(random_code)})")
    session['one-time_code'] = random_code
    check_email_result = check_user_email(user_email, random_code)
    return await render_template('sign_up_confirm.html')



@app.route('/ticket_history', methods=['GET', 'POST'])
async def ticket_history():
    user_id = session.get('user_id')
    if not user_id:
        return "Доступ запрещён, сначала необходимо пройти регистрацию", 403
    user = await get_user_by_id(user_id)
    if not user:
        return "Пользователь не найден", 403
    return await render_template('ticket_history.html')


@app.errorhandler(InternalServerError)
async def handle_exception(e:InternalServerError):
    original = getattr(e, "original_exception", None)
    if original is not None:
        error_message = str(original)
    else:
        error_message = str(e)
    return f"Ошибка сервера! Детали: {error_message}", 500

@app.errorhandler(404)
async def not_found(error):
    return "Страница не найдена!", 404

if __name__ == '__main__':
    # try:
    #     asyncio.run(connect())
    #     asyncio.run(create_models())
    # except Exception as exc:
    #     raise f'Ошибка: {exc}'
    # asyncio.run(run_server())
    app.run(debug=True)