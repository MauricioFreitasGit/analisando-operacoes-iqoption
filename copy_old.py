
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import threading
import time
from datetime import datetime
import re

api_id = '5551122'
api_hash = 'a68253ae775c80ca03bdf83b5af3f4ed'
phone = '5511950306022'
client = TelegramClient(phone, api_id, api_hash)
idGravado = [0]
idMensagemAtual = [0]


print('Conectando..')


client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Coloque o codigo recebido: '))

tempoloop = 4

def foo():
        
    def pegar_mensagens_canal(title):
        # Pegando os dados do Canal, informando apenas o nome
        channel = client.get_entity(title)
        # Aqui nós estamos pegando as ultimas 100 mensagens
        messages = client.get_messages(channel, limit=1)

        # As mensagens retornam "ao contrário", então a chave 0 é a mais recente e a chave 99 seria a "mais antiga"
        msg = []
        for i, x in enumerate(messages):
            if str(x.text).strip() != '':
                msg.append(x.text)  #o x.text é onde está a mensagem
                idMensagemAtual.clear()
                idMensagemAtual.append(x.id)
                # msg.append(" Análise Extra!:bar_chart: EURUSD - Em região de Suporte.:white_check_mark: Possível alta em uma das próximas 4 velas de M5:alarm_clock: 20:25")  # o x.text é onde está a mensagem
                # msg.append("Par - GBPCAD Ordem - CALL Horário - 14:30 Expiração M5 Se perder, fazer no máximo 1 gale. :warning:Apenas entrar se a ultima vela de m5 encerrar de Baixa.")  # o x.text é onde está a mensagem
                # msg.append("GBPJPY - CALL")  # o x.text é onde está a mensagem
                # msg.append("teste teste")  # o x.text é onde está a mensagem
                """ print(i, ' -> ', x.text) """
                """ print(len(x.text.strip())) """

        return msg
        

    # Esquema simples para exibir e poder selecionar de qual Canais(e Alguns grupos) você quer pegar as mensagens
    # Se você quer pular essa parte, basta remover a parte abaixo(do canais = [] até o input()) e substituir por canais = ['NOME DO CANAL'] e qual = 0
    canais = []
    id = 0
    for dialog in client.iter_dialogs():
        if dialog.is_channel:
            canais.append(dialog.title)
            id += 1

    contador = 0
    for item in canais:
        if canais[contador] == "SINAIS MILIONÁRIOS":
            qual = contador
        else:
            contador += 1

    # input() para saber qual canal você quer copiar os dados
    """ qual = int(input('\n Selecione o ID do Canal: ')) """
    if idGravado[0] == 0:
        print("Grupo: " + canais[qual])
    #print("Grupo: " + canais[qual])  # Só para exibir qual o nome do Canal escolhido

    # Chamei a função responsavel por pegar as mensagens do canal
    mensagens = pegar_mensagens_canal(canais[qual])

    #print('\n', 15 * '-', 'Validando',15 * '-')


    # For enviando todas as mensagens retornadas, neste caso eu travei para enviar apenas 1
    for mensagem in mensagens:
        texto_dividido = mensagem.split()
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        if len(texto_dividido)>1:
            if texto_dividido[1] == "Análise" or texto_dividido[0] == "Par" :
                
                if idMensagemAtual[0] != idGravado[0]:
                    idGravado.clear()
                    idGravado.append(idMensagemAtual[0])
                    client.send_message('Canal milionario',mensagem)
                    print('MENSAGEM ENVIADA')
                    print("Horário Mensagem", dt_string)

                else:
                    break
                
            elif texto_dividido[1] == "-" and now.hour== 11 or now.hour == 12:
                if idMensagemAtual[0] != idGravado[0]:
                    idGravado.clear()
                    idGravado.append(idMensagemAtual[0])
                    client.send_message('Canal milionario',mensagem)
                    print('MENSAGEM ENVIADA')
                    
                    print("Horário Mensagem", dt_string)
                else:
                    break

WAIT_TIME_SECONDS = tempoloop
ticker = threading.Event()

while not ticker.wait(WAIT_TIME_SECONDS):
    foo()
