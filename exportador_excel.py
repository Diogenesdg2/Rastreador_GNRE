import pandas as pd


def gerar_excel(dados, caminho_saida):
    """
    Gera a planilha Excel com os dados extraídos.
    """

    if not dados:
        dados = []

    df = pd.DataFrame(dados)

    colunas = [
        "tipo",
        "data_vencimento",
        "documento_origem",
        "total_recolher",
        "codigo_barras",
        "valor_pago",
        "data_pagamento",
        "hora_pagamento",
        "arquivo",
    ]

    for coluna in colunas:
        if coluna not in df.columns:
            df[coluna] = ""

    df = df[colunas]

    # Garante que documento_origem e codigo_barras sejam texto,
    # para o Excel não remover zeros à esquerda.
    df["documento_origem"] = df["documento_origem"].astype(str)
    df["codigo_barras"] = df["codigo_barras"].astype(str)

    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="GNRE")

        ws = writer.book["GNRE"]

        # Formatar como texto
        coluna_documento = colunas.index("documento_origem") + 1
        coluna_codigo = colunas.index("codigo_barras") + 1

        for row in range(2, ws.max_row + 1):
            ws.cell(row=row, column=coluna_documento).number_format = "@"
            ws.cell(row=row, column=coluna_codigo).number_format = "@"

        # Largura das colunas
        larguras = {
            "A": 24,
            "B": 18,
            "C": 22,
            "D": 18,
            "E": 60,
            "F": 18,
            "G": 18,
            "H": 18,
            "I": 80,
        }

        for coluna, largura in larguras.items():
            ws.column_dimensions[coluna].width = largura