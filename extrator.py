import re


# ============================================================
# Utilitarios basicos
# ============================================================

def limpar_codigo_barras(codigo):
    if not codigo:
        return ""
    return re.sub(r"\D", "", str(codigo))


def normalizar_texto(texto):
    if not texto:
        return ""

    substituicoes = {
        "´": "", "`": "", "ˆ": "", "~": "",
        "ç": "c", "Ç": "C",
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "Á": "A", "À": "A", "Ã": "A", "Â": "A",
        "é": "e", "ê": "e", "É": "E", "Ê": "E",
        "í": "i", "Í": "I",
        "ó": "o", "ô": "o", "õ": "o",
        "Ó": "O", "Ô": "O", "Õ": "O",
        "ú": "u", "Ú": "U",
    }

    texto = str(texto)

    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)

    return texto


def obter_linhas(texto):
    if not texto:
        return []
    return [linha.strip() for linha in str(texto).splitlines() if linha.strip()]


def normalizar_valor(valor):
    if not valor:
        return ""

    valor = str(valor).strip()
    valor = re.sub(r"[^\d\.,]", "", valor)

    if not valor:
        return ""

    if re.fullmatch(r"\d+\.\d{2}", valor):
        inteiro, decimal = valor.split(".")
        return f"{int(inteiro):,}".replace(",", ".") + f",{decimal}"

    if re.fullmatch(r"\d+,\d{2}", valor):
        return valor

    if re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}", valor):
        return valor

    if re.fullmatch(r"\d{1,3}(?:,\d{3})*\.\d{2}", valor):
        numero = float(valor.replace(",", ""))
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return valor.replace(".", ",")


# ============================================================
# Separacao GNRE / Comprovante
# ============================================================

def encontrar_primeira_posicao_comprovante(texto):
    texto_norm = normalizar_texto(texto)

    padroes = [
        r"COMPROVANTE\s+DE\s+PAGAMENTO",
        r"COMPROVANTE\s+BANCARIO",
        r"DADOS\s+DE\s+PAGAMENTO",
        r"PAGAMENTO\s+EFETUADO",
        r"CONTA\s+DEBITADA",
        r"DADOS\s+DA\s+CONTA\s+DEBITADA",
        r"BANCO\s+ITAU",
        r"ITAU\s+UNIBANCO",
        r"BRADESCO",
        r"PAG\s*UTIL",
        r"AUTENTICACAO\s+BANCARIA",
        r"Comprovantedepagamentocomcodigodebarras",
        r"Comprovantedepagamento",
        r"Pagamentoefetuado",
    ]

    posicoes = []

    for padrao in padroes:
        match = re.search(padrao, texto_norm, re.IGNORECASE)
        if match:
            posicoes.append(match.start())

    return min(posicoes) if posicoes else -1


def separar_trecho_gnre(texto):
    texto_norm = normalizar_texto(texto)
    pos = encontrar_primeira_posicao_comprovante(texto_norm)
    return texto_norm[:pos] if pos != -1 else texto_norm


def separar_trecho_comprovante(texto):
    texto_norm = normalizar_texto(texto)
    pos = encontrar_primeira_posicao_comprovante(texto_norm)
    return texto_norm[pos:] if pos != -1 else texto_norm


# ============================================================
# Identificacao
# ============================================================

