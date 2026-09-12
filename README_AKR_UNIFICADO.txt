ARMENKR + AKR CONTENT HQ — BOT UNIFICADO
========================================

Este repo conserva el bot viejo de ARMENKR y agrega las funciones AKR Content HQ.
CORRE UN SOLO BOT y usa el mismo DISCORD_TOKEN de tu bot viejo en Railway.

NUEVOS COMANDOS AKR
-------------------
/setup_akr_content     -> crea/reorganiza la estructura AKR ligera
/archivar_akr_pesado   -> mueve canales extra a 📦 ARCHIVO AKR sin borrar canales
/post_akr_messages     -> publica bienvenida, reglas y ayuda AKR
/server_audit          -> reporte del servidor
/idea                  -> ideas de contenido FC27
/hook                  -> hooks
/guion                 -> guiones
/caption                -> captions + hashtags
/contenido_hoy         -> plan diario
/analizar_noticia      -> convierte una noticia en contenido
/rss_add               -> agrega RSS
/rss_list              -> lista RSS
/rss_check_now         -> revisión manual de RSS

COMANDOS VIEJOS CONSERVADOS
---------------------------
/organizar /paneles /envivo /configurarredes /testbienvenida
/ranking /mipuntos /darvip /quitarvip /darog /quitarog /actualizartop

CAMBIO IMPORTANTE
-----------------
Antes, al reiniciar el bot, el código viejo intentaba reorganizar el servidor automáticamente.
En esta versión eso está DESACTIVADO para no volver a llenar el Discord de canales.

- /organizar = setup viejo, manual
- /setup_akr_content = setup nuevo ligero, manual

RAILWAY
-------
Variables mínimas:
DISCORD_TOKEN = token del BOT VIEJO (no el bot nuevo de pruebas)
GUILD_ID = ID del servidor
NEWS_CHECK_MINUTES = 30

Start Command ya está definido en railway.json:
python main.py

RSS Y PERSISTENCIA
------------------
Por defecto los feeds se guardan en akr_bot_data.json.
Railway puede borrar archivos locales en un redeploy.
Si quieres que los RSS sobrevivan a redeploys, crea un Railway Volume y monta /data,
y agrega variable:
AKR_DATA_DIR=/data

ORDEN RECOMENDADO DESPUÉS DEL DEPLOY
------------------------------------
1. /setup_akr_content
2. /archivar_akr_pesado
3. /post_akr_messages
4. /server_audit

SEGURIDAD
---------
Nunca subas .env ni tokens al repo.
Si un token fue mostrado en un chat o captura, resetea el token antes de usarlo en Railway.
