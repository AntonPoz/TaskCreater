# import hashlib
#
# password = 'test'
# hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
# print(hashed_password)


# import asyncio
#
# from quart import Quart
#
# app = Quart(__name__)
#
# # class UserData(Quart):
# #     email =
#
# @app.route('/',  methods=['POST'])
# async def main():
#
#     return 'Hello man'
#
# if __name__ == "__main__":
#     asyncio.run(app.run_task())

import re

reg_exp = '[А-ЯЁа-яё0-9\s\\"\«»]{2,200}'
string = 'ООО "Рога и копыта"'
print(string.upper())
print(re.match(reg_exp, string))