def identificar_tipo_documento(texto):
    texto_norm = normalizar_texto(texto).upper()
    texto_compacto = re.sub(r"\s+", "", texto_norm)

    tem_gnre = (
        "GUIA NACIONAL DE RECOLHIMENTO" in texto_norm
        or "TRIBUTOS ESTADUAIS" in texto_norm
        or "TOTAL A RECOLHER" in texto_norm
        or "UF FAVORECIDA" in texto_norm
        or "DOCUMENTO DE ORIGEM" in texto_norm
        or "DATA DE VENCIMENTO" in texto_norm
        or "VALOR PRINCIPAL" in texto_norm
    )

    tem_comprovante = (
        "COMPROVANTE DE PAGAMENTO" in texto_norm
        or "COMPROVANTEDEPAGAMENTO" in texto_compacto
        or "COMPROVANTEDEPAGAMENTOCOMCODIGODEBARRAS" in texto_compacto
        or "PAGAMENTO EFETUADO" in texto_norm
        or "PAGAMENTOEFETUADO" in texto_compacto
        or "DADOS DE PAGAMENTO" in texto_norm
        or "CONTA DEBITADA" in texto_norm
        or "ITAU" in texto_norm
        or "BRADESCO" in texto_norm
        or "PAG UTIL" in texto_norm
        or "PAGUTIL" in texto_compacto
        or "AUTENTICACAO BANCARIA" in texto_norm
        or "AUTENTICACAOBANCARIA" in texto_compacto
    )

    if tem_gnre and tem_comprovante:
        return "GNRE_COM_COMPROVANTE"

    if tem_gnre:
        return "GNRE"

    if tem_comprovante:
        return "COMPROVANTE"

    return "DESCONHECIDO"


# ============================================================
# Codigo de barras
# ============================================================

def extrair_codigo_barras(texto):
    if not texto:
        return ""

    candidatos = re.findall(r"[\d\s\-\.]{40,160}", texto)

    for candidato in candidatos:
        codigo = limpar_codigo_barras(candidato)
        if len(codigo) == 48 and codigo.startswith("8"):
            return codigo

    for candidato in candidatos:
        codigo = limpar_codigo_barras(candidato)
        if 44 <= len(codigo) <= 48 and codigo.startswith("8"):
            return codigo

    return ""


# ============================================================
# Documento de Origem
# ============================================================

def parece_chave_nfe(chave):
    chave = re.sub(r"\D", "", str(chave))

    if len(chave) != 44:
        return False

    if chave.startswith("8"):
        return False

    # Modelo NF-e fica em [20:22]
    if chave[20:22] != "55":
        return False

    # Numero NF-e correto dentro da chave.
    # Exemplo:
    # 35260302921800000170550030000216911771741520
    # numero NF-e = chave[25:34] = 000021691
    numero_nfe = chave[25:34]

    if numero_nfe == "000000000":
        return False

    return True


def tratar_documento_origem(numero):
    if not numero:
        return ""

    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        return ""

    # Se for chave NF-e valida, retorna o numero da NF-e.
    if len(numero) == 44 and parece_chave_nfe(numero):
        return numero[25:34]

    return numero


def numero_valido_documento_origem(numero):
    if not numero:
        return False

    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        return False

    ignorar = {
        # falsos ja encontrados
        "100102",
        "13610220",
        "1935735100",
        "3385",
        "00804",
        "804",
        "1088",
        "0626",
        "626",
        "17",
        "1817",
        "202690",
        "20269",
        "020269",

        # CNPJs / codigos / pedacos de arrecadacao
        "02921800000170",
        "85860000000104",
        "85850000000",
        "85860000000",
        "85840000000",
        "85830000000",
        "85810000000",
        "42498675000152",

        # falsos positivos de 9 digitos
        "181202000",
        "302000190",
        "490000000",
        "649000000",
        "597832600",
        "359783260",

        # zeros
        "000",
        "0000",
        "00000",
        "000000",
        "0000000",
        "00000000",
        "000000000",
    }

    if numero in ignorar:
        return False

    # Ano isolado
    if numero in {"2024", "2025", "2026", "2027", "2028", "2029", "2030"}:
        return False

    # CPF/CNPJ
    if len(numero) in {11, 14}:
        return False

    # Codigo de barras/arrecadacao
    if len(numero) >= 40 and numero.startswith("8"):
        return False

    # Chave NF-e valida
    if len(numero) == 44:
        return parece_chave_nfe(numero)

    # Numero NF-e vindo de chave
    if len(numero) == 9 and numero.startswith("000"):
        return True

    # Bloqueia outros numeros de 9 digitos
    if len(numero) == 9:
        return False

    # Bloqueia numeros longos que nao sejam chave NF-e
    if len(numero) >= 10:
        return False

    # Bloqueia curtos demais
    if len(numero) < 5:
        return False

    # Documento Origem real nestes PDFs costuma ter 5 ou 6 digitos:
    # 22405, 22624, 22620, 21584, 21687, 21750 etc.
    if 5 <= len(numero) <= 6:
        return True

    return False


