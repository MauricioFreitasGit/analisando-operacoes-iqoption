from os import truncate
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import threading
import time
from datetime import datetime
import re
import sys
from iqoptionapi.stable_api import IQ_Option
from time import mktime, sleep
import time, pytz
from threading import Thread, get_ident, Lock
from decimal import Decimal
import telegram_send

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
    print('Login não encontrado, favor criar um arquivo txt na raiz do projeto com usuário e senha separado por vírgula!')
    sys.exit()


leituraParametros = 'parametros.txt'

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

API = IQ_Option(usuario, senha)
API.connect()
API.change_balance(tipoConta) # PRACTICE / REAL

if API.check_connect():
	print(' Conectado com sucesso!')
else:
	print(' Erro ao conectar')
	input('\n\n Aperte enter para sair')
	sys.exit()

#timeFrame = ''
timeFrame = 5
somaValorEntrada = 0
lucro = 0


client = TelegramClient(phone, api_id, api_hash)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Coloque o codigo recebido: '))


tempoLoop = 1
tipoAnalise = 0
dictAgendaEntrada = dict()
listAgendaEntrada = list()

valorEntradaInicial = 0.0
valorEntrada = 0.0
qtdeGale = 0 
qtdeGaleInicial = 0 
qtdeEntrada_12 = 0 
tipoAnalise = 0 
tipoConta = 'D' 
stopWin = 0.0
stopLoss = 0.0
pararRobo = False
distribuicaoGerenciamento = 0
verificarVelaAnteriorAlta = False
verificarVelaAnteriorBaixa = False
valorStopLossGerenciamentoAnaliseExtra = 0
valorStopLossGerenciamentoAoVivo = 0
valorStopWinGerenciamentoAnaliseExtra = 0
valorStopWinGerenciamentoAoVivo = 0
lucroOperacoesAoVivo = 0
lucroOperacoesAnaliseExtra = 0
entradaAbortada = False
tipoAnalise = 0

global stopAoVivoBatido, stopAnaliExtraBatido
stopAoVivoBatido = False
stopAnaliExtraBatido = False


