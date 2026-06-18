import json

with open("cardapio.json", "r", encoding="utf-8") as f:
    cardapio = json.load(f)

try:
    with open("pedidos.json", "r", encoding="utf-8") as f:
        pedidos = json.load(f)

except FileNotFoundError:
    pedidos = []

while True:
    print("\n=== PIZZARIA JD ARCO ÍRIS ===")
    print("1 - Ver cardápio")
    print("2 - Fazer pedido")
    print("3 - Falar com atendente")
    print("4 - Consultar pedido")
    print("5 - Sair")

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        for categoria, itens in cardapio.items():
            print(f"\n🍕 {categoria.upper()}")

            for item, preco in itens.items():
                if isinstance(preco, dict):
                    print(
                        f"  {item.title()} - "
                        f"Broto R${preco['broto']:.2f} | "
                        f"Grande R${preco['grande']:.2f}"
                    )
                else:
                    print(f"  {item.title()} - R${preco:.2f}")

    elif opcao == "2":
        nome = input("Nome: ")
        telefone = input("Telefone: ")
        endereco = input("Endereço: ")

        numero_pedido = len(pedidos) + 1

        itens_pedido = []
        total_pedido = 0

        while True:
            categorias = list(cardapio.keys())

            print("\nCategorias disponíveis:")
            for i, cat in enumerate(categorias, 1):
                print(f"{i} - {cat.title()}")

            try:
                escolha_categoria = int(
                    input("Escolha a categoria: ")
                )

                if 1 <= escolha_categoria <= len(categorias):
                    categoria = categorias[escolha_categoria - 1]
                else:
                    print("❌ Categoria inválida.")
                    continue

            except ValueError:
                print("❌ Digite apenas números.")
                continue

            itens = list(cardapio[categoria].keys())

            print(f"\nItens em {categoria.title()}:")

            for i, item in enumerate(itens, 1):
                print(f"{i} - {item.title()}")

            try:
                escolha_item = int(
                    input("Escolha o item: ")
                )

                if 1 <= escolha_item <= len(itens):
                    item = itens[escolha_item - 1]
                else:
                    print("❌ Item inválido.")
                    continue

            except ValueError:
                print("❌ Digite apenas números.")
                continue

            preco_item = cardapio[categoria][item]

            if isinstance(preco_item, dict):
                tamanhos = list(preco_item.keys())

                print("\nTamanhos disponíveis:")
                for i, tamanho in enumerate(tamanhos, 1):
                    print(f"{i} - {tamanho.title()}")

                try:
                    escolha_tamanho = int(
                        input("Escolha o tamanho: ")
                    )

                    if 1 <= escolha_tamanho <= len(tamanhos):
                        tamanho_label = tamanhos[
                            escolha_tamanho - 1
                        ]

                        preco_final = preco_item[
                            tamanho_label
                        ]

                    else:
                        print("❌ Tamanho inválido.")
                        continue

                except ValueError:
                    print("❌ Digite apenas números.")
                    continue

            else:
                tamanho_label = ""
                preco_final = preco_item

            descricao = item.title()

            if tamanho_label:
                descricao += f" {tamanho_label.title()}"

            itens_pedido.append(descricao)
            total_pedido += preco_final

            while True:
                mais = input(
                    "\nDeseja adicionar mais itens? (s/n): "
                ).lower()

                if mais in ("s", "n"):
                    break

                print("❌ Digite apenas S ou N.")

            if mais == "n":
                break

        pedido = {
            "numero": numero_pedido,
            "cliente": nome,
            "telefone": telefone,
            "itens": itens_pedido,
            "endereco": endereco,
            "total": total_pedido,
            "status": "Recebido"
        }

        pedidos.append(pedido)

        with open("pedidos.json", "w", encoding="utf-8") as f:
            json.dump(
                pedidos,
                f,
                ensure_ascii=False,
                indent=4
    )
    

        print("\n=== PEDIDO CONFIRMADO ===")
        print(f"📌 Pedido nº {numero_pedido}")
        print(f"Cliente: {nome}")
        print(f"Telefone: {telefone}")
        print(f"Endereço: {endereco}")

        print("\nItens:")
        for item in itens_pedido:
            print(f"- {item}")

        print(f"\n💰 Total: R$ {total_pedido:.2f}")
        print("📦 Status: Recebido")

    elif opcao == "3":
        print("Encaminhando para atendente...")

    elif opcao == "4":
        try:
            numero = int(
                input("Número do pedido: ")
            )

            encontrado = False

            for pedido in pedidos:
                if pedido["numero"] == numero:
                    print("\n=== STATUS DO PEDIDO ===")
                    print(
                        f"Pedido nº {pedido['numero']}"
                    )
                    print(
                        f"Cliente: {pedido['cliente']}"
                    )

                    print("\nItens:")
                    for item in pedido["itens"]:
                        print(f"- {item}")

                    print(
                        f"\n💰 Total: "
                        f"R$ {pedido['total']:.2f}"
                    )

                    print(
                        f"📦 Status: "
                        f"{pedido['status']}"
                    )

                    encontrado = True
                    break

            if not encontrado:
                print("❌ Pedido não encontrado.")

        except ValueError:
            print("❌ Digite apenas números.")

    elif opcao == "5":
        print("Obrigado pela preferência!")
        break

    else:
        print("❌ Opção inválida.")