def limpar_texto_para_documento_origem(texto):
    texto = normalizar_texto(texto)

    # Remove datas, horas e valores para evitar falsos positivos.
    texto = re.sub(r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(?::\d{2})?\b", " ", texto)
    texto = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", " ", texto)
    texto = re.sub(r"\b\d{2}:\d{2}(?::\d{2})?\b", " ", texto)
    texto = re.sub(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", " ", texto)
    texto = re.sub(r"\b\d+\.\d{2}\b", " ", texto)
    texto = re.sub(r"R\$\s*\d+(?:[\.,]\d{2})?", " ", texto, flags=re.IGNORECASE)

    return texto


def extrair_documento_origem_por_campo(texto):
    """
    Extrai Documento Origem somente quando o valor aparece junto ou
    imediatamente depois do rotulo:

    - No Documento de Origem
    - Nº Documento de Origem
    - Documento de Origem

    Nao procura numero solto em blocos grandes, porque isso pega:
    - No de Controle
    - codigo de barras
    - receita
    - pedacos como 202690, 1817, 17
    """
    if not texto:
        return ""

    texto_norm = normalizar_texto(texto)
    texto_limpo = limpar_texto_para_documento_origem(texto_norm)

    linhas = [
        re.sub(r"\s+", " ", linha).strip()
        for linha in texto_limpo.splitlines()
        if linha.strip()
    ]

    padrao_rotulo = re.compile(
        r"(?:N[oº°]?\s*)?Documento\s+de\s+Origem",
        re.IGNORECASE,
    )

    # 1) Rotulo e valor na mesma linha
    for linha in linhas:
        match = padrao_rotulo.search(linha)

        if not match:
            continue

        depois = linha[match.end():]

        # Chave NF-e na mesma linha
        chaves = re.findall(r"\b\d{44}\b", depois)
        for chave in chaves:
            if parece_chave_nfe(chave):
                return tratar_documento_origem(chave)

        # Documento curto na mesma linha
        candidatos = re.findall(r"\b\d{5,6}\b", depois)
        for numero in candidatos:
            if numero_valido_documento_origem(numero):
                return numero

    # 2) Rotulo em uma linha e valor na linha imediatamente seguinte
    for i, linha in enumerate(linhas):
        if not padrao_rotulo.search(linha):
            continue

        proximas = linhas[i + 1:i + 3]

        for prox in proximas:
            prox_upper = prox.upper()

            # Se a proxima linha ja for outro campo, nao usa
            if any(p in prox_upper for p in [
                "PERIODO",
                "REFERENCIA",
                "RECEITA",
                "CONVENIO",
                "PRODUTO",
                "VALOR",
                "TOTAL",
                "DATA",
                "VENCIMENTO",
                "CODIGO",
                "BARRAS",
                "CONTROLE",
                "CNPJ",
                "CPF",
                "CONTRIBUINTE",
                "EMITENTE",
                "FAVORECIDA",
                "UF",
            ]):
                continue

            chaves = re.findall(r"\b\d{44}\b", prox)
            for chave in chaves:
                if parece_chave_nfe(chave):
                    return tratar_documento_origem(chave)

            candidatos = re.findall(r"\b\d{5,6}\b", prox)
            for numero in candidatos:
                if numero_valido_documento_origem(numero):
                    return numero

    return ""


def extrair_chave_nfe_quebrada(texto):
    """
    Procura chave NF-e mesmo quando o PDF quebra a chave com espacos,
    quebras de linha, hifens ou pontos.
    """
    if not texto:
        return ""

    texto_limpo = limpar_texto_para_documento_origem(texto)

    candidatos = re.findall(r"(?:\d[\s\-\.]*){44,70}", texto_limpo)

    for candidato in candidatos:
        digitos = re.sub(r"\D", "", candidato)

        if len(digitos) < 44:
            continue

        for inicio in range(0, len(digitos) - 43):
            janela = digitos[inicio:inicio + 44]

            if parece_chave_nfe(janela):
                return tratar_documento_origem(janela)

    blocos = re.findall(r"\d{2,}", texto_limpo)

    for i in range(len(blocos)):
        acumulado = ""

        for j in range(i, min(i + 12, len(blocos))):
            acumulado += blocos[j]

            if len(acumulado) >= 44:
                for inicio in range(0, len(acumulado) - 43):
                    janela = acumulado[inicio:inicio + 44]

                    if parece_chave_nfe(janela):
                        return tratar_documento_origem(janela)

            if len(acumulado) > 70:
                break

    return ""


def extrair_documento_curto_por_rotulo(texto):
    """
    Fallback restrito:
    tenta encontrar numero curto somente na mesma linha do rotulo.
    """
    texto_limpo = limpar_texto_para_documento_origem(texto)

    linhas = [
        re.sub(r"\s+", " ", linha).strip()
        for linha in texto_limpo.splitlines()
        if linha.strip()
    ]

    padrao_rotulo = re.compile(
        r"(?:N[oº°]?\s*)?Documento\s+de\s+Origem",
        re.IGNORECASE,
    )

    for linha in linhas:
        match = padrao_rotulo.search(linha)

        if not match:
            continue

        depois = linha[match.end():]
        candidatos = re.findall(r"\b\d{5,6}\b", depois)

        for numero in candidatos:
            if numero_valido_documento_origem(numero):
                return numero

    return ""


def extrair_documento_curto_por_blocos(texto):
    """
    Fallback final extremamente restrito.
    Nao varre blocos grandes.
    """
    return extrair_documento_origem_por_campo(texto)


def extrair_documento_origem(texto):
    texto_norm = normalizar_texto(texto)
    texto_gnre = separar_trecho_gnre(texto_norm)

    # ÚNICA fonte confiável:
    # campo explícito "No Documento de Origem" / "Documento de Origem"
    doc = extrair_documento_origem_por_campo(texto_gnre)

    if doc and numero_valido_documento_origem(doc):
        return doc

    # Se não achou o campo explicitamente, deixa vazio.
    # Não tenta chave NF-e, código de barras, No de Controle ou fallback por blocos.
    return ""
# ============================================================
# Datas e valores da GNRE
# ============================================================

def extrair_data_vencimento(texto):
    texto_gnre = separar_trecho_gnre(texto)
    texto_norm = normalizar_texto(texto_gnre)

    match = re.search(
        r"Data\s+de\s+vencimento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        texto_norm,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    linhas = obter_linhas(texto_norm)

    for i, linha in enumerate(linhas):
        if "DATA DE VENCIMENTO" in linha.upper():
            for item in linhas[i:i + 8]:
                match_data = re.search(r"\b\d{2}/\d{2}/\d{4}\b", item)
                if match_data:
                    return match_data.group(0)

    datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto_norm)

    return datas[0] if datas else ""


def extrair_total_recolher(texto):
    texto_gnre = separar_trecho_gnre(texto)
    texto_norm = normalizar_texto(texto_gnre)
    linhas = obter_linhas(texto_norm)

    padrao_direto = re.search(
        r"Total\s+a\s+recolher\s*[:\-]?\s*(?:R\$)?\s*(\d{1,3}(?:\.\d{3})*[,.]\d{2}|\d+[,.]\d{2})",
        texto_norm,
        re.IGNORECASE,
    )

    if padrao_direto:
        return normalizar_valor(padrao_direto.group(1))

    for i, linha in enumerate(linhas):
        if "TOTAL A RECOLHER" in linha.upper():
            proximas = linhas[i:i + 20]
            valores = []

            for item in proximas:
                encontrados = re.findall(
                    r"\b(?:\d{1,3}(?:\.\d{3})*[,.]\d{2}|\d+[,.]\d{2})\b",
                    item,
                )

                for valor in encontrados:
                    valor_norm = normalizar_valor(valor)

                    if valor_norm and valor_norm != "0,00":
                        valores.append(valor_norm)

            if valores:
                return valores[-1]

    valores = re.findall(
        r"\b(?:\d{1,3}(?:\.\d{3})*[,.]\d{2}|\d+[,.]\d{2})\b",
        texto_norm,
    )

    valores_validos = []

    for valor in valores:
        valor_norm = normalizar_valor(valor)

        if valor_norm and valor_norm != "0,00":
            valores_validos.append(valor_norm)

    return valores_validos[-1] if valores_validos else ""


# ============================================================
# Comprovante: valor pago e data/hora
# ============================================================

def extrair_valor_pago(texto):
    texto_comprovante = separar_trecho_comprovante(texto)
    texto_comprovante = normalizar_texto(texto_comprovante)

    padroes = [
        r"Valor\s+do\s+Pagamento\s*[:\-]?\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2}|\d+,\d{2})",
        r"Valor\s+Pagamento\s*[:\-]?\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2}|\d+,\d{2})",
        r"Valor\s*[:\-]?\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2}|\d+,\d{2})",
        r"Valor(?:\s|\n|\r)*R\$(?:\s|\n|\r)*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2}|\d+,\d{2})",
        r"Valor.{0,50}?R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2}|\d+,\d{2})",
        r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2}|\d+,\d{2})",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto_comprovante, re.IGNORECASE | re.DOTALL)

        if match:
            return normalizar_valor(match.group(1))

    match = re.search(
        r"Valor.*?R\$\s*(\d+(?:[\.,]\d{2}))",
        texto_comprovante,
        re.IGNORECASE | re.DOTALL,
    )

    if match:
        return normalizar_valor(match.group(1))

    return ""


def extrair_data_hora_pagamento(texto):
    texto_comprovante = separar_trecho_comprovante(texto)
    texto_comprovante = normalizar_texto(texto_comprovante)

    padroes_colados = [
        r"em\s*(\d{2}/\d{2}/\d{4})\s*(?:as|às)?\s*(\d{2}:\d{2}:\d{2})",
        r"em(\d{2}/\d{2}/\d{4})as(\d{2}:\d{2}:\d{2})",
        r"Pagamentoefetuado.*?em\s*(\d{2}/\d{2}/\d{4})\s*(?:as|às)?\s*(\d{2}:\d{2}:\d{2})",
        r"Pagamentoefetuado.*?em(\d{2}/\d{2}/\d{4})as(\d{2}:\d{2}:\d{2})",
    ]

    for padrao in padroes_colados:
        match = re.search(padrao, texto_comprovante, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1), match.group(2)

    padroes_bradesco = [
        r"Data\s+de\s+Pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Data\s+do\s+Pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Data\s+Pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Pagamento\s+em\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Pago\s+em\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
    ]

    for padrao in padroes_bradesco:
        match = re.search(padrao, texto_comprovante, re.IGNORECASE | re.DOTALL)

        if match:
            data = match.group(1)
            hora_match = re.search(r"\b(\d{2}:\d{2}:\d{2})\b", texto_comprovante)
            return data, hora_match.group(1) if hora_match else ""

    if re.search(
        r"BRADESCO|PAG\s*UTIL|PAGUTIL|AUTENTICACAO\s+BANCARIA",
        texto_comprovante,
        re.IGNORECASE,
    ):
        padroes_contexto = [
            r"(?:Valor\s+do\s+Pagamento|Valor\s+Pagamento).*?(\d{2}/\d{2}/\d{4})",
            r"(?:Autenticacao).*?(\d{2}/\d{2}/\d{4})",
            r"(?:Banco\s+Bradesco|Bradesco).*?(\d{2}/\d{2}/\d{4})",
            r"(\d{2}/\d{2}/\d{4}).{0,180}(?:Valor\s+do\s+Pagamento|Valor\s+Pagamento|Autenticacao|Bradesco)",
        ]

        for padrao in padroes_contexto:
            match = re.search(padrao, texto_comprovante, re.IGNORECASE | re.DOTALL)

            if match:
                data = match.group(1)
                hora_match = re.search(r"\b(\d{2}:\d{2}:\d{2})\b", texto_comprovante)
                return data, hora_match.group(1) if hora_match else ""

        datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto_comprovante)

        if datas:
            hora_match = re.search(r"\b(\d{2}:\d{2}:\d{2})\b", texto_comprovante)
            return datas[-1], hora_match.group(1) if hora_match else ""

    padroes_itau = [
        r"Pagamento\s+efetuado\s+em\s*(\d{2}/\d{2}/\d{4})\s*(?:as|às|`as)\s*(\d{2}:\d{2}:\d{2})",
        r"Pagamento\s+efetuado\s+em\s*(\d{2}/\d{2}/\d{4}).{0,100}?(\d{2}:\d{2}:\d{2})",
        r"(\d{2}/\d{2}/\d{4}).{0,100}?(\d{2}:\d{2}:\d{2})",
    ]

    for padrao in padroes_itau:
        match = re.search(padrao, texto_comprovante, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1), match.group(2)

    return "", ""


