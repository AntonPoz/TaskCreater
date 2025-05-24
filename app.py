from quart import Quart, render_template, redirect, url_for, request, session
import asyncio
import hashlib
from createdb import connect, create_models,  check_user_password, Tortoise, checking_user_presence, create_user
# from hypercorn.config import Config
# from hypercorn.asyncio import serve
from werkzeug.exceptions import InternalServerError
import logging
import random
import json
from check_user_data import check_user_data, check_user_email, check_company_name


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
    await Tortoise.close_connections()

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
            user_mail = form['email']
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
            if form['email'] == '' or form['company_tin'] == ''\
                    or form['phone_number'] == '' or form['phone_number'] == ''\
                    or form['password'] == '':
                error = 'Заполните все поля!'
                return await render_template('sign_up.html', error=error)
            user_data = {
                'user_mail': form['email'],
                'company_tin': form['company_tin'],
                'phone_number': form['phone_number'],
                'contract_number': form['contract_number'],
                'password': form['password']
            }
            session['user_data'] = user_data
            try:
                check_company_tin_result = await check_company_name(user_data['company_tin'])
                error = 'Данные компании - не корректны!'
            except Exception as exc:
                return await render_template('sign_up.html', error=error)
            print(check_company_tin_result)
            # json_response = json.load(check_company_tin_result)
            # company_tin = json_response['items'][0]['ЮЛ']["ИНН"]

            company_tin = check_company_tin_result['items'][0]['ЮЛ']["ИНН"]

            if company_tin == user_data['company_tin']:
                return redirect(url_for('sign_up_confirm'))

        return await render_template('sign_up.html', error=error)
    except Exception as e:
        app.logger.error(f"Sign in error: {str(e)}", exc_info=True)
        return await render_template('sign_up.html',
                                     error='Внутренняя ошибка сервера'), 500


@app.route('/sign_up_confirm', methods=['GET', 'POST'])
async def sign_up_confirm():
    user_data = session.get('user_data')
    user_email = user_data['user_mail']
    if request.method=='POST':
        form = await request.form
        if session['one-time_code'] == int(form['verification_code']):
            if not await checking_user_presence(user_email):
                create_user_result = await create_user(user_data)
                print('User:', create_user_result)
                if create_user_result:
                    return redirect(url_for('ticket_history'))
            else:
                # TO DO
                # Сделать страницу с информацией об отказе для пользователя.
                # Добавить кнопку возврата на предыдущую страницу.
                return 'Пользователь с такой почтой уже существует'

    random_code = random.randrange(100000, 999999)
    session['one-time_code'] = random_code
    check_email_result = check_user_email(user_email, random_code)
    return await render_template('sign_up_confirm.html')



@app.route('/ticket_history', methods=['GET', 'POST'])
async def ticket_history():
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