def IniciarProcesso(valorEntradaInicial, valorEntrada, qtdeGaleParam, qtdeGaleInicial, qtdeEntrada_12, tipoConta, stopWinPram, stopLossParam, distribuicaoGerenciamento, verificarVelaAnteriorAlta, verificarVelaAnteriorBaixa):
    
    global stopWin, stopLoss, qtdeGale, valorStopWinGerenciamentoAnaliseExtra, valorStopWinGerenciamentoAoVivo, valorStopLossGerenciamentoAnaliseExtra
    global valorStopLossGerenciamentoAoVivo, lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra, tipoAnalise

    stopWin = stopWinPram
    stopLoss = stopLossParam
    qtdeGale = qtdeGaleParam

    baseCalculoWin = round((stopWin / 100),2)
    valorStopWinGerenciamentoAnaliseExtra = baseCalculoWin * int(distribuicaoGerenciamento[0])
    valorStopWinGerenciamentoAoVivo = baseCalculoWin * int(distribuicaoGerenciamento[2])


    baseCalculoStop = round((stopLoss / 100),2)
    valorStopLossGerenciamentoAnaliseExtra = baseCalculoStop * int(distribuicaoGerenciamento[0])
    valorStopGerenciamentoSinais_12 = baseCalculoStop * int(distribuicaoGerenciamento[1])
    valorStopLossGerenciamentoAoVivo = baseCalculoStop * int(distribuicaoGerenciamento[2])

    somaValoresDistribuidos = int(distribuicaoGerenciamento[0]) + int(distribuicaoGerenciamento[2])

    if somaValoresDistribuidos > 100:
        print('Valores informados para distribuição do gerenciamento, somados não podem passar de 100, o processo será finalizado!')
        sys.exit()

    def pegar_mensagens_canal(canal):
        # Pegando os dados do Canal, informando apenas o nome
        channel = client.get_entity(canal)
        messages = client.get_messages(channel, limit=1)
 
        # As mensagens retornam "ao contrário", então a chave 0 é a mais recente e a chave 99 seria a "mais antiga"
        msg = []
        for i, x in enumerate(messages):
            if str(x.text).strip() != '':
                msg.append(x.text)  

        return msg
    
    def EfetuarEntradaDigitais(par, valorEntrada, direcao, timeFrame):
        return API.buy_digital_spot_v2(par, valorEntrada, direcao, timeFrame)


    def EfetuarEntradaBinarias(par, valorEntrada, direcao, timeFrame):
        return API.buy(valorEntrada, par, direcao, timeFrame)


    def BuscarResultadoBinarias(id, par, direcao, timeFrame, valorEntrada, tipoAnalise):
        global lucro, lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra, somaValorEntrada, qtdeGale

        valor = 0
        resultado,valor = API.check_win_v3(id)
        
        valor = valor if valor >= 0 else float('-' + str(abs(valorEntrada)))
        lucro += round(valor, 2)

        if tipoAnalise == 1:
            lucroOperacoesAnaliseExtra += round(valor, 2)
        elif tipoAnalise == 2:
            lucroOperacoesAoVivo += round(valor, 2)

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

            if tipoAnalise != 3:
                entradaMartingale = True
                entradaMartingale, valorEntrada = GerenciamentoGale(valorEntrada, tipoAnalise)

                if entradaMartingale == True:
                    status, id = EfetuarEntradaBinarias(par, valorEntrada, direcao, timeFrame)
                    if status == True:
                        telegram_send.send(messages=['Entrada Martingale no valor de R$'+ str(round(valorEntrada,2)) +' efetuada com sucesso!'])
                        #Thread(target=BuscarResultadoBinarias, args=(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)).start()
                        BuscarResultadoBinarias(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)
                    else:
                        print('Falha ao efetuar entrada...Processo interno na IQ Option')
                else:
                    if qtdeGale == 0:
                        valorEntrada = valorEntradaInicial

        telegram_send.send(messages = ['💸Seu saldo é de R$' + str(round(lucro, 2))])
        VerificaStop(lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra, tipoAnalise, valorEntradaInicial)
        sleep(1)

    
    def BuscarResultadoDigitais(id, par, direcao, timeFrame, valorEntrada, tipoAnalise):
        global lucro, lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra, somaValorEntrada, qtdeGale
        while True:
            valor = 0
            status,valor = API.check_win_digital_v2(id)
            
            if status:
                valor = valor if valor > 0 else float('-' + str(abs(valorEntrada)))
                lucro += round(valor, 2)

                if tipoAnalise == 1:
                    lucroOperacoesAnaliseExtra += round(valor, 2)
                elif tipoAnalise == 2:
                    lucroOperacoesAoVivo += round(valor, 2)

                if valor > 0:
                    telegram_send.send(messages = ['✅Resultado da operação: WIN✅\n💰Valor: R$' + str(round(valor, 2)) + ''])

                    valorEntrada = valorEntradaInicial
                    qtdeGale = qtdeGaleInicial
                    somaValorEntrada = 0
                else:
                    telegram_send.send(messages = ['❌RESULTADO: LOSS❌\n💰Valor: R$-' + str(round(valorEntrada,2)) + ''])
                    
                    somaValorEntrada += valorEntrada

                    if tipoAnalise != 3:
                        entradaMartingale = True
                        entradaMartingale, valorEntrada = GerenciamentoGale(valorEntrada, tipoAnalise)

                        if entradaMartingale == True:
                            status, id = EfetuarEntradaDigitais(par, valorEntrada, direcao, timeFrame)
                            if status == True:
                                telegram_send.send(messages=['Entrada Martingale no valor de R$'+ str(round(valorEntrada,2)) +' efetuada com sucesso!'])

                                #Thread(target=BuscarResultadoDigitais, args=(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)).start()
                                BuscarResultadoDigitais(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)
                            else:
                                print('Falha ao efetuar entrada...Processo interno na IQ Option') 
                        else:
                            if qtdeGale == 0:
                                valorEntrada = valorEntradaInicial

                telegram_send.send(messages = ['💸Seu saldo é de R$' + str(round(lucro, 2))])
                VerificaStop(lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra, tipoAnalise, valorEntradaInicial)
                break

            sleep(1)

    def IniciarOperacao(listAgendaEntrada, horaEntradaTimestamp, valorEntrada, tipoAnalise):
        verificarVelaAnterior = False
        entradaValida = True

        if tipoAnalise == 1:
            if valorEntrada > valorStopLossGerenciamentoAnaliseExtra:
                valorEntrada = valorStopLossGerenciamentoAnaliseExtra

            print('Próxima entrada será de',listAgendaEntrada[0]['direcao'], 'efetuada as',listAgendaEntrada[0]['horarioEntrada'])

        elif tipoAnalise == 2:
            if valorEntrada > valorStopLossGerenciamentoAoVivo:
                valorEntrada = valorStopLossGerenciamentoAoVivo

            if listAgendaEntrada[0]['verificarVelaAnteriorAlta'] == False and listAgendaEntrada[0]['verificarVelaAnteriorBaixa'] == False:
                print('Próxima entrada será de',listAgendaEntrada[0]['direcao'], 'efetuada as',listAgendaEntrada[0]['horarioEntrada'])

            elif listAgendaEntrada[0]['verificarVelaAnteriorAlta'] == True:
                print('Entrada será de',listAgendaEntrada[0]['direcao'], 'efetuada as',listAgendaEntrada[0]['horarioEntrada'], 'se a vela anterior terminar de Alta')
                verificarVelaAnterior = True
                entradaValida = False
            
            elif listAgendaEntrada[0]['verificarVelaAnteriorBaixa'] == True:
                print('Entrada será de ',listAgendaEntrada[0]['direcao'], ' efetuada as ',listAgendaEntrada[0]['horarioEntrada'], ' se a vela anterior terminar de Baixa')
                verificarVelaAnterior = True
                entradaValida = False


        par = listAgendaEntrada[0]['par']
        direcao = listAgendaEntrada[0]['direcao']
        velaAnteriroVerificada = False
        tipoParidade = listAgendaEntrada[0]['tipoParidade']

        direcaoEntrada = 'Venda' if direcao == 'put' else 'Compra'
        contaTipo = 'demostração' if tipoConta == 'D' else 'Real'

        telegram_send.send(messages=['A proxima entrada será de ' + direcaoEntrada + ' no par ' + par + ' em ' + tipoParidade + ' na conta ' + contaTipo])
        while BuscarHoraAtualTimestamp() < horaEntradaTimestamp:
            if (horaEntradaTimestamp - BuscarHoraAtualTimestamp()) >= 15:
                tempoEspera = 10
            else:
                tempoEspera = 0

                if verificarVelaAnterior == True:
                    if velaAnteriroVerificada == False:
                        horaAtuaTimestamp = BuscarHoraAtualTimestamp()
                        if (horaEntradaTimestamp - horaAtuaTimestamp) > 3 and (horaEntradaTimestamp - horaAtuaTimestamp) < 6:
                            velas = API.get_candles(par, (timeFrame * 60), 1, time.time())
                            AberturaVelaAnteriorEntrada = round(Decimal(velas[0]['open']),5)
                            fechamentoVelaAnteriorEntrada = round(Decimal(velas[0]['close']),5)
                            velaAnteriroVerificada = True
                            entradaValida = True

                            if listAgendaEntrada[0]['verificarVelaAnteriorAlta'] == True:
                                if AberturaVelaAnteriorEntrada > fechamentoVelaAnteriorEntrada: #vela de Baixa
                                    entradaValida = False
                            elif listAgendaEntrada[0]['verificarVelaAnteriorBaixa'] == True:
                                if AberturaVelaAnteriorEntrada < fechamentoVelaAnteriorEntrada: #vela de Alta
                                    entradaValida = False
                
                if (BuscarHoraAtualTimestamp() + 1) >= horaEntradaTimestamp:
                    if entradaValida == True:
                        if tipoParidade == 'digital':
                            status, id = EfetuarEntradaDigitais(par, valorEntrada, direcao, timeFrame)
                        else:
                            status, id = EfetuarEntradaBinarias(par, valorEntrada, direcao, timeFrame)

                        if status == True:
                            telegram_send.send(messages=['Entrada efetuada com sucesso!'])

                            #Thread(target=BuscarResultadoDigitais, args=(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)).start()
                            #Thread(target=BuscarResultadoBinarias, args=(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)).start()
                            if tipoParidade == 'digital':
                                BuscarResultadoDigitais(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)
                            else:
                                BuscarResultadoBinarias(id, par, direcao, timeFrame, valorEntrada, tipoAnalise)
                            status = False
                            listAgendaEntrada.clear()
                        else:
                            print('Falha ao efetuar entrada...Processo interno na IQ Option')    
            sleep(tempoEspera)


    def GerenciamentoGale(valorEntrada, tipoAnalise):

        global qtdeGale, somaValorEntrada

        if qtdeGale > 0:
            valorEntrada = (somaValorEntrada * 2)

            if tipoAnalise == 1:
                if lucroOperacoesAnaliseExtra > 0:
                    if valorEntrada > (lucroOperacoesAnaliseExtra + valorStopLossGerenciamentoAnaliseExtra):
                        if valorEntrada >= 2.0 and valorStopLossGerenciamentoAnaliseExtra > lucroOperacoesAnaliseExtra and (valorStopLossGerenciamentoAnaliseExtra - lucroOperacoesAnaliseExtra) >= 2.0:
                            valorEntrada = valorStopLossGerenciamentoAnaliseExtra - lucroOperacoesAnaliseExtra
                        else:
                            somaValorEntrada = 0
                            valorEntrada = valorEntradaInicial
                            qtdeGale = qtdeGaleInicial
                            return False, valorEntrada
                else:
                    if valorEntrada > (valorStopLossGerenciamentoAnaliseExtra - abs(lucroOperacoesAnaliseExtra)):
                        if valorEntrada >= 2.0 and (valorStopLossGerenciamentoAnaliseExtra - abs(lucroOperacoesAnaliseExtra)) >= 2.0:
                            valorEntrada = valorStopLossGerenciamentoAnaliseExtra - abs(lucroOperacoesAnaliseExtra)
                        else:
                            somaValorEntrada = 0
                            valorEntrada = valorEntradaInicial
                            qtdeGale = qtdeGaleInicial
                            return False, valorEntrada

            elif tipoAnalise == 2:
                if lucroOperacoesAoVivo > 0:
                    if valorEntrada > (lucroOperacoesAoVivo + valorStopLossGerenciamentoAoVivo):
                        if valorEntrada >= 2.0 and valorStopLossGerenciamentoAoVivo > lucroOperacoesAoVivo and (valorStopLossGerenciamentoAoVivo - lucroOperacoesAoVivo) >= 2.0:
                            valorEntrada = valorStopLossGerenciamentoAoVivo - lucroOperacoesAoVivo
                        else:
                            somaValorEntrada = 0
                            valorEntrada = valorEntradaInicial
                            qtdeGale = qtdeGaleInicial
                            return False, valorEntrada
                else:
                    if valorEntrada > (valorStopLossGerenciamentoAoVivo - abs(lucroOperacoesAoVivo)):
                        if valorEntrada >= 2.0 and (valorStopLossGerenciamentoAoVivo - abs(lucroOperacoesAoVivo)) >= 2.0:
                            valorEntrada = valorStopLossGerenciamentoAoVivo - abs(lucroOperacoesAoVivo)
                        else:
                            somaValorEntrada = 0
                            valorEntrada = valorEntradaInicial
                            qtdeGale = qtdeGaleInicial
                            return False, valorEntrada

            qtdeGale -= 1

            if qtdeGale <= 0:
                somaValorEntrada = valorEntradaInicial 

            return True, valorEntrada

        else:
            somaValorEntrada = 0
            valorEntrada = valorEntradaInicial
            qtdeGale = qtdeGaleInicial
        
        return False, valorEntrada


    def RegistrarStop(valor,tipoRegistro):
        try:
            data_atual = str(datetime.now().strftime('%d/%m/%Y %H:%M'))
            arquivo = open('saldo.txt', 'r') 
            if arquivo.read != '':
                conteudo = arquivo.readlines()
                if tipoRegistro == 'loss':
                    conteudo.append('\n' + tipoRegistro + data_atual + ': R$' + str(round(valor,2)))  
                else:
                    conteudo.append('\n' + tipoRegistro + data_atual + ': R$' + str(round(valor,2)))   
                arquivo = open('saldo.txt', 'w') 
                arquivo.writelines(conteudo)    
                arquivo.close()
        except Exception as erro:
            print('Erro no método RegistrarStop')
 
    def VerificaStop(lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra, tipoAnalise, valorEntradaInicial):

        if tipoAnalise == 2:
            StopGerenciamentoAoVivo(lucroOperacoesAoVivo, valorEntrada, valorEntradaInicial)
        elif tipoAnalise == 1:
             StopGerenciamentoAnaliseExtra(lucroOperacoesAnaliseExtra, valorEntrada, valorEntradaInicial)


    def StopGerenciamentoAoVivo(lucroOperacoesAoVivo, valorEntrada, valorEntradaInicial):
        global stopAoVivoBatido

        if stopAoVivoBatido == False:

            if lucroOperacoesAoVivo > 0:
                if valorEntrada > valorStopLossGerenciamentoAoVivo or (valorStopLossGerenciamentoAoVivo - lucroOperacoesAoVivo) < 2.0:
                    stopAoVivoBatido = True
                else:
                    if valorStopLossGerenciamentoAoVivo > lucroOperacoesAoVivo and (valorStopLossGerenciamentoAoVivo - lucroOperacoesAoVivo) < valorEntradaInicial:
                        valorEntrada = valorStopLossGerenciamentoAoVivo - lucroOperacoesAoVivo
                        telegram_send.send(messages=['Valor da entrada reduzido para R$' + str(valorEntrada) + ' e respeitar o gerenciamento!'])

            else:
                if valorEntrada > (valorStopLossGerenciamentoAoVivo - abs(lucroOperacoesAoVivo)):
                    if valorEntrada >= 2.0 and (valorStopLossGerenciamentoAoVivo - abs(lucroOperacoesAoVivo)) >= 2.0:
                        valorEntrada = valorStopLossGerenciamentoAoVivo - abs(lucroOperacoesAoVivo)
                        telegram_send.send(messages=['Valor da entrada reduzido para R$' + str(valorEntrada) + ' e respeitar o gerenciamento!'])
                    else:
                        stopAoVivoBatido = True


            if stopAoVivoBatido == True:
                telegram_send.send(messages=['Stop Loss de R$' + str(lucroOperacoesAoVivo) + ' para operações ao vivo batido!'])
                RegistrarStop(lucroOperacoesAoVivo,'loss')

            if lucroOperacoesAoVivo >= float(abs(valorStopWinGerenciamentoAoVivo)):
                telegram_send.send(messages=['Stop Win no valor de R$' + str(lucroOperacoesAoVivo) + ' para operações ao vivo Batido!'])
                stopAoVivoBatido = True
                RegistrarStop(lucroOperacoesAoVivo,'win')

    
    def StopGerenciamentoAnaliseExtra(lucroOperacoesAnaliseExtra, valorEntrada, valorEntradaInicial):
        global stopAnaliExtraBatido
        
        if stopAnaliExtraBatido == False:

            if lucroOperacoesAnaliseExtra > 0:
                if valorEntrada > valorStopLossGerenciamentoAnaliseExtra or (valorStopLossGerenciamentoAnaliseExtra - lucroOperacoesAnaliseExtra) < 2.0:
                    stopAnaliExtraBatido = True
                else:
                    if valorStopLossGerenciamentoAnaliseExtra > lucroOperacoesAnaliseExtra and (valorStopLossGerenciamentoAnaliseExtra - lucroOperacoesAnaliseExtra) < valorEntradaInicial:
                        valorEntrada = valorStopLossGerenciamentoAnaliseExtra - lucroOperacoesAnaliseExtra
                        telegram_send.send(messages=['Valor da entrada reduzido para R$' + str(valorEntrada) + ' e respeitar o gerenciamento!'])

            else:
                if valorEntrada > (valorStopLossGerenciamentoAnaliseExtra - abs(lucroOperacoesAnaliseExtra)):
                    if valorEntrada >= 2.0 and (valorStopLossGerenciamentoAnaliseExtra - abs(lucroOperacoesAnaliseExtra)) >= 2.0:
                        valorEntrada = valorStopLossGerenciamentoAnaliseExtra - abs(lucroOperacoesAnaliseExtra)
                        telegram_send.send(messages=['Valor da entrada reduzido para R$' + str(valorEntrada) + ' e respeitar o gerenciamento!'])
                    else:
                        stopAnaliExtraBatido = True


            if stopAnaliExtraBatido == True:
                telegram_send.send(messages=['Stop Loss no valor de R$' + str(lucroOperacoesAnaliseExtra) + ' para a operações de Análise Extra batido!'])
                RegistrarStop(lucroOperacoesAnaliseExtra,'loss')

            if lucroOperacoesAnaliseExtra >= float(abs(valorStopWinGerenciamentoAnaliseExtra)):
                telegram_send.send(messages=['Stop Win deR$' + str(lucroOperacoesAnaliseExtra) + ' para operações de Análise Extra Batido!'])
                stopAnaliExtraBatido = True
                RegistrarStop(lucroOperacoesAnaliseExtra,'win')


    def BuscarHoraAtualTimestamp():
        return int(mktime(datetime.strptime(datetime.now().strftime('%Y/%m/%d') + ' ' + (datetime.now()).strftime('%H:%M:%S'), "%Y/%m/%d %H:%M:%S").timetuple()))

    def BuscarHoraEntradaTimestamp(horaEntrada):
        if len(horaEntrada) == 5:
            return int(mktime(datetime.strptime(datetime.now().strftime('%Y/%m/%d') + ' ' + horaEntrada + ':00', "%Y/%m/%d %H:%M:%S").timetuple()))
        elif len(horaEntrada) == 8:
            return int(mktime(datetime.strptime(datetime.now().strftime('%Y/%m/%d') + ' ' + horaEntrada, "%Y/%m/%d %H:%M:%S").timetuple()))

    def ValidarOperacao(listAgendaEntrada, valorEntrada, tipoAnalise):

        horaEntrada = listAgendaEntrada[0]['horarioEntrada']
        horaEntradaTimestamp = BuscarHoraEntradaTimestamp(horaEntrada)

        if len(listAgendaEntrada) == 1:
            if listAgendaEntrada[0]['operacaoRealizada'] == False:
                IniciarOperacao(listAgendaEntrada, horaEntradaTimestamp, valorEntrada, tipoAnalise)

    def ValidarOperacao_12(listAgendaEntrada, valorStopGerenciamentoSinais_12, tipoAnalise):
        horaEntrada = listAgendaEntrada[0]['horarioEntrada']
        horaEntradaTimestamp = BuscarHoraEntradaTimestamp(horaEntrada)
        qtdeSinais_12 = len(listAgendaEntrada)
        valorEntrada_12 = round((valorStopGerenciamentoSinais_12 / qtdeSinais_12),2)
        if valorEntrada_12 < 2:
            valorEntrada_12 = 2.0

        IniciarOperacao_12(listAgendaEntrada, horaEntradaTimestamp, valorEntrada_12, valorStopGerenciamentoSinais_12, tipoAnalise)


    def IniciarOperacao_12(listAgendaEntrada, horaEntradaTimestamp, valorEntrada_12, valorStopGerenciamentoSinais_12, tipoAnalise):
        valorGerenciamento = valorStopGerenciamentoSinais_12
        entradaEfetuada = False
        while BuscarHoraAtualTimestamp() < horaEntradaTimestamp:
            if (BuscarHoraAtualTimestamp() + 2) >= horaEntradaTimestamp and entradaEfetuada == False:
                for dadosEntrada in listAgendaEntrada:
                    par = dadosEntrada['par']
                    direcao = dadosEntrada['direcao']

                    if valorEntrada_12 > 2:

                        #status, id = EfetuarEntradaDigitais(par, valorEntrada_12, direcao, timeFrame)
                        status, id = EfetuarEntradaBinarias(par, valorEntrada_12, direcao, timeFrame)
                        entradaEfetuada = True
                        print('Entrada efetuada com sucesso!')
                    else:
                        valorGerenciamento -= 2
                        if valorGerenciamento >= 0:
                            #status, id = EfetuarEntradaDigitais(par, valorEntrada_12, direcao, timeFrame)
                            status, id = EfetuarEntradaBinarias(par, valorEntrada_12, direcao, timeFrame)
                            entradaEfetuada = True
                            print('Entrada efetuada com sucesso!')

                    if status == True:
                        #Thread(target=BuscarResultadoDigitais, args=(id, par, direcao, timeFrame, valorEntrada_12, tipoAnalise)).start()
                        Thread(target=BuscarResultadoBinarias, args=(id, par, direcao, timeFrame, valorEntrada_12, tipoAnalise)).start()
                        status == False

        listAgendaEntrada.clear()

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
        #if canais[contador] == "Canal de testes":
            cont = contador
        else:
            contador += 1

    # input() para saber qual canal você quer copiar os dados
    """ qual = int(input('\n Selecione o ID do Canal: ')) """

    #print("Grupo: " + canais[cont])  # Só para exibir qual o nome do Canal escolhido

    # Chamei a função responsavel por pegar as mensagens do canal
    mensagens = pegar_mensagens_canal(canais[cont])

    #print('\n', 15 * '-', 'Validando',15 * '-')

    # Aqui eu estou pegando as infos do user que vai receber as mensagens de acordo com o USERNAME, mas também dá para definir via access_hash
    #destino = client.get_input_entity('@PapaiN1Bot')
    # destino = client.get_input_entity('@iqteste_bot')

    def PreecherDadosEntrada(infoParidade, paridade, tipoAnalise, direcao, horario, operacaoRealizada, verificarVelaAnteriorAlta, verificarVelaAnteriorBaixa):
        
        dictAgendaEntrada['par'] = paridade
        dictAgendaEntrada['tipoParidade'] = infoParidade['tipoParidade']
        dictAgendaEntrada['payout'] = infoParidade['payout']
        dictAgendaEntrada['tipoAnalise'] = tipoAnalise
        dictAgendaEntrada['direcao'] = direcao.lower()
        dictAgendaEntrada['horarioEntrada'] = horario
        dictAgendaEntrada['operacaoRealizada'] = operacaoRealizada
        dictAgendaEntrada['verificarVelaAnteriorAlta'] = verificarVelaAnteriorAlta
        dictAgendaEntrada['verificarVelaAnteriorBaixa'] = verificarVelaAnteriorBaixa

        if len(listAgendaEntrada) > 0:
            paridadeDuplicadaLista = False

            for parLista in listAgendaEntrada:
                if parLista['par'] == paridade:
                    paridadeDuplicadaLista = True

            if paridadeDuplicadaLista == False:
                listAgendaEntrada.append(dictAgendaEntrada.copy())

        else:
            listAgendaEntrada.append(dictAgendaEntrada.copy())


    for mensagem in mensagens:

        if mensagem != None:
            texto_dividido = mensagem.split()
            sinais = mensagem.split('\n')

            horarioAtual = BuscarHoraAtualTimestamp()

            #Sinais das 12hs
            if texto_dividido[0] != 'Par' and texto_dividido[1] == "-":
                horario_12 = '12:00'
                horario_11_59 = '11:59'
                horarioEntrada = BuscarHoraEntradaTimestamp(horario_12)
                horarioIntervalo_12 = BuscarHoraEntradaTimestamp(horario_11_59)

                if horarioAtual < horarioEntrada and horarioAtual >= horarioIntervalo_12:
                    tipoAnalise = 3

                    for dados in sinais:
                        if dados != '' and qtdeEntrada_12 > 0:
                            direcao = re.search("(CALL|PUT)", dados).group()
                            paridade = re.search("([A-Z]{6})", dados).group()
                            infoParidade = DefineTipoMaiorPayout(paridade)
                            PreecherDadosEntrada(infoParidade, paridade, tipoAnalise, direcao, horario_12, False, False, False)
                            qtdeEntrada_12 -= 1

                    break

            elif texto_dividido[0] == 'Par' and texto_dividido[1] == '-' or  texto_dividido[1] == "Análise" and texto_dividido[2] == "Extra!":
                global horario 
                horario = re.search("([0-9]{2}\:[0-9]{2})", mensagem)
                if horario == None :
                    horario = re.search("([0-9]{2})", mensagem).group() + ":00"
                else:
                    horario = horario.group()
                horarioEntrada = BuscarHoraEntradaTimestamp(horario)
                if horarioEntrada > horarioAtual and (horarioEntrada - horarioAtual) <= 1200: #Agenda com no máximo 20 minutos de antecedencia 
                #if horarioEntrada > horarioAtual : #Agenda com no máximo 20 minutos de antecedencia 
                    #Analise Extra

                    if texto_dividido[1] == "Análise" and stopAnaliExtraBatido == False:
                        paridade = re.search("([A-Z]{6})", mensagem).group().upper()
                        infoParidade = DefineTipoMaiorPayout(paridade)

                        tipo = re.search("([Ss]uporte|[Rr]esist[eê]ncia)", mensagem).group()
                        print("Horario atual: " + horario)

                        if tipo == "Resistência":
                            direcao = 'put'
                        else:
                            direcao = 'call'

                        tipoAnalise = 1 
                        PreecherDadosEntrada(infoParidade, paridade, tipoAnalise, direcao, horario, False, False, False)
                        break
                        #client.send_message(destino, texto_agendamento)

                    # Sinais ao vivo
                    elif texto_dividido[0] == "Par" and texto_dividido[1] == '-' and stopAoVivoBatido == False:
                        
                        #horario = re.search("([0-9]{2}\:[0-9]{2})", mensagem).group()
                        paridade = re.search("([A-Z]{6})", mensagem).group() 
                        infoParidade = DefineTipoMaiorPayout(paridade)

                        direcao = re.search("(CALL|PUT)", mensagem).group()

                        if re.search("\\bALTA\\b", mensagem, re.IGNORECASE):
                            verificarVelaAnteriorAlta = True

                        if re.search("\\bBAIXA\\b", mensagem, re.IGNORECASE):
                            verificarVelaAnteriorBaixa = True
                        
                        print("Horario atual: " + horario)
                        tipoAnalise = 2
                        PreecherDadosEntrada(infoParidade, paridade, tipoAnalise, direcao, horario, False, verificarVelaAnteriorAlta, verificarVelaAnteriorBaixa)
                        break
                else:
                    listAgendaEntrada.clear()
    

    if len(listAgendaEntrada) > 0:
        global entradaAbortada
        if tipoAnalise == 3:
            if BuscarHoraAtualTimestamp() >= BuscarHoraEntradaTimestamp('11:59:30') and BuscarHoraAtualTimestamp() <= BuscarHoraEntradaTimestamp('11:59:55'):
                ValidarOperacao_12(listAgendaEntrada, valorStopGerenciamentoSinais_12, tipoAnalise)
                listAgendaEntrada.clear()
        else:
            if listAgendaEntrada[0]['payout'] >= 0.10:
                entradaAbortada = False
                ValidarOperacao(listAgendaEntrada, valorEntrada, tipoAnalise)

            elif entradaAbortada == False:
                telegram_send.send(messages=['Entrada abortada, payout inferior a 80%'])
                entradaAbortada = True
                
    #else:
        #print('Aguardando sinais para agendamento!')

