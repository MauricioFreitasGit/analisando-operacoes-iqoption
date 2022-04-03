from telethon import TelegramClient, events
import re

file = 'login.txt'

if open(file, 'r').read() != '':

    dadosLogin = open(file, 'r').read()
    dados = dadosLogin.split(',')
    phone = dados[2]
    api_id = dados[3]
    api_hash = dados[4]

client = TelegramClient(phone, api_id, api_hash)

print('Conectando..')


@client.on(events.NewMessage)
async def my_event_handler(event):
    chat = await event.get_chat()
    texto = event.message.message
    #print(texto)
    #print(chat)

    async def montarSinal(event, texto, canal, gale):
        condicao = re.search("(alta|ALTA|Alta|Baixa|baixa|BAIXA)", texto)
        timeframe = re.search("([Mm][0-9])", texto)

        if canal == "BINARIA_AO_VIVO":
            sentido = re.search("(COMPRA|VENDA)", texto)
            paridade = re.search("([A-Z]{6})", texto)
            horario = re.search("([0-9]{2}\:[0-9]{2})", texto)

            if sentido != None:
                if sentido.group() == "COMPRA":
                    direcao = re.search("(CALL|PUT)", "CALL")
                else:
                    direcao = re.search("(CALL|PUT)", "PUT")
        elif canal == "RATO_CEGO":
            texto_dividido = texto.split()
            sentido = re.search("(COMPRA|VENDA)", texto)
            paridade = re.search("([A-Z]{6})", texto)
            horario = re.search("([0-9]{2}\:[0-9]{2}:00)", texto)
            tempoexpiracao = "M"+texto_dividido[17]

            if sentido != None:
                if sentido.group() == "COMPRA":
                    direcao = re.search("(CALL|PUT)", "CALL")
                else:
                    direcao = re.search("(CALL|PUT)", "PUT")

        else:
            direcao = re.search("(CALL|PUT)", texto)
            paridade = re.search("([A-Z]{6}-OTC|[A-Z]{6})", texto)
            horario = re.search("([0-9]{2}\:[0-9]{2}|[0-9]{1}\:[0-9]{2})", texto)

        if horario == None and paridade != None and direcao != None:
            horario = re.search("([0-9]{2})", texto)

        if direcao != None and paridade != None and horario != None:
            if len(horario.group()) == 2:
                horario = re.search(horario.group()+ ":00", horario.group()+ ":00")
            if condicao != None:
                sinal = "🔥"+canal+"🔥" + "\n📊 Expiração: " + timeframe.group().upper() + "\n🎯 Ativo: " + paridade.group() + \
                    "\n📈 Direção: " + direcao.group().lower() + "\n⏰ Horário: " + \
                    horario.group() + "\n🐔 Gale: " + str(gale) + "\n🔀 Condição: " + condicao.group().upper()
            else:
                if timeframe != None:
                    sinal = "🔥"+canal+"🔥" + "\n📊 Expiração: " + timeframe.group().upper() + "\n🎯 Ativo: " + paridade.group() + \
                        "\n📈 Direção: " + direcao.group().lower() + "\n⏰ Horário: " + \
                        horario.group() + "\n🐔 Gale: " + str(gale) + "\n🔀 Condição: Nenhuma"
                else:
                    sinal = "🔥"+canal+"🔥\n" + "\n📊 Expiração: " + tempoexpiracao + "\n🎯 Ativo: " + paridade.group() + \
                        "\n📈 Direção: " + direcao.group().lower() + "\n⏰ Horário: " + \
                        str(horario.group()[0:5]) + "\n🐔 Gale: " + str(gale) + "\n🔀 Condição: Nenhuma"
            entity = await client.get_entity('Canal milionario')
            await client.send_message(entity, sinal)

            # await event.reply(sinal)

    async def verificarCanaisValidos(chatCompleto, event, texto):
        #valida se a mensagem não é do nosso bot
        if chatCompleto.id != 1797139273:
            chat = chatCompleto.title
            if chat == "Canal de testes":
                await montarSinal(event, texto, "CANAL_DE_TESTE", 1)
            elif chat == "Canal milionario":
                await montarSinal(event, texto, "CANAL_MILIONARIO", 1)
            elif chat == "Bot Sinais":
                await montarSinal(event, texto, "BOT_SINAL", 1)
            elif chat == "GRUPO VIP MILIONÁRIO":
                await montarSinal(event, texto, "MTM", 1)
            elif chat == "100K Club Sinais Grátis OB @Peres.nt":
                await montarSinal(event, texto, "PERES_TRADERS", 1)
            elif chat == "BINARIA AO VIVO FREE":
                await montarSinal(event, texto, "BINARIA_AO_VIVO", 1)
            elif chat == "MÉTODO RATO CEGO - SEM MARTINGALE":
                await montarSinal(event, texto, "RATO_CEGO", 0)
            elif chat == "Método Trader Milionário💎":
                await montarSinal(event, texto, "Método_Trader_Milionário_free", 1)
            else:
                print("fora")

    await verificarCanaisValidos(chat, event, texto)


client.start()
client.run_until_disconnected()
