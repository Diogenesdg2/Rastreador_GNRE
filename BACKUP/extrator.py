import re


def limpar_codigo_barras(codigo):
    if not codigo:
        return ""

    return re.sub(r"\D", "", str(codigo))


def normalizar_texto(texto):
    if not texto:
        return ""

    substituicoes = {
        "´": "",
        "`": "",
        "ˆ": "",
        "ç": "c",
        "Ç": "C",
        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "Á": "A",
        "À": "A",
        "Ã": "A",
        "Â": "A",
        "é": "e",
        "ê": "e",
        "É": "E",
        "Ê": "E",
        "í": "i",
        "Í": "I",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "Ó": "O",
        "Ô": "O",
        "Õ": "O",
        "ú": "u",
        "Ú": "U",
    }

    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)

    return texto


def obter_linhas(texto):
    if not texto:
        return []

    return [linha.strip() for linha in texto.splitlines() if linha.strip()]


def extrair_codigo_barras(texto):
    if not texto:
        return ""

    candidatos = re.findall(r"[\d\s\-\.]{40,120}", texto)

    for candidato in candidatos:
        codigo = limpar_codigo_barras(candidato)

        if len(codigo) == 48 and codigo.startswith("8"):
            return codigo

    for candidato in candidatos:
        codigo = limpar_codigo_barras(candidato)

        if 44 <= len(codigo) <= 48 and codigo.startswith("8"):
            return codigo

    return ""


def identificar_tipo_documento(texto):
    texto_norm = normalizar_texto(texto).upper()

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
        or "PAGAMENTO EFETUADO" in texto_norm
        or "DADOS DE PAGAMENTO" in texto_norm
        or "CONTA DEBITADA" in texto_norm
        or "ITAU" in texto_norm
        or "ITAÚ" in texto_norm
    )

    if tem_gnre and tem_comprovante:
        return "GNRE_COM_COMPROVANTE"

    if tem_gnre:
        return "GNRE"

    if tem_comprovante:
        return "COMPROVANTE"

    return "DESCONHECIDO"


def separar_trecho_gnre(texto):
    texto_norm = normalizar_texto(texto)
    texto_upper = texto_norm.upper()

    marcadores_comprovante = [
        "COMPROVANTE DE PAGAMENTO",
        "DADOS DE PAGAMENTO",
        "PAGAMENTO EFETUADO",
        "CONTA DEBITADA",
        "BANCO ITAU",
        "ITAU UNIBANCO",
        "ITAÚ UNIBANCO",
    ]

    posicoes = []

    for marcador in marcadores_comprovante:
        pos = texto_upper.find(marcador)

        if pos != -1:
            posicoes.append(pos)

    if posicoes:
        primeira_posicao = min(posicoes)
        return texto_norm[:primeira_posicao]

    return texto_norm


def separar_trecho_comprovante(texto):
    texto_norm = normalizar_texto(texto)
    texto_upper = texto_norm.upper()

    marcadores = [
        "COMPROVANTE DE PAGAMENTO",
        "DADOS DE PAGAMENTO",
        "PAGAMENTO EFETUADO",
        "CONTA DEBITADA",
        "BANCO ITAU",
        "ITAU UNIBANCO",
        "ITAÚ UNIBANCO",
    ]

    posicoes = []

    for marcador in marcadores:
        pos = texto_upper.find(marcador)

        if pos != -1:
            posicoes.append(pos)

    if posicoes:
        primeira_posicao = min(posicoes)
        return texto_norm[primeira_posicao:]

    return texto_norm


def tratar_documento_origem(numero):
    """
    Trata o Documento de Origem.

    Regras:
    - Se tiver até 10 dígitos, mantém como está.
      Exemplo:
      21584 -> 21584

    - Se tiver mais de 10 dígitos e parecer chave NF-e,
      extrai o número da NF.

    Na chave NF-e de 44 dígitos:
    posições humanas:
    1-2   UF
    3-6   AAMM
    7-20  CNPJ
    21-22 modelo
    23-25 série
    26-34 número da NF
    35-43 código numérico
    44    dígito verificador

    Em Python:
    numero da NF = [25:34]
    """
    if not numero:
        return ""

    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        return ""

    # Documento curto: mantém inteiro
    if len(numero) <= 10:
        return numero

    # Chave NF-e/documento longo: extrai número da NF
    if len(numero) >= 34:
        return numero[25:34]

    # Caso intermediário: mantém como veio
    return numero


