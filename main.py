import os
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from decimal import Decimal, InvalidOperation

from extrator import extrair_dados_documento, numero_valido_documento_origem, tratar_documento_origem
from leitor_pdf import extrair_texto_pdf, extrair_documento_origem_por_posicao
from exportador_excel import exportar_excel


class RastreadorGNRE:
    def __init__(self, root):
        self.root = root
        self.root.title("Rastreador GNRE - Conferência")
        self.root.geometry("1500x800")

        self.dados = []
        self.dados_filtrados = []

        self.pasta_pdfs_var = tk.StringVar()
        self.caminho_excel_var = tk.StringVar()
        self.filtro_data_pagamento_var = tk.StringVar(value="Todas")

        self.label_total_recolher = None
        self.label_total_pago = None
        self.label_quantidade = None
        self.combo_data_pagamento = None

        self.criar_interface()

    def criar_interface(self):
        frame_topo = tk.Frame(self.root)
        frame_topo.pack(fill="x", padx=5, pady=5)

        tk.Label(frame_topo, text="Pasta dos PDFs:", anchor="w").grid(row=0, column=0, sticky="w")
        entrada_pasta = tk.Entry(frame_topo, textvariable=self.pasta_pdfs_var)
        entrada_pasta.grid(row=1, column=0, sticky="ew", padx=(0, 5))
        tk.Button(frame_topo, text="Selecionar", command=self.selecionar_pasta).grid(row=1, column=1)

        tk.Label(frame_topo, text="Salvar planilha em:", anchor="w").grid(row=2, column=0, sticky="w", pady=(8, 0))
        entrada_excel = tk.Entry(frame_topo, textvariable=self.caminho_excel_var)
        entrada_excel.grid(row=3, column=0, sticky="ew", padx=(0, 5))
        tk.Button(frame_topo, text="Selecionar", command=self.selecionar_excel).grid(row=3, column=1)

        frame_topo.columnconfigure(0, weight=1)

        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(fill="x", padx=5, pady=5)

        tk.Button(
            frame_botoes,
            text="Processar PDFs",
            command=self.processar_pdfs,
            bg="#1f77b4",
            fg="white",
            width=18
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            frame_botoes,
            text="Editar linha selecionada",
            command=self.editar_linha_selecionada,
            width=22
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            frame_botoes,
            text="Remover item",
            command=self.remover_item_selecionado,
            bg="#d62728",
            fg="white",
            width=16
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            frame_botoes,
            text="Remover zeros à esquerda",
            command=self.remover_zeros_documento_origem,
            width=24
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            frame_botoes,
            text="Gerar Excel",
            command=self.gerar_excel,
            bg="#2ca02c",
            fg="white",
            width=18
        ).pack(side="left")

        frame_filtros = tk.Frame(self.root)
        frame_filtros.pack(fill="x", padx=5, pady=(5, 0))

        tk.Label(
            frame_filtros,
            text="Filtrar por Data Pag.:"
        ).pack(side="left", padx=(0, 5))

        self.combo_data_pagamento = ttk.Combobox(
            frame_filtros,
            textvariable=self.filtro_data_pagamento_var,
            state="readonly",
            width=16,
            values=["Todas"]
        )
        self.combo_data_pagamento.pack(side="left", padx=(0, 20))
        self.combo_data_pagamento.bind("<<ComboboxSelected>>", self.aplicar_filtro_data_pagamento)

        self.label_quantidade = tk.Label(
            frame_filtros,
            text="Registros: 0",
            font=("Arial", 10, "bold")
        )
        self.label_quantidade.pack(side="left", padx=(0, 25))

        self.label_total_recolher = tk.Label(
            frame_filtros,
            text="Total: R$ 0,00",
            font=("Arial", 10, "bold"),
            fg="#1f77b4"
        )
        self.label_total_recolher.pack(side="left", padx=(0, 25))

        self.label_total_pago = tk.Label(
            frame_filtros,
            text="Valor Pago: R$ 0,00",
            font=("Arial", 10, "bold"),
            fg="#2ca02c"
        )
        self.label_total_pago.pack(side="left", padx=(0, 25))

        tk.Button(
            frame_filtros,
            text="Limpar filtro",
            command=self.limpar_filtro,
            width=14
        ).pack(side="left")

        frame_tabela = tk.Frame(self.root)
        frame_tabela.pack(fill="both", expand=True, padx=5, pady=5)

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

        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

        self.tabela.heading("arquivo", text="Arquivo")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("data_vencimento", text="Vencimento")
        self.tabela.heading("documento_origem", text="Documento Origem")
        self.tabela.heading("total_recolher", text="Total")
        self.tabela.heading("codigo_barras", text="Código Barras")
        self.tabela.heading("valor_pago", text="Valor Pago")
        self.tabela.heading("data_pagamento", text="Data Pag.")
        self.tabela.heading("hora_pagamento", text="Hora Pag.")

        self.tabela.column("arquivo", width=280, anchor="w")
        self.tabela.column("tipo", width=170, anchor="center")
        self.tabela.column("data_vencimento", width=110, anchor="center")
        self.tabela.column("documento_origem", width=150, anchor="center")
        self.tabela.column("total_recolher", width=100, anchor="center")
        self.tabela.column("codigo_barras", width=360, anchor="center")
        self.tabela.column("valor_pago", width=110, anchor="center")
        self.tabela.column("data_pagamento", width=110, anchor="center")
        self.tabela.column("hora_pagamento", width=110, anchor="center")

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta dos PDFs")

        if pasta:
            self.pasta_pdfs_var.set(pasta)

            if not self.caminho_excel_var.get():
                self.caminho_excel_var.set(os.path.join(pasta, "GNRE.xlsx"))

    def selecionar_excel(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar planilha em",
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")]
        )

        if caminho:
            self.caminho_excel_var.set(caminho)

    def listar_pdfs_recursivo(self, pasta):
        arquivos_pdf = []

        for raiz, _, arquivos in os.walk(pasta):
            for nome in arquivos:
                if nome.lower().endswith(".pdf"):
                    arquivos_pdf.append(os.path.join(raiz, nome))

        return sorted(arquivos_pdf)

    def converter_valor_para_decimal(self, valor):
        try:
            if valor is None:
                return Decimal("0")

            valor = str(valor).strip()

            if not valor:
                return Decimal("0")

            valor = valor.replace("R$", "").strip()
            valor = valor.replace(" ", "")

            if "," in valor:
                valor = valor.replace(".", "").replace(",", ".")

            return Decimal(valor)

        except (InvalidOperation, ValueError):
            return Decimal("0")

    def formatar_moeda(self, valor):
        valor = Decimal(valor).quantize(Decimal("0.01"))
        texto = f"{valor:,.2f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return texto

    def remover_zeros_documento_origem(self):
        if not self.dados:
            messagebox.showwarning("Atenção", "Nenhum dado processado para ajustar.")
            return

        resposta = messagebox.askyesno(
            "Confirmar",
            "Deseja remover os zeros à esquerda da coluna Documento Origem?\n\n"
            "Exemplo:\n"
            "000021691 → 21691\n\n"
            "Essa alteração será aplicada nos dados da tela e também no Excel gerado."
        )

        if not resposta:
            return

        alterados = 0

        for item in self.dados:
            documento = str(item.get("documento_origem", "")).strip()

            if documento and documento.isdigit():
                novo_documento = documento.lstrip("0")

                if novo_documento == "":
                    novo_documento = "0"

                if novo_documento != documento:
                    item["documento_origem"] = novo_documento
                    alterados += 1

        self.atualizar_combo_datas_pagamento()
        self.aplicar_filtro_data_pagamento()

        messagebox.showinfo(
            "Concluído",
            f"Zeros à esquerda removidos.\n\nRegistros alterados: {alterados}"
        )

    def remover_item_selecionado(self):
        item_selecionado = self.tabela.selection()

        if not item_selecionado:
            messagebox.showwarning("Atenção", "Selecione uma linha para remover.")
            return

        item_id = item_selecionado[0]
        dados_linha = self.localizar_dado_por_item_tabela(item_id)

        if dados_linha is None:
            messagebox.showerror("Erro", "Não foi possível localizar a linha selecionada.")
            return

        arquivo = dados_linha.get("arquivo", "")

        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja realmente remover este item da lista?\n\n{arquivo}"
        )

        if not confirmar:
            return

        self.dados = [
            item for item in self.dados
            if item.get("_id_tabela") != item_id
        ]

        self.dados_filtrados = [
            item for item in self.dados_filtrados
            if item.get("_id_tabela") != item_id
        ]

        self.atualizar_combo_datas_pagamento()
        self.aplicar_filtro_data_pagamento()

        messagebox.showinfo(
            "Item removido",
            "O item selecionado foi removido com sucesso."
        )

    def calcular_totais(self, dados):
        total_recolher = Decimal("0")
        total_pago = Decimal("0")

        for item in dados:
            total_recolher += self.converter_valor_para_decimal(item.get("total_recolher", "0"))
            total_pago += self.converter_valor_para_decimal(item.get("valor_pago", "0"))

        return total_recolher, total_pago

    def atualizar_totalizadores(self):
        total_recolher, total_pago = self.calcular_totais(self.dados_filtrados)

        self.label_quantidade.config(
            text=f"Registros: {len(self.dados_filtrados)}"
        )

        self.label_total_recolher.config(
            text=f"Total: R$ {self.formatar_moeda(total_recolher)}"
        )

        self.label_total_pago.config(
            text=f"Valor Pago: R$ {self.formatar_moeda(total_pago)}"
        )

    def limpar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

    def inserir_linha_tabela(self, dados):
        self.tabela.insert(
            "",
            "end",
            iid=dados.get("_id_tabela"),
            values=(
                dados.get("arquivo", ""),
                dados.get("tipo", ""),
                dados.get("data_vencimento", ""),
                dados.get("documento_origem", ""),
                dados.get("total_recolher", ""),
                dados.get("codigo_barras", ""),
                dados.get("valor_pago", ""),
                dados.get("data_pagamento", ""),
                dados.get("hora_pagamento", ""),
            )
        )

    def atualizar_tabela(self):
        self.limpar_tabela()

        for dados in self.dados_filtrados:
            self.inserir_linha_tabela(dados)

        self.atualizar_totalizadores()

    def atualizar_combo_datas_pagamento(self):
        datas = sorted({
            str(item.get("data_pagamento", "")).strip()
            for item in self.dados
            if str(item.get("data_pagamento", "")).strip()
        })

        valores = ["Todas"] + datas

        self.combo_data_pagamento["values"] = valores

        if self.filtro_data_pagamento_var.get() not in valores:
            self.filtro_data_pagamento_var.set("Todas")

    def aplicar_filtro_data_pagamento(self, event=None):
        data_selecionada = self.filtro_data_pagamento_var.get().strip()

        if not data_selecionada or data_selecionada == "Todas":
            self.dados_filtrados = list(self.dados)
        else:
            self.dados_filtrados = [
                item for item in self.dados
                if str(item.get("data_pagamento", "")).strip() == data_selecionada
            ]

        self.atualizar_tabela()

    def limpar_filtro(self):
        self.filtro_data_pagamento_var.set("Todas")
        self.aplicar_filtro_data_pagamento()

    def caminho_debug(self, pasta_pdfs):
        return os.path.join(pasta_pdfs, "debug_documento_origem.txt")

    def limpar_debug(self, pasta_pdfs):
        caminho = self.caminho_debug(pasta_pdfs)

        try:
            if os.path.exists(caminho):
                os.remove(caminho)
        except Exception:
            pass

    def gravar_debug_documento_origem(self, pasta_pdfs, caminho_pdf, texto, dados, documento_posicao):
        caminho_debug = self.caminho_debug(pasta_pdfs)

        try:
            linhas = texto.splitlines() if texto else []

            linhas_com_numeros = []
            for linha in linhas:
                if any(char.isdigit() for char in linha):
                    linhas_com_numeros.append(linha)

            with open(caminho_debug, "a", encoding="utf-8") as debug:
                debug.write("\n\n============================================================\n")
                debug.write(f"ARQUIVO: {caminho_pdf}\n")
                debug.write("============================================================\n")
                debug.write(f"TIPO: {dados.get('tipo', '')}\n")
                debug.write(f"VENCIMENTO: {dados.get('data_vencimento', '')}\n")
                debug.write(f"TOTAL: {dados.get('total_recolher', '')}\n")
                debug.write(f"VALOR PAGO: {dados.get('valor_pago', '')}\n")
                debug.write(f"CODIGO BARRAS: {dados.get('codigo_barras', '')}\n")
                debug.write(f"DOCUMENTO POSICAO: {documento_posicao}\n")

                debug.write("\n---------------- LINHAS COM NUMEROS ----------------\n")
                for linha in linhas_com_numeros[:300]:
                    debug.write(linha + "\n")

                debug.write("\n---------------- TEXTO COMPLETO EXTRAIDO ----------------\n")
                debug.write((texto or "")[:15000])
                debug.write("\n")

        except Exception as erro:
            try:
                with open(caminho_debug, "a", encoding="utf-8") as debug:
                    debug.write("\n\nERRO AO GRAVAR DEBUG\n")
                    debug.write(f"ARQUIVO: {caminho_pdf}\n")
                    debug.write(str(erro))
                    debug.write("\n")
            except Exception:
                pass

    def gravar_debug_erro(self, pasta_pdfs, caminho_pdf, erro):
        caminho_debug = self.caminho_debug(pasta_pdfs)

        try:
            with open(caminho_debug, "a", encoding="utf-8") as debug:
                debug.write("\n\n============================================================\n")
                debug.write(f"ERRO AO PROCESSAR: {caminho_pdf}\n")
                debug.write("============================================================\n")
                debug.write(str(erro))
                debug.write("\n")
                debug.write(traceback.format_exc())
                debug.write("\n")
        except Exception:
            pass

    def validar_documento_extraido(self, documento):
        documento = str(documento or "").strip()

        if not documento:
            return ""

        documento_tratado = tratar_documento_origem(documento)

        if numero_valido_documento_origem(documento_tratado):
            return documento_tratado

        return ""

    def processar_pdfs(self):
        pasta_pdfs = self.pasta_pdfs_var.get().strip()

        if not pasta_pdfs:
            messagebox.showwarning("Atenção", "Selecione a pasta dos PDFs.")
            return

        if not os.path.isdir(pasta_pdfs):
            messagebox.showerror("Erro", "A pasta dos PDFs não existe.")
            return

        arquivos_pdf = self.listar_pdfs_recursivo(pasta_pdfs)

        if not arquivos_pdf:
            messagebox.showwarning(
                "Atenção",
                "Nenhum PDF encontrado na pasta selecionada ou nas subpastas."
            )
            return

        self.dados = []
        self.dados_filtrados = []
        self.filtro_data_pagamento_var.set("Todas")
        self.limpar_tabela()
        self.atualizar_totalizadores()
        self.limpar_debug(pasta_pdfs)

        total_arquivos = len(arquivos_pdf)
        sem_documento_origem = 0
        erros = 0

        for indice, caminho_pdf in enumerate(arquivos_pdf, start=1):
            self.root.title(f"Rastreador GNRE - Processando {indice}/{total_arquivos}")
            self.root.update_idletasks()

            try:
                texto = extrair_texto_pdf(caminho_pdf)
                dados = extrair_dados_documento(texto)

                documento_posicao = ""

                dados["documento_origem"] = self.validar_documento_extraido(
                    dados.get("documento_origem", "")
                )

                if not dados.get("documento_origem"):
                    documento_posicao = extrair_documento_origem_por_posicao(caminho_pdf)
                    documento_posicao_validado = self.validar_documento_extraido(documento_posicao)

                    if documento_posicao_validado:
                        dados["documento_origem"] = documento_posicao_validado
                    else:
                        documento_posicao = ""

                nome_relativo = os.path.relpath(caminho_pdf, pasta_pdfs)

                dados["arquivo"] = nome_relativo
                dados["caminho_pdf"] = caminho_pdf
                dados["_id_tabela"] = f"item_{len(self.dados)}"

                if not dados.get("documento_origem"):
                    sem_documento_origem += 1
                    self.gravar_debug_documento_origem(
                        pasta_pdfs=pasta_pdfs,
                        caminho_pdf=caminho_pdf,
                        texto=texto,
                        dados=dados,
                        documento_posicao=documento_posicao
                    )

                self.dados.append(dados)

            except Exception as erro:
                erros += 1
                self.gravar_debug_erro(pasta_pdfs, caminho_pdf, erro)

                dados_erro = {
                    "arquivo": os.path.relpath(caminho_pdf, pasta_pdfs),
                    "caminho_pdf": caminho_pdf,
                    "_id_tabela": f"item_{len(self.dados)}",
                    "tipo": "ERRO",
                    "data_vencimento": "",
                    "documento_origem": "",
                    "total_recolher": "",
                    "codigo_barras": "",
                    "valor_pago": "",
                    "data_pagamento": "",
                    "hora_pagamento": "",
                }

                self.dados.append(dados_erro)

        self.dados_filtrados = list(self.dados)
        self.atualizar_combo_datas_pagamento()
        self.atualizar_tabela()

        self.root.title("Rastreador GNRE - Conferência")

        mensagem = f"Processamento concluído.\n\nPDFs encontrados: {total_arquivos}\nProcessados: {len(self.dados)}"

        if sem_documento_origem:
            mensagem += f"\nSem Documento de Origem: {sem_documento_origem}"
            mensagem += f"\n\nDebug gerado em:\n{self.caminho_debug(pasta_pdfs)}"

        if erros:
            mensagem += f"\nErros: {erros}"
            mensagem += f"\n\nVeja também o debug em:\n{self.caminho_debug(pasta_pdfs)}"

        messagebox.showinfo("Concluído", mensagem)

    def localizar_dado_por_item_tabela(self, item_id):
        for dado in self.dados:
            if dado.get("_id_tabela") == item_id:
                return dado

        return None

    def editar_linha_selecionada(self):
        item_selecionado = self.tabela.selection()

        if not item_selecionado:
            messagebox.showwarning("Atenção", "Selecione uma linha para editar.")
            return

        item_id = item_selecionado[0]
        dados_linha = self.localizar_dado_por_item_tabela(item_id)

        if dados_linha is None:
            messagebox.showerror("Erro", "Não foi possível localizar a linha selecionada.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Editar linha")
        janela.geometry("600x430")
        janela.transient(self.root)
        janela.grab_set()

        campos = [
            ("tipo", "Tipo"),
            ("data_vencimento", "Vencimento"),
            ("documento_origem", "Documento Origem"),
            ("total_recolher", "Total"),
            ("codigo_barras", "Código Barras"),
            ("valor_pago", "Valor Pago"),
            ("data_pagamento", "Data Pag."),
            ("hora_pagamento", "Hora Pag."),
        ]

        variaveis = {}

        for linha, (chave, rotulo) in enumerate(campos):
            tk.Label(janela, text=rotulo, anchor="w").grid(row=linha, column=0, sticky="w", padx=10, pady=5)
            var = tk.StringVar(value=dados_linha.get(chave, ""))
            entrada = tk.Entry(janela, textvariable=var, width=70)
            entrada.grid(row=linha, column=1, sticky="ew", padx=10, pady=5)
            variaveis[chave] = var

        janela.columnconfigure(1, weight=1)

        def salvar_edicao():
            for chave, var in variaveis.items():
                dados_linha[chave] = var.get().strip()

            self.atualizar_combo_datas_pagamento()
            self.aplicar_filtro_data_pagamento()

            janela.destroy()

        frame_botoes = tk.Frame(janela)
        frame_botoes.grid(row=len(campos), column=0, columnspan=2, pady=15)

        tk.Button(frame_botoes, text="Salvar", command=salvar_edicao, bg="#2ca02c", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(frame_botoes, text="Cancelar", command=janela.destroy, width=15).pack(side="left", padx=5)

    def gerar_excel(self):
        if not self.dados:
            messagebox.showwarning("Atenção", "Nenhum dado processado para gerar o Excel.")
            return

        caminho_excel = self.caminho_excel_var.get().strip()

        if not caminho_excel:
            messagebox.showwarning("Atenção", "Selecione onde salvar a planilha.")
            return

        dados_para_exportar = list(self.dados_filtrados)

        if not dados_para_exportar:
            messagebox.showwarning("Atenção", "Nenhum dado no filtro atual para gerar o Excel.")
            return

        try:
            exportar_excel(dados_para_exportar, caminho_excel)

            filtro_atual = self.filtro_data_pagamento_var.get().strip()

            if filtro_atual and filtro_atual != "Todas":
                detalhe = f"\n\nFiltro aplicado: Data Pag. {filtro_atual}"
            else:
                detalhe = "\n\nFiltro aplicado: Todas as datas"

            messagebox.showinfo(
                "Sucesso",
                f"Planilha gerada com sucesso:\n{caminho_excel}{detalhe}"
            )

        except Exception as erro:
            messagebox.showerror("Erro", f"Erro ao gerar Excel:\n{erro}")


def main():
    root = tk.Tk()
    app = RastreadorGNRE(root)
    root.mainloop()


if __name__ == "__main__":
    main()