# ============================================================
# Saidas principais
# ============================================================

def extrair_gnre(texto):
    texto_gnre = separar_trecho_gnre(texto)

    return {
        "tipo": "GNRE",
        "data_vencimento": extrair_data_vencimento(texto_gnre),
        "documento_origem": extrair_documento_origem(texto_gnre),
        "total_recolher": extrair_total_recolher(texto_gnre),
        "codigo_barras": extrair_codigo_barras(texto_gnre),
        "valor_pago": "",
        "data_pagamento": "",
        "hora_pagamento": "",
    }


def extrair_comprovante(texto):
    texto_comprovante = separar_trecho_comprovante(texto)
    data_pagamento, hora_pagamento = extrair_data_hora_pagamento(texto_comprovante)

    return {
        "tipo": "COMPROVANTE",
        "data_vencimento": "",
        "documento_origem": "",
        "total_recolher": "",
        "codigo_barras": extrair_codigo_barras(texto_comprovante),
        "valor_pago": extrair_valor_pago(texto_comprovante),
        "data_pagamento": data_pagamento,
        "hora_pagamento": hora_pagamento,
    }


def extrair_gnre_com_comprovante(texto):
    texto_gnre = separar_trecho_gnre(texto)
    texto_comprovante = separar_trecho_comprovante(texto)

    data_pagamento, hora_pagamento = extrair_data_hora_pagamento(texto_comprovante)

    codigo_gnre = extrair_codigo_barras(texto_gnre)
    codigo_comprovante = extrair_codigo_barras(texto_comprovante)

    total_recolher = extrair_total_recolher(texto_gnre)
    valor_pago = extrair_valor_pago(texto_comprovante)

    if not total_recolher and valor_pago:
        total_recolher = valor_pago

    return {
        "tipo": "GNRE_COM_COMPROVANTE",
        "data_vencimento": extrair_data_vencimento(texto_gnre),
        "documento_origem": extrair_documento_origem(texto_gnre),
        "total_recolher": total_recolher,
        "codigo_barras": codigo_gnre or codigo_comprovante,
        "valor_pago": valor_pago,
        "data_pagamento": data_pagamento,
        "hora_pagamento": hora_pagamento,
    }


def extrair_dados_documento(texto):
    tipo = identificar_tipo_documento(texto)

    if tipo == "GNRE_COM_COMPROVANTE":
        return extrair_gnre_com_comprovante(texto)

    if tipo == "GNRE":
        return extrair_gnre(texto)

    if tipo == "COMPROVANTE":
        return extrair_comprovante(texto)

    return {
        "tipo": "DESCONHECIDO",
        "data_vencimento": "",
        "documento_origem": "",
        "total_recolher": "",
        "codigo_barras": extrair_codigo_barras(texto),
        "valor_pago": "",
        "data_pagamento": "",
        "hora_pagamento": "",
    }

def extrair_documento_origem(texto):
    return ""