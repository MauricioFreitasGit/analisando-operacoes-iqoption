from os import truncate
from telethon.client import messageparse
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import threading
from datetime import datetime
import sys
from iqoptionapi.stable_api import IQ_Option
from time import mktime, sleep
import time, pytz
from threading import Thread
from decimal import Decimal
import telegram_send
import re

file = 'login.txt'

if open(file, 'r').read() != '':

    dadosLogin = open(file, 'r').read()
    dados = dadosLogin.split(',')
    usuario = dados[0]
    senha = dados[1]
    phone = dados[2]
    api_id = dados[3]
    api_hash = dados[4]
else:
    print('Login não encontrado, favor criar um arquivo txt na raiz do projeto com usuário e senha separado por vírgula. O Bot será fechado')
    telegram_send.send(messages=['Login não encontrado, favor criar um arquivo txt na raiz do projeto com usuário e senha separado por vírgula. O Bot será fechado'])
    sys.exit()


leituraParametros = 'parametros.txt'
idGravado = [0]
idMensagemAtual = [0]
try:
    if open(leituraParametros, 'r').read() != '':
        parametros = open(leituraParametros, 'r').read()
        dados = parametros.split(',')
        conta = dados[0]

        if conta.upper() == 'D':
            tipoConta = 'PRACTICE'
        elif conta.upper() == 'R':
            tipoConta = 'REAL'

except Exception as erro:
    print('Erro inesperado ao tentar ler arquivo com parâmetro '"'tipoConta'"' no Telegram!')
    telegram_send.send(messages=['Erro inesperado ao tentar ler arquivo com parâmetro '"'tipoConta'"' no Telegram!'])

API = IQ_Option(usuario, senha)
API.connect()
API.change_balance(tipoConta) # PRACTICE / REAL

if API.check_connect():
	print(' Conectado com sucesso!')
else:
	print(' Erro ao conectar')
	input('\n\n Aperte enter para sair')
	sys.exit()


client = TelegramClient(phone, api_id, api_hash)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Coloque o codigo recebido: '))


tempoLoop = 1
timeFrame = 5
somaValorEntrada = 0.0
lucro = 0.0
stopBatido = False
valorEntradaInicial = 0.0
valorEntrada = 0.0
qtdeGaleInicial = 0
qtdeGale = 0
operacaoAbortada = False
pararRobo = False


