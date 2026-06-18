import json
from twilio.rest import Client

# ── Twilio ────────────────────────────────────────────
# Pega no dashboard do Twilio: twilio.com/console
ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AUTH_TOKEN  = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_NUM  = "whatsapp:+14155238886"  # número sandbox do Twilio

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# ── helpers ───────────────────────────────────────────

def carregar_pedidos():
    try:
        with open("pedidos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def salvar_pedidos(pedidos):
    with open("pedidos.json", "w", encoding="utf-8") as f:
        json.dump(pedidos, f, ensure_ascii=False, indent=4)

def notificar_cliente(telefone, numero_pedido, status):
    emojis = {
        "Recebido":          "📬",
        "Em preparo":        "👨‍🍳",
        "Saiu para entrega": "🛵",
        "Entregue":          "✅"
    }
    emoji = emojis.get(status, "📦")
    mensagem = (
        f"{emoji} *Atualização do seu pedido!*\n\n"
        f"📌 Pedido nº {numero_pedido}\n"
        f"📦 Status: *{status}*"
    )
    client.messages.create(
        from_=TWILIO_NUM,
        to=telefone,
        body=mensagem
    )
    print(f"✅ Cliente notificado: {status}")

# ── painel ────────────────────────────────────────────

opcoes_status = [
    "Recebido",
    "Em preparo",
    "Saiu para entrega",
    "Entregue"
]

while True:
    pedidos = carregar_pedidos()

    print("\n=== PAINEL DA PIZZARIA ===")
    print("1 - Ver pedidos")
    print("2 - Atualizar status")
    print("3 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        if not pedidos:
            print("Nenhum pedido encontrado.")
        else:
            for pedido in pedidos:
                print(f"\n📌 Pedido nº {pedido['numero']}")
                print(f"Cliente:   {pedido['cliente']}")
                print(f"Telefone:  {pedido['telefone']}")
                print(f"Endereço:  {pedido['endereco']}")
                print(f"Pagamento: {pedido.get('pagamento', 'Não informado')}")
                print("Itens:")
                for item in pedido["itens"]:
                    print(f"  - {item}")
                print(f"Total:  R$ {pedido['total']:.2f}")
                print(f"Status: {pedido['status']}")

    elif opcao == "2":
        try:
            numero = int(input("Número do pedido: "))
            encontrado = False

            for pedido in pedidos:
                if pedido["numero"] == numero:
                    encontrado = True

                    print(f"\nStatus atual: {pedido['status']}")
                    for i, s in enumerate(opcoes_status, 1):
                        print(f"{i} - {s}")

                    escolha = int(input("Novo status: "))

                    if 1 <= escolha <= len(opcoes_status):
                        novo_status = opcoes_status[escolha - 1]
                        pedido["status"] = novo_status
                        salvar_pedidos(pedidos)

                        # Notifica o cliente no WhatsApp
                        notificar_cliente(
                            pedido["telefone"],
                            pedido["numero"],
                            novo_status
                        )
                    else:
                        print("❌ Opção inválida.")
                    break

            if not encontrado:
                print("❌ Pedido não encontrado.")

        except ValueError:
            print("❌ Digite apenas números.")

    elif opcao == "3":
        print("Encerrando painel...")
        break

    else:
        print("❌ Opção inválida.")