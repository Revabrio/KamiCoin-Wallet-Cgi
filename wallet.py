import requests
import time
import base64
import ecdsa
import json
import ast
from wallet_config import public_key, private_key
import binascii

def wallet():
    response = None
    while response not in ["1", "2", "3", "4", "5"]:
        response = input("""Выберите пункт меню:
        1. Сгенерировать новый кошелек
        2. Отправить монеты на другой кошелек
        3. Получить список блоков
        4. Просмотреть баланс кошелька
        5. Выйти\n""")
    if response == "1":
        #   Создание нового кошелька
        print("""=========================================\n
ОБЯЗАТЕЛЬНО сохраните данные кошелька у безопасном месте!!!!!\n
=========================================\n""")
        generate_ECDSA_keys()
    elif response == "2":
        type_transfer = input(
            "Пожалуйста, введите с какого кошелька вы хотите перевести монеты (1 - текущий, 2 - другой)\n")
        while (int(type_transfer) != 1 or int(type_transfer) !=2):
            type_transfer = input(
                "Пожалуйста повторите попытку или введите 0 для выхода\n")
            if int(type_transfer) == 0:
                return wallet()
        if int(type_transfer) == 1:
            addr_from = public_key
            addr_private = private_key
        else:
            addr_from = input("Введите публичный ключ (адресс отправителя):\n")
            addr_private = input("Введите приватный ключ (адресса отправителя):\n")
        addr_to = input("Адресс получателя перевода\n")
        amount = input("Сумма перевода\n")
        print("=========================================\n\n")
        print("Проверьте, правильно ли введена информация, после подтверждения отменить перевод будет не возможно?!!\n")
        print(F"От: {public_key}\nПриватный ключ: {private_key}\nК кому: {addr_to}\nСумма: {amount}\n")
        response = input("y/n\n")
        if response.lower() == "y":
            send_transaction(public_key, private_key, addr_to, amount)
        elif response.lower() == "n":
            return wallet()  #  возвращаемся в главное меню
    elif response == "3":
        print(check_transactions())
        return wallet()  #  возвращаемся в главное меню
    elif response == "4":
        type_transfer = input(
            "Пожалуйста, введите баланс какого кошелька вы хотите проверить (1 - текущего, 2 - другого)\n")
        while (int(type_transfer) != 1 or int(type_transfer) != 2):
            type_transfer = input(
                "Пожалуйста повторите попытку или введите 0 для выхода\n")
            if int(type_transfer) == 0:
                return wallet()
        if int(type_transfer) == 1:
            wallet_address = public_key
        else:
            wallet_address = input("Введите адресс кошелька, баланс которого хотите проверить:\n")
        print(get_wallet_balance(wallet_address))
        return wallet()
    else:
        quit()


def send_transaction(addr_from, private_key, addr_to, amount):
    """Функция формирования и отправления транз-акции. На вход принимает:
    
    addr_from: str - Адресс отправителя
    private_key: str - Приватный ключ отправителя
    addr_to: str - Адресс получателя
    amount: int - Сумма транз-акции
    
    Формирует подпись из адресса отправителя, получателя, суммы и времени, в которое
    была создана транз-акция. Время добавляется в функции подписи.
    Так-же, после отправления запроса функция ждет ответа от сервера, о подтверждении
    или отказе транз-акции.
    """

    if len(private_key) == 64:
        signature, message = sign_ECDSA_msg(private_key, addr_from, addr_to, amount)
        url = 'http://localhost:5000/txion'
        payload = {"from": addr_from,
                   "to": addr_to,
                   "amount": amount,
                   "signature": signature.decode(),
                   "message": message}
        headers = {"Content-Type": "application/json"}

        res = requests.post(url, json=payload, headers=headers)
        print(res.text)
    else:
        print("Что то пошло не так! Пожалуйста, перепроверьте данные и попробуйте снова!")
    wallet()


def check_transactions():
    """
    """
    try:
        res = requests.get('http://localhost:5000/blocks')
        parsed = json.loads(res.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))
    except requests.ConnectionError:
        print('Ошибка подключения к ноде. Пожалуйста проверьте ваше интернет-подключение!')
    wallet()


def get_wallet_balance(wallet_address):
    """Функция проверки баланса кошелька. На вход принимает
    адресс проверяемого кошелька:

    :param wallet_address:

    Далее функция берет все блоки из блокчейна, и пересчитывает
    все транз-акции, которые были совершены с данным адрессом.
    На выход отправляет баланс, который она посчитала.

    :return:
    """
    blockchain = json.loads(requests.get('http://localhost:5000/blocks').text)

    balance = 0

    for block in blockchain:
        data = block['data']
        transactions = ast.literal_eval(data)['transactions']
        if transactions == None:
            pass
        else:
            for transaction in transactions:
                if transaction['from'] == wallet_address:
                    balance -= int(transaction['amount'])
                if transaction['to'] == wallet_address:
                    balance += int(transaction['amount'])

    return balance


def generate_ECDSA_keys():
    """Функция генерации нового кошелька для блокчейна. С помощью функций библиотеки
    генерирует кошелек, и сохраняет его в файл, имя которому дает пользователь.
    """
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)  # this is your sign (private key)
    private_key = sk.to_string().hex()  # convert your private key to hex
    vk = sk.get_verifying_key()  # this is your verification key (public key)
    public_key = vk.to_string().hex()
    # we are going to encode the public key to make it shorter
    public_key = base64.b64encode(bytes.fromhex(public_key))

    filename = input("Пожалуйста напишите названия вашего кошелька: ") + ".txt"
    with open(filename, "w") as f:
        f.write(F"Приватный ключ: {private_key}\nАдресс кошелька / Публичный ключ: {public_key.decode()}")
    print(F"Ваш новый кошелек был создан и записан в файл {filename}")


def sign_ECDSA_msg(private_key, addr_from, addr_to, amount):
    """Функция подписи транз-акции, на вход принимает приватный ключ отправителя,
    адресс отправителя, адресс получаетеля и сумму.
    В самой функции еще добавляет время, в которое была создана транз-акция.
    На выходе выдает созданную подпись и текст сообщения, которое было подписано.
    """

    message = str(addr_from) + str(addr_to) + str(amount) + str(round(time.time()))
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature, message


if __name__ == '__main__':
    print("""       =========================================\n
        KAMICOIN v1.0.0 - BLOCKCHAIN SYSTEM\n
       =========================================\n\n
        """)
    wallet()
    input("Нажмите ENTER для выхода...")