def iniciarProcesso(valorEntradaInicial, stopWin, stopLoss, tipoGerenciamento, pararRobo):
    global operacaoAbortada, qtdeGale, valorEntrada

    def pegar_mensagens_canal(canal):
        try:
            channel = client.get_entity(canal)
            messages = client.get_messages(channel, limit=1)
            msg = []

            for i, x in enumerate(messages):
                if str(x.text).strip() != '':
                    msg.append(x.text)  
                    idMensagemAtual.clear()
                    idMensagemAtual.append(x.id)
            return msg
        except:    
            print('Erro inesperado na captura do canal do Telegram!')
            telegram_send.send(messages=['Erro inesperado na captura do canal do Telegram!'])

    def EfetuarEntradaDigitais(par, valorEntrada, direcao, timeFrame):
        try:
            return API.buy_digital_spot_v2(par, valorEntrada, direcao, timeFrame)
        except:    
            print('Erro inesperado no momento da entrada Digitais!')
            telegram_send.send(messages=['Erro inesperado no momento da entrada Digitais!'])

    def EfetuarEntradaBinarias(par, valorEntrada, direcao, timeFrame):
        try:
            return API.buy(valorEntrada, par, direcao, timeFrame)
        except:    
            print('Erro inesperado no momento da entrada Binarias!')
            telegram_send.send(messages=['Erro inesperado no momento da entrada Binarias!'])

    def GerenciamentoGale():

        global somaValorEntrada, qtdeGale, valorEntrada
        try:
            if qtdeGale > 0:
                valorEntrada = (somaValorEntrada * 2)

                if lucro > 0:
                    if valorEntrada > (lucro + stopLoss):
                        valorEntrada = stopLoss + lucro
                else:
                    if valorEntrada > (stopLoss - abs(lucro)):
                        if valorEntrada >= 2.0 and (stopLoss - abs(lucro)) >= 2.0:
                            valorEntrada = stopLoss - abs(lucro)
                        else:
                            somaValorEntrada = 0
                            valorEntrada = valorEntradaInicial
                            qtdeGale = qtdeGaleInicial
                            return False

                qtdeGale -= 1

                if qtdeGale <= 0:
                    somaValorEntrada = valorEntradaInicial 

                return True

            else:
                somaValorEntrada = 0
                valorEntrada = valorEntradaInicial
                qtdeGale = qtdeGaleInicial
            
            return False
        except:    
            print('Erro inesperado no Gerenciamento/Gale!')
            telegram_send.send(messages=['Erro inesperado no Gerenciamento/Gale!'])

    def StopGerenciamento():
        global stopBatido, lucro, valorEntrada
        try:
            if stopBatido == False:

                if lucro > 0:
                    if valorEntrada > (stopLoss + lucro):
                        valorEntrada = stopLoss + lucro
                        telegram_send.send(messages=['Valor da entrada reduzido para R$' + str(round(valorEntrada, 2)) + ' respeitando o gerenciamento!'])

                else:
                    if (abs(lucro) + 1.9) > stopLoss:
                        stopBatido = True

                    if valorEntrada > (stopLoss - abs(lucro)) and stopBatido == False:
                        if valorEntrada >= 2.0 and (stopLoss - abs(lucro)) >= 2.0:
                            valorEntrada = stopLoss - abs(lucro)
                            telegram_send.send(messages=['Valor da entrada reduzido para R$' + str(round(valorEntrada, 2)) + ' respeitando o gerenciamento!'])
                        else:
                            stopBatido = True

                if stopBatido == True:
                    telegram_send.send(messages=['Stop Loss batido no valor de R$' + str(round(lucro, 2))])

                if lucro >= float(abs(stopWin)):
                    telegram_send.send(messages=['Stop Win batido no valor de R$' + str(round(lucro, 2))])
                    stopBatido = True
        except:    
            print('Erro inesperado no Gerenciamento/Stop!')
            telegram_send.send(messages=['Erro inesperado Gerenciamento/Stop!'])

    def BuscarResultadoBinarias(id, par, direcao, timeFrame):
        global lucro, somaValorEntrada, qtdeGale, valorEntrada
        evitaDuplicidadeMensagem = 0
        try:
            valor = 0
            resultado,valor = API.check_win_v3(id)
            
            valor = valor if valor >= 0 else float('-' + str(abs(valorEntrada)))
            lucro += round(valor, 2)

            if valor > 0:
                #print('RESULTADO: WIN / LUCRO:' + str(round(valor, 2)))
                telegram_send.send(messages = ['✅Resultado da operação: WIN✅\n💰Valor: R$' + str(round(valor, 2)) + ''])

                valorEntrada = valorEntradaInicial
                qtdeGale = qtdeGaleInicial
                somaValorEntrada = 0
            else:
                if valor < 0:
                    telegram_send.send(messages = ['❌RESULTADO: LOSS❌\n💰Valor: R$-' + str(round(valorEntrada,2)) + ''])
                else:
                    telegram_send.send(messages = ['RESULTADO: EMPATE / LUCRO: 0,00'])

                somaValorEntrada += valorEntrada

                entradaMartingale = True
                entradaMartingale = GerenciamentoGale()

                if entradaMartingale == True:
                    evitaDuplicidadeMensagem = 1
                    status, id = EfetuarEntradaBinarias(par, valorEntrada, direcao, timeFrame)
                    if status == True:
                        telegram_send.send(messages=['Entrada Martingale no valor de R$'+ str(round(valorEntrada,2)) +' efetuada com sucesso!'])
                        #Thread(target=BuscarResultadoBinarias, args=(id, par, direcao, timeFrame, valorEntrada)).start()
                        BuscarResultadoBinarias(id, par, direcao, timeFrame)
                    else:
                        telegram_send.send(messages=['Falha ao efetuar entrada...Processo interno na Corretora'])
                else:
                    if qtdeGale == 0:
                        valorEntrada = valorEntradaInicial
            
            if evitaDuplicidadeMensagem == 0:
                telegram_send.send(messages = ['💸Seu saldo é de R$' + str(round(lucro, 2))])
                StopGerenciamento()


        except:    
            print('Erro inesperado Entrada/Busca resultado/Binarias!')
            telegram_send.send(messages=['Erro inesperado Entrada/Busca resultado/Binarias!'])

    def BuscarResultadoDigitais(id, par, direcao, timeFrame):
        global lucro, somaValorEntrada, qtdeGale, valorEntrada
        try:
            while True:
                valor = 0
                status,valor = API.check_win_digital_v2(id)
                
                if status:
                    valor = valor if valor > 0 else float('-' + str(abs(valorEntrada)))
                    lucro += round(valor, 2)

                    if valor > 0:
                        telegram_send.send(messages = ['✅Resultado da operação: WIN✅\n💰Valor: R$' + str(round(valor, 2)) + ''])

                        valorEntrada = valorEntradaInicial
                        qtdeGale = qtdeGaleInicial
                        somaValorEntrada = 0
                    else:
                        telegram_send.send(messages = ['❌RESULTADO: LOSS❌\n💰Valor: R$-' + str(round(valorEntrada,2)) + ''])
                        
                        somaValorEntrada += valorEntrada
                        entradaMartingale = True
                        entradaMartingale = GerenciamentoGale()

                        if entradaMartingale == True:
                            status, id = EfetuarEntradaDigitais(par, valorEntrada, direcao, timeFrame)
                            if status == True:
                                telegram_send.send(messages=['Entrada Martingale no valor de R$'+ str(round(valorEntrada,2)) +' efetuada com sucesso!'])

                                #Thread(target=BuscarResultadoDigitais, args=(id, par, direcao, timeFrame, valorEntrada)).start()
                                BuscarResultadoDigitais(id, par, direcao, timeFrame)
                            else:
                                print('Falha ao efetuar entrada...Processo interno na IQ Option') 
                        else:
                            if qtdeGale == 0:
                                valorEntrada = valorEntradaInicial
                        
                    break
                sleep(0.3)

            telegram_send.send(messages = ['💸Seu saldo é de R$' + str(round(lucro, 2))])
            StopGerenciamento()
        except:    
            print('Erro inesperado Entrada/Busca resultado/Digitais!')
            telegram_send.send(messages=['Erro inesperado Entrada/Busca resultado/Digitais!'])
        
    def BuscarHoraAtualTimestamp():
        return int(mktime(datetime.strptime(datetime.now().strftime('%Y/%m/%d') + ' ' + (datetime.now()).strftime('%H:%M:%S'), "%Y/%m/%d %H:%M:%S").timetuple()))

    def BuscarHoraEntradaTimestamp(horaEntrada):
        if len(horaEntrada) == 5:
            return int(mktime(datetime.strptime(datetime.now().strftime('%Y/%m/%d') + ' ' + horaEntrada + ':00', "%Y/%m/%d %H:%M:%S").timetuple()))
        elif len(horaEntrada) == 8:
            return int(mktime(datetime.strptime(datetime.now().strftime('%Y/%m/%d') + ' ' + horaEntrada, "%Y/%m/%d %H:%M:%S").timetuple()))

    def DefineTipoMaiorPayout(dictSinal):
        
        global API
        payoutDigitais = 0
        payoutBinarias = 0
        par = dictSinal['ativo']
        
        print(' Iniciando análise de Payout...', end='\r')

        try:
            retDigitais = API.get_all_open_time()
        except:
            print('Erro ao buscar paridades!')
            telegram_send.send(messages=['Erro ao buscar paridades!'])
        
        if retDigitais == None:
            try:
                retDigitais = API.get_all_open_time()
            except:
                print('Erro ao buscar paridades!')
                telegram_send.send(messages=['Erro ao buscar paridades!'])
                #API = con()
                if retDigitais == None:
                    print('Erro None ao buscar paridades!')
                    telegram_send.send(messages=['Erro None ao buscar paridades!'])
            

        if retDigitais != None and retDigitais != '':
            try:
                for infoPar in retDigitais['digital']:
                    if retDigitais['digital'][ infoPar ]['open']:
                        if infoPar == par:
                            payoutDigitais = round( int(API.get_digital_payout(infoPar)) / 100 , 2)
                            break
            except:
                print('Erro ao buscar payout das Digitais!')
                telegram_send.send(messages=['Erro ao buscar payout das Digitais!'])

            try:
                retBinarias = API.get_all_profit()
                for tipo in ['turbo']:
                    for infoPar in retDigitais[ tipo ]:
                        if retDigitais[ tipo ][ infoPar ]['open']:
                            if infoPar == par:
                                payoutBinarias = retBinarias[ infoPar ][ tipo ]
                                break
            except:
                print('Erro ao buscar payout das Binárias!')
                telegram_send.send(messages=['Erro ao buscar payout das Binárias!'])


            if payoutDigitais <= payoutBinarias:
                dictSinal['tipoAtivo'] = 'turbo'
                dictSinal['payout'] = payoutBinarias
            else:
                dictSinal['tipoAtivo'] = 'digital'
                dictSinal['payout'] = payoutDigitais

            print('Ativo', par, 'indicado para',dictSinal['tipoAtivo'],'em função do payout de',int(dictSinal['payout'] * 100),'%')

        return dictSinal


    def IniciarOperacao(dictSinal, horaEntrada):
        global qtdeGale, valorEntrada
        
        qtdeGale = dictSinal['gale']
        verificarVelaAnterior = False
        velaAnteriroVerificada = False
        entradaValida = False
        direcaoEntrada = 'Venda' if dictSinal['direcao'] == 'put' else 'Compra'
        contaTipo = 'Demostração' if dictSinal['tipoConta'] == 'PRACTICE' else 'Real'
        tempoEspera = 0
        StopGerenciamento()

        if dictSinal['condicao'] == 'BAIXA':
            verificarVelaAnterior = True
            print('Operação será de ',direcaoEntrada, ', se a vela anterior terminar de Baixa')
        elif dictSinal['condicao'] == 'ALTA':
            verificarVelaAnterior = True
            print('Operação será de ',direcaoEntrada, ', se a vela anterior terminar de Alta')

        telegram_send.send(messages=['A proxima entrada será de ' + direcaoEntrada + ' no ativo ' + dictSinal['ativo'] + ' em ' + dictSinal['tipoAtivo'] + ' na conta ' + contaTipo])

        def EfetuarOperacao():
            while True:
                try:
                    horaAtual = BuscarHoraAtualTimestamp()
                    if horaAtual <= horaEntrada + 2:
                        if (horaAtual + 1) >= horaEntrada:
                            if dictSinal['tipoAtivo'] == 'digital':
                                status, id = EfetuarEntradaDigitais(dictSinal['ativo'], valorEntrada, dictSinal['direcao'], dictSinal['timeframe'])
                            else:
                                status, id = EfetuarEntradaBinarias(dictSinal['ativo'], valorEntrada, dictSinal['direcao'], dictSinal['timeframe'])

                            if status == True:
                                telegram_send.send(messages=['Entrada efetuada com sucesso!'])

                                if dictSinal['tipoAtivo'] == 'digital':
                                    BuscarResultadoDigitais(id, dictSinal['ativo'], dictSinal['direcao'], dictSinal['timeframe'])
                                else:
                                    BuscarResultadoBinarias(id, dictSinal['ativo'], dictSinal['direcao'], dictSinal['timeframe'])
                                break
                            else:
                                print('Falha ao efetuar entrada...Processo interno na IQ Option')
                                telegram_send.send(messages=['Falha ao efetuar entrada...Processo interno na IQ Option'])
                                break
                    else:
                        break
                except Exception as erro:
                    print('Erro inesperado na rotina de Operação!')
                    telegram_send.send(messages=['Erro inesperado na rotina de Operação!'])


        while BuscarHoraAtualTimestamp() < horaEntrada:
            if (horaEntrada - BuscarHoraAtualTimestamp()) >= 15:
                tempoEspera = 10
            else:
                if verificarVelaAnterior == False:
                    EfetuarOperacao()
                    tempoEspera = 0
                else:
                    if velaAnteriroVerificada == False:
                        horaAtuaTimestamp = BuscarHoraAtualTimestamp()
                        if (horaEntrada - horaAtuaTimestamp) <= 2 and (horaEntrada >= horaAtuaTimestamp):
                            try:
                                velas = API.get_candles(dictSinal['ativo'], (dictSinal['timeframe'] * 60), 1, time.time())
                                AberturaVelaAnteriorEntrada = round(Decimal(velas[0]['open']),5)
                                fechamentoVelaAnteriorEntrada = round(Decimal(velas[0]['close']),5)
                                velaAnteriroVerificada = True
                                entradaValida = True

                                if dictSinal['condicao'] == 'ALTA':
                                    if AberturaVelaAnteriorEntrada >= fechamentoVelaAnteriorEntrada: #vela de Baixa ou doji
                                        entradaValida = False
                                elif dictSinal['condicao'] == 'BAIXA':
                                    if AberturaVelaAnteriorEntrada <= fechamentoVelaAnteriorEntrada: #vela de Alta ou doji
                                        entradaValida = False

                                if entradaValida == True:
                                    EfetuarOperacao()
                                    tempoEspera = 0

                            except Exception as erro:
                                print('Erro inesperado na rotina de entrada do get_candles!')
                                telegram_send.send(messages=['Erro inesperado na rotina de entrada do get_candles!'])

                sleep(tempoEspera)


    def PreencherDictSinais(texto, tipoConta):
        try:
            timeframe = re.search("(: M(\d))", str(texto))
            ativo = re.search("([A-Z]{6}-OTC|[A-Z]{6})", str(texto))
            direcao = re.search("(call|put)", str(texto))
            horario = re.search("([0-9]{2}\:[0-9]{2})", str(texto))
            gale = re.search("([a-z]e: [0-9])", str(texto))
            condicao = '' if re.search("(ALTA|BAIXA)", str(texto)) == None else re.search("(ALTA|BAIXA)", str(texto)).group()
            tipoAtivo = ''
            payout = 0
 
            if direcao != None and ativo != None and horario != None and gale != None:
                return {'timeframe': int(timeframe.group(2)), 'tipoConta': tipoConta, 'ativo': ativo.group(), 'direcao': direcao.group(), 'horario': horario.group(), 'gale': int(re.search("[0-9]",gale.group()).group()), 'condicao': condicao, 'tipoAtivo': tipoAtivo, 'payout': payout} 
            else:
                return 0
        except Exception as erro:
            print('Erro inesperado ao tentar ler mensagem Splitada!')
            telegram_send.send(messages=['Erro inesperado ao tentar ler mensagem Splitada!'])


    mensagem = ""
    canal = "Canal milionario"
    try:
        for dialog in client.iter_dialogs():
            if dialog.is_channel:
                if dialog.title == canal:
                    mensagem = pegar_mensagens_canal(canal)
                    break
    except Exception as erro:
        print('Erro inesperado ao tentar capturar mensagem do canal do Telegram!')
        telegram_send.send(messages=['Erro inesperado ao tentar capturar mensagem do canal do Telegram!'])

    if mensagem == '':
        print('Canal não encontrado!')

    try:
        if (datetime.now().strftime('%H:%M')=='23:50'):
            global lucro,stopBatido
            lucro = 0.0
            stopBatido = False
            valorEntrada = valorEntradaInicial
        if mensagem != None and mensagem != '' and stopBatido == False:
            if idMensagemAtual[0] != idGravado[0]:
                idGravado.clear()
                idGravado.append(idMensagemAtual[0])
                operacaoAbortada = False
                dictSinal = PreencherDictSinais(mensagem, tipoConta)

                if dictSinal != 0:
                    horarioAtual = BuscarHoraAtualTimestamp()
                    horaEntrada = BuscarHoraEntradaTimestamp(dictSinal['horario'])
                    if horaEntrada > horarioAtual and (horaEntrada - horarioAtual) <= 1200:
                        
                            if operacaoAbortada == False:
                                dictSinal = DefineTipoMaiorPayout(dictSinal)

                                if dictSinal['payout'] >= 0.10:
                                    operacaoAbortada = False
                                    IniciarOperacao(dictSinal, horaEntrada)
                                else:
                                    operacaoAbortada = True

                                    if dictSinal['payout'] == 0:
                                        print('Operação abortada, Ativo encontra-se fechado')
                                        telegram_send.send(messages=['Operação abortada, Ativo encontra-se fechado'])
                                    else:
                                        print('Operação abortada, payout inferior a 80%')
                                        telegram_send.send(messages=['Operação abortada, payout inferior a 80%'])
                            else:
                                operacaoAbortada = False
                    else:
                        operacaoAbortada = False
                else:
                    print('Bot não conseguiu fazer a leitura do Sinal!')
                    telegram_send.send(messages=['Bot não conseguiu fazer a leitura do Sinal!'])
    except:
        print('Erro inesperado Definição Payout/Iniciar Operação!')
        telegram_send.send(messages=['Erro inesperado Definição Payout/Iniciar Operação!'])

