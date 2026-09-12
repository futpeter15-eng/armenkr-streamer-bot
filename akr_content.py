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
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
import feedparser


# =========================================================
# CONFIGURACIÓN AKR LIGERA
# =========================================================

NEWS_CHECK_MINUTES = max(5, int(os.getenv("NEWS_CHECK_MINUTES", "30") or "30"))
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("AKR_DATA_DIR", str(BASE_DIR)))
DATA_FILE = DATA_DIR / "akr_bot_data.json"

BLUEPRINT: Dict[str, List[Tuple[str, str]]] = {
    "👑 AKR HQ": [
        ("bienvenida", "Bienvenida oficial de AKR."),
        ("reglas", "Reglas de comunidad."),
        ("anuncios-akr", "Anuncios oficiales, cambios y directos."),
        ("redes-oficiales", "Links oficiales de AKR."),
    ],
    "🎬 CONTENIDO": [
        ("comandos-akr", "Comandos del bot y ayuda rápida."),
        ("ideas-y-guiones", "Ideas, hooks, guiones, captions y contenido para hoy."),
        ("clips-para-editar", "Clips brutos pendientes de edición."),
        ("videos-listos", "Videos listos o publicados para apoyar."),
    ],
    "⚽ FC27": [
        ("ultimate-team", "Ultimate Team, mercado, SBCs y RTG."),
        ("the-grounds", "The Grounds, builds, clips y ranked grind."),
        ("tacticas", "Formaciones, instrucciones y gameplay competitivo."),
    ],
    "💬 COMUNIDAD": [
        ("chat", "Chat general de la comunidad."),
        ("clips-comunidad", "Clips enviados por la comunidad."),
        ("memes-fc", "Memes, fails y rage de FC."),
    ],
    "🎮 EXTRA": [
        ("gta", "GTA y contenido secundario."),
        ("coches-y-tuning", "Carros, tuning y temas del garaje."),
        ("otros-juegos", "ARK, Minecraft y cualquier juego secundario."),
    ],
    "🛡️ STAFF": [
        ("chat-admins", "Chat privado de staff."),
        ("logs", "Logs y control del servidor."),
    ],
}

VOICE_CHANNELS = {
    "💬 COMUNIDAD": ["voz-general"],
    "🛡️ STAFF": ["voz-staff"],
}

ROLE_BLUEPRINT = [
    ("👑 AKR", 0xFFD166),
    ("🛡️ Admin", 0xE63946),
    ("🔨 Moderador", 0xF77F00),
    ("🎬 Creador", 0x9B5DE5),
    ("⚽ FC27", 0x06D6A0),
    ("🔴 Directos", 0xFF0000),
    ("👥 Comunidad", 0xADB5BD),
]

OLD_CHANNEL_MAP = {
    "bienvenidas": "bienvenida",
    "bienvenida": "bienvenida",
    "normativas": "reglas",
    "reglas": "reglas",
    "redes-sociales": "redes-oficiales",
    "redes-oficiales": "redes-oficiales",
    "en-vivo": "anuncios-akr",
    "anuncios": "anuncios-akr",
    "anuncios-akr": "anuncios-akr",
    "comandos": "comandos-akr",
    "comandos-akr": "comandos-akr",
    "ideas-generadas": "ideas-y-guiones",
    "hooks-y-guiones": "ideas-y-guiones",
    "titulos-captions-hashtags": "ideas-y-guiones",
    "contenido-para-hoy": "ideas-y-guiones",
    "ideas-rapidas": "ideas-y-guiones",
    "ideas-aprobadas": "ideas-y-guiones",
    "pendiente-de-grabar": "ideas-y-guiones",
    "pendiente-de-editar": "clips-para-editar",
    "clips": "clips-comunidad",
    "clips-comunidad": "clips-comunidad",
    "videos-listos": "videos-listos",
    "publicado-hoy": "videos-listos",
    "miniaturas-overlays": "videos-listos",
    "noticias-crudas": "anuncios-akr",
    "noticias-fc27": "anuncios-akr",
    "noticias-ultimate-team": "ultimate-team",
    "noticias-the-grounds": "the-grounds",
    "noticias-streaming": "anuncios-akr",
    "ultimate-team": "ultimate-team",
    "the-grounds": "the-grounds",
    "tacticas": "tacticas",
    "gameplay-analysis": "tacticas",
    "mentalidad-competitiva": "tacticas",
    "road-to-fc27": "tacticas",
    "chat": "chat",
    "memes": "memes-fc",
    "memes-fc": "memes-fc",
    "cumpleanos": "chat",
    "cumpleaños": "chat",
    "gta": "gta",
    "gta-clips": "gta",
    "coches-y-tuning": "coches-y-tuning",
    "ark": "otros-juegos",
    "ark-parches": "otros-juegos",
    "minecraft": "otros-juegos",
    "datos-bot": "logs",
    "warns": "logs",
    "control-staff": "chat-admins",
    "comandos-staff": "chat-admins",
    "chat-admins": "chat-admins",
    "logs": "logs",
}

