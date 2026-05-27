import fitz
import re


def extrair_texto_pdf(caminho_pdf):
    """
    Leitura rápida do texto do PDF.

    Mantém somente get_text("text"), que é leve e suficiente
    para a maior parte dos PDFs.
    """
    texto = ""

    try:
        with fitz.open(caminho_pdf) as doc:
            for pagina in doc:
                texto += pagina.get_text("text") + "\n"
    except Exception:
        return ""

    return texto


def extrair_documento_origem_por_posicao(caminho_pdf):
    """
    Extração rápida do Documento de Origem pela posição visual.

    Usada apenas como fallback quando o extrator.py não encontrou.
    Lê somente a primeira página e tenta:
    1) recortes de texto;
    2) blocos próximos ao topo da GNRE.
    """
    try:
        with fitz.open(caminho_pdf) as doc:
            if len(doc) == 0:
                return ""

            pagina = doc[0]
            largura = pagina.rect.width
            altura = pagina.rect.height

            recortes = [
                # Topo direito padrão
                fitz.Rect(largura * 0.55, altura * 0.08, largura * 1.00, altura * 0.40),

                # Topo central/direito
                fitz.Rect(largura * 0.35, altura * 0.08, largura * 1.00, altura * 0.42),

                # Faixa superior quase inteira
                fitz.Rect(largura * 0.00, altura * 0.08, largura * 1.00, altura * 0.45),

                # Região do meio superior, caso o PDF esteja deslocado
                fitz.Rect(largura * 0.00, altura * 0.15, largura * 1.00, altura * 0.55),

                # Área direita mais baixa
                fitz.Rect(largura * 0.50, altura * 0.20, largura * 1.00, altura * 0.62),
            ]

            for area in recortes:
                texto_area = pagina.get_text("text", clip=area)

                resultado = extrair_documento_origem_do_texto_local(texto_area)

                if resultado:
                    return resultado

            # Fallback leve por blocos:
            # pega apenas blocos da metade superior da primeira página.
            blocos = pagina.get_text("blocks")
            textos_blocos = []

            for bloco in blocos:
                x0, y0, x1, y1, texto_bloco = bloco[:5]

                if y0 <= altura * 0.60:
                    textos_blocos.append(str(texto_bloco))

            texto_blocos = "\n".join(textos_blocos)

            resultado = extrair_documento_origem_do_texto_local(texto_blocos)

            if resultado:
                return resultado

            return ""

    except Exception:
        return ""

def extrair_documento_origem_do_texto_local(texto):
    if not texto:
        return ""

    texto = normalizar_texto_local(texto)

    # Remove datas
    texto = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", " ", texto)

    # Remove valores monetários
    texto = re.sub(r"\b\d{1,3}(?:\.\d{3})*,\d{2}\b", " ", texto)
    texto = re.sub(r"\b\d+\.\d{2}\b", " ", texto)

    # Remove horários
    texto = re.sub(r"\b\d{2}:\d{2}(?::\d{2})?\b", " ", texto)

    # 1) Busca chave NF-e mesmo se vier quebrada com espaços ou quebras
    candidatos_quebrados = re.findall(
        r"(?:\d[\s\-.]*){44,60}",
        texto
    )

    for candidato in candidatos_quebrados:
        digitos = re.sub(r"\D", "", candidato)

        chave = localizar_chave_nfe_local(digitos)

        if chave:
            return tratar_documento_origem_local(chave)

    # 2) Busca depois do rótulo Documento de Origem
    texto_compacto = re.sub(r"\s+", " ", texto)

    match = re.search(
        r"(?:N[oº°]?\s*)?Documento\s+de\s+Origem\s*[:\-]?\s*(.{0,120})",
        texto_compacto,
        re.IGNORECASE
    )

    if match:
        trecho = match.group(1)

        candidatos = re.findall(r"\d{4,60}", trecho)

        for candidato in candidatos:
            if documento_origem_valido_local(candidato):
                return tratar_documento_origem_local(candidato)

    # 3) Procura números válidos no recorte
    numeros = re.findall(r"\b\d{4,60}\b", texto)

    for numero in numeros:
        if documento_origem_valido_local(numero):
            return tratar_documento_origem_local(numero)

    return ""


def localizar_chave_nfe_local(digitos):
    if not digitos:
        return ""

    digitos = re.sub(r"\D", "", str(digitos))

    if len(digitos) < 44:
        return ""

    for i in range(0, len(digitos) - 43):
        chave = digitos[i:i + 44]

        if chave_valida_basica_local(chave):
            return chave

    return ""


def chave_valida_basica_local(chave):
    chave = re.sub(r"\D", "", str(chave))

    if len(chave) != 44:
        return False

    # Código de barras de GNRE começa com 8, não é chave NF-e
    if chave.startswith("8"):
        return False

    # Posição 21-22 da chave NF-e = modelo.
    # Para NF-e normalmente é 55.
    if chave[20:22] != "55":
        return False

    # UF São Paulo = 35 costuma aparecer nos seus PDFs
    # mas não bloqueia outras UFs.
    if not chave[:2].isdigit():
        return False

    return True


def documento_origem_valido_local(numero):
    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        return False

    ignorar = {
        "100102",
        "13610220",
        "1935735100",
        "3385",
        "00804",
        "804",
        "02921800000170",
        "85860000000104",
        "85850000000",
        "85860000000",
        "85840000000",
        "85830000000",
        "000",
        "0000",
        "00000",
        "000000",
        "0000000",
        "00000000",
    }

    if numero in ignorar:
        return False

    if numero in {
        "2020", "2021", "2022", "2023", "2024",
        "2025", "2026", "2027", "2028", "2029", "2030"
    }:
        return False

    # Período referência, exemplo 032026
    if (
        len(numero) == 6
        and numero.endswith(("2024", "2025", "2026", "2027", "2028", "2029", "2030"))
    ):
        return False

    # CPF/CNPJ
    if len(numero) in {11, 14}:
        return False

    # Código de barras/arrecadação
    if len(numero) >= 40 and numero.startswith("8"):
        return False

    # Número de controle GNRE
    if len(numero) == 16 and re.match(r"^(11|12|13)0200\d{10}$", numero):
        return False

    # Número de controle começando com ano
    if len(numero) >= 14 and numero.startswith(("2024", "2025", "2026", "2027", "2028")):
        return False

    # Documento curto
    if 4 <= len(numero) <= 10:
        return True

    # Chave NF-e
    if len(numero) >= 44:
        return bool(localizar_chave_nfe_local(numero))

    return False


def tratar_documento_origem_local(numero):
    numero = re.sub(r"\D", "", str(numero))

    chave = localizar_chave_nfe_local(numero)

    if chave:
        return chave[25:34]

    if len(numero) > 10 and len(numero) >= 34:
        return numero[25:34]

    return numero


def normalizar_texto_local(texto):
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