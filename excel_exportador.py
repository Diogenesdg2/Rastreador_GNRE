import pandas as pd


def gerar_excel(registros, caminho_saida):
    """
    Gera uma planilha Excel com os registros extraídos dos PDFs.
    """
    if not registros:
        print("Nenhum registro encontrado para exportar.")
        return

    df = pd.DataFrame(registros)

    df.to_excel(caminho_saida, index=False)