HEAVY_AKR_CHANNELS = [
    "roles", "en-vivo", "ideas-generadas", "hooks-y-guiones", "titulos-captions-hashtags", "contenido-para-hoy",
    "noticias-crudas", "noticias-fc27", "noticias-ultimate-team", "noticias-the-grounds", "noticias-streaming",
    "ideas-rapidas", "ideas-aprobadas", "publicado-hoy", "miniaturas-overlays",
    "gameplay-analysis", "mentalidad-competitiva", "road-to-fc27", "calendario-akr",
    "pendiente-de-grabar", "pendiente-de-editar", "pendiente-de-subir", "resultados-semana",
    "cumpleaños", "gta-clips", "ark-parches", "control-staff", "warns", "datos-bot", "comandos-staff",
    "dibujos", "musica-bot", "niveles-bot", "config-bots", "sorteos-vip",
]

HEAVY_AKR_CATEGORIES = [
    "📌 CONTENT COMMAND CENTER", "📰 NEWS ROOM", "🎬 CONTENT LAB", "⚽ FC27 COMPETITIVO",
    "📅 PRODUCCIÓN AKR", "🎮 OTROS JUEGOS",
    "━━ 📍・𝐒𝐄𝐑𝐕𝐈𝐃𝐎𝐑 ━━", "━━ 🚀・𝐄𝐍𝐓𝐑𝐄𝐓𝐄𝐍𝐈𝐌𝐈𝐄𝐍𝐓𝐎 ━━",
    "━━ 💗・𝐀𝐌𝐈𝐆𝐎𝐒 ━━", "━━ ⛏️・𝐌𝐈𝐍𝐄𝐂𝐑𝐀𝐅𝐓 ━━", "━━ 🦖・𝐃𝐎𝐃Ó𝐅𝐈𝐋𝐎𝐒 | 𝐀𝐑𝐊 ━━",
    "━━ 🚗・𝐆𝐓𝐀 ━━", "━━ 🤖・𝐁𝐎𝐓𝐒 ━━", "━━ 💎・𝐕𝐈𝐏 𝐋𝐎𝐔𝐍𝐆𝐄 ━━",
]

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
# REGISTRO EN EL BOT EXISTENTE
# =========================================================

