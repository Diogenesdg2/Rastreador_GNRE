import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from extrator import extrair_dados_documento
from leitor_pdf import extrair_texto_pdf
from exportador_excel import gerar_excel


dados_processados = []


def selecionar_pasta_pdfs():
    pasta = filedialog.askdirectory()

    if pasta:
        entrada_pasta_pdfs.delete(0, tk.END)
        entrada_pasta_pdfs.insert(0, pasta)

        caminho_excel = os.path.join(pasta, "GNRE.xlsx")
        entrada_excel.delete(0, tk.END)
        entrada_excel.insert(0, caminho_excel)


def selecionar_arquivo_excel():
    arquivo = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Arquivo Excel", "*.xlsx")]
    )

    if arquivo:
        entrada_excel.delete(0, tk.END)
        entrada_excel.insert(0, arquivo)


def limpar_grid():
    for item in grid.get_children():
        grid.delete(item)


def carregar_grid():
    limpar_grid()

    for idx, dado in enumerate(dados_processados):
        grid.insert(
            "",
            tk.END,
            iid=str(idx),
            values=(
                os.path.basename(dado.get("arquivo", "")),
                dado.get("tipo", ""),
                dado.get("data_vencimento", ""),
                dado.get("documento_origem", ""),
                dado.get("total_recolher", ""),
                dado.get("codigo_barras", ""),
                dado.get("valor_pago", ""),
                dado.get("data_pagamento", ""),
                dado.get("hora_pagamento", ""),
            )
        )


def buscar_pdfs_na_pasta(pasta):
    arquivos_pdf = []

    for raiz, subpastas, arquivos in os.walk(pasta):
        for nome_arquivo in arquivos:
            if nome_arquivo.lower().endswith(".pdf"):
                arquivos_pdf.append(os.path.join(raiz, nome_arquivo))

    arquivos_pdf.sort()
    return arquivos_pdf


def processar_pdfs():
    global dados_processados

    pasta = entrada_pasta_pdfs.get().strip()

    if not pasta:
        messagebox.showwarning("Atenção", "Selecione a pasta onde estão os PDFs.")
        return

    if not os.path.isdir(pasta):
        messagebox.showerror("Erro", "A pasta selecionada não existe.")
        return

    dados_processados = []
    limpar_grid()

    try:
        arquivos_pdf = buscar_pdfs_na_pasta(pasta)

        if not arquivos_pdf:
            messagebox.showwarning(
                "Atenção",
                "Nenhum arquivo PDF foi encontrado na pasta selecionada."
            )
            return

        erros = []

        for caminho_pdf in arquivos_pdf:
            try:
                texto = extrair_texto_pdf(caminho_pdf)
                dados = extrair_dados_documento(texto)

                # Documento Origem vem exclusivamente do PDF,
                # extraído e tratado dentro do extrator.py.
                dados["documento_origem"] = str(
                    dados.get("documento_origem", "")
                ).strip()

                dados["arquivo"] = caminho_pdf
                dados_processados.append(dados)

            except Exception as erro_pdf:
                erros.append(f"{os.path.basename(caminho_pdf)}: {erro_pdf}")

                dados_processados.append({
                    "arquivo": caminho_pdf,
                    "tipo": "ERRO",
                    "data_vencimento": "",
                    "documento_origem": "",
                    "total_recolher": "",
                    "codigo_barras": "",
                    "valor_pago": "",
                    "data_pagamento": "",
                    "hora_pagamento": "",
                })

        carregar_grid()

        if erros:
            messagebox.showwarning(
                "Processamento concluído com avisos",
                "Alguns PDFs não foram processados corretamente:\n\n"
                + "\n".join(erros[:10])
            )

        label_status.config(
            text=f"{len(dados_processados)} PDF(s) encontrado(s) e processado(s).",
            fg="green"
        )

    except Exception as erro:
        messagebox.showerror(
            "Erro",
            f"Ocorreu um erro durante o processamento dos PDFs:\n\n{erro}"
        )

        label_status.config(
            text="Erro durante o processamento.",
            fg="red"
        )


def editar_linha():
    selecionado = grid.selection()

    if not selecionado:
        messagebox.showwarning("Atenção", "Selecione uma linha para editar.")
        return

    indice = int(selecionado[0])
    dado = dados_processados[indice]

    janela = tk.Toplevel(root)
    janela.title("Editar dados")
    janela.geometry("620x430")
    janela.resizable(False, False)

    campos = [
        ("Tipo", "tipo"),
        ("Data vencimento", "data_vencimento"),
        ("Documento origem", "documento_origem"),
        ("Total recolher", "total_recolher"),
        ("Código barras", "codigo_barras"),
        ("Valor pago", "valor_pago"),
        ("Data pagamento", "data_pagamento"),
        ("Hora pagamento", "hora_pagamento"),
        ("Arquivo", "arquivo"),
    ]

    entradas = {}

    for linha_idx, (rotulo, chave) in enumerate(campos):
        tk.Label(janela, text=rotulo).grid(
            row=linha_idx,
            column=0,
            padx=10,
            pady=5,
            sticky="w"
        )

        entrada = tk.Entry(janela, width=70)
        entrada.grid(
            row=linha_idx,
            column=1,
            padx=10,
            pady=5
        )

        entrada.insert(0, dado.get(chave, ""))

        if chave == "arquivo":
            entrada.config(state="readonly")

        entradas[chave] = entrada

    def salvar_edicao():
        for chave, entrada in entradas.items():
            if chave == "arquivo":
                continue

            dado[chave] = entrada.get().strip()

        carregar_grid()
        janela.destroy()

    tk.Button(
        janela,
        text="Salvar",
        command=salvar_edicao,
        width=20,
        bg="#2E86C1",
        fg="white"
    ).grid(row=len(campos), column=0, columnspan=2, pady=20)


