#Import do botchat
import logging
import os
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove,InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, Updater, CommandHandler, MessageHandler, Filters, CallbackContext,CallbackQueryHandler
#Final imports


# botchat
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

file = 'login.txt'

if open(file, 'r').read() != '':

    dadosLogin = open(file, 'r').read()
    dados = dadosLogin.split(',')
    token = dados[5]
else:
    print('Login não encontrado, favor criar um arquivo txt na raiz do projeto com usuário e senha separado por vírgula!')

logger = logging.getLogger(__name__)

# variaveis goblais
tipoConta = 'D'
valorEntrada = '2'
stopLossPadrao = '5'
stopWinPadrao = '5'
tipoGerenciamento = '1'
tipoDadoAlterado = ''
pararRobo = 'False'

#menu do comando iniciar
reply_keyboard = [
    ['🚀 Iniciar', '⏹  Parar', '💰 Saldo'],
    ['🛠 Configurar','🆘 Ajuda'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

""" COMANDOS """
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Eai {user.mention_markdown_v2()} o bot foi iniciado, partiu ficar rico \!',
        reply_markup=markup,
    )
    alteraValorEnviado('stopBot','False',update,context)

def parar(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text("Por enquanto é só, bot pausado 🍃")

    alteraValorEnviado('stopBot','True',update,context)

def configurar(update: Update,context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Tipo de conta Real" if tipoConta == 'r'.upper() else "Tipo de conta Demonstração", callback_data='contaPadrao')],
        [InlineKeyboardButton("Valor entrada " +  valorEntrada, callback_data='valorEntradaPadrao')],
        [InlineKeyboardButton("Stop Win " + stopWinPadrao, callback_data='stopWinPadrao')],
        [InlineKeyboardButton("Stop Loss " + stopLossPadrao, callback_data='stopLossPadrao')],
        [InlineKeyboardButton("Tipo gerenciamento " + tipoGerenciamento, callback_data='gerenciamentoPadrao')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Selecione o parâmetro que deseja alterar:', reply_markup=reply_markup)

def contapadrao(update: Update, context: CallbackContext) -> None:
    global tipoConta
    tipoConta = context.args[0]

    if tipoConta.upper() == "D":
        tipoConta = 'PRACTICE'
        update.message.reply_text(
            'tipo de conta padrão definido como ' + tipoConta)
    elif tipoConta.upper() == "R":
        tipoConta = 'REAL'
        update.message.reply_text(
            'tipo de conta padrão definido como ' + tipoConta)
    else:
        update.message.reply_text(
            'Por favor insira o tipo de operação desejada')
    configurar(update,context)

def valorpadrao(update: Update, context: CallbackContext) -> None:
    global valorEntrada
    valorEntrada = context.args[0]

    update.message.reply_text("Você definiu " + valorEntrada + " como valor padrão.")

    configurar(update,context)

def ajuda(update: Update, context: CallbackContext) -> None:
    texto = "Utilize o comando desejado seguido de seu valor por exemplo /contapadrao 33\n \n Os comandos para definir as configurações padrão são : \n \n/contapadrao  - Para definir a conta da corretora que será usada."
    update.message.reply_text(texto)

def saldo(update: Update, context: CallbackContext) -> None:
    arquivo = open('saldo.txt', 'r')
    lista = 'Seguem abaixo seus resultados!\n'
    for linha in arquivo:
        lista += '\n'  + linha  
    update.message.reply_text(lista)
    arquivo.close()
""" CASO SEJA INSERIDO UM COMANDO INVÁLIDO """
def comandoInvalido(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Comando inválido, para solicitar ajudar digite o comando /ajuda")
""" FINAL DOS COMANDOS """


""" FLAG DE DECISÃO - utilizada para identificar qual variavel sera fornecida """
def alteraValorEnviado(tipodado,valor,update:Update,context:CallbackContext):
    global valorEntrada,  tipoGerenciamento, tipoConta, stopWinPadrao, stopLossPadrao,pararRobo
    
    if tipodado == 'valorEntradaPadrao':
        valorEntrada = valor
        update.message.reply_text("Você definiu " + valor + " como valor padrão.")    
    elif tipodado == 'gerenciamentoPadrao':
        tipoGerenciamento = valor
        update.message.reply_text("Você definiu " + valor + " como analise padrão.")
    elif tipodado == 'contaPadrao':
        tipoConta = valor.upper()
        update.message.reply_text("Você definiu " + valor + " como conta padrão.")
    elif tipodado == 'stopWinPadrao':
        stopWinPadrao = valor
        update.message.reply_text("Você definiu " + valor + " como Stop Win padrão.")
    elif tipodado == 'stopLossPadrao':
        stopLossPadrao = valor
        update.message.reply_text("Você definiu " + valor + " como Stop Loss padrão.")
    elif tipodado == 'stopBot':
        pararRobo = valor


    parametros = f'{tipoConta},{valorEntrada},{stopWinPadrao},{stopLossPadrao},{tipoGerenciamento},{pararRobo}'
    atualizaArquivoParametros(parametros)

    #reinicia a flag de decisão
    global tipoDadoAlterado
    tipoDadoAlterado = ''

    configurar(update,context)
""" FINAL FLAG """

def atualizaArquivoParametros(parametros):

    arquivo = open('parametros.txt', 'w') # Abre novamente o arquivo (escrita)
    arquivo.writelines(parametros)    # escreva o conteúdo criado anteriormente nele.
    arquivo.close()

""" INFORMA O TEXTO DE ALTERAÇÃO BASEADO NA VARIAVEL QUE O USUARIO CLICOU E CONFIGURA A FLAG """
def mensagemDeAlteracaoDeDados(update: Update, _: CallbackContext):
    query = update.callback_query
    query.answer()
    global tipoDadoAlterado
    if query.data == "valorEntradaPadrao":
        tipoDadoAlterado = 'valorEntradaPadrao'
        query.edit_message_text("Escolha um valor para definir a entrada padrão")
    elif query.data == "gerenciamentoPadrao":
        tipoDadoAlterado = 'gerenciamentoPadrao'
        query.edit_message_text(f"Escolha um valor para definir o tipo de analise padrão {os.linesep}")
    elif query.data == "contaPadrao":
        tipoDadoAlterado = 'contaPadrao'
        query.edit_message_text("Digite '"'D'"' para Conta Demosntração ou '"'R'"' para Conta Real")
    elif query.data == "stopWinPadrao":
        tipoDadoAlterado = 'stopWinPadrao'
        query.edit_message_text("Escolha um valor para definir o Stop Win")
    elif query.data == "stopLossPadrao":
        tipoDadoAlterado = 'stopLossPadrao'
        query.edit_message_text("Escolha um valor para definir o Stop Loss")
    else:
        query.edit_message_text("não idenficicado")

""" RECEBE AS MENSAGENS ENVIADAS PARA O BOT """
def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    if tipoDadoAlterado == '':
        if update.message.text == "🚀 Iniciar":
            update.message.reply_text("Bot iniciado")
            alteraValorEnviado('stopBot','False',update,context)
        elif update.message.text == "⏹  Parar":
            alteraValorEnviado('stopBot','True',update,context)
            update.message.reply_text("Bot parado")
        elif update.message.text == "💰 Saldo":
            arquivo = open('saldo.txt', 'r')
            if arquivo.read != '':
                lista = 'Seguem abaixo seus resultados!\n'
                for linha in arquivo:
                    lista += '\n'  + linha  
                update.message.reply_text(lista)
            arquivo.close()
        elif update.message.text == "🛠 Configurar":
            configurar(update,context)
        elif update.message.text == "🆘 Ajuda":
            update.message.reply_text("Iniciando ajuda iniciada")
        else:
            update.message.reply_text("Desculpe não entendi o comando deseja /ajuda ?")
    else:
        alteraValorEnviado(tipoDadoAlterado,update.message.text,update,context)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # GERA OS COMANDOS
    dispatcher.add_handler(CommandHandler("iniciar", start))
    dispatcher.add_handler(CommandHandler("parar", parar))
    dispatcher.add_handler(CommandHandler("contapadrao", contapadrao))
    dispatcher.add_handler(CommandHandler("configurar", configurar))
    dispatcher.add_handler(CommandHandler("ajuda", ajuda))
    dispatcher.add_handler(CommandHandler("saldo", saldo))
    dispatcher.add_handler(CommandHandler("valorpadrao", valorpadrao))
    dispatcher.add_handler(CallbackQueryHandler(mensagemDeAlteracaoDeDados))
    dispatcher.add_handler(MessageHandler(Filters.command, comandoInvalido))
    """ dispatcher.add_handler(CommandHandler("help", help_command)) """

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()