def numero_valido_documento_origem(numero):
    """
    Valida candidatos para Documento de Origem.
    """
    if not numero:
        return False

    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        return False

    ignorar = {
        "100102",          # Código da Receita
        "13610220",        # CEP
        "1935735100",      # telefone
        "3385",
        "00804",
        "804",
        "02921800000170",
        "85860000000104",
        "85850000000",
        "85860000000",
        "000",
        "0000",
        "00000",
        "000000",
        "0000000",
        "00000000",
    }

    if numero in ignorar:
        return False

    # Ignora anos
    if numero in {"2024", "2025", "2026", "2027", "2028", "2029", "2030"}:
        return False

    # Ignora CPF/CNPJ
    if len(numero) in {11, 14}:
        return False

    # Ignora código de barras/arrecadação começando com 8
    if len(numero) >= 40 and numero.startswith("8"):
        return False

    # Documento curto, exemplo 21584
    if 5 <= len(numero) <= 12:
        return True

    # Chave NF-e ou documento longo
    if len(numero) > 12:
        return True

    return False


def extrair_documento_origem(texto):
    """
    Extrai o Documento de Origem da GNRE.

    Casos:
    - Documento curto:
      21584 -> 21584

    - Chave NF-e:
      35260302921800000170550030000216851318311008 -> 000021685
    """
    texto_norm = normalizar_texto(texto)
    texto_gnre = separar_trecho_gnre(texto_norm)

    linhas = obter_linhas(texto_gnre)

    def limpar_linha_para_numeros(linha):
        # Remove datas completas
        linha = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", " ", linha)

        # Remove datas com hora, se aparecer
        linha = re.sub(r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(?::\d{2})?\b", " ", linha)

        # Remove valores monetários
        linha = re.sub(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", " ", linha)

        # Remove horários
        linha = re.sub(r"\b\d{2}:\d{2}(?::\d{2})?\b", " ", linha)

        return linha

    # 1) Primeiro tenta pegar entre o rótulo e "Periodo de Referencia"
    texto_limpo = limpar_linha_para_numeros(texto_gnre)
    texto_compacto = re.sub(r"\s+", " ", texto_limpo)

    padrao_intervalo = (
        r"N[oº°]?\s*Documento\s+de\s+Origem"
        r"\s*[:\-]?\s*"
        r"(.*?)"
        r"Periodo\s+de\s+Referencia"
    )

    match = re.search(
        padrao_intervalo,
        texto_compacto,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        conteudo = match.group(1)

        numeros = re.findall(r"\b\d{5,60}\b", conteudo)

        numeros = [
            n for n in numeros
            if numero_valido_documento_origem(n)
        ]

        if numeros:
            return tratar_documento_origem(numeros[-1])

    # 2) Procura depois de cada ocorrência de "Total a recolher"
    # Nos PDFs enviados, o valor real aparece próximo dessa região.
    for i, linha in enumerate(linhas):
        if "TOTAL A RECOLHER" in linha.upper():
            bloco = linhas[i:i + 18]

            candidatos = []

            for item in bloco:
                item_limpo = limpar_linha_para_numeros(item)
                numeros = re.findall(r"\b\d{5,60}\b", item_limpo)

                for numero in numeros:
                    if numero_valido_documento_origem(numero):
                        candidatos.append(numero)

            if candidatos:
                return tratar_documento_origem(candidatos[-1])

    # 3) Procura em bloco próximo ao rótulo "Documento de Origem"
    for i, linha in enumerate(linhas):
        if "DOCUMENTO DE ORIGEM" in linha.upper():
            bloco = linhas[i:i + 12]

            candidatos = []

            for item in bloco:
                item_limpo = limpar_linha_para_numeros(item)
                numeros = re.findall(r"\b\d{5,60}\b", item_limpo)

                for numero in numeros:
                    if numero_valido_documento_origem(numero):
                        candidatos.append(numero)

            if candidatos:
                return tratar_documento_origem(candidatos[-1])

    # 4) Fallback: procura nas últimas linhas da GNRE
    ultimas_linhas = linhas[-50:]

    candidatos = []

    for item in ultimas_linhas:
        item_limpo = limpar_linha_para_numeros(item)
        numeros = re.findall(r"\b\d{5,60}\b", item_limpo)

        for numero in numeros:
            if numero_valido_documento_origem(numero):
                candidatos.append(numero)

    if candidatos:
        return tratar_documento_origem(candidatos[-1])

    return ""


def extrair_data_vencimento(texto):
    texto_gnre = separar_trecho_gnre(texto)
    texto_norm = normalizar_texto(texto_gnre)

    match = re.search(
        r"Data\s+de\s+vencimento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        texto_norm,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    linhas = obter_linhas(texto_norm)

    for i, linha in enumerate(linhas):
        if "DATA DE VENCIMENTO" in linha.upper():
            proximas = linhas[i:i + 8]

            for item in proximas:
                match_data = re.search(r"\b\d{2}/\d{2}/\d{4}\b", item)

                if match_data:
                    return match_data.group(0)

    datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto_norm)

    if datas:
        return datas[0]

    return ""


def extrair_total_recolher(texto):
    texto_gnre = separar_trecho_gnre(texto)
    linhas = obter_linhas(texto_gnre)

    for i, linha in enumerate(linhas):
        if "TOTAL A RECOLHER" in linha.upper():
            proximas = linhas[i:i + 12]

            valores = []

            for item in proximas:
                encontrados = re.findall(
                    r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b",
                    item
                )
                valores.extend(encontrados)

            valores_validos = [v for v in valores if v != "0,00"]

            if valores_validos:
                return valores_validos[-1]

    valores = re.findall(
        r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b",
        texto_gnre
    )

    valores_validos = [v for v in valores if v != "0,00"]

    if valores_validos:
        return valores_validos[-1]

    return ""


def extrair_valor_pago(texto):
    texto_comprovante = separar_trecho_comprovante(texto)

    padroes = [
        r"Valor\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"Valor\s*[:\-]?\s*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"Valor(?:\s|\n|\r)*R\$(?:\s|\n|\r)*(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto_comprovante, re.IGNORECASE)

        if match:
            return match.group(1)

    return ""


def extrair_data_hora_pagamento(texto):
    texto_comprovante = separar_trecho_comprovante(texto)
    texto_comprovante = normalizar_texto(texto_comprovante)

    # =========================
    # MODELO NOVO BRADESCO / PAG ÚTIL
    # =========================
    # Possíveis formatos:
    # Data de Pagamento: 31/03/2026
    # Data Pagamento 31/03/2026
    # Data do Pagamento 31/03/2026
    # Pagamento em 31/03/2026
    padroes_bradesco = [
        r"Data\s+de\s+Pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Data\s+do\s+Pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Data\s+Pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Pagamento\s+em\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        r"Pago\s+em\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
    ]

    for padrao in padroes_bradesco:
        match = re.search(
            padrao,
            texto_comprovante,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            data = match.group(1)

            # Bradesco normalmente não traz hora.
            hora_match = re.search(
                r"\b(\d{2}:\d{2}:\d{2})\b",
                texto_comprovante
            )

            hora = hora_match.group(1) if hora_match else ""

            return data, hora

    # =========================
    # FALLBACK ESPECÍFICO BRADESCO
    # =========================
    # Se o texto tiver cara de Bradesco/Pag Útil, pega a data mais provável.
    # Geralmente é a data próxima de "Valor do Pagamento", "Banco Bradesco",
    # "Autenticação" ou "Pag Útil".
    if re.search(r"BRADESCO|PAG\s*ÚTIL|PAG\s*UTIL", texto_comprovante, re.IGNORECASE):
        padroes_contexto = [
            r"(?:Valor\s+do\s+Pagamento|Valor\s+Pagamento).*?(\d{2}/\d{2}/\d{4})",
            r"(?:Autenticacao|Autenticação).*?(\d{2}/\d{2}/\d{4})",
            r"(?:Banco\s+Bradesco|Bradesco).*?(\d{2}/\d{2}/\d{4})",
            r"(\d{2}/\d{2}/\d{4}).{0,120}(?:Valor\s+do\s+Pagamento|Valor\s+Pagamento|Autenticacao|Autenticação|Bradesco)",
        ]

        for padrao in padroes_contexto:
            match = re.search(
                padrao,
                texto_comprovante,
                re.IGNORECASE | re.DOTALL
            )

            if match:
                data = match.group(1)

                hora_match = re.search(
                    r"\b(\d{2}:\d{2}:\d{2})\b",
                    texto_comprovante
                )

                hora = hora_match.group(1) if hora_match else ""

                return data, hora

        # Último fallback para Bradesco:
        # pega a última data do comprovante, pois costuma ser a data efetiva do pagamento.
        datas = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto_comprovante)

        if datas:
            data = datas[-1]

            hora_match = re.search(
                r"\b(\d{2}:\d{2}:\d{2})\b",
                texto_comprovante
            )

            hora = hora_match.group(1) if hora_match else ""

            return data, hora

    # =========================
    # MODELO ANTIGO ITAÚ
    # =========================
    padroes_itau = [
        r"Pagamento efetuado em\s*(\d{2}/\d{2}/\d{4})\s*(?:as|às|`as)\s*(\d{2}:\d{2}:\d{2})",
        r"Pagamento efetuado em\s*(\d{2}/\d{2}/\d{4}).{0,60}?(\d{2}:\d{2}:\d{2})",
        r"(\d{2}/\d{2}/\d{4}).{0,60}?(\d{2}:\d{2}:\d{2})",
    ]

    for padrao in padroes_itau:
        match = re.search(
            padrao,
            texto_comprovante,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return match.group(1), match.group(2)

    return "", ""

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

    return {
        "tipo": "GNRE_COM_COMPROVANTE",
        "data_vencimento": extrair_data_vencimento(texto_gnre),
        "documento_origem": extrair_documento_origem(texto_gnre),
        "total_recolher": extrair_total_recolher(texto_gnre),
        "codigo_barras": codigo_gnre or codigo_comprovante,
        "valor_pago": extrair_valor_pago(texto_comprovante),
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