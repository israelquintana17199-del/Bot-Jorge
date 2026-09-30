#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sqlite3
import datetime
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
from flask import Flask
import threading
import os

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Jorge activo"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

threading.Thread(target=run_flask, daemon=True).start()

    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, MessageHandler, ContextTypes, filters
)

# ═══════════════════════════════════════════════════════
# CONFIGURACIÓN - EDITAR ESTOS VALORES
# ═══════════════════════════════════════════════════════

TOKEN = "8606112595:AAH_3dzdlM5pr_Kqbvz77FYwMYGMaAKL0Cs"
OWNER_ID = 5042643884

# CREDENCIALES DEL CORREO REMITENTE (GMAIL)
EMAIL_REMITENTE = "israelquintana17199@gmail.com"
CONTRASENA_APP = "mvwg bupn pcyf nbtj"

# SERVIDOR SMTP DE GMAIL (siempre usamos este para enviar)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# Estados para ConversationHandler
CORREO_OBJETIVO, CANTIDAD_SPAM, MENSAJE_SPAM = range(3)

# ═══════════════════════════════════════════════════════
# BASE DE DATOS
# ═══════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            link TEXT,
            fecha_registro TEXT
        )
    ''')
    conn.commit()
    conn.close()

def registrar_usuario(user_id, username, first_name, last_name):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    
    fecha = datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")
    link = f"tg://user?id={user_id}"
    username_str = f"@{username}" if username else "Sin username"
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios 
            (user_id, username, first_name, last_name, link, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username_str, first_name, last_name, link, fecha))
        conn.commit()
        nuevo = cursor.rowcount > 0
    except:
        nuevo = False
    
    conn.close()
    return nuevo, fecha

def contar_usuarios():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def obtener_info_usuario(user_id):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE user_id = ?', (user_id,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

# ═══════════════════════════════════════════════════════
# MENSAJES CON DISEÑO
# ═══════════════════════════════════════════════════════

def mensaje_bienvenida():
    return """
╔════════════════════════════════════╗
║     🤖 SPAM BOT ACTIVADO           ║
╠════════════════════════════════════╣
║                                    ║
║  ✨ ¡Bienvenido al sistema!       ║
║                                    ║
║  📋 Comandos disponibles:         ║
║     /start - Iniciar bot          ║
║     /help - Ver ayuda             ║
║     /cmds - Ver comandos          ║
║                                    ║
║  ❓ ¿Dudas? Contacta al owner:    ║
║     👤 @soygaymegustalaverga      ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_cmds():
    return """
╔════════════════════════════════════╗
║      📋 COMANDOS PARA EL BOT       ║
╠════════════════════════════════════╣
║                                    ║
║  📧 Spam Email                     ║
║  📧 Gmail/Outlook/Yahoo/etc       ║
║                                    ║
║  Selecciona una opción:           ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_mi_info(user_id, username, first_name, last_name, fecha_registro):
    link = f"tg://user?id={user_id}"
    username_str = username if username else "No disponible"
    nombre = f"{first_name or ''} {last_name or ''}".strip() or "No disponible"
    
    return f"""
╔══════════════════════════════════════╗
║     👤 TU INFORMACIÓN DE USUARIO     ║
╠══════════════════════════════════════╣
║                                      ║
║  ☆ 🆔 ID: `{user_id}`               ║
║                                      ║
║  ☆ 👤 Usuario: {username_str}       ║
║                                      ║
║  ☆ 🔗 Link: [Click aquí]({link})    ║
║                                      ║
║  ☆ 📅 Fecha de registro:            ║
║     `{fecha_registro}`               ║
║                                      ║
╚══════════════════════════════════════╝
"""

def mensaje_pedir_correo():
    return """
╔════════════════════════════════════╗
║         📧 SPAM EMAIL              ║
╠════════════════════════════════════╣
║                                    ║
║  Ingresa un correo válido:         ║
║                                    ║
║  ✉️ Gmail (@gmail.com)            ║
║  ✉️ Outlook (@outlook/hotmail)   ║
║  ✉️ Yahoo (@yahoo.com)            ║
║  ✉️ iCloud (@icloud.com)           ║
║  ✉️ Cualquier otro...              ║
║                                    ║
║  Al que deseas spamear ▪︎          ║
║                                    ║
║  Ejemplo: victima@outlook.com      ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_correo_recibido(correo, proveedor):
    return f"""
╔════════════════════════════════════╗
║      ✅ CORREO RECIBIDO            ║
╠════════════════════════════════════╣
║                                    ║
║  📧 Correo objetivo:               ║
║  `{correo}`                        ║
║                                    ║
║  🌐 Proveedor: {proveedor}        ║
║                                    ║
║  Ingresa la cantidad de spam      ║
║  que quieres enviar:              ║
║                                    ║
║  Ejemplo: 15                       ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_cantidad_recibida(cantidad):
    return f"""
╔════════════════════════════════════╗
║     ✅ CANTIDAD REGISTRADA         ║
╠════════════════════════════════════╣
║                                    ║
║  Cantidad: {cantidad} mensajes    ║
║                                    ║
║  Ahora ingresa el mensaje         ║
║  que quieres enviar:              ║
║                                    ║
║  (Escribe el texto completo       ║
║   que se enviará en cada correo)  ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_enviando(cantidad, correo):
    return f"""
╔════════════════════════════════════╗
║      ⏳ ENVIANDO SPAM...           ║
╠════════════════════════════════════╣
║                                    ║
║  📧 Destinatario: {correo}        ║
║  📨 Cantidad: {cantidad} mensajes ║
║                                    ║
║  Por favor espera...              ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_exito(cantidad, correo):
    return f"""
╔════════════════════════════════════╗
║    ✅ SPAM ENVIADO CON ÉXITO       ║
╠════════════════════════════════════╣
║                                    ║
║  📨 {cantidad} mensajes enviados  ║
║     a {correo}                     ║
║                                    ║
║  ✔️ Proceso completado            ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_error(error):
    return f"""
╔════════════════════════════════════╗
║      ❌ ERROR AL ENVIAR            ║
╠════════════════════════════════════╣
║                                    ║
║  {error}                          ║
║                                    ║
╚════════════════════════════════════╝
"""

def mensaje_notificacion(user_id, username, first_name, last_name, fecha, total):
    nombre_completo = f"{first_name or ''} {last_name or ''}".strip() or "Sin nombre"
    
    return f"""
🆕 *NUEVO USUARIO REGISTRADO*

🆔 *ID:* `{user_id}`
👤 *Usuario:* {username or 'Sin username'}
📝 *Nombre:* {nombre_completo}
🔗 *Link:* [Click aquí](tg://user?id={user_id})
📅 *Fecha:* `{fecha}`

📊 *Total usuarios:* {total}
"""

# ═══════════════════════════════════════════════════════
# TECLADOS
# ═══════════════════════════════════════════════════════

def teclado_cmds():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔵 Spam Email", callback_data="spam_gmail")],
        [InlineKeyboardButton("🟣 Actividades", callback_data="actividades")],
        [InlineKeyboardButton("🔴 Spams en curso", callback_data="spams_curso")],
        [InlineKeyboardButton("🩷 Mi info", callback_data="mi_info")],
    ])

def teclado_volver():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver al menú", callback_data="ver_cmds")]
    ])

# ═══════════════════════════════════════════════════════
# FUNCIONES DE SPAM
# ═══════════════════════════════════════════════════════

def validar_correo(correo):
    """Valida formato de correo electrónico"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, correo) is not None

def obtener_proveedor(correo):
    """Obtiene el proveedor del correo"""
    try:
        dominio = correo.split('@')[1].lower()
        proveedores = {
            'gmail.com': 'GMAIL',
            'outlook.com': 'OUTLOOK',
            'hotmail.com': 'HOTMAIL',
            'live.com': 'LIVE',
            'yahoo.com': 'YAHOO',
            'yahoo.es': 'YAHOO',
            'yahoo.com.mx': 'YAHOO',
            'icloud.com': 'ICLOUD',
            'me.com': 'ICLOUD',
            'aol.com': 'AOL',
            'protonmail.com': 'PROTONMAIL',
            'yandex.com': 'YANDEX',
            'mail.ru': 'MAIL.RU',
            'zoho.com': 'ZOHO',
        }
        return proveedores.get(dominio, dominio.upper())
    except:
        return "DESCONOCIDO"

def enviar_spam(correo_objetivo, cantidad, mensaje_texto):
    """
    Envía spam usando SIEMPRE el servidor SMTP de Gmail
    pero permite cualquier correo como destinatario
    """
    try:
        # SIEMPRE usamos el servidor de Gmail para enviar
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMITENTE, CONTRASENA_APP)
        
        for i in range(cantidad):
            msg = MIMEMultipart()
            msg['From'] = EMAIL_REMITENTE
            msg['To'] = correo_objetivo
            msg['Subject'] = f"Spam #{i+1}"
            
            cuerpo = f"{mensaje_texto}\n\n---\nMensaje {i+1} de {cantidad}"
            msg.attach(MIMEText(cuerpo, 'plain'))
            
            server.send_message(msg)
        
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)

# ═══════════════════════════════════════════════════════
# COMANDOS BÁSICOS
# ═══════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    nuevo, fecha = registrar_usuario(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )
    
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contactar Owner", url="https://t.me/soygaymegustalaverga")],
        [InlineKeyboardButton("📋 Ver Comandos", callback_data="ver_cmds")]
    ])
    
    await update.message.reply_text(
        mensaje_bienvenida(),
        reply_markup=teclado,
        parse_mode='Markdown'
    )
    
    if nuevo:
        total = contar_usuarios()
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=mensaje_notificacion(
                    user.id,
                    user.username,
                    user.first_name,
                    user.last_name,
                    fecha,
                    total
                ),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Error al notificar al owner: {e}")

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        mensaje_cmds(),
        reply_markup=teclado_cmds(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_ayuda = """
╔════════════════════════════════════╗
║           📖 AYUDA DEL BOT         ║
╠════════════════════════════════════╣
║                                    ║
║  /start - Iniciar el bot          ║
║  /help - Mostrar esta ayuda       ║
║  /cmds - Ver menú de comandos     ║
║  /stats - Ver estadísticas        ║
║                                    ║
║  ✉️ Soporta: Cualquier correo    ║
║     Gmail, Outlook, Yahoo, etc    ║
║                                    ║
╚════════════════════════════════════╝
"""
    await update.message.reply_text(texto_ayuda)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ No tienes permiso para usar este comando.")
        return
    
    total = contar_usuarios()
    await update.message.reply_text(f"""
╔════════════════════════════════════╗
║         📊 ESTADÍSTICAS            ║
╠════════════════════════════════════╣
║                                    ║
║  👥 Total usuarios: {total}              ║
║                                    ║
╚════════════════════════════════════╝
""")

# ═══════════════════════════════════════════════════════
# CONVERSACIÓN SPAM EMAIL
# ═══════════════════════════════════════════════════════

async def iniciar_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia la conversación de spam"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text=mensaje_pedir_correo(),
        parse_mode='Markdown'
    )
    
    return CORREO_OBJETIVO

async def recibir_correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el correo objetivo"""
    correo = update.message.text.strip()
    
    if not validar_correo(correo):
        await update.message.reply_text(
            "❌ *Correo inválido*\n\nPor favor ingresa un correo válido.\nEjemplo: `usuario@outlook.com`",
            parse_mode='Markdown'
        )
        return CORREO_OBJETIVO
    
    proveedor = obtener_proveedor(correo)
    
    context.user_data['correo_objetivo'] = correo
    context.user_data['proveedor'] = proveedor
    
    await update.message.reply_text(
        mensaje_correo_recibido(correo, proveedor),
        parse_mode='Markdown'
    )
    
    return CANTIDAD_SPAM

async def recibir_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la cantidad de mensajes"""
    texto = update.message.text.strip()
    
    try:
        cantidad = int(texto)
        if cantidad < 1 or cantidad > 100:
            await update.message.reply_text(
                "❌ *Cantidad inválida*\n\nIngresa un número entre 1 y 100.",
                parse_mode='Markdown'
            )
            return CANTIDAD_SPAM
    except ValueError:
        await update.message.reply_text(
            "❌ *Error*\n\nIngresa solo números.",
            parse_mode='Markdown'
        )
        return CANTIDAD_SPAM
    
    context.user_data['cantidad'] = cantidad
    
    await update.message.reply_text(
        mensaje_cantidad_recibida(cantidad),
        parse_mode='Markdown'
    )
    
    return MENSAJE_SPAM

async def recibir_mensaje_y_enviar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el mensaje y envía el spam"""
    mensaje = update.message.text
    correo = context.user_data.get('correo_objetivo')
    cantidad = context.user_data.get('cantidad')
    
    # Mensaje de enviando
    msg_proceso = await update.message.reply_text(
        mensaje_enviando(cantidad, correo),
        parse_mode='Markdown'
    )
    
    # Enviar spam (siempre usando servidor de Gmail)
    exito, error = enviar_spam(correo, cantidad, mensaje)
    
    if exito:
        # NOTIFICACIÓN AL USUARIO QUE SOLICITÓ EL SPAM
        await msg_proceso.edit_text(
            mensaje_exito(cantidad, correo),
            reply_markup=teclado_volver(),
            parse_mode='Markdown'
        )
    else:
        await msg_proceso.edit_text(
            mensaje_error(error),
            reply_markup=teclado_volver(),
            parse_mode='Markdown'
        )
    
    # Limpiar datos
    context.user_data.clear()
    return ConversationHandler.END

async def cancelar_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la conversación"""
    await update.message.reply_text(
        "❌ Operación cancelada.",
        reply_markup=teclado_volver()
    )
    context.user_data.clear()
    return ConversationHandler.END

# ═══════════════════════════════════════════════════════
# CALLBACKS
# ═══════════════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "spam_gmail":
        await query.edit_message_text(text=mensaje_pedir_correo(), parse_mode='Markdown')
        return CORREO_OBJETIVO

    elif query.data == "actividades":
        await query.edit_message_text(
            text="""
╔════════════════════════════════════╗
║         🟣 ACTIVIDADES             ║
╠════════════════════════════════════╣
║                                    ║
║  No hay actividades recientes...  ║
║                                    ║
╚════════════════════════════════════╝
""",
            reply_markup=teclado_cmds()
        )
    
    elif query.data == "spams_curso":
        await query.edit_message_text(
            text="""
╔════════════════════════════════════╗
║       🔴 SPAMS EN CURSO            ║
╠════════════════════════════════════╣
║                                    ║
║  No hay spams activos...          ║
║                                    ║
╚════════════════════════════════════╝
""",
            reply_markup=teclado_cmds()
        )
    
    elif query.data == "mi_info":
        info = obtener_info_usuario(user.id)
        if info:
            fecha_reg = info[6] if len(info) > 6 else "N/A"
            username_str = info[2] if info[2] else "No disponible"
            first_name = info[3]
            last_name = info[4]
        else:
            fecha_reg = datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")
            username_str = f"@{user.username}" if user.username else "No disponible"
            first_name = user.first_name
            last_name = user.last_name
        
        await query.edit_message_text(
            text=mensaje_mi_info(
                user.id,
                username_str,
                first_name,
                last_name,
                fecha_reg
            ),
            reply_markup=teclado_cmds(),
            parse_mode='Markdown'
        )
    
    elif query.data == "ver_cmds":
        await query.edit_message_text(
            text=mensaje_cmds(),
            reply_markup=teclado_cmds(),
            parse_mode='Markdown'
        )

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════


def main():
    init_db()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    application = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern='^spam_gmail$')],
        states={
            CORREO_OBJETIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_correo)],
            CANTIDAD_SPAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad)],
            MENSAJE_SPAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_mensaje_y_enviar)],
        },
        fallbacks=[CommandHandler('cancel', cancelar_spam)],
        per_message=False,
        allow_reentry=True
    )

    application.add_handler(conv)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmds", cmds))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^(actividades|spams_curso|mi_info|ver_cmds|volver)$'))

    print("Bot Jorge iniciado... FINAL")
    application.run_polling()

if __name__ == "__main__":
    main()