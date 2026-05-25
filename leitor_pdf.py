import fitz
import re


def extrair_texto_pdf(caminho_pdf):
    texto = ""

    with fitz.open(caminho_pdf) as doc:
        for pagina in doc:
            texto += pagina.get_text("text") + "\n"

    return texto


def extrair_documento_origem_por_posicao(caminho_pdf):
    """
    Extrai o Documento de Origem usando a posição visual no PDF GNRE.

    A região fica no lado direito:
    - abaixo de Data de vencimento
    - acima de Período de Referência
    """
    try:
        with fitz.open(caminho_pdf) as doc:
            if len(doc) == 0:
                return ""

            pagina = doc[0]

            largura = pagina.rect.width
            altura = pagina.rect.height

            # Recorte da área direita onde fica "No Documento de Origem"
            # Ajustado por proporção da página para funcionar melhor em A4/imagem.
            x0 = largura * 0.70
            y0 = altura * 0.16
            x1 = largura * 0.99
            y1 = altura * 0.34

            area = fitz.Rect(x0, y0, x1, y1)

            texto_area = pagina.get_text("text", clip=area)
            texto_area = re.sub(r"[ \t]+", " ", texto_area)

            # Remove datas para evitar 06/03/2026 virar 2026
            texto_area = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", " ", texto_area)

            # Tenta pegar depois do rótulo
            match = re.search(
                r"(?:N[oº°]?\s*)?Documento\s+de\s+Origem\s*[:\-]?\s*(\d{4,60})",
                texto_area,
                re.IGNORECASE
            )

            if match:
                return tratar_documento_origem_local(match.group(1))

            # Se vier por linhas:
            linhas = [
                linha.strip()
                for linha in texto_area.splitlines()
                if linha.strip()
            ]

            for i, linha in enumerate(linhas):
                if "DOCUMENTO" in linha.upper() and "ORIGEM" in linha.upper():
                    proximas = linhas[i + 1:i + 4]

                    for item in proximas:
                        nums = re.findall(r"\b\d{4,60}\b", item)

                        for num in nums:
                            if documento_origem_valido_local(num):
                                return tratar_documento_origem_local(num)

            # Último fallback dentro da área:
            numeros = re.findall(r"\b\d{4,60}\b", texto_area)

            numeros = [
                n for n in numeros
                if documento_origem_valido_local(n)
            ]

            if numeros:
                # Na área recortada, geralmente:
                # data vencimento foi removida,
                # depois vem documento origem,
                # depois período referência.
                # Então priorizamos número que não pareça mês/ano.
                return tratar_documento_origem_local(numeros[0])

            return ""

    except Exception:
        return ""


def documento_origem_valido_local(numero):
    numero = re.sub(r"\D", "", str(numero))

    if not numero:
        return False

    # Nunca aceitar anos
    if numero in {
        "2020", "2021", "2022", "2023", "2024",
        "2025", "2026", "2027", "2028", "2029", "2030"
    }:
        return False

    # Não aceitar período referência, exemplo 022026, 032026
    if len(numero) == 6 and numero.endswith(("2024", "2025", "2026", "2027", "2028", "2029", "2030")):
        return False

    # Chave grande
    if len(numero) >= 40:
        return True

    # Documento comum
    if 4 <= len(numero) <= 12:
        return True

    return False


def tratar_documento_origem_local(numero):
    numero = re.sub(r"\D", "", str(numero))

    if len(numero) >= 44:
        chave = numero[:44]
        return chave[25:34]

    return numero