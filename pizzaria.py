import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

with open("cardapio.json", "r", encoding="utf-8") as f:
    cardapio = json.load(f)

sessoes = {}

# ── helpers ──────────────────────────────────────────

def carregar_pedidos():
    try:
        with open("pedidos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_pedidos(pedidos):
    with open("pedidos.json", "w", encoding="utf-8") as f:
        json.dump(pedidos, f, ensure_ascii=False, indent=4)

def sessao(numero):
    if numero not in sessoes:
        sessoes[numero] = {"etapa": "menu"}
    return sessoes[numero]

# ── montagem de textos ────────────────────────────────

def texto_menu():
    return (
        "🍕 *PIZZARIA JD ARCO ÍRIS*\n\n"
        "1 - Ver cardápio\n"
        "2 - Fazer pedido\n"
        "3 - Consultar pedido\n"
        "4 - Falar com atendente"
    )

def texto_cardapio():
    linhas = ["📋 *CARDÁPIO — Escolha uma categoria:*\n"]
    for i, categoria in enumerate(cardapio.keys(), 1):
        linhas.append(f"{i} - {categoria.title()}")
    linhas.append("\n0 - Voltar ao menu")
    return "\n".join(linhas)

def texto_categorias():
    categorias = list(cardapio.keys())
    linhas = ["Escolha a categoria:\n"]
    for i, cat in enumerate(categorias, 1):
        linhas.append(f"{i} - {cat.title()}")
    return "\n".join(linhas)

def texto_itens(categoria):
    itens = list(cardapio[categoria].keys())
    linhas = [f"Itens em *{categoria.title()}*:\n"]
    for i, item in enumerate(itens, 1):
        linhas.append(f"{i} - {item.title()}")
    return "\n".join(linhas)

def texto_itens_com_preco(categoria):
    itens = cardapio[categoria]
    linhas = [f"📋 *{categoria.upper()}*\n"]
    for i, (item, preco) in enumerate(itens.items(), 1):
        if isinstance(preco, dict):
            linhas.append(
                f"{i} - {item.title()}\n"
                f"     Broto R${preco['broto']:.2f} | Grande R${preco['grande']:.2f}"
            )
        else:
            linhas.append(f"{i} - {item.title()} — R${preco:.2f}")
    linhas.append("\n0 - Voltar às categorias")
    return "\n".join(linhas)

def texto_pagamento():
    return (
        "💳 *Forma de pagamento:*\n\n"
        "1 - Dinheiro\n"
        "2 - PIX\n"
        "3 - Cartão de débito\n"
        "4 - Cartão de crédito"
    )

def confirmar_pedido(numero, s):
    pedidos = carregar_pedidos()
    numero_pedido = len(pedidos) + 1
    pedido = {
        "numero": numero_pedido,
        "cliente": s["nome"],
        "telefone": numero,
        "itens": s["itens_pedido"],
        "endereco": s["endereco"],
        "total": s["total"],
        "pagamento": s["pagamento"],
        "status": "Recebido"
    }
    pedidos.append(pedido)
    salvar_pedidos(pedidos)

    itens_fmt = "\n".join(f"- {i}" for i in s["itens_pedido"])
    troco_txt = f"💵 Troco: R$ {s['troco']:.2f}\n" if s.get("troco") else ""

    return (
        f"✅ *PEDIDO CONFIRMADO!*\n\n"
        f"📌 Pedido nº {numero_pedido}\n"
        f"Cliente: {s['nome']}\n"
        f"Endereço: {s['endereco']}\n\n"
        f"Itens:\n{itens_fmt}\n\n"
        f"💰 Total: R$ {s['total']:.2f}\n"
        f"💳 Pagamento: {s['pagamento']}\n"
        f"{troco_txt}"
        f"📦 Status: Recebido\n\n"
        f"Guarde o número *{numero_pedido}* para consultar seu pedido."
    )

# ── webhook ───────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    numero = request.form.get("From")
    mensagem = request.form.get("Body", "").strip()
    s = sessao(numero)
    resposta = processar(numero, mensagem, s)
    twiml = MessagingResponse()
    twiml.message(resposta)
    return str(twiml)

# ── máquina de estados ────────────────────────────────

def processar(numero, msg, s):
    etapa = s["etapa"]

    if etapa == "menu":
        if msg == "1":
            s["etapa"] = "cardapio_categoria"
            return texto_cardapio()
        elif msg == "2":
            s["etapa"] = "pedido_nome"
            return "Qual o seu nome?"
        elif msg == "3":
            s["etapa"] = "consultar"
            return "Qual o número do seu pedido?"
        elif msg == "4":
            s["etapa"] = "menu"
            return "☎️ Encaminhando para atendente..."
        else:
            return "Olá! Seja bem-vindo à Pizzaria JD Arco Íris! 🍕\n\n" + texto_menu()

    elif etapa == "cardapio_categoria":
        if msg == "0":
            s["etapa"] = "menu"
            return texto_menu()
        categorias = list(cardapio.keys())
        try:
            escolha = int(msg) - 1
            if 0 <= escolha < len(categorias):
                categoria = categorias[escolha]
                s["categoria_cardapio"] = categoria
                s["etapa"] = "cardapio_itens"
                return texto_itens_com_preco(categoria)
            else:
                return "❌ Número inválido.\n\n" + texto_cardapio()
        except ValueError:
            return "❌ Digite apenas números.\n\n" + texto_cardapio()

    elif etapa == "cardapio_itens":
        if msg == "0":
            s["etapa"] = "cardapio_categoria"
            return texto_cardapio()
        else:
            return texto_itens_com_preco(s["categoria_cardapio"])

    elif etapa == "pedido_nome":
        s["nome"] = msg
        s["etapa"] = "pedido_endereco"
        return "Qual o seu endereço?"

    elif etapa == "pedido_endereco":
        s["endereco"] = msg
        s["itens_pedido"] = []
        s["total"] = 0.0
        s["etapa"] = "pedido_categoria"
        return texto_categorias()

    elif etapa == "pedido_categoria":
        categorias = list(cardapio.keys())
        try:
            escolha = int(msg) - 1
            if 0 <= escolha < len(categorias):
                s["categoria_atual"] = categorias[escolha]
                s["etapa"] = "pedido_item"
                return texto_itens(s["categoria_atual"])
            else:
                return "❌ Número inválido.\n\n" + texto_categorias()
        except ValueError:
            return "❌ Digite apenas números.\n\n" + texto_categorias()

    elif etapa == "pedido_item":
        categoria = s["categoria_atual"]
        itens = list(cardapio[categoria].keys())
        try:
            escolha = int(msg) - 1
            if 0 <= escolha < len(itens):
                s["item_atual"] = itens[escolha]
                preco = cardapio[categoria][s["item_atual"]]
                if isinstance(preco, dict):
                    s["etapa"] = "pedido_tamanho"
                    return "Tamanho:\n1 - Broto\n2 - Grande"
                else:
                    s["itens_pedido"].append(s["item_atual"].title())
                    s["total"] += preco
                    s["etapa"] = "pedido_mais"
                    return (
                        f"✅ {s['item_atual'].title()} adicionado!\n\n"
                        f"Deseja mais alguma coisa?\n"
                        f"1 - Sim\n2 - Não, finalizar pedido"
                    )
            else:
                return "❌ Número inválido.\n\n" + texto_itens(categoria)
        except ValueError:
            return "❌ Digite apenas números.\n\n" + texto_itens(categoria)

    elif etapa == "pedido_tamanho":
        categoria = s["categoria_atual"]
        item = s["item_atual"]
        preco_item = cardapio[categoria][item]
        tamanhos = list(preco_item.keys())
        try:
            escolha = int(msg) - 1
            if 0 <= escolha < len(tamanhos):
                tamanho = tamanhos[escolha]
                preco_final = preco_item[tamanho]
                descricao = f"{item.title()} {tamanho.title()}"
                s["itens_pedido"].append(descricao)
                s["total"] += preco_final
                s["etapa"] = "pedido_mais"
                return (
                    f"✅ {descricao} adicionado!\n\n"
                    f"Deseja mais alguma coisa?\n"
                    f"1 - Sim\n2 - Não, finalizar pedido"
                )
            else:
                return "❌ Número inválido.\n\n1 - Broto\n2 - Grande"
        except ValueError:
            return "❌ Digite apenas números."

    elif etapa == "pedido_mais":
        if msg == "1":
            s["etapa"] = "pedido_categoria"
            return texto_categorias()
        elif msg == "2":
            s["etapa"] = "pedido_pagamento"
            return texto_pagamento()
        else:
            return "Digite 1 para adicionar mais ou 2 para finalizar."

    elif etapa == "pedido_pagamento":
        opcoes = ["Dinheiro", "PIX", "Cartão de débito", "Cartão de crédito"]
        try:
            escolha = int(msg) - 1
            if 0 <= escolha < len(opcoes):
                s["pagamento"] = opcoes[escolha]
                if s["pagamento"] == "Dinheiro":
                    s["etapa"] = "pedido_troco"
                    return f"💵 Qual o valor que vai pagar?\n(Total: R$ {s['total']:.2f})"
                else:
                    s["etapa"] = "menu"
                    sessoes[numero] = {"etapa": "menu"}
                    return confirmar_pedido(numero, s)
            else:
                return "❌ Número inválido.\n\n" + texto_pagamento()
        except ValueError:
            return "❌ Digite apenas números.\n\n" + texto_pagamento()

    elif etapa == "pedido_troco":
        try:
            valor_pago = float(msg.replace(",", "."))
            if valor_pago < s["total"]:
                return f"❌ Valor insuficiente. O total é R$ {s['total']:.2f}. Quanto vai pagar?"
            s["troco"] = valor_pago - s["total"]
            sessoes[numero] = {"etapa": "menu"}
            return confirmar_pedido(numero, s)
        except ValueError:
            return "❌ Digite apenas o valor. Exemplo: 100 ou 50.00"

    elif etapa == "consultar":
        try:
            numero_pedido = int(msg)
            pedidos = carregar_pedidos()
            for pedido in pedidos:
                if pedido["numero"] == numero_pedido:
                    itens_fmt = "\n".join(f"- {i}" for i in pedido["itens"])
                    sessoes[numero] = {"etapa": "menu"}
                    return (
                        f"📌 *Pedido nº {pedido['numero']}*\n"
                        f"Cliente: {pedido['cliente']}\n\n"
                        f"Itens:\n{itens_fmt}\n\n"
                        f"💰 Total: R$ {pedido['total']:.2f}\n"
                        f"💳 Pagamento: {pedido.get('pagamento', 'Não informado')}\n"
                        f"📦 Status: {pedido['status']}"
                    )
            sessoes[numero] = {"etapa": "menu"}
            return "❌ Pedido não encontrado.\n\n" + texto_menu()
        except ValueError:
            return "❌ Digite apenas o número do pedido."

    return texto_menu()

if __name__ == "__main__":
    app.run(debug=True)