def AtualizaParametrosEntradaOrigemTelegram():
    leituraParametros = 'parametros.txt'

    try:
        if open(leituraParametros, 'r').read() != '':
            parametros = open(leituraParametros, 'r').read()
            dados = parametros.split(',')
            tipoConta = dados[0]
            valorEntradaInicial = round(float(dados[1]), 2)
            valorEntrada = valorEntradaInicial
            qtdeGale = int(dados[2])
            qtdeGaleInicial = qtdeGale
            qtdeEntrada_12 = int(dados[3])
            tipoAnalise = int(dados[4])
            stopWin = round(float(dados[5]), 2)
            stopLoss = round(float(dados[6]), 2)
            distribuicaoGerenciamento = dados[7].split(';')
            pararRobo = dados[8]
            return valorEntradaInicial, valorEntrada, qtdeGale, qtdeGaleInicial, qtdeEntrada_12, tipoAnalise, tipoConta, stopWin, stopLoss, distribuicaoGerenciamento , pararRobo
        else:
            print('Arquivo de para atualização de parãmetros não encontrado!')
            sys.exit()

    except Exception as erro:
        print('Erro inesperado ao tentar ler arquivo com parâmetros do Telegram!')

def DefineTipoMaiorPayout(par):
    
    global API
    paresDigitais = 0
    paresBinarias = 0
    infoPayoutParidade = dict()
	
    print(' Iniciando análise de Payout...', end='\r')

    try:
        retDigitais = API.get_all_open_time()
    except:
        print('Erro ao buscar paridades!')
    
    if retDigitais == None:
        try:
            retDigitais = API.get_all_open_time()
        except:
            print('Erro ao buscar paridades!')
            #API = con()
            if retDigitais == None:
                print('Erro ao buscar paridades!')
        

    if retDigitais != None and retDigitais != '':
        try:
            for infoPar in retDigitais['digital']:
                if retDigitais['digital'][ infoPar ]['open']:
                    if infoPar == par:
                        paresDigitais = round( int(API.get_digital_payout(infoPar)) / 100 , 2)
                        break
        except:
            print('Erro ao buscar payout das Digitais!')

        retBinarias = API.get_all_profit()
        try:
            for tipo in ['turbo']:
                for infoPar in retDigitais[ tipo ]:
                    if retDigitais[ tipo ][ infoPar ]['open']:
                        if infoPar == par:
                            paresBinarias = retBinarias[ infoPar ][ tipo ]
                            break
        except:
            print('Erro ao buscar payout das Binárias!')


        if paresDigitais <= paresBinarias:
            infoPayoutParidade['par'] = par
            infoPayoutParidade['payout'] = paresBinarias
            infoPayoutParidade['tipoParidade'] = 'turbo'
        else:
            infoPayoutParidade['par'] = par
            infoPayoutParidade['payout'] = paresDigitais
            infoPayoutParidade['tipoParidade'] = 'digital'

        print('Paridade', par, 'indicado para',infoPayoutParidade['tipoParidade'],'em função do payout de',int(infoPayoutParidade['payout'] * 100),'%')

    return infoPayoutParidade

def ReconfigurarNovoCiclo():
    global stopAoVivoBatido, stopAnaliExtraBatido, lucroOperacoesAoVivo, lucroOperacoesAnaliseExtra
    stopAoVivoBatido = False
    stopAnaliExtraBatido = False
    lucroOperacoesAoVivo = 0
    lucroOperacoesAnaliseExtra = 0

WAIT_TIME_SECONDS = tempoLoop
ticker = threading.Event()

while not ticker.wait(WAIT_TIME_SECONDS):
    parametros = AtualizaParametrosEntradaOrigemTelegram()
    
    if (datetime.now()).strftime('%H:%M') >= '16:00' and (datetime.now()).strftime('%H:%M') <= '16:05':
        ReconfigurarNovoCiclo()
        sleep(300)
    if parametros[10] == 'True' :
        pass
    else:
        IniciarProcesso(parametros[0], parametros[1], parametros[2], parametros[3], parametros[4], parametros[6], parametros[7], parametros[8], parametros[9], verificarVelaAnteriorAlta, verificarVelaAnteriorBaixa)