def AtualizaParametrosEntradaOrigemTelegram():
    global valorEntrada
    leituraParametros = 'parametros.txt'
    try:
        if open(leituraParametros, 'r').read() != '':
            parametros = open(leituraParametros, 'r').read()
            dados = parametros.split(',')
            valorEntradaInicial = round(float(dados[1]), 2)
            valorEntrada = valorEntradaInicial
            stopWin = round(float(dados[2]), 2)
            stopLoss = round(float(dados[3]), 2)
            tipoGerenciamento = dados[4]
            pararRobo = dados[5]
            return valorEntradaInicial, valorEntrada, stopWin, stopLoss, tipoGerenciamento, pararRobo
        else:
            print('Arquivo de parâmetros para configuração não encontrado! O Bot será fechado!')
            telegram_send.send(messages=['Arquivo de parâmetros para configuração não encontrado, O Bot será fechado!'])
            sys.exit()

    except Exception as erro:
        print('Erro inesperado ao tentar ler arquivo com parâmetros do Telegram!')
        telegram_send.send(messages=['Erro inesperado ao tentar ler arquivo com parâmetros do Telegram!'])


WAIT_TIME_SECONDS = tempoLoop
ticker = threading.Event()

while not ticker.wait(WAIT_TIME_SECONDS):
    parametros = AtualizaParametrosEntradaOrigemTelegram()

    iniciarProcesso(parametros[0], parametros[2], parametros[3], parametros[4],parametros[5])
