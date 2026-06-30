"""
Validação do Google reCAPTCHA v3 (invisível).

O front-end gera um token a cada submit de login/cadastro e envia junto
no corpo da requisição. Esse módulo valida o token na API do Google e
verifica se a nota (score) é alta o suficiente para considerar a ação
como humana.
"""
import requests
from flask import current_app

GOOGLE_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def validar_recaptcha(token: str, acao_esperada: str = None) -> tuple[bool, str]:
    """
    Verifica o token do reCAPTCHA v3 com o Google.
    Retorna (ok, mensagem_de_erro_se_houver).
    """
    secret = current_app.config.get("RECAPTCHA_SECRET_KEY")
    nota_minima = current_app.config.get("RECAPTCHA_MIN_SCORE", 0.5)

    if not secret:
        # Sem chave configurada no .env — não bloqueia o usuário em dev,
        # mas avisa no log para não passar batido em produção.
        current_app.logger.warning(
            "RECAPTCHA_SECRET_KEY não configurada no .env. Captcha não foi validado."
        )
        return True, ""

    if not token:
        return False, "Captcha não preenchido. Recarregue a página e tente novamente."

    try:
        resp = requests.post(
            GOOGLE_VERIFY_URL,
            data={"secret": secret, "response": token},
            timeout=8,
        )
        resultado = resp.json()
    except Exception as e:
        current_app.logger.error(f"Erro ao validar reCAPTCHA: {e}")
        # Falha de rede ao validar não deve impedir o usuário de usar o site
        return True, ""

    if not resultado.get("success"):
        current_app.logger.error(
            f"reCAPTCHA falhou. Resposta completa do Google: {resultado}"
        )
        return False, "Falha na verificação do captcha. Tente novamente."

    if acao_esperada and resultado.get("action") != acao_esperada:
        return False, "Verificação de captcha inválida."

    score = resultado.get("score", 0)
    if score < nota_minima:
        return False, "Não foi possível confirmar que você não é um robô."

    return True, ""