def register_akr_content(bot, guild_id: int):
    """Registra todos los comandos AKR en la MISMA instancia del bot ARMENKR."""

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

                embed = discord.Embed(
                    title=title,
                    description=summary or "Nueva publicación detectada.",
                    colour=discord.Colour.blue(),
                )
                embed.set_author(name=f"📰 {name}")
                if link:
                    embed.url = link
                try:
                    await channel.send(embed=embed)
                except discord.HTTPException:
                    continue

                ideas_ch = get_text_channel_by_name(channel.guild, "ideas-y-guiones")
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

    async def setup_akr_content(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        report = []
        created_categories = created_channels = moved_channels = created_roles = created_voice = 0

        for role_name, color in ROLE_BLUEPRINT:
            if not discord.utils.get(guild.roles, name=role_name):
                try:
                    await guild.create_role(name=role_name, colour=discord.Colour(color), reason="AKR Content HQ setup")
                    created_roles += 1
                except discord.Forbidden:
                    report.append(f"No pude crear el rol {role_name}. Revisa Manage Roles y posición del bot.")
                except Exception as exc:
                    report.append(f"Error creando rol {role_name}: {exc}")

        for category_name, channels in BLUEPRINT.items():
            category = get_category_by_name(guild, category_name)
            if category is None:
                try:
                    kwargs = {}
                    if category_name == "🛡️ STAFF":
                        kwargs["overwrites"] = _staff_overwrites_light(guild)
                    category = await guild.create_category(category_name, reason="AKR Content HQ setup", **kwargs)
                    created_categories += 1
                except Exception as exc:
                    report.append(f"No pude crear categoría {category_name}: {exc}")
                    continue
            elif category_name == "🛡️ STAFF":
                try:
                    await category.edit(overwrites=_staff_overwrites_light(guild), reason="AKR staff privado")
                except Exception:
                    pass

            for channel_name, topic in channels:
                existing = get_text_channel_by_name(guild, channel_name)

                if existing is None:
                    for old_slug, desired in OLD_CHANNEL_MAP.items():
                        if desired != channel_name:
                            continue
                        old_channel = next((ch for ch in guild.text_channels if slugify(ch.name) == old_slug), None)
                        if old_channel:
                            try:
                                await old_channel.edit(name=channel_name, category=category, topic=topic, reason="AKR Content HQ reorganize")
                                existing = old_channel
                                moved_channels += 1
                                break
                            except Exception as exc:
                                report.append(f"No pude renombrar/mover #{old_channel.name}: {exc}")

                if existing is None:
                    try:
                        kwargs = {}
                        if category_name == "🛡️ STAFF":
                            kwargs["overwrites"] = _staff_overwrites_light(guild)
                        await guild.create_text_channel(channel_name, category=category, topic=topic, reason="AKR Content HQ setup", **kwargs)
                        created_channels += 1
                    except Exception as exc:
                        report.append(f"No pude crear #{channel_name}: {exc}")
                elif existing.category != category or existing.topic != topic:
                    try:
                        await existing.edit(category=category, topic=topic, reason="AKR Content HQ organize")
                        moved_channels += 1
                    except Exception as exc:
                        report.append(f"No pude mover #{existing.name}: {exc}")

        for category_name, voice_names in VOICE_CHANNELS.items():
            category = get_category_by_name(guild, category_name)
            if category is None:
                continue
            for voice_name in voice_names:
                if get_voice_channel_by_name(guild, voice_name) is None:
                    try:
                        kwargs = {}
                        if category_name == "🛡️ STAFF":
                            kwargs["overwrites"] = _staff_overwrites_light(guild)
                        await guild.create_voice_channel(voice_name, category=category, reason="AKR Content HQ voice setup", **kwargs)
                        created_voice += 1
                    except Exception as exc:
                        report.append(f"No pude crear voz {voice_name}: {exc}")

        summary = (
            "✅ AKR Content HQ LIGERO setup terminado.\n\n"
            f"Categorías creadas: {created_categories}\n"
            f"Canales creados: {created_channels}\n"
            f"Canales movidos/renombrados: {moved_channels}\n"
            f"Canales de voz creados: {created_voice}\n"
            f"Roles creados: {created_roles}\n"
        )
        if report:
            summary += "\n⚠️ Detalles:\n" + "\n".join(report[:15])
            if len(report) > 15:
                summary += f"\n...y {len(report) - 15} detalles más."
        await interaction.followup.send(summary, ephemeral=True)

    async def archivar_akr_pesado(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        desired_text = {slugify(ch) for channels in BLUEPRINT.values() for ch, _ in channels}
        desired_voice = {slugify(ch) for voices in VOICE_CHANNELS.values() for ch in voices}
        heavy_slugs = {slugify(ch) for ch in HEAVY_AKR_CHANNELS}
        heavy_categories = {slugify(c) for c in HEAVY_AKR_CATEGORIES}

        archive = get_category_by_name(guild, "📦 ARCHIVO AKR")
        if archive is None:
            archive = await guild.create_category("📦 ARCHIVO AKR", reason="AKR ligero archive")

        moved = []
        for ch in list(guild.text_channels) + list(guild.voice_channels):
            ch_slug = slugify(ch.name)
            is_desired = ch_slug in desired_text or ch_slug in desired_voice
            is_heavy_channel = ch_slug in heavy_slugs
            is_in_heavy_category = ch.category and slugify(ch.category.name) in heavy_categories
            if (is_heavy_channel or is_in_heavy_category) and not is_desired:
                try:
                    await ch.edit(category=archive, reason="AKR ligero archive")
                    moved.append(ch.name)
                except Exception:
                    pass

        msg = "✅ Limpieza ligera terminada. No borré ningún canal."
        if moved:
            msg += "\nMoví a 📦 ARCHIVO AKR:\n" + "\n".join(f"- {name}" for name in moved[:30])
            if len(moved) > 30:
                msg += f"\n...y {len(moved)-30} más."
        else:
            msg += "\nNo encontré canales pesados para archivar."
        await interaction.followup.send(msg, ephemeral=True)

    async def post_akr_messages(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        welcome_ch = get_text_channel_by_name(guild, "bienvenida")
        rules_ch = get_text_channel_by_name(guild, "reglas")
        cmd_ch = get_text_channel_by_name(guild, "comandos-akr")
        posted = []

        if welcome_ch:
            embed = discord.Embed(
                title="Bienvenido a AKR Content HQ",
                description=(
                    "Este servidor es el centro de operaciones de AKR para FC27, Ultimate Team, The Grounds, "
                    "streaming y creación de contenido.\n\n"
                    "Aquí llegan noticias, se generan ideas, se guardan clips, se arman guiones y se convierte todo en contenido.\n\n"
                    "**AKR — Foco. Disciplina. Victoria.**"
                ),
                colour=discord.Colour.gold(),
            )
            await welcome_ch.send(embed=embed)
            posted.append("#bienvenida")

        if rules_ch:
            embed = discord.Embed(
                title="Reglas AKR",
                description=(
                    "1. Respeto primero.\n2. Cero spam o links raros.\n3. Nada de racismo, acoso o toxicidad pesada.\n"
                    "4. Si mandas clips, que tengan contexto.\n5. Si aportas ideas, piensa en contenido real.\n"
                    "6. Aquí venimos a mejorar, competir y crear."
                ),
                colour=discord.Colour.red(),
            )
            await rules_ch.send(embed=embed)
            posted.append("#reglas")

        if cmd_ch:
            embed = discord.Embed(
                title="Comandos AKR",
                description=(
                    "`/idea tema` — ideas de video\n`/hook tema` — hooks\n`/guion tema duracion` — guion\n"
                    "`/caption tema` — título, caption y hashtags\n`/contenido_hoy` — plan diario\n"
                    "`/analizar_noticia noticia` — convierte una noticia en ideas\n"
                    "`/rss_add` — agrega RSS\n`/rss_check_now` — revisa RSS\n"
                    "`/setup_akr_content` — estructura ligera\n`/archivar_akr_pesado` — archiva extras sin borrar"
                ),
                colour=discord.Colour.blue(),
            )
            await cmd_ch.send(embed=embed)
            posted.append("#comandos-akr")

        await interaction.followup.send(
            "✅ Mensajes publicados en: " + (", ".join(posted) if posted else "ningún canal; ejecuta /setup_akr_content primero"),
            ephemeral=True,
        )

    async def server_audit(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Este comando solo funciona dentro de un servidor.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        lines = ["REPORTE AKR CONTENT HQ", f"Servidor: {guild.name}", f"Miembros: {guild.member_count}", ""]
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

    command("setup_akr_content", "Crea la estructura ligera de AKR Content HQ sin borrar tu servidor.", setup_akr_content, admin=True)
    command("archivar_akr_pesado", "Mueve canales extra a 📦 ARCHIVO AKR sin borrar nada.", archivar_akr_pesado, admin=True)
    command("post_akr_messages", "Publica mensajes base de bienvenida, reglas y comandos AKR.", post_akr_messages, admin=True)
    command("server_audit", "Genera un reporte rápido del servidor actual.", server_audit, admin=True)
    command("idea", "Genera ideas de contenido AKR para FC27 sin IA.", idea, params={"tema": "Tema del contenido"})
    command("hook", "Genera hooks competitivos para un tema sin IA.", hook, params={"tema": "Tema del video"})
    command("guion", "Genera un guion para TikTok, Short o Reel sin IA.", guion, params={"tema": "Tema del video", "duracion": "Ejemplo: 20s, 30s, 60s"})
    command("caption", "Genera título, caption y hashtags sin IA.", caption, params={"tema": "Tema del video"})
    command("contenido_hoy", "Genera un plan de contenido para hoy sin IA.", contenido_hoy)
    command("analizar_noticia", "Convierte una noticia en ideas de contenido usando plantilla.", analizar_noticia, params={"noticia": "Texto, link o contexto de la noticia"})
    command("rss_add", "Agrega un feed RSS para noticias automáticas.", rss_add, admin=True, params={"nombre": "Nombre de la fuente", "url": "URL RSS", "canal": "Canal donde publicar"})
    command("rss_list", "Lista los feeds RSS configurados.", rss_list, admin=True)
    command("rss_check_now", "Revisa ahora mismo los feeds RSS.", rss_check_now, admin=True)

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

    rss_task = None

    async def akr_ready_listener():
        nonlocal rss_task
        if rss_task is None or rss_task.done():
            rss_task = asyncio.create_task(rss_worker(), name="akr-rss-worker")
        print(f"🎬 AKR Content HQ integrado | RSS cada {NEWS_CHECK_MINUTES} min")

    bot.add_listener(akr_ready_listener, "on_ready")
