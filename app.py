from quart import Quart, render_template, redirect, url_for, request, session
import asyncio
import hashlib
from createdb import connect, create_models,  check_user, Tortoise
# from hypercorn.config import Config
# from hypercorn.asyncio import serve
import logging
from check_user_data import check_user_data


app = Quart(__name__)
app.secret_key = 'Just hash. All day, all night'
app.logger.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    filename="app.log",  # Имя файла для записи логов
    filemode="a",        # Режим записи ("a" - дописывать, "w" - перезаписывать)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Формат сообщения
    datefmt="%Y-%m-%d %H:%M:%S",  # Формат даты
)

@app.before_serving
async def startup():
    """Выполняется при запуске приложения"""
    try:
        app.logger.info(f"Before connect")
        await connect()
        await create_models()
        app.logger.info(f"After create_models")
    except Exception as exc:
        app.logger.error(f"DB init error: {exc}")
        raise f'Ошибка: {exc}'

@app.after_serving
async def shutdown():
    """Выполняется при завершении работы"""
    await Tortoise.close_connections()

@app.route('/')
async def main():
    return await render_template('base.html')


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
                check_user_result = await check_user(user_mail, hashed_password)
                if check_user_result:
                    print(check_user_result)
                    session['user_id'] = check_user_result.id
                    return redirect(url_for('ticket_history'))
                else:
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
        app.logger.info(f"In func")
        if request.method == 'POST':

            form = await request.form
            if form['email'] == '' or form['company_name'] == ''\
                    or form['contact_number'] == '' or form['contract_number'] == ''\
                    or form['password'] == '':
                error = 'Заполните все поля!'
                return await render_template('sign_up.html', error=error)
            user_data = {
                'user_mail': form['email'],
                'company_name': form['company_name'],
                'contact_number': form['contact_number'],
                'contract_number': form['contract_number'],
                'password': form['password']
            }
            return redirect(url_for('sign_up_confirm', user_data=user_data))
            # check_user_data = await check_user_data(user_mail, hashed_password)



            # else:

                # check_user_result = await check_user(user_mail, hashed_password)

                # hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
                # check_user_result = await check_user(user_mail, hashed_password)
                # if check_user_result:
                #     print(check_user_result)
                #     session['user_id'] = check_user_result.id
                #     return redirect(url_for('ticket_history'))
                # else:
                #     error = 'Неправильное имя пользователя или пароль!'
        return await render_template('sign_up.html', error=error)
    except Exception as e:
        app.logger.error(f"Sign in error: {str(e)}", exc_info=True)
        return await render_template('sign_up.html',
                                     error='Внутренняя ошибка сервера'), 500


@app.route('/sign_up_confirm', methods=['GET', 'POST'])
def sign_up_confirm():
    pass



@app.route('/ticket_history', methods=['GET', 'POST'])
async def ticket_history():
    return await render_template('ticket_history.html')


if __name__ == '__main__':
    # try:
    #     asyncio.run(connect())
    #     asyncio.run(create_models())
    # except Exception as exc:
    #     raise f'Ошибка: {exc}'
    # asyncio.run(run_server())
    app.run(debug=True)