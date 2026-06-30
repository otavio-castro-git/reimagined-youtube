"""
Envio de email via SMTP (Gmail) — usado para enviar o código de
verificação de cadastro.

Não usa Flask-Mail para evitar mais uma dependência; usa smtplib da
biblioteca padrão do Python, que já basta para enviar pelo Gmail.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def enviar_email_codigo(destinatario: str, codigo: str) -> bool:
    """
    Envia o email com o código de verificação de 6 dígitos.
    Retorna True se enviou com sucesso, False se falhou (e loga o erro).
    """
    remetente = current_app.config.get("MAIL_DEFAULT_SENDER")
    usuario   = current_app.config.get("MAIL_USERNAME")
    senha     = current_app.config.get("MAIL_PASSWORD")
    servidor  = current_app.config.get("MAIL_SERVER")
    porta     = current_app.config.get("MAIL_PORT")
    usar_tls  = current_app.config.get("MAIL_USE_TLS")

    if not usuario or not senha:
        # Sem credenciais configuradas (.env). Em desenvolvimento, registra
        # o código no log do servidor para não travar testes locais.
        current_app.logger.warning(
            "MAIL_USERNAME/MAIL_PASSWORD não configurados no .env. "
            f"Código de verificação para {destinatario}: {codigo}"
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Seu código de verificação - ViewTube"
    msg["From"]    = remetente
    msg["To"]      = destinatario

    texto_plano = (
        f"Seu código de verificação do ViewTube é: {codigo}\n\n"
        f"Esse código expira em 10 minutos.\n"
        f"Se você não solicitou este cadastro, pode ignorar este email."
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color:#FF3B30;">View<span style="color:#111;">Tube</span></h2>
        <p>Olá!</p>
        <p>Use o código abaixo para confirmar seu cadastro:</p>
        <div style="background:#1a1a1a; color:#fff; font-size:28px; font-weight:bold;
                    letter-spacing:6px; text-align:center; padding:18px; border-radius:10px; margin:20px 0;">
            {codigo}
        </div>
        <p style="color:#555; font-size:13px;">Esse código expira em 10 minutos.</p>
        <p style="color:#888; font-size:12px;">Se você não solicitou este cadastro, pode ignorar este email.</p>
    </div>
    """

    msg.attach(MIMEText(texto_plano, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(servidor, porta) as server:
            if usar_tls:
                server.starttls(context=contexto)
            server.login(usuario, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        return True
    except Exception as e:
        current_app.logger.error(f"Falha ao enviar email para {destinatario}: {e}")
        return False
