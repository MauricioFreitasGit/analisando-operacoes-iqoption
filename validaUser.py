# from telethon import TelegramClient, events
from datetime import datetime
# file = 'login.txt'

# if open(file, 'r').read() != '':

#     dadosLogin = open(file, 'r').read()
#     dados = dadosLogin.split(',')
#     phone = dados[2]
#     api_id = dados[3]
#     api_hash = dados[4]

# client = TelegramClient(phone, api_id, api_hash)
# print('Conectando..')

# @client.on(events.UserUpdate)
# async def handler(event):
#     # If someone is uploading, say something
#     #print(event)
#     print(event.status)
#     # print(event.status)
#     print(event.user_id)
#     #print(event.get_user())
#     #print(event.get_input_user())

#     # print(await event.get_user())
#     if event.user_id == 5044329114 and event.status:
#         await client.send_message(event.user_id, 'Você esta online')

# client.start()
# client.run_until_disconnected()


def registrarResultado(grupo,gaule,moeda,resultado):
    arquivo = open('saldo.txt', 'a') 
    linha = "GRUPO:" + grupo + ";MOEDA:" + moeda + ";GAULE:" + gaule +  ";RESULTADO:" + resultado + ";DATA:" + datetime.today().strftime('%d-%m-%Y') + ";HORA:"+ datetime.today().strftime('%H:%M')
    arquivo.writelines(linha + "\n")    
    arquivo.close()

registrarResultado("MTM","0","EURUSD","LOSS")
registrarResultado("MTM","0","EURUSD","WIN")
registrarResultado("MTM","1","EURUSD","LOSS")
