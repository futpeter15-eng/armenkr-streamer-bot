"""
AKR Content HQ - módulo integrado para ARMENKR Streamer Bot.

Este archivo NO inicia otro bot. Registra comandos y funciones AKR sobre
la misma instancia de discord.py que ya usa el bot principal.
"""

import asyncio
import json
import os
import re
import textwrap
import unicodedata
import urllib.request
import urllib.parse
import html as html_lib
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
import feedparser


# =========================================================
# CONFIGURACIÓN AKR LIGERA
# =========================================================

NEWS_CHECK_MINUTES = max(5, int(os.getenv("NEWS_CHECK_MINUTES", "30") or "30"))
FC_NEWS_CHECK_MINUTES = max(2, int(os.getenv("FC_NEWS_CHECK_MINUTES", "3") or "3"))
STREAM_CHECK_MINUTES = max(1, int(os.getenv("STREAM_CHECK_MINUTES", "2") or "2"))
EA_FC27_NEWS_URL = os.getenv(
    "EA_FC27_NEWS_URL",
    "https://www.ea.com/es/games/ea-sports-fc/fc-27/news?page=1&type=latest",
)
FC_STATE_MARKER = "ARMENKR_FC_STATE:"

# Redes oficiales ARMENKR. Streamcord publica Twitch/YouTube y Noti publica TikTok
# en el mismo canal 🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨. ARMENKR no duplica esos avisos.
ARMENKR_TWITCH = "https://www.twitch.tv/armenkr"
ARMENKR_YOUTUBE = "https://www.youtube.com/@armenkr1901"
ARMENKR_TIKTOK = "https://www.tiktok.com/@armenkr"

# Identidad visual única ARMENKR. Los bots externos (Streamcord, Noti y TweetShift)
# usan las plantillas incluidas más abajo para mantener el mismo lenguaje visual.
BRAND_GOLD = 0xD4AF37
BRAND_RED = 0xD90429
BRAND_DARK = 0x16181D
BRAND_BLUE = 0x2563EB
BRAND_GREEN = 0x19A974
BRAND_ORANGE = 0xF59E0B
BRAND_FOOTER = "ARMENKR • FOCO. DISCIPLINA. VICTORIA."
BRAND_AUTHOR = "ARMENKR // CONTENT HQ"


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("AKR_DATA_DIR", str(BASE_DIR)))
DATA_FILE = DATA_DIR / "akr_bot_data.json"

BLUEPRINT: Dict[str, List[Tuple[str, str]]] = {
    "👑・𝙄𝙉𝙄𝘾𝙄𝙊": [
        ("👋・𝙗𝙞𝙚𝙣𝙫𝙚𝙣𝙞𝙙𝙖", "Bienvenida e información esencial de la comunidad."),
        ("📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨", "Reglas rápidas y selección de roles."),
        ("📢・𝙖𝙣𝙪𝙣𝙘𝙞𝙤𝙨", "Anuncios oficiales y novedades importantes."),
        ("🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨", "Twitch + YouTube por Streamcord · TikTok por Noti · redes oficiales ARMENKR."),
    ],
    "🎬・𝘾𝙊𝙉𝙏𝙀𝙉𝙄𝘿𝙊": [
        ("💡・𝙞𝙙𝙚𝙖𝙨", "Ideas, hooks, guiones y oportunidades de contenido."),
        ("🎞️・𝙘𝙡𝙞𝙥𝙨", "Clips pendientes, material para editar y videos terminados."),
        ("🤖・𝙘𝙤𝙢𝙖𝙣𝙙𝙤𝙨-𝙗𝙤𝙩", "Comandos y herramientas de ARMENKR."),
    ],
    "⚽・𝙁𝘾 27": [
        ("📰・𝙣𝙤𝙩𝙞𝙘𝙞𝙖𝙨-𝙛𝙘", "Noticias oficiales de EA SPORTS FC 27 detectadas automáticamente cada pocos minutos."),
        ("🛠️・𝙥𝙖𝙧𝙘𝙝𝙚𝙨-𝙛𝙘", "Title Updates, gameplay changes, hotfixes y notas de parche oficiales."),
        ("✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "Ultimate Team, The Grounds, campañas, temporadas, recompensas y novedades para contenido rápido."),
    ],
    "💬・𝘾𝙊𝙈𝙐𝙉𝙄𝘿𝘼𝘿": [
        ("💬・𝙘𝙝𝙖𝙩", "Chat general de la comunidad."),
        ("😂・𝙢𝙚𝙢𝙚𝙨-𝙮-𝙘𝙡𝙞𝙥𝙨", "Memes, clips, fails y momentos de la comunidad."),
    ],
    "🎮・𝙂𝘼𝙈𝙄𝙉𝙂": [
        ("🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "GTA, Minecraft, ARK y juegos fuera de FC27."),
    ],
    "🔒・𝘼𝙈𝙄𝙂𝙊𝙎": [
        ("💬・𝙘𝙝𝙖𝙩-𝙖𝙢𝙞𝙜𝙤𝙨", "Chat privado para amigos."),
        ("📅・𝙥𝙡𝙖𝙣𝙚𝙨", "Planes, salidas y organización entre amigos."),
        ("😂・𝙛𝙤𝙩𝙤𝙨-𝙮-𝙢𝙚𝙢𝙚𝙨", "Fotos, memes y cosas del grupo privado."),
    ],
    "🛡️・𝙎𝙏𝘼𝙁𝙁": [
        ("🛡️・𝙨𝙩𝙖𝙛𝙛", "Chat privado de administración y moderación."),
        ("📋・𝙡𝙤𝙜𝙨", "Logs y avisos internos del bot."),
        ("🗄️・𝙙𝙖𝙩𝙤𝙨-𝙗𝙤𝙩", "Datos internos de ARMENKR. No borrar."),
    ],
}

VOICE_CHANNELS = {
    "💬・𝘾𝙊𝙈𝙐𝙉𝙄𝘿𝘼𝘿": ["🔊・𝙜𝙚𝙣𝙚𝙧𝙖𝙡"],
    "🎮・𝙂𝘼𝙈𝙄𝙉𝙂": ["🔊・𝙜𝙖𝙢𝙞𝙣𝙜"],
    "🔒・𝘼𝙈𝙄𝙂𝙊𝙎": ["🔊・𝙨𝙖𝙡𝙖-𝙙𝙚-𝙖𝙢𝙞𝙜𝙤𝙨", "🎮・𝙜𝙖𝙢𝙞𝙣𝙜-𝙖𝙢𝙞𝙜𝙤𝙨"],
}

ROLE_BLUEPRINT = [
    ("🛡️ Admin", 0xE63946),
    ("🔨 Moderador", 0xF77F00),
    ("💗 Amigos", 0xFF69B4),
    ("⚽ FC27", 0x06D6A0),
    ("🔔 Directos", 0xE74C3C),
    ("👥 Comunidad", 0xADB5BD),
]

# Canales viejos que se reutilizan para evitar perder historial cuando sea posible.
OLD_CHANNEL_MAP = {
    "bienvenidas": "👋・𝙗𝙞𝙚𝙣𝙫𝙚𝙣𝙞𝙙𝙖", "bienvenida": "👋・𝙗𝙞𝙚𝙣𝙫𝙚𝙣𝙞𝙙𝙖",
    "normativas": "📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨", "reglas": "📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨", "reglas-y-roles": "📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨", "roles": "📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨",
    "anuncios-akr": "📢・𝙖𝙣𝙪𝙣𝙘𝙞𝙤𝙨", "anuncios": "📢・𝙖𝙣𝙪𝙣𝙘𝙞𝙤𝙨", "noticias-crudas": "📢・𝙖𝙣𝙪𝙣𝙘𝙞𝙤𝙨",
    "redes-sociales": "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨", "redes-oficiales": "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨", "en-vivo": "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨", "redes-y-en-vivo": "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨", "redes-y-directos": "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨",
    "ideas-y-guiones": "💡・𝙞𝙙𝙚𝙖𝙨", "ideas-generadas": "💡・𝙞𝙙𝙚𝙖𝙨", "hooks-y-guiones": "💡・𝙞𝙙𝙚𝙖𝙨", "titulos-captions-hashtags": "💡・𝙞𝙙𝙚𝙖𝙨", "contenido-para-hoy": "💡・𝙞𝙙𝙚𝙖𝙨", "ideas-rapidas": "💡・𝙞𝙙𝙚𝙖𝙨", "ideas-aprobadas": "💡・𝙞𝙙𝙚𝙖𝙨", "pendiente-de-grabar": "💡・𝙞𝙙𝙚𝙖𝙨", "ideas": "💡・𝙞𝙙𝙚𝙖𝙨",
    "pendiente-de-editar": "🎞️・𝙘𝙡𝙞𝙥𝙨", "clips-para-editar": "🎞️・𝙘𝙡𝙞𝙥𝙨", "videos-listos": "🎞️・𝙘𝙡𝙞𝙥𝙨", "publicado-hoy": "🎞️・𝙘𝙡𝙞𝙥𝙨", "miniaturas-overlays": "🎞️・𝙘𝙡𝙞𝙥𝙨", "clips": "🎞️・𝙘𝙡𝙞𝙥𝙨",
    "comandos-akr": "🤖・𝙘𝙤𝙢𝙖𝙣𝙙𝙤𝙨-𝙗𝙤𝙩", "comandos": "🤖・𝙘𝙤𝙢𝙖𝙣𝙙𝙤𝙨-𝙗𝙤𝙩", "comandos-bot": "🤖・𝙘𝙤𝙢𝙖𝙣𝙙𝙤𝙨-𝙗𝙤𝙩",
    "noticias-fc27": "📰・𝙣𝙤𝙩𝙞𝙘𝙞𝙖𝙨-𝙛𝙘", "noticias-fc": "📰・𝙣𝙤𝙩𝙞𝙘𝙞𝙖𝙨-𝙛𝙘",
    "parches-fc": "🛠️・𝙥𝙖𝙧𝙘𝙝𝙚𝙨-𝙛𝙘", "patch-notes": "🛠️・𝙥𝙖𝙧𝙘𝙝𝙚𝙨-𝙛𝙘",
    "fc27": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "ultimate-team": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "the-grounds": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "tacticas": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "noticias-ultimate-team": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "noticias-the-grounds": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤", "nuevo-contenido": "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤",
    "chat": "💬・𝙘𝙝𝙖𝙩", "clips-comunidad": "😂・𝙢𝙚𝙢𝙚𝙨-𝙮-𝙘𝙡𝙞𝙥𝙨", "memes": "😂・𝙢𝙚𝙢𝙚𝙨-𝙮-𝙘𝙡𝙞𝙥𝙨", "memes-fc": "😂・𝙢𝙚𝙢𝙚𝙨-𝙮-𝙘𝙡𝙞𝙥𝙨", "memes-y-clips": "😂・𝙢𝙚𝙢𝙚𝙨-𝙮-𝙘𝙡𝙞𝙥𝙨",
    "gta": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "gta-clips": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "coches-y-tuning": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "ark": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "ark-parches": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "minecraft": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨", "otros-juegos": "🎮・𝙤𝙩𝙧𝙤𝙨-𝙟𝙪𝙚𝙜𝙤𝙨",
    "chat-admins": "🛡️・𝙨𝙩𝙖𝙛𝙛", "control-staff": "🛡️・𝙨𝙩𝙖𝙛𝙛", "comandos-staff": "🛡️・𝙨𝙩𝙖𝙛𝙛", "staff": "🛡️・𝙨𝙩𝙖𝙛𝙛",
    "warns": "📋・𝙡𝙤𝙜𝙨", "logs": "📋・𝙡𝙤𝙜𝙨", "datos-bot": "🗄️・𝙙𝙖𝙩𝙤𝙨-𝙗𝙤𝙩",
    "chat-amigos": "💬・𝙘𝙝𝙖𝙩-𝙖𝙢𝙞𝙜𝙤𝙨", "planes": "📅・𝙥𝙡𝙖𝙣𝙚𝙨", "fotos-y-memes": "😂・𝙛𝙤𝙩𝙤𝙨-𝙮-𝙢𝙚𝙢𝙚𝙨",
}

# Categorías de setups anteriores. /setup_discord_limpio elimina las que sobren.
LEGACY_CATEGORIES = {
    "👑 AKR HQ", "🎬・𝘾𝙊𝙉𝙏𝙀𝙉𝙄𝘿𝙊", "⚽ FC27", "💬・𝘾𝙊𝙈𝙐𝙉𝙄𝘿𝘼𝘿", "🎮 EXTRA", "🛡️・𝙎𝙏𝘼𝙁𝙁", "👑・𝙄𝙉𝙄𝘾𝙄𝙊", "🎬・𝘾𝙊𝙉𝙏𝙀𝙉𝙄𝘿𝙊", "💬・𝘾𝙊𝙈𝙐𝙉𝙄𝘿𝘼𝘿", "🎮・𝙂𝘼𝙈𝙄𝙉𝙂", "🔒・𝘼𝙈𝙄𝙂𝙊𝙎", "🛡️・𝙎𝙏𝘼𝙁𝙁",
    "📌 CONTENT COMMAND CENTER", "📰 NEWS ROOM", "🎬 CONTENT LAB", "⚽ FC27 COMPETITIVO",
    "📅 PRODUCCIÓN AKR", "🎮 OTROS JUEGOS", "📦 ARCHIVO AKR",
    "━━ 📍・SERVIDOR ━━", "━━ 🚀・ENTRETENIMIENTO ━━",
    "━━ 💗 Amigos ━━", "━━ ⛏️ Minecraft ━━", "━━ 🦖・DODÓFILOS | ARK ━━",
    "━━ 🚗 GTA ━━", "━━ 🤖 Bots ━━", "━━ 💎 VIP LOUNGE ━━",
}

# Nombres conocidos de canales viejos/redundantes. Se eliminan si no fueron reutilizados.
LEGACY_CHANNELS = set(OLD_CHANNEL_MAP.keys()) | {
    "cumpleanos", "cumpleaños", "niveles", "niveles-bot", "dibujos", "musica-bot", "música-bot",
    "config-bots", "sorteos-vip", "calendario-akr", "pendiente-de-subir", "resultados-semana",
    "voz-general", "voz-staff", "voz", "general-voz",
}

HOOK_BANK = [
    "FC27 no se improvisa.",
    "Este error te cuesta partidos.",
    "No fue suerte, fue lectura de juego.",
    "Así piensa un jugador competitivo.",
    "Esto separa a los buenos de los normales.",
    "No juego por clips, juego para ganar.",
    "Si juegas FC27, mira esto.",
    "El detalle que casi nadie corrige.",
    "Así se gana un partido cerrado.",
    "La paciencia también gana partidos.",
    "Esto lo voy a perfeccionar en FC27.",
    "No compitas tilteado.",
    "El mercado castiga al desesperado.",
    "No gastes monedas sin pensar.",
    "The Grounds se juega con cabeza.",
    "Ultimate Team no es solo cartas, es estrategia.",
]

CLOSERS = [
    "AKR no juega por jugar.",
    "Foco. Disciplina. Victoria.",
    "Pequeños detalles ganan partidos.",
    "Camino competitivo a FC27.",
    "El que analiza, mejora.",
    "Nos vemos en el próximo clip.",
]

HASHTAGS_BASE = "#FC27 #EASportsFC #UltimateTeam #TheGrounds #FIFAClips #GamingLatino #AKR #RoadToFC27 #TikTokGaming #YouTubeShorts"


# =========================================================
# UTILIDADES
# =========================================================

def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in normalized if not unicodedata.combining(c))
    ascii_name = ascii_name.lower().strip()
    ascii_name = re.sub(r"[^a-z0-9áéíóúñü\-]+", "-", ascii_name)
    return re.sub(r"-+", "-", ascii_name).strip("-")


def get_text_channel_by_name(guild: discord.Guild, name: str) -> Optional[discord.TextChannel]:
    target = slugify(name)
    for ch in guild.text_channels:
        if slugify(ch.name) == target:
            return ch
    return None


def get_category_by_name(guild: discord.Guild, name: str) -> Optional[discord.CategoryChannel]:
    target = slugify(name)
    for cat in guild.categories:
        if slugify(cat.name) == target:
            return cat
    return None


def get_voice_channel_by_name(guild: discord.Guild, name: str) -> Optional[discord.VoiceChannel]:
    target = slugify(name)
    for ch in guild.voice_channels:
        if slugify(ch.name) == target:
            return ch
    return None


def split_message(text: str, limit: int = 1900) -> List[str]:
    chunks = []
    while len(text) > limit:
        idx = text.rfind("\n", 0, limit)
        if idx == -1:
            idx = limit
        chunks.append(text[:idx])
        text = text[idx:].lstrip()
    chunks.append(text)
    return chunks


def load_data() -> dict:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    if not DATA_FILE.exists():
        return {"feeds": [], "seen": {}}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"feeds": [], "seen": {}}