def gerar_excel_final():
    caminho_excel = entrada_excel.get().strip()

    if not caminho_excel:
        messagebox.showwarning("Atenção", "Selecione onde salvar a planilha.")
        return

    if not dados_processados:
        messagebox.showwarning("Atenção", "Processe os PDFs antes.")
        return

    try:
        gerar_excel(dados_processados, caminho_excel)

        messagebox.showinfo(
            "Sucesso",
            f"Excel gerado com sucesso:\n\n{caminho_excel}"
        )

        label_status.config(text="Excel gerado com sucesso.", fg="green")

    except Exception as erro:
        messagebox.showerror(
            "Erro",
            f"Erro ao gerar Excel:\n\n{erro}"
        )

        label_status.config(text="Erro ao gerar Excel.", fg="red")


# =========================
# Interface
# =========================

root = tk.Tk()
root.title("Rastreador GNRE - Conferência")
root.geometry("1200x650")


tk.Label(root, text="Pasta dos PDFs:").pack(anchor="w", padx=10, pady=(10, 0))

frame_pasta = tk.Frame(root)
frame_pasta.pack(fill="x", padx=10)

entrada_pasta_pdfs = tk.Entry(frame_pasta)
entrada_pasta_pdfs.pack(side="left", fill="x", expand=True)

tk.Button(
    frame_pasta,
    text="Selecionar",
    command=selecionar_pasta_pdfs
).pack(side="left", padx=5)


tk.Label(root, text="Salvar planilha em:").pack(anchor="w", padx=10, pady=(10, 0))

frame_excel = tk.Frame(root)
frame_excel.pack(fill="x", padx=10)

entrada_excel = tk.Entry(frame_excel)
entrada_excel.pack(side="left", fill="x", expand=True)

tk.Button(
    frame_excel,
    text="Selecionar",
    command=selecionar_arquivo_excel
).pack(side="left", padx=5)


frame_botoes = tk.Frame(root)
frame_botoes.pack(pady=10)

tk.Button(
    frame_botoes,
    text="Processar PDFs",
    command=processar_pdfs,
    width=18,
    bg="#2E86C1",
    fg="white"
).pack(side="left", padx=5)

tk.Button(
    frame_botoes,
    text="Editar linha selecionada",
    command=editar_linha,
    width=22
).pack(side="left", padx=5)

tk.Button(
    frame_botoes,
    text="Gerar Excel",
    command=gerar_excel_final,
    width=18,
    bg="#27AE60",
    fg="white"
).pack(side="left", padx=5)


frame_grid = tk.Frame(root)
frame_grid.pack(fill="both", expand=True, padx=10, pady=10)


colunas = (
    "arquivo",
    "tipo",
    "data_vencimento",
    "documento_origem",
    "total_recolher",
    "codigo_barras",
    "valor_pago",
    "data_pagamento",
    "hora_pagamento",
)

grid = ttk.Treeview(
    frame_grid,
    columns=colunas,
    show="headings",
    height=18
)

grid.heading("arquivo", text="Arquivo")
grid.heading("tipo", text="Tipo")
grid.heading("data_vencimento", text="Vencimento")
grid.heading("documento_origem", text="Documento Origem")
grid.heading("total_recolher", text="Total")
grid.heading("codigo_barras", text="Código Barras")
grid.heading("valor_pago", text="Valor Pago")
grid.heading("data_pagamento", text="Data Pag.")
grid.heading("hora_pagamento", text="Hora Pag.")

grid.column("arquivo", width=220, anchor="w")
grid.column("tipo", width=160, anchor="center")
grid.column("data_vencimento", width=100, anchor="center")
grid.column("documento_origem", width=140, anchor="center")
grid.column("total_recolher", width=90, anchor="e")
grid.column("codigo_barras", width=300, anchor="w")
grid.column("valor_pago", width=90, anchor="e")
grid.column("data_pagamento", width=100, anchor="center")
grid.column("hora_pagamento", width=90, anchor="center")


scroll_y = ttk.Scrollbar(frame_grid, orient="vertical", command=grid.yview)
scroll_x = ttk.Scrollbar(frame_grid, orient="horizontal", command=grid.xview)

grid.configure(
    yscrollcommand=scroll_y.set,
    xscrollcommand=scroll_x.set
)

grid.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

frame_grid.grid_rowconfigure(0, weight=1)
frame_grid.grid_columnconfigure(0, weight=1)


grid.bind("<Double-1>", lambda event: editar_linha())


label_status = tk.Label(root, text="", fg="black")
label_status.pack(pady=5)


root.mainloop()