def save_data(data: dict) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"AKR RSS: no pude guardar datos: {exc}")


def manage_guild_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        perms = interaction.user.guild_permissions if interaction.guild else None
        return bool(perms and (perms.manage_guild or perms.administrator))
    return app_commands.check(predicate)


async def send_text_response(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    for chunk in split_message(text):
        await interaction.followup.send(chunk)


def brand_embed(
    guild: Optional[discord.Guild],
    *,
    title: str,
    description: str = "",
    colour: int = BRAND_GOLD,
    url: Optional[str] = None,
    author: str = BRAND_AUTHOR,
    footer: str = BRAND_FOOTER,
) -> discord.Embed:
    """Crea embeds ARMENKR con una identidad visual uniforme."""
    embed = discord.Embed(
        title=title,
        description=description,
        url=url,
        colour=discord.Colour(colour),
    )
    icon_url = None
    if guild and guild.icon:
        icon_url = guild.icon.url
    embed.set_author(name=author, icon_url=icon_url)
    embed.set_footer(text=footer)
    return embed


def _staff_overwrites_light(guild: discord.Guild) -> dict:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
    }
    if guild.me:
        overwrites[guild.me] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True, manage_channels=True
        )
    for role in guild.roles:
        s = slugify(role.name)
        if role.permissions.administrator or s in {"admin", "moderador", "staff", "akr"} or "admin" in s or "moderador" in s:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
    return overwrites


def _friends_overwrites_light(guild: discord.Guild) -> dict:
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
    }
    if guild.me:
        overwrites[guild.me] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True, manage_channels=True
        )
    for role in guild.roles:
        s = slugify(role.name)
        if role.permissions.administrator or "admin" in s or "moderador" in s or "amigos" in s:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True
            )
    return overwrites


# =========================================================
# PLANTILLAS DE CONTENIDO SIN IA
# =========================================================

def topic_slug(tema: str) -> str:
    t = tema.lower()
    if "ultimate" in t or " ut " in f" {t} " or "carta" in t or "mercado" in t:
        return "ultimate"
    if "ground" in t or "build" in t:
        return "grounds"
    if "def" in t or "tact" in t or "formacion" in t or "formación" in t:
        return "competitivo"
    if "stream" in t or "tiktok" in t or "youtube" in t:
        return "streaming"
    return "general"


def generate_ideas_template(tema: str) -> str:
    ideas_by_kind = {
        "ultimate": [
            ("No compres por hype", "No gastes tus monedas antes de ver esto.", "Explica por qué al inicio de UT muchos compran mal y cómo esperar mejores precios."),
            ("Equipo barato competitivo", "Este equipo barato puede competir desde el día uno.", "Muestra una plantilla humilde y explica ritmo, química, defensa y costo."),
            ("Cartas que sí valen", "No todas las cartas caras son buenas.", "Compara una carta popular con una opción barata y eficiente."),
            ("Mercado sin pánico", "El mercado castiga al desesperado.", "Explica cuándo vender, cuándo esperar y por qué no comprar por emoción."),
            ("Road to Glory AKR", "Voy a construir mi club sin excusas.", "Presenta objetivos de la serie: Rivals, Champions, upgrades y reglas."),
        ],
        "grounds": [
            ("Build competitiva", "Esta build no es para lucirse, es para ganar.", "Muestra atributos clave según posición."),
            ("Errores en The Grounds", "The Grounds se pierde por ego, no por falta de skill.", "Habla de jugar solo, no soltar balón y abandonar posición."),
            ("Lectura de espacios", "No corrí por correr, ataqué el espacio correcto.", "Explica movimiento sin balón, pase simple y timing."),
            ("Rol de equipo", "Tu build no sirve si no entiendes tu rol.", "Explica cómo jugar según posición y cuándo apoyar o esperar."),
            ("Ranked grind", "Cada partido tiene que enseñarme algo.", "Cuenta tu progreso y una lección por derrota."),
        ],
        "competitivo": [
            ("No sacar centrales", "Este error defensivo regala partidos.", "Muestra por qué sacar centrales abre espacios y cómo cerrar líneas."),
            ("Paciencia en ataque", "No todos los ataques son para correr.", "Explica pausa, pase atrás y esperar movimiento."),
            ("Timed finishing", "La diferencia está en la definición.", "Habla de practicar tiros verdes y elegir mejor el ángulo."),
            ("Mentalidad anti-tilt", "Perder tilteado te hace perder dos veces.", "Explica cortar racha, analizar y volver."),
            ("Análisis de derrota", "No perdí por mala suerte, perdí por esto.", "Revisa un error específico y cómo corregirlo."),
        ],
        "streaming": [
            ("Contenido diario", "No espero FC27, estoy construyendo antes.", "Explica tu rutina de clips, streams y aprendizaje."),
            ("Hook competitivo", "Los primeros dos segundos deciden el video.", "Muestra 3 hooks y cuál usarías para un clip."),
            ("Setup de creador", "No necesito el setup perfecto para empezar.", "Muestra lo básico: mic, cámara, overlay, Discord y calendario."),
            ("Serie AKR", "Este no es un canal random, es una historia.", "Presenta Road to FC27 como serie con metas semanales."),
            ("Comunidad", "Quiero una comunidad que compita y cree.", "Invita a clips, ideas, preguntas y retos."),
        ],
        "general": [
            ("Road to FC27", "FC27 todavía no sale y yo ya empecé.", "Presenta tu camino competitivo y tus metas."),
            ("Errores que corregiré", "Estos errores no los repito en FC27.", "Lista 3 errores de gameplay o mentalidad."),
            ("Rutina de mejora", "Voy a entrenar FC como si fuera deporte real.", "Explica defensa, definición, tácticas y análisis."),
            ("Clip con análisis", "Este clip tiene más lectura de lo que parece.", "Muestra una jugada y explica la decisión clave."),
            ("Meta AKR", "No quiero ser uno más jugando FC.", "Define tu identidad: competitivo, latino, constante."),
        ],
    }
    selected = ideas_by_kind[topic_slug(tema)]
    lines = [f"🎬 **Ideas AKR para:** {tema}\n"]
    for i, (title, hook, body) in enumerate(selected, start=1):
        lines += [
            f"**{i}. {title}**",
            f"Hook: {hook}",
            "Estructura: 0-2s hook → 3-15s contexto → 15-25s explicación → cierre con pregunta.",
            f"Idea: {body}",
            "Pregunta final: ¿Ustedes harían lo mismo o jugarían diferente?\n",
        ]
    return "\n".join(lines)


def generate_hooks_template(tema: str) -> str:
    return f"⚡ **Hooks competitivos para:** {tema}\n\n" + "\n".join(f"{i}. {h}" for i, h in enumerate(HOOK_BANK, 1))


def generate_script_template(tema: str, duracion: str) -> str:
    hook = HOOK_BANK[0]
    tl = tema.lower()
    if "def" in tl:
        hook = "Este error defensivo te cuesta partidos."
    elif "ultimate" in tl or "mercado" in tl:
        hook = "No gastes tus monedas antes de ver esto."
    elif "ground" in tl:
        hook = "The Grounds se juega con cabeza, no con ego."
    return f"""🎥 **Guion AKR — {tema} — {duracion}**

**0-2s | Hook**
{hook}

**3-8s | Contexto**
Estoy preparándome para FC27 con mentalidad competitiva. No quiero llegar a aprender desde cero, quiero llegar listo.

**9-20s | Punto principal**
El enfoque de hoy es: {tema}. La idea no es jugar por jugar, es identificar un detalle, corregirlo y convertirlo en ventaja.

**21-30s | Cierre**
{CLOSERS[2]} {CLOSERS[1]}

**Texto en pantalla**
AKR Road to FC27\nNo juego por clips, juego para ganar.

**Caption**
Preparándome para FC27 desde antes. Cada detalle cuenta.

**Hashtags**
{HASHTAGS_BASE}"""


def generate_caption_template(tema: str) -> str:
    return f"""📱 **Títulos para:** {tema}
1. FC27 no se improvisa
2. Este detalle gana partidos
3. AKR Road to FC27
4. No juego por clips, juego para ganar
5. Así se prepara un jugador competitivo
6. El error que no voy a repetir en FC27
7. Ultimate Team con cabeza, no con emoción
8. The Grounds es mentalidad y lectura
9. Cada derrota deja una lección
10. Foco. Disciplina. Victoria.

**Captions**
1. Preparándome para FC27 desde ya. No hay excusas.
2. Pequeños detalles ganan partidos.
3. AKR Road to FC27 empieza antes del lanzamiento.
4. No se trata de jugar más, se trata de jugar mejor.
5. Competir también es analizar.

**Hashtags**
{HASHTAGS_BASE}"""


def generate_today_template() -> str:
    return f"""📅 **Plan de contenido AKR para hoy**

**TikTok/Short 1 — Road to FC27**
Hook: FC27 todavía no sale y yo ya empecé.
Idea: habla de tu meta competitiva y tu enfoque en Ultimate Team + The Grounds.

**TikTok/Short 2 — Error competitivo**
Hook: Este error defensivo te cuesta partidos.
Idea: muestra un clip viejo o explica un error que vas a corregir.

**TikTok/Short 3 — Ultimate Team**
Hook: No gastes monedas por emoción.
Idea: video rápido sobre jugar con cabeza desde el día uno.

**Video largo YouTube**
Título: Mi plan para dominar FC27 como creador competitivo.

**Tema para stream**
Preparación competitiva para FC27: analizar clips, hablar de metas y jugar para corregir errores.

**Frase del día**
No juego por clips, juego para ganar.

**Hashtags**
{HASHTAGS_BASE}"""


def analyze_news_template(noticia: str) -> str:
    clean = textwrap.shorten(noticia.replace("\n", " "), width=500, placeholder="...")
    return f"""📰 **Noticia convertida en contenido AKR**

**Texto base**
{clean}

**Ángulo competitivo**
¿Cómo afecta esto a jugadores que quieren competir en FC27, Ultimate Team o The Grounds?

**Idea TikTok 1**
Hook: Si esto cambia el gameplay, muchos van a sufrir.
Guion: explica el cambio, qué puede afectar y cómo te vas a preparar.

**Idea TikTok 2**
Hook: Esto puede cambiar la forma de jugar FC27.
Guion: menciona el impacto y pregunta a la comunidad qué opina.

**Idea TikTok 3**
Hook: No todos van a adaptarse a este cambio.
Guion: enfoque de mentalidad competitiva y adaptación rápida.

**Caption**
Adaptarse rápido también es competir.

**Hashtags**
{HASHTAGS_BASE}"""



# =========================================================
# MONITOR OFICIAL FC27 + DIRECTOS
# =========================================================

class _EAArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_href = None
        self.current_text = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href", "")
        if "/games/ea-sports-fc/fc-27/news/" in href:
            self.current_href = href
            self.current_text = []

    def handle_data(self, data):
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current_href:
            title = re.sub(r"\s+", " ", " ".join(self.current_text)).strip()
            href = self.current_href
            self.current_href = None
            self.current_text = []
            if len(title) >= 8:
                if href.startswith("/"):
                    href = "https://www.ea.com" + href
                self.items.append((title, href))


def _http_text(url: str, *, timeout: int = 20) -> tuple[str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (ARMENKR Discord Bot; +https://discord.com)",
            "Accept-Language": "es,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        final_url = response.geturl()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace"), final_url


def _http_json(url: str, *, headers: Optional[dict] = None, data: Optional[bytes] = None, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def fetch_ea_fc27_articles() -> List[Tuple[str, str]]:
    html, _ = _http_text(EA_FC27_NEWS_URL)
    parser = _EAArticleParser()
    parser.feed(html)
    seen = set()
    items = []
    for title, url in parser.items:
        url = url.split("?")[0].rstrip("/")
        if url in seen:
            continue
        seen.add(url)
        items.append((html_lib.unescape(title), url))
    return items[:25]


def classify_fc_article(title: str) -> str:
    t = title.lower()
    patch_words = (
        "patch", "title update", "notas del parche", "actualización del juego",
        "actualizacion del juego", "game update", "actualización de jugabilidad",
        "actualizacion de jugabilidad",
    )
    content_words = (
        "ultimate team", "football ultimate team", " fut ", "temporada", "season",
        "campaña", "campaign", "recompensa", "reward", "the grounds", "clubes", "clubs",
        "valoraciones", "ratings", "evolución", "evolution", "icon", "hero", "soundtrack",
        "modo carrera", "career", "pretemporada", "promo",
    )
    padded = f" {t} "
    if any(word in padded for word in patch_words):
        return "patch"
    if any(word in padded for word in content_words):
        return "content"
    return "news"


def _extract_meta(html: str, prop: str) -> Optional[str]:
    patterns = [
        rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(prop)}["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.I)
        if m:
            return html_lib.unescape(m.group(1))
    return None


def _stream_slug(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    parts = [p for p in parsed.path.split("/") if p]
    return parts[0].lstrip("@") if parts else ""


def check_youtube_live(url: str) -> dict:
    base = url.rstrip("/")
    if not base.endswith("/live"):
        base += "/live"
    html, final_url = _http_text(base)
    live = "isLiveBroadcast" in html or '"isLive":true' in html or '"isLiveNow":true' in html
    title = _extract_meta(html, "og:title") or "ARMENKR está en vivo"
    thumb = _extract_meta(html, "og:image")
    watch_url = final_url if "watch" in final_url else base
    return {"supported": True, "live": bool(live), "title": title, "url": watch_url, "thumbnail": thumb}


def check_kick_live(url: str) -> dict:
    slug = _stream_slug(url)
    if not slug:
        return {"supported": False, "reason": "URL de Kick inválida"}
    data = _http_json(f"https://kick.com/api/v2/channels/{urllib.parse.quote(slug)}", headers={"User-Agent": "Mozilla/5.0"})
    livestream = data.get("livestream") or None
    if not livestream:
        return {"supported": True, "live": False, "url": url}
    return {
        "supported": True,
        "live": True,
        "title": livestream.get("session_title") or livestream.get("slug") or "ARMENKR está en vivo",
        "url": url,
        "thumbnail": (livestream.get("thumbnail") or {}).get("url") if isinstance(livestream.get("thumbnail"), dict) else None,
    }


def _twitch_app_token() -> Optional[str]:
    client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
    secret = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    if not client_id or not secret:
        return None
    body = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": secret,
        "grant_type": "client_credentials",
    }).encode()
    data = _http_json("https://id.twitch.tv/oauth2/token", data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    return data.get("access_token")


def check_twitch_live(url: str) -> dict:
    login = _stream_slug(url)
    client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
    if not login or not client_id:
        return {"supported": False, "reason": "Faltan TWITCH_CLIENT_ID/TWITCH_CLIENT_SECRET en Railway"}
    token = _twitch_app_token()
    if not token:
        return {"supported": False, "reason": "No pude autenticar con Twitch"}
    endpoint = "https://api.twitch.tv/helix/streams?" + urllib.parse.urlencode({"user_login": login})
    data = _http_json(endpoint, headers={"Authorization": f"Bearer {token}", "Client-Id": client_id})
    rows = data.get("data") or []
    if not rows:
        return {"supported": True, "live": False, "url": url}
    row = rows[0]
    thumb = (row.get("thumbnail_url") or "").replace("{width}", "1280").replace("{height}", "720")
    return {"supported": True, "live": True, "title": row.get("title") or "ARMENKR está en vivo", "url": url, "thumbnail": thumb}

# =========================================================
# REGISTRO EN EL BOT EXISTENTE
# =========================================================

def register_akr_content(bot, guild_id: int):
    """Registra todos los comandos AKR en la MISMA instancia del bot ARMENKR."""

    stream_last_state: Dict[str, bool] = {}

    async def _load_marker(guild: discord.Guild, marker: str) -> Optional[dict]:
        ch = get_text_channel_by_name(guild, "📋・𝙡𝙤𝙜𝙨")
        if not ch:
            return None
        try:
            async for msg in ch.history(limit=150):
                if msg.author == guild.me and msg.content.startswith(marker):
                    raw = msg.content[len(marker):]
                    try:
                        value = json.loads(raw)
                        return value if isinstance(value, dict) else None
                    except json.JSONDecodeError:
                        return None
        except discord.HTTPException:
            return None
        return None

    async def _save_marker(guild: discord.Guild, marker: str, data: dict) -> None:
        ch = get_text_channel_by_name(guild, "📋・𝙡𝙤𝙜𝙨")
        if not ch:
            return
        payload = marker + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if len(payload) > 1900:
            payload = payload[:1890]
        try:
            async for msg in ch.history(limit=150):
                if msg.author == guild.me and msg.content.startswith(marker):
                    await msg.edit(content=payload)
                    return
            await ch.send(payload)
        except discord.HTTPException:
            pass

    async def check_fc_news_once() -> int:
        await bot.wait_until_ready()
        guild = bot.get_guild(guild_id)
        if not guild:
            return 0

        try:
            articles = await asyncio.to_thread(fetch_ea_fc27_articles)
        except Exception as exc:
            print(f"AKR FC monitor error leyendo EA: {type(exc).__name__}: {exc}")
            return 0
        if not articles:
            return 0

        hashes = {hashlib.sha1(url.encode("utf-8")).hexdigest(): (title, url) for title, url in articles}
        state = await _load_marker(guild, FC_STATE_MARKER)

        # Primera ejecución: toma una foto del estado actual para no llenar Discord con noticias antiguas.
        # El comando /fc_check_now seguirá confirmando que el monitor quedó activo.
        if not state:
            await _save_marker(guild, FC_STATE_MARKER, {"hashes": list(hashes.keys())[:25]})
            print(f"⚽ FC monitor inicializado con {len(hashes)} artículos actuales.")
            return 0

        seen = set(state.get("hashes", []))
        new_rows = [(title, url, h) for h, (title, url) in hashes.items() if h not in seen]
        if not new_rows:
            return 0

        role = discord.utils.get(guild.roles, name="⚽ FC27")
        ideas_ch = get_text_channel_by_name(guild, "💡・𝙞𝙙𝙚𝙖𝙨")
        sent = 0

        # La web suele devolver lo más nuevo primero; publicamos del más antiguo al más nuevo.
        for title, url, h in reversed(new_rows):
            kind = classify_fc_article(title)
            if kind == "patch":
                ch = get_text_channel_by_name(guild, "🛠️・𝙥𝙖𝙧𝙘𝙝𝙚𝙨-𝙛𝙘")
                label, emoji, colour = "PARCHE / UPDATE", "🛠️", 0xE67E22
            elif kind == "content":
                ch = get_text_channel_by_name(guild, "✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤")
                label, emoji, colour = "NUEVO CONTENIDO", "✨", 0x2ECC71
            else:
                ch = get_text_channel_by_name(guild, "📰・𝙣𝙤𝙩𝙞𝙘𝙞𝙖𝙨-𝙛𝙘")
                label, emoji, colour = "NOTICIA FC27", "📰", 0x3498DB

            if not ch:
                continue

            embed = brand_embed(
                guild,
                title=f"{emoji}・𝙁𝘾 27 // {label}",
                description=(
                    f"**{title}**\n\n"
                    "Información detectada desde la fuente oficial de EA SPORTS FC. "
                    "Confirma el artículo y conviértelo en contenido mientras el tema está fresco."
                ),
                url=url,
                colour=colour,
                author="ARMENKR // FC27 INTEL",
            )
            embed.add_field(name="⚡ ACCIÓN RÁPIDA", value="Lee → confirma → resume → da tu opinión → publica.", inline=False)
            embed.add_field(name="🔗 FUENTE", value=f"[Abrir publicación oficial]({url})", inline=False)
            try:
                await ch.send(
                    content=role.mention if role else None,
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
                )
                sent += 1
            except discord.HTTPException:
                continue

            if ideas_ch:
                idea_embed = brand_embed(
                    guild,
                    title="⚡・𝘾𝙊𝙉𝙏𝙀𝙉𝙏 𝘼𝙇𝙀𝙍𝙏 // 𝙁𝘾 27",
                    description=f"**{title}**\n\n[Ver fuente]({url})",
                    colour=BRAND_GOLD,
                    author="ARMENKR // CONTENT OPS",
                )
                idea_embed.add_field(name="🎣 HOOK A", value="Esto acaba de cambiar en FC27 y tienes que saberlo.", inline=False)
                idea_embed.add_field(name="🎣 HOOK B", value="EA acaba de anunciar esto para FC27.", inline=False)
                idea_embed.add_field(name="🎬 FORMATO", value="0–2s hook → 3–15s qué cambió → 15–30s por qué importa → opinión/pregunta.", inline=False)
                try:
                    await ideas_ch.send(embed=idea_embed)
                except discord.HTTPException:
                    pass

        combined = list(hashes.keys())[:25]
        await _save_marker(guild, FC_STATE_MARKER, {"hashes": combined})
        return sent

    async def _load_stream_config(guild: discord.Guild) -> dict:
        return (await _load_marker(guild, STREAM_CONFIG_MARKER)) or {}

    async def _save_stream_config(guild: discord.Guild, data: dict) -> None:
        await _save_marker(guild, STREAM_CONFIG_MARKER, data)

    async def _stream_status(platform: str, url: str) -> dict:
        if platform == "youtube":
            return await asyncio.to_thread(check_youtube_live, url)
        if platform == "kick":
            return await asyncio.to_thread(check_kick_live, url)
        if platform == "twitch":
            return await asyncio.to_thread(check_twitch_live, url)
        if platform == "tiktok":
            return {"supported": False, "reason": "TikTok no ofrece un detector público estable para este bot; usa /envivo para TikTok."}
        return {"supported": False, "reason": "Plataforma no compatible"}

    async def _send_live_alert(guild: discord.Guild, platform: str, info: dict, configured_url: str) -> None:
        ch = get_text_channel_by_name(guild, "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨")
        if not ch:
            return
        role = discord.utils.get(guild.roles, name="🔔 Directos")
        live_url = info.get("url") or configured_url
        embed = discord.Embed(
            title=f"🔴 ARMENKR ESTÁ EN VIVO — {platform.upper()}",
            description=f"**{info.get('title') or 'Ya estamos en directo.'}**\n\nCaigan al stream. 🔥",
            url=live_url,
            colour=discord.Colour.red(),
        )
        if info.get("thumbnail"):
            embed.set_image(url=info["thumbnail"])
        embed.add_field(name="▶️ Entrar al directo", value=f"[ABRIR STREAM]({live_url})", inline=False)
        embed.set_footer(text="ARMENKR • Directos automáticos")
        await ch.send(
            content=role.mention if role else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
        )

    async def check_streams_once(*, alert_transitions: bool = True) -> dict:
        await bot.wait_until_ready()
        guild = bot.get_guild(guild_id)
        if not guild:
            return {}
        config = await _load_stream_config(guild)
        results = {}
        for platform in ("twitch", "youtube", "kick", "tiktok"):
            url = (config.get(platform) or "").strip()
            if not url:
                continue
            try:
                info = await _stream_status(platform, url)
            except Exception as exc:
                info = {"supported": False, "reason": f"{type(exc).__name__}: {exc}"}
            results[platform] = info
            if not info.get("supported"):
                continue
            live = bool(info.get("live"))
            previous = stream_last_state.get(platform)
            stream_last_state[platform] = live
            # No avisa al arrancar para evitar duplicados; solo cuando detecta OFFLINE -> LIVE.
            if alert_transitions and previous is False and live:
                try:
                    await _send_live_alert(guild, platform, info, url)
                except discord.HTTPException:
                    pass
        return results

    async def check_rss_feeds_once() -> int:
        await bot.wait_until_ready()
        data = load_data()
        feeds = data.get("feeds", [])
        seen = data.setdefault("seen", {})
        new_count = 0

        for feed in feeds:
            url = feed.get("url")
            channel_id = feed.get("channel_id")
            name = feed.get("name", "Fuente")
            channel = bot.get_channel(channel_id)
            if not url or not isinstance(channel, discord.TextChannel):
                continue

            parsed = await asyncio.to_thread(feedparser.parse, url)
            entries = parsed.entries[:5]
            feed_seen = set(seen.setdefault(url, []))

            for entry in reversed(entries):
                entry_id = entry.get("id") or entry.get("link") or entry.get("title")
                if not entry_id or entry_id in feed_seen:
                    continue

                title = entry.get("title", "Sin título")
                link = entry.get("link", "")
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))
                summary = textwrap.shorten(summary, width=450, placeholder="...")

                embed = brand_embed(
                    channel.guild,
                    title="📰・𝙄𝙉𝙏𝙀𝙇 // NUEVA PUBLICACIÓN",
                    description=f"**{title}**\n\n{summary or 'Nueva publicación detectada.'}",
                    colour=BRAND_BLUE,
                    url=link or None,
                    author=f"ARMENKR // {name.upper()}",
                )
                if link:
                    embed.add_field(name="🔗 FUENTE", value=f"[Abrir publicación]({link})", inline=False)
                try:
                    await channel.send(embed=embed)
                except discord.HTTPException:
                    continue

                ideas_ch = get_text_channel_by_name(channel.guild, "💡・𝙞𝙙𝙚𝙖𝙨")
                if ideas_ch:
                    template = analyze_news_template(f"{title}\n{summary}\n{link}")
                    try:
                        await ideas_ch.send("**Idea automática desde noticia**\n" + split_message(template)[0])
                    except discord.HTTPException:
                        pass

                feed_seen.add(entry_id)
                seen[url] = list(feed_seen)[-100:]
                new_count += 1
                await asyncio.sleep(0.5)

        save_data(data)
        return new_count

    async def _apply_clean_layout(guild: discord.Guild, *, delete_extras: bool = False):
        report = []
        created_categories = created_channels = moved_channels = created_roles = created_voice = 0
        deleted_channels = deleted_categories = 0
        used_channel_ids = set()
        used_voice_ids = set()

        # Roles mínimos. Reutilizamos y renombramos los roles antiguos para quitar
        # las letras Unicode "fancy" sin duplicar roles ni perder miembros/permisos.
        for role_name, color in ROLE_BLUEPRINT:
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                target_slug = slugify(role_name)
                role = next((r for r in guild.roles if r.name != "@everyone" and slugify(r.name) == target_slug), None)
            if role is not None:
                try:
                    if role.name != role_name:
                        await role.edit(name=role_name, colour=discord.Colour(color), reason="ARMENKR estilo tipográfico limpio")
                except discord.Forbidden:
                    report.append(f"No pude renombrar el rol {role.name}. Revisa Manage Roles y la posición del bot.")
                except Exception as exc:
                    report.append(f"Error actualizando rol {role.name}: {exc}")
                continue
            try:
                await guild.create_role(name=role_name, colour=discord.Colour(color), reason="ARMENKR Discord limpio")
                created_roles += 1
            except discord.Forbidden:
                report.append(f"No pude crear el rol {role_name}. Revisa Manage Roles y la posición del bot.")
            except Exception as exc:
                report.append(f"Error creando rol {role_name}: {exc}")

        # Canales especiales de Discord que conviene reutilizar si existen.
        special_candidates = {
            "📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨": getattr(guild, "rules_channel", None),
            "📢・𝙖𝙣𝙪𝙣𝙘𝙞𝙤𝙨": getattr(guild, "public_updates_channel", None),
        }

        for category_name, channels in BLUEPRINT.items():
            category = get_category_by_name(guild, category_name)
            if category is None:
                try:
                    kwargs = {}
                    if category_name == "🛡️・𝙎𝙏𝘼𝙁𝙁":
                        kwargs["overwrites"] = _staff_overwrites_light(guild)
                    elif category_name == "🔒・𝘼𝙈𝙄𝙂𝙊𝙎":
                        kwargs["overwrites"] = _friends_overwrites_light(guild)
                    category = await guild.create_category(category_name, reason="ARMENKR Discord limpio", **kwargs)
                    created_categories += 1
                except Exception as exc:
                    report.append(f"No pude crear categoría {category_name}: {exc}")
                    continue
            else:
                try:
                    edit_kwargs = {"name": category_name, "reason": "ARMENKR diseño limpio"}
                    if category_name == "🛡️・𝙎𝙏𝘼𝙁𝙁":
                        edit_kwargs["overwrites"] = _staff_overwrites_light(guild)
                    elif category_name == "🔒・𝘼𝙈𝙄𝙂𝙊𝙎":
                        edit_kwargs["overwrites"] = _friends_overwrites_light(guild)
                    await category.edit(**edit_kwargs)
                except Exception as exc:
                    report.append(f"No pude actualizar {category_name}: {exc}")

            for channel_name, topic in channels:
                existing = get_text_channel_by_name(guild, channel_name)
                if existing and existing.id in used_channel_ids:
                    existing = None

                # Primero intentamos aprovechar canales especiales (reglas/updates/system).
                if existing is None:
                    special = special_candidates.get(channel_name)
                    if isinstance(special, discord.TextChannel) and special.id not in used_channel_ids:
                        existing = special

                # Después reutilizamos aliases antiguos para conservar historial cuando sea posible.
                if existing is None:
                    aliases = [old_slug for old_slug, desired in OLD_CHANNEL_MAP.items() if desired == channel_name]
                    old_channel = next(
                        (ch for ch in guild.text_channels if ch.id not in used_channel_ids and slugify(ch.name) in aliases),
                        None,
                    )
                    if old_channel:
                        existing = old_channel

                overwrites = None
                if category_name == "🛡️・𝙎𝙏𝘼𝙁𝙁":
                    overwrites = _staff_overwrites_light(guild)
                elif category_name == "🔒・𝘼𝙈𝙄𝙂𝙊𝙎":
                    overwrites = _friends_overwrites_light(guild)

                if existing is None:
                    try:
                        kwargs = {"category": category, "topic": topic, "reason": "ARMENKR Discord limpio"}
                        if overwrites is not None:
                            kwargs["overwrites"] = overwrites
                        existing = await guild.create_text_channel(channel_name, **kwargs)
                        created_channels += 1
                    except Exception as exc:
                        report.append(f"No pude crear #{channel_name}: {exc}")
                        continue
                else:
                    try:
                        kwargs = {"name": channel_name, "category": category, "topic": topic, "reason": "ARMENKR Discord limpio"}
                        if overwrites is not None:
                            kwargs["overwrites"] = overwrites
                        await existing.edit(**kwargs)
                        moved_channels += 1
                    except Exception as exc:
                        report.append(f"No pude mover/renombrar #{existing.name}: {exc}")
                used_channel_ids.add(existing.id)

        # Orden visual de categorías para que el servidor quede limpio y consistente.
        for pos, category_name in enumerate(BLUEPRINT.keys()):
            category = get_category_by_name(guild, category_name)
            if category is not None:
                try:
                    await category.edit(position=pos, reason="ARMENKR orden visual")
                except Exception:
                    pass

        # Voz
        for category_name, voice_names in VOICE_CHANNELS.items():
            category = get_category_by_name(guild, category_name)
            if category is None:
                continue
            for voice_name in voice_names:
                existing = get_voice_channel_by_name(guild, voice_name)
                if existing and existing.id in used_voice_ids:
                    existing = None
                if existing is None:
                    # Reutiliza voces viejas antes de crear más.
                    aliases = {
                        "🔊・𝙜𝙚𝙣𝙚𝙧𝙖𝙡": {"voz-general", "general", "voz", "general-voz"},
                        "🔊・𝙜𝙖𝙢𝙞𝙣𝙜": {"gaming", "gaming-general"},
                        "🔊・𝙨𝙖𝙡𝙖-𝙙𝙚-𝙖𝙢𝙞𝙜𝙤𝙨": {"sala-de-amigos", "amigos", "voz-amigos"},
                        "🎮・𝙜𝙖𝙢𝙞𝙣𝙜-𝙖𝙢𝙞𝙜𝙤𝙨": {"gaming-amigos", "gaming-amigos-voz"},
                    }.get(voice_name, set())
                    existing = next(
                        (ch for ch in guild.voice_channels if ch.id not in used_voice_ids and slugify(ch.name) in aliases),
                        None,
                    )

                overwrites = _friends_overwrites_light(guild) if category_name == "🔒・𝘼𝙈𝙄𝙂𝙊𝙎" else None
                if existing is None:
                    try:
                        kwargs = {"category": category, "reason": "ARMENKR Discord limpio"}
                        if overwrites is not None:
                            kwargs["overwrites"] = overwrites
                        existing = await guild.create_voice_channel(voice_name, **kwargs)
                        created_voice += 1
                    except Exception as exc:
                        report.append(f"No pude crear voz {voice_name}: {exc}")
                        continue
                else:
                    try:
                        kwargs = {"name": voice_name, "category": category, "reason": "ARMENKR Discord limpio"}
                        if overwrites is not None:
                            kwargs["overwrites"] = overwrites
                        await existing.edit(**kwargs)
                        moved_channels += 1
                    except Exception as exc:
                        report.append(f"No pude mover voz {existing.name}: {exc}")
                used_voice_ids.add(existing.id)

        if delete_extras:
            # Borrado solicitado: todo canal de texto/voz/foro/stage que no forma parte del diseño final.
            # Los canales especiales de Comunidad de Discord que no pudimos reutilizar se conservan para no romper el servidor.
            protected_ids = {
                ch.id for ch in (
                    getattr(guild, "system_channel", None),
                    getattr(guild, "rules_channel", None),
                    getattr(guild, "public_updates_channel", None),
                ) if ch is not None
            }
            desired_ids = used_channel_ids | used_voice_ids
            invocation_channel_id = None

            # Recolectamos todos los canales normales que Discord deja eliminar.
            extras = []
            for ch in list(guild.channels):
                if isinstance(ch, discord.CategoryChannel):
                    continue
                if ch.id in desired_ids:
                    continue
                if ch.id in protected_ids:
                    # Si un canal especial quedó fuera del diseño, intentamos mantenerlo solo por requisito de Discord.
                    continue
                extras.append(ch)

            for ch in extras:
                try:
                    await ch.delete(reason="Limpieza solicitada: diseño ARMENKR minimalista")
                    deleted_channels += 1
                    await asyncio.sleep(0.15)
                except discord.Forbidden:
                    report.append(f"Sin permiso para borrar {getattr(ch, 'name', ch.id)}.")
                except discord.HTTPException as exc:
                    report.append(f"Discord no dejó borrar {getattr(ch, 'name', ch.id)}: {exc}")
                except Exception as exc:
                    report.append(f"Error borrando {getattr(ch, 'name', ch.id)}: {exc}")

            desired_category_slugs = {slugify(name) for name in BLUEPRINT}
            # Borra categorías sobrantes que hayan quedado vacías.
            for category in list(guild.categories):
                if slugify(category.name) in desired_category_slugs:
                    continue
                if category.channels:
                    continue
                try:
                    await category.delete(reason="Limpieza solicitada: categorías innecesarias")
                    deleted_categories += 1
                    await asyncio.sleep(0.15)
                except Exception as exc:
                    report.append(f"No pude borrar categoría {category.name}: {exc}")

        return {
            "created_categories": created_categories,
            "created_channels": created_channels,
            "moved_channels": moved_channels,
            "created_roles": created_roles,
            "created_voice": created_voice,
            "deleted_channels": deleted_channels,
            "deleted_categories": deleted_categories,
            "report": report,
        }

    async def setup_akr_content(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        result = await _apply_clean_layout(guild, delete_extras=False)
        summary = (
            "✅ Diseño ARMENKR preparado sin borrar canales.\n\n"
            f"Categorías creadas: {result['created_categories']}\n"
            f"Canales creados: {result['created_channels']}\n"
            f"Canales movidos/renombrados: {result['moved_channels']}\n"
            f"Canales de voz creados: {result['created_voice']}\n"
            f"Roles creados: {result['created_roles']}\n\n"
            "Para aplicar la limpieza completa y borrar lo que sobra usa `/setup_discord_limpio`."
        )
        if result["report"]:
            summary += "\n\n⚠️ Detalles:\n" + "\n".join(result["report"][:10])
        await interaction.followup.send(summary, ephemeral=True)

    async def setup_discord_limpio(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        result = await _apply_clean_layout(guild, delete_extras=True)
        summary = (
            "✅ Discord ARMENKR reorganizado y limpiado.\n\n"
            "Diseño final: 7 categorías compactas, incluyendo FC27 y área privada de amigos.\n"
            f"Categorías creadas: {result['created_categories']}\n"
            f"Canales creados: {result['created_channels']}\n"
            f"Canales movidos/renombrados: {result['moved_channels']}\n"
            f"Canales de voz creados: {result['created_voice']}\n"
            f"Canales innecesarios borrados: {result['deleted_channels']}\n"
            f"Categorías vacías borradas: {result['deleted_categories']}\n"
            f"Roles creados: {result['created_roles']}\n\n"
            "🔒 `AMIGOS` solo es visible para el rol **🤝 Amigos**, admins y moderadores."
        )
        if result["report"]:
            summary += "\n\n⚠️ No pude cambiar algunas cosas:\n" + "\n".join(result["report"][:12])
            if len(result["report"]) > 12:
                summary += f"\n...y {len(result['report']) - 12} detalles más."
        await interaction.followup.send(summary, ephemeral=True)

    async def setup_discord_final(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        result = await _apply_clean_layout(guild, delete_extras=True)

        # El dueño recibe el rol FC27 para enterarse rápido de noticias/parches si el bot puede asignarlo.
        fc_role = discord.utils.get(guild.roles, name="⚽ FC27")
        if guild.owner and fc_role and guild.me and fc_role < guild.me.top_role:
            try:
                if fc_role not in guild.owner.roles:
                    await guild.owner.add_roles(fc_role, reason="ARMENKR radar FC27")
            except discord.HTTPException:
                pass

        posted = await _publish_final_panels(guild)
        # Inicializa el estado del monitor FC27 sin inundar con noticias viejas.
        try:
            await check_fc_news_once()
        except Exception as exc:
            result["report"].append(f"Radar FC27: {type(exc).__name__}: {exc}")

        summary = (
            "✅ **ARMENKR FINAL aplicado.**\n\n"
            "• Identidad Premium Esports uniforme en categorías, canales y embeds.\n"
            "• Emojis consistentes y categorías compactas.\n"
            "• Área 🔒 Amigos privada.\n"
            "• Un solo canal para Twitch + YouTube + TikTok.\n"
            "• Radar automático de noticias, parches y contenido de FC27.\n"
            "• Canales fuera del diseño final eliminados (excepto canales especiales de Discord que no se pueden tocar).\n\n"
            f"Categorías creadas: {result['created_categories']}\n"
            f"Canales creados: {result['created_channels']}\n"
            f"Canales movidos/renombrados: {result['moved_channels']}\n"
            f"Canales borrados: {result['deleted_channels']}\n"
            f"Categorías vacías borradas: {result['deleted_categories']}\n"
            f"Paneles actualizados: {len(posted)}"
        )
        if result["report"]:
            summary += "\n\n⚠️ Detalles: \n" + "\n".join(result["report"][:10])
        await interaction.followup.send(summary, ephemeral=True)

    async def archivar_akr_pesado(interaction: discord.Interaction):
        await interaction.response.send_message(
            "i️ Este diseño ya no usa archivo. Para dejar el servidor limpio usa `/setup_discord_limpio`; "
            "ese comando borra los canales que no forman parte del diseño final.",
            ephemeral=True,
        )

    async def _replace_panel(channel: Optional[discord.TextChannel], marker: str, embed: discord.Embed, *, pin: bool = False):
        if channel is None:
            return False
        # Evita duplicados si vuelves a correr el setup final.
        try:
            async for msg in channel.history(limit=50):
                if msg.author == channel.guild.me and msg.embeds:
                    footer = (msg.embeds[0].footer.text or "") if msg.embeds[0].footer else ""
                    if footer == marker:
                        await msg.edit(embed=embed)
                        if pin and not msg.pinned:
                            try:
                                await msg.pin(reason="Panel oficial ARMENKR")
                            except discord.HTTPException:
                                pass
                        return True
        except discord.HTTPException:
            pass
        msg = await channel.send(embed=embed)
        if pin:
            try:
                await msg.pin(reason="Panel oficial ARMENKR")
            except discord.HTTPException:
                pass
        return True

    async def _publish_final_panels(guild: discord.Guild) -> List[str]:
        welcome_ch = get_text_channel_by_name(guild, "👋・𝙗𝙞𝙚𝙣𝙫𝙚𝙣𝙞𝙙𝙖")
        rules_ch = get_text_channel_by_name(guild, "📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨")
        social_ch = get_text_channel_by_name(guild, "🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨")
        cmd_ch = get_text_channel_by_name(guild, "🤖・𝙘𝙤𝙢𝙖𝙣𝙙𝙤𝙨-𝙗𝙤𝙩")
        fc_ch = get_text_channel_by_name(guild, "📰・𝙣𝙤𝙩𝙞𝙘𝙞𝙖𝙨-𝙛𝙘")
        posted = []

        if welcome_ch:
            embed = brand_embed(
                guild,
                title="👑・𝘼𝙍𝙈𝙀𝙉𝙆𝙍 // 𝙒𝙀𝙇𝘾𝙊𝙈𝙀",
                description=(
                    "**FC27 • Gaming • Directos • Comunidad**\n\n"
                    "Empieza en **📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨**, entra a **💬・𝙘𝙝𝙖𝙩** y activa solo las notificaciones que te interesen.\n\n"
                    "`FOCO  //  DISCIPLINA  //  VICTORIA`"
                ),
                colour=BRAND_GOLD,
                author="ARMENKR // COMMUNITY",
                footer="ARMENKR FINAL • BIENVENIDA",
            )
            if await _replace_panel(welcome_ch, "ARMENKR FINAL • BIENVENIDA", embed):
                posted.append("👋・𝙗𝙞𝙚𝙣𝙫𝙚𝙣𝙞𝙙𝙖")

        if rules_ch:
            embed = brand_embed(
                guild,
                title="📜・𝘼𝙍𝙈𝙀𝙉𝙆𝙍 // 𝘾𝙊𝘿𝙀",
                description=(
                    "`01` Respeto primero.\n"
                    "`02` Cero spam, estafas o links sospechosos.\n"
                    "`03` Nada de racismo, acoso o toxicidad pesada.\n"
                    "`04` Usa cada canal para lo que es.\n"
                    "`05` Clips, ideas y opiniones sí; drama innecesario no.\n"
                    "`06` **🔒 Amigos** es un espacio privado."
                ),
                colour=BRAND_RED,
                author="ARMENKR // COMMUNITY",
                footer="ARMENKR FINAL • REGLAS",
            )
            if await _replace_panel(rules_ch, "ARMENKR FINAL • REGLAS", embed):
                posted.append("📜・𝙧𝙚𝙜𝙡𝙖𝙨-𝙮-𝙧𝙤𝙡𝙚𝙨")

        if social_ch:
            embed = brand_embed(
                guild,
                title="🔴・𝘼𝙍𝙈𝙀𝙉𝙆𝙍 // 𝙇𝙄𝙑𝙀 𝙃𝙐𝘽",
                description="Un solo punto para **directos + redes oficiales**. Sin spam y sin avisos duplicados.",
                colour=BRAND_RED,
                author="ARMENKR // LIVE",
                footer="ARMENKR FINAL • REDES",
            )
            embed.add_field(name="🟣 Twitch", value=f"[twitch.tv/armenkr]({ARMENKR_TWITCH})", inline=False)
            embed.add_field(name="▶️ YouTube", value=f"[@armenkr1901]({ARMENKR_YOUTUBE})", inline=False)
            embed.add_field(name="🎵 TikTok", value=f"[@armenkr]({ARMENKR_TIKTOK})", inline=False)
            embed.add_field(
                name="🤖 Avisos automáticos",
                value="**Streamcord:** Twitch + YouTube\n**Noti:** TikTok LIVE\nConfigura ambos bots para publicar aquí: `🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨`.",
                inline=False,
            )

            if await _replace_panel(social_ch, "ARMENKR FINAL • REDES", embed, pin=True):
                posted.append("🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨")

        if fc_ch:
            embed = brand_embed(
                guild,
                title="⚽・𝙁𝘾 27 // 𝙄𝙉𝙏𝙀𝙇 𝘿𝙀𝙎𝙆",
                description=(
                    f"Radar oficial de EA SPORTS FC 27 cada **{FC_NEWS_CHECK_MINUTES} min**.\n\n"
                    "**📰 NOTICIAS** — anuncios oficiales\n"
                    "**🛠️ PATCHES** — Title Updates / hotfixes\n"
                    "**✨ CONTENT** — campañas, promos, UT, The Grounds y oportunidades rápidas\n\n"
                    "Cada novedad genera una oportunidad en **💡・𝙞𝙙𝙚𝙖𝙨**."
                ),
                colour=BRAND_GREEN,
                author="ARMENKR // FC27 INTEL",
                footer="ARMENKR FINAL • FC27 RADAR",
            )
            embed.add_field(name="Fuente principal", value=f"[EA SPORTS FC 27 — Novedades y actualizaciones]({EA_FC27_NEWS_URL})", inline=False)

            if await _replace_panel(fc_ch, "ARMENKR FINAL • FC27 RADAR", embed, pin=True):
                posted.append("📰・𝙣𝙤𝙩𝙞𝙘𝙞𝙖𝙨-𝙛𝙘")

        if cmd_ch:
            embed = brand_embed(
                guild,
                title="🤖・𝘼𝙍𝙈𝙀𝙉𝙆𝙍 // 𝘾𝙊𝙉𝙏𝙍𝙊𝙇",
                description=(
                    "`/idea` • ideas de video\n"
                    "`/hook` • hooks rápidos\n"
                    "`/guion` • guion para Short/TikTok/Reel\n"
                    "`/caption` • título + caption + hashtags\n"
                    "`/contenido_hoy` • plan diario\n"
                    "`/analizar_noticia` • noticia → contenido\n"
                    "`/fc_check_now` • revisar radar FC27\n"
                    "`/branding_bots` • plantillas visuales de Streamcord / Noti / TweetShift\n"
                    "`/server_audit` • auditoría del servidor"
                ),
                colour=BRAND_BLUE,
                author="ARMENKR // CONTROL",
                footer="ARMENKR FINAL • COMANDOS",
            )
            if await _replace_panel(cmd_ch, "ARMENKR FINAL • COMANDOS", embed):
                posted.append("🤖・𝙘𝙤𝙢𝙖𝙣𝙙𝙤𝙨-𝙗𝙤𝙩")

        return posted

    async def post_akr_messages(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        posted = await _publish_final_panels(guild)
        await interaction.followup.send(
            "✅ Paneles finales actualizados: " + (", ".join(posted) if posted else "ninguno; ejecuta /setup_discord_final primero"),
            ephemeral=True,
        )

    async def server_audit(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        lines = ["REPORTE ARMENKR", f"Servidor: {guild.name}", f"Miembros: {guild.member_count}", ""]
        lines += ["CATEGORÍAS Y CANALES", "===================="]
        for category in guild.categories:
            lines.append(f"\n📁 {category.name}")
            for ch in category.channels:
                prefix = "#" if isinstance(ch, discord.TextChannel) else "🔊"
                lines.append(f"   {prefix} {ch.name}")
        lines += ["\nROLES", "===================="]
        for role in guild.roles:
            if role.name != "@everyone":
                lines.append(f"{role.name} — miembros: {len(role.members)}")
        lines += ["\nBOTS", "===================="]
        for member in [m for m in guild.members if m.bot]:
            lines.append(member.name)
        all_desired_channels = [ch for channels in BLUEPRINT.values() for ch, _ in channels]
        existing_slugs = {slugify(ch.name) for ch in guild.text_channels}
        missing = [ch for ch in all_desired_channels if slugify(ch) not in existing_slugs]
        lines += ["\nFALTANTES AKR", "===================="]
        lines += [f"- #{m}" for m in missing] if missing else ["No faltan canales principales del blueprint AKR."]
        text = "\n".join(lines)
        if len(text) > 1900:
            report_path = DATA_DIR / "akr_server_audit.txt"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(text, encoding="utf-8")
            await interaction.followup.send("Reporte generado:", file=discord.File(report_path), ephemeral=True)
        else:
            await interaction.followup.send(f"```txt\n{text}\n```", ephemeral=True)

    async def idea(interaction: discord.Interaction, tema: str):
        await send_text_response(interaction, generate_ideas_template(tema))

    async def hook(interaction: discord.Interaction, tema: str):
        await send_text_response(interaction, generate_hooks_template(tema))

    async def guion(interaction: discord.Interaction, tema: str, duracion: str = "30s"):
        await send_text_response(interaction, generate_script_template(tema, duracion))

    async def caption(interaction: discord.Interaction, tema: str):
        await send_text_response(interaction, generate_caption_template(tema))

    async def contenido_hoy(interaction: discord.Interaction):
        await send_text_response(interaction, generate_today_template())

    async def analizar_noticia(interaction: discord.Interaction, noticia: str):
        await send_text_response(interaction, analyze_news_template(noticia))

    async def branding_bots(interaction: discord.Interaction):
        guild = interaction.guild
        embed = brand_embed(
            guild,
            title="🎛️・𝘽𝙍𝘼𝙉𝘿 𝙆𝙄𝙏 // 𝘽𝙊𝙏𝙎",
            description=(
                "Usa estas plantillas en los dashboards de los bots externos para que todo el servidor hable el mismo idioma visual. "
                "No uses `@everyone` ni menciones roles."
            ),
            colour=BRAND_GOLD,
            author="ARMENKR // BRAND SYSTEM",
        )
        embed.add_field(
            name="🔴 STREAMCORD // TWITCH + YOUTUBE",
            value=(
                "**Título:** `🔴・𝘼𝙍𝙈𝙀𝙉𝙆𝙍 // 𝙇𝙄𝙑𝙀`\n"
                "**Texto:** `ARMENKR está en directo. Entra, saluda y disfruta el stream.`\n"
                "**Canal:** `🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨`\n"
                "**Color recomendado:** `#D90429`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎵 NOTI // TIKTOK LIVE",
            value=(
                "**Título:** `🔴・𝘼𝙍𝙈𝙀𝙉𝙆𝙍 // 𝙏𝙄𝙆𝙏𝙊𝙆 𝙇𝙄𝙑𝙀`\n"
                "**Texto:** `@armenkr acaba de entrar en directo en TikTok.`\n"
                "**Canal:** `🔴・𝙧𝙚𝙙𝙚𝙨-𝙮-𝙙𝙞𝙧𝙚𝙘𝙩𝙤𝙨`\n"
                "**Color recomendado:** `#D90429`"
            ),
            inline=False,
        )
        embed.add_field(
            name="👀 TWEETSHIFT // FUTSHERIFF",
            value=(
                "**Prefijo:** `👀・𝙁𝘾 27 // 𝙍𝙐𝙈𝙊𝙍`\n"
                "**Etiqueta:** `Fuente: @FutSheriff • No oficial hasta confirmación de EA.`\n"
                "**Canal:** `✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤`\n"
                "**Color recomendado:** `#D4AF37`"
            ),
            inline=False,
        )
        embed.add_field(
            name="📊 TWEETSHIFT // FUTBIN",
            value=(
                "**Prefijo:** `📊・𝙁𝘾 27 // 𝘾𝙊𝙉𝙏𝙀𝙉𝙏`\n"
                "**Etiqueta:** `Fuente: @FUTBIN • Datos/comunidad, separado de EA oficial.`\n"
                "**Canal:** `✨・𝙣𝙪𝙚𝙫𝙤-𝙘𝙤𝙣𝙩𝙚𝙣𝙞𝙙𝙤`\n"
                "**Color recomendado:** `#2563EB`"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def rss_add(interaction: discord.Interaction, nombre: str, url: str, canal: discord.TextChannel):
        data = load_data()
        feeds = data.setdefault("feeds", [])
        if any(f.get("url") == url for f in feeds):
            await interaction.response.send_message("Ese feed ya existe.", ephemeral=True)
            return
        feeds.append({"name": nombre, "url": url, "channel_id": canal.id})
        save_data(data)
        await interaction.response.send_message(f"✅ Feed agregado: **{nombre}** → {canal.mention}", ephemeral=True)

    async def rss_list(interaction: discord.Interaction):
        data = load_data()
        feeds = data.get("feeds", [])
        if not feeds:
            await interaction.response.send_message("No hay feeds configurados todavía.", ephemeral=True)
            return
        lines = ["Feeds RSS AKR:"]
        for f in feeds:
            ch = interaction.guild.get_channel(f.get("channel_id")) if interaction.guild else None
            lines.append(f"- {f.get('name')} → {ch.mention if ch else 'canal no encontrado'}")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    async def rss_check_now(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        count = await check_rss_feeds_once()
        await interaction.followup.send(f"✅ Revisión RSS terminada. Nuevas publicaciones: {count}", ephemeral=True)

    async def fc_check_now(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        count = await check_fc_news_once()
        await interaction.followup.send(
            f"✅ Monitor oficial FC27 revisado. Publicaciones nuevas detectadas: **{count}**.",
            ephemeral=True,
        )

    async def configurar_directos(
        interaction: discord.Interaction,
        twitch: Optional[str] = None,
        youtube: Optional[str] = None,
        kick: Optional[str] = None,
        tiktok: Optional[str] = None,
    ):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Solo funciona dentro del servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        config = await _load_stream_config(guild)
        updates = {"twitch": twitch, "youtube": youtube, "kick": kick, "tiktok": tiktok}
        changed = []
        for platform, value in updates.items():
            if value is None:
                continue
            value = value.strip()
            if value.lower() in {"quitar", "remove", "none", "-"}:
                config.pop(platform, None)
                changed.append(f"{platform}: eliminado")
                continue
            if not value.startswith(("https://", "http://")):
                await interaction.followup.send(f"❌ El enlace de {platform} debe empezar por https://", ephemeral=True)
                return
            config[platform] = value
            changed.append(f"{platform}: configurado")
        if not changed:
            await interaction.followup.send("i️ No enviaste ningún enlace. Puedes poner `quitar` para eliminar uno.", ephemeral=True)
            return
        await _save_stream_config(guild, config)
        stream_last_state.clear()
        await interaction.followup.send(
            "✅ Canales de directo guardados.\n" + "\n".join(f"• {x}" for x in changed)
            + "\n\nYouTube se comprueba automáticamente. Twitch necesita `TWITCH_CLIENT_ID` y `TWITCH_CLIENT_SECRET` en Railway. Kick usa su endpoint público. TikTok queda disponible para aviso manual con `/envivo`.",
            ephemeral=True,
        )

    async def directos_status(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        config = await _load_stream_config(guild) if guild else {}
        if not config:
            await interaction.followup.send("No hay canales de directo configurados todavía.", ephemeral=True)
            return
        results = await check_streams_once(alert_transitions=False)
        lines = ["**Monitor de directos ARMENKR**"]
        for platform in ("twitch", "youtube", "kick", "tiktok"):
            url = config.get(platform)
            if not url:
                continue
            info = results.get(platform, {})
            if info.get("supported"):
                status = "🔴 EN VIVO" if info.get("live") else "⚫ offline"
            else:
                status = "⚠️ " + info.get("reason", "sin detector automático")
            lines.append(f"• **{platform.title()}** — {status}\n  {url}")
        await interaction.followup.send("\n".join(lines), ephemeral=True)

    async def directos_check_now(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        results = await check_streams_once(alert_transitions=True)
        if not results:
            await interaction.followup.send("No hay enlaces configurados. Usa `/configurar_directos`.", ephemeral=True)
            return
        live = [p for p, info in results.items() if info.get("supported") and info.get("live")]
        await interaction.followup.send(
            "✅ Revisión terminada. " + ("En vivo: **" + ", ".join(live) + "**" if live else "No detecté directos activos."),
            ephemeral=True,
        )

    def command(name, description, callback, *, admin=False, params=None):
        cb = callback
        if admin:
            cb = manage_guild_only()(cb)
        if params:
            cb = app_commands.describe(**params)(cb)
        cmd = app_commands.Command(name=name, description=description, callback=cb)
        bot.tree.add_command(cmd)
        if admin:
            @cmd.error
            async def _err(interaction: discord.Interaction, error: app_commands.AppCommandError):
                msg = "Necesitas permiso de Manage Server o Administrator para usar este comando."
                if not isinstance(error, app_commands.CheckFailure):
                    msg = f"Ocurrió un error en /{name}: {type(error).__name__}"
                if interaction.response.is_done():
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await interaction.response.send_message(msg, ephemeral=True)
        return cmd

    command("setup_akr_content", "Prepara el diseño limpio de ARMENKR sin borrar canales.", setup_akr_content, admin=True)
    command("setup_discord_limpio", "Reorganiza el servidor y borra canales innecesarios.", setup_discord_limpio, admin=True)
    command("setup_discord_final", "Aplica el diseño final ARMENKR, limpia y publica paneles.", setup_discord_final, admin=True)
    command("archivar_akr_pesado", "Comando legado: ahora la limpieza se hace con /setup_discord_limpio.", archivar_akr_pesado, admin=True)
    command("post_akr_messages", "Publica mensajes base de bienvenida, reglas y comandos AKR.", post_akr_messages, admin=True)
    command("server_audit", "Genera un reporte rápido del servidor actual.", server_audit, admin=True)
    command("idea", "Genera ideas de contenido AKR para FC27 sin IA.", idea, params={"tema": "Tema del contenido"})
    command("hook", "Genera hooks competitivos para un tema sin IA.", hook, params={"tema": "Tema del video"})
    command("guion", "Genera un guion para TikTok, Short o Reel sin IA.", guion, params={"tema": "Tema del video", "duracion": "Ejemplo: 20s, 30s, 60s"})
    command("caption", "Genera título, caption y hashtags sin IA.", caption, params={"tema": "Tema del video"})
    command("contenido_hoy", "Genera un plan de contenido para hoy sin IA.", contenido_hoy)
    command("analizar_noticia", "Convierte una noticia en ideas de contenido usando plantilla.", analizar_noticia, params={"noticia": "Texto, link o contexto de la noticia"})
    command("branding_bots", "Muestra el estilo visual para Streamcord, Noti y TweetShift.", branding_bots, admin=True)
    command("rss_add", "Agrega un feed RSS para noticias automáticas.", rss_add, admin=True, params={"nombre": "Nombre de la fuente", "url": "URL RSS", "canal": "Canal donde publicar"})
    command("rss_list", "Lista los feeds RSS configurados.", rss_list, admin=True)
    command("rss_check_now", "Revisa ahora mismo los feeds RSS.", rss_check_now, admin=True)
    command("fc_check_now", "Revisa ahora la página oficial de noticias de EA SPORTS FC 27.", fc_check_now, admin=True)

    async def rss_worker():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await check_rss_feeds_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"AKR RSS error: {type(exc).__name__}: {exc}")
            await asyncio.sleep(NEWS_CHECK_MINUTES * 60)

    async def fc_worker():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await check_fc_news_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"AKR FC monitor error: {type(exc).__name__}: {exc}")
            await asyncio.sleep(FC_NEWS_CHECK_MINUTES * 60)

    rss_task = None
    fc_task = None

    async def akr_ready_listener():
        nonlocal rss_task, fc_task
        if rss_task is None or rss_task.done():
            rss_task = asyncio.create_task(rss_worker(), name="akr-rss-worker")
        if fc_task is None or fc_task.done():
            fc_task = asyncio.create_task(fc_worker(), name="akr-fc27-worker")
        print(
            f"🎬 ARMENKR FINAL | RSS {NEWS_CHECK_MINUTES}m | FC27 oficial {FC_NEWS_CHECK_MINUTES}m | "
            "directos: Streamcord + Noti"
        )

    bot.add_listener(akr_ready_listener, "on_ready")
