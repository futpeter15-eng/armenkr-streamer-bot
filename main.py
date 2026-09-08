"""
ARMENKR STREAMER SERVER BOT V1
==============================

Objetivo:
- Mejorar el servidor actual sin convertirlo en algo irreconocible.
- Mantener Servidor / Comunidad / Entretenimiento / Amigos / Minecraft / Dodófilos / Staff.
- Agregar GTA, Bots y funciones de streamer.
- Renombrar y ordenar canales existentes cuando sea posible, evitando duplicados.
- Panel de roles, redes sociales, bienvenida y avisos de directo.
- Ocultar Minecraft / ARK / GTA según los roles elegidos.
"""

import os
import re
import json
import asyncio
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


# =========================================================
# CONFIGURACIÓN / BRANDING
# =========================================================

SERVER_NAME = "👑 ARMENKR | COMUNIDAD"
ACCENT = 0xD4AF37

def get_config():
    token = os.getenv("DISCORD_TOKEN")
    guild_id_raw = os.getenv("GUILD_ID")

    if not token:
        raise RuntimeError("Falta la variable DISCORD_TOKEN.")
    if not guild_id_raw or not guild_id_raw.isdigit():
        raise RuntimeError("Falta GUILD_ID o no es un ID válido.")

    return token, int(guild_id_raw)


# =========================================================
# ROLES
# =========================================================

ROLE_OWNER = "👑・𝐀𝐑𝐌𝐄𝐍𝐊𝐑"
ROLE_ADMIN = "🛡️・𝐀𝐃𝐌𝐈𝐍"
ROLE_MOD = "🔨・𝐌𝐎𝐃𝐄𝐑𝐀𝐃𝐎𝐑"
ROLE_VIP = "💎・𝐕𝐈𝐏"
ROLE_OG = "🔥・𝐎𝐆"
ROLE_FRIENDS = "💗・𝐀𝐌𝐈𝐆𝐎𝐒"
ROLE_COMMUNITY = "👥・𝐂𝐎𝐌𝐔𝐍𝐈𝐃𝐀𝐃"
ROLE_LIVE = "🔔・𝐃𝐈𝐑𝐄𝐂𝐓𝐎𝐒"
ROLE_MC = "⛏️・𝐌𝐈𝐍𝐄𝐂𝐑𝐀𝐅𝐓"
ROLE_ARK = "🦖・𝐀𝐑𝐊"
ROLE_GTA = "🚗・𝐆𝐓𝐀"
ROLE_BOTS = "🤖・𝐁𝐎𝐓𝐒"

STAFF_ROLES = {ROLE_OWNER, ROLE_ADMIN, ROLE_MOD}
SELF_ROLES = {
    "live": ROLE_LIVE,
    "minecraft": ROLE_MC,
    "ark": ROLE_ARK,
    "gta": ROLE_GTA,
}

BASE_ROLES = [
    (ROLE_OWNER, 0xD4AF37, True),
    (ROLE_ADMIN, 0xC0392B, True),
    (ROLE_MOD, 0xE67E22, True),
    (ROLE_VIP, 0x9B59B6, True),
    (ROLE_OG, 0xE74C3C, False),
    (ROLE_FRIENDS, 0xFF69B4, False),
    (ROLE_COMMUNITY, 0x95A5A6, False),
    (ROLE_LIVE, 0xE74C3C, False),
    (ROLE_MC, 0x2ECC71, False),
    (ROLE_ARK, 0x3498DB, False),
    (ROLE_GTA, 0x27AE60, False),
    (ROLE_BOTS, 0x5865F2, True),
]


# =========================================================
# CATEGORÍAS / CANALES
# =========================================================

CAT_SERVER = "━━ 📍・𝐒𝐄𝐑𝐕𝐈𝐃𝐎𝐑 ━━"
CAT_COMMUNITY = "━━ 🌎・𝐂𝐎𝐌𝐔𝐍𝐈𝐃𝐀𝐃 ━━"
CAT_ENT = "━━ 🚀・𝐄𝐍𝐓𝐑𝐄𝐓𝐄𝐍𝐈𝐌𝐈𝐄𝐍𝐓𝐎 ━━"
CAT_FRIENDS = "━━ 💗・𝐀𝐌𝐈𝐆𝐎𝐒 ━━"
CAT_MC = "━━ ⛏️・𝐌𝐈𝐍𝐄𝐂𝐑𝐀𝐅𝐓 ━━"
CAT_ARK = "━━ 🦖・𝐃𝐎𝐃Ó𝐅𝐈𝐋𝐎𝐒 | 𝐀𝐑𝐊 ━━"
CAT_GTA = "━━ 🚗・𝐆𝐓𝐀 ━━"
CAT_BOTS = "━━ 🤖・𝐁𝐎𝐓𝐒 ━━"
CAT_STAFF = "━━ 🛡️・𝐒𝐓𝐀𝐅𝐅 ━━"

CH_WELCOME = "📣・𝑩𝒊𝒆𝒏𝒗𝒆𝒏𝒊𝒅𝒂𝒔"
CH_RULES = "📕・𝑵𝒐𝒓𝒎𝒂𝒕𝒊𝒗𝒂𝒔"
CH_SOCIALS = "🌐・𝑹𝒆𝒅𝒆𝒔-𝑺𝒐𝒄𝒊𝒂𝒍𝒆𝒔"
CH_LIVE = "🔴・𝑬𝒏-𝑽𝒊𝒗𝒐"
CH_ANNOUNCE = "📢・𝑨𝒏𝒖𝒏𝒄𝒊𝒐𝒔"
CH_ROLES = "🎭・𝑬𝒍𝒊𝒈𝒆-𝑻𝒖𝒔-𝑹𝒐𝒍𝒆𝒔"

CH_CHAT = "💬・𝑪𝒉𝒂𝒕"
CH_BIRTHDAY = "🎂・𝑪𝒖𝒎𝒑𝒍𝒆𝒂ñ𝒐𝒔"
CH_LEVELS = "💯・𝑵𝒊𝒗𝒆𝒍𝒆𝒔"
VOICE_COMMUNITY = "🔊・𝐕𝐎𝐙"

CH_DRAWINGS = "🎨・𝑫𝒊𝒃𝒖𝒋𝒐𝒔"
CH_MEMES = "😜・𝑴𝒆𝒎𝒆𝒔"
CH_CLIPS = "🎬・𝑪𝒍𝒊𝒑𝒔"

CH_FRIENDS_CHAT = "💬・𝑪𝒉𝒂𝒕-𝑨𝒎𝒊𝒈𝒐𝒔"
CH_FRIENDS_MUSIC = "🎵・𝑴𝒖́𝒔𝒊𝒄𝒂"
VOICE_FRIENDS = "🔊・𝐕𝐎𝐙-𝐀𝐌𝐈𝐆𝐎𝐒"

CH_MC_MODS = "🧩・𝒎𝒐𝒅𝒔"
CH_MC_IP = "🌐・𝒊𝒑"
CH_MC_CHAT = "💬・𝒕𝒆𝒙𝒕𝒐"
VOICE_MC = "🔊・𝐕𝐎𝐙"

CH_ARK_CHAT = "💬・𝒂𝒓𝒌"
CH_ARK_PATCHES = "🛠️・𝒂𝒓𝒌-𝒑𝒂𝒓𝒄𝒉𝒆𝒔"
CH_ARK_MUSIC = "🎵・𝑴𝒖́𝒔𝒊𝒄𝒂"
VOICE_ARK = "🔊・𝐕𝐎𝐙"

CH_GTA_CHAT = "💬・𝒈𝒕𝒂"
CH_GTA_CLIPS = "📸・𝒈𝒕𝒂-𝒄𝒍𝒊𝒑𝒔"
CH_GTA_CARS = "🏎️・𝒄𝒐𝒄𝒉𝒆𝒔-𝒚-𝒕𝒖𝒏𝒊𝒏𝒈"
VOICE_GTA = "🔊・𝐕𝐎𝐙-𝐆𝐓𝐀"

CH_BOT_COMMANDS = "🤖・𝑪𝒐𝒎𝒂𝒏𝒅𝒐𝒔"
CH_BOT_MUSIC = "🎵・𝑴𝒖́𝒔𝒊𝒄𝒂-𝑩𝒐𝒕"
CH_BOT_LEVELS = "📊・𝑵𝒊𝒗𝒆𝒍𝒆𝒔-𝑩𝒐𝒕"

CH_STAFF_CHAT = "💬・𝑪𝒉𝒂𝒕-𝑨𝒅𝒎𝒊𝒏𝒔"
CH_STAFF_CONTROL = "⚙️・𝑪𝒐𝒏𝒕𝒓𝒐𝒍-𝑺𝒕𝒂𝒇𝒇"
CH_WARNS = "🚨・𝑾𝒂𝒓𝒏𝒔"
CH_LOGS = "📋・𝑳𝒐𝒈𝒔"
CH_DATA = "🗄️・𝑫𝒂𝒕𝒐𝒔-𝑩𝒐𝒕"
VOICE_STAFF = "🔊・𝐕𝐎𝐙-𝐒𝐓𝐀𝐅𝐅"

BLUEPRINT = [
    (CAT_SERVER, [
        ("text", CH_WELCOME),
        ("text", CH_RULES),
        ("text", CH_SOCIALS),
        ("text", CH_LIVE),
        ("text", CH_ANNOUNCE),
        ("text", CH_ROLES),
    ]),
    (CAT_COMMUNITY, [
        ("text", CH_CHAT),
        ("text", CH_BIRTHDAY),
        ("text", CH_LEVELS),
        ("voice", VOICE_COMMUNITY),
    ]),
    (CAT_ENT, [
        ("text", CH_DRAWINGS),
        ("text", CH_MEMES),
        ("text", CH_CLIPS),
    ]),
    (CAT_FRIENDS, [
        ("text", CH_FRIENDS_CHAT),
        ("text", CH_FRIENDS_MUSIC),
        ("voice", VOICE_FRIENDS),
    ]),
    (CAT_MC, [
        ("text", CH_MC_MODS),
        ("text", CH_MC_IP),
        ("text", CH_MC_CHAT),
        ("voice", VOICE_MC),
    ]),
    (CAT_ARK, [
        ("text", CH_ARK_CHAT),
        ("text", CH_ARK_PATCHES),
        ("text", CH_ARK_MUSIC),
        ("voice", VOICE_ARK),
    ]),
    (CAT_GTA, [
        ("text", CH_GTA_CHAT),
        ("text", CH_GTA_CLIPS),
        ("text", CH_GTA_CARS),
        ("voice", VOICE_GTA),
    ]),
    (CAT_BOTS, [
        ("text", CH_BOT_COMMANDS),
        ("text", CH_BOT_MUSIC),
        ("text", CH_BOT_LEVELS),
    ]),
    (CAT_STAFF, [
        ("text", CH_STAFF_CHAT),
        ("text", CH_STAFF_CONTROL),
        ("text", CH_WARNS),
        ("text", CH_LOGS),
        ("text", CH_DATA),
        ("voice", VOICE_STAFF),
    ]),
]


# =========================================================
# MIGRACIÓN DESDE EL SERVIDOR ACTUAL
# =========================================================

CATEGORY_ALIASES = {
    CAT_SERVER: ["Servidor", "📍 Servidor"],
    CAT_COMMUNITY: ["Comunidad", "🌎 Comunidad"],
    CAT_ENT: ["Entretenimiento", "🚀 Entretenimiento"],
    CAT_FRIENDS: ["Amigos", "💗 Amigos"],
    CAT_MC: ["minecraft", "Minecraft"],
    CAT_ARK: ["Dodofilicos", "Dodófilos", "🦖 Dodofilicos", "🦖 Dodófilos"],
    CAT_STAFF: ["Staff", "🧩 Staff", "🛡️ Staff"],
}

CHANNEL_ALIASES = {
    CAT_SERVER: {
        CH_WELCOME: ["Bienvenidas", "📣 Bienvenidas"],
        CH_RULES: ["Normativas", "📕 Normativas"],
        CH_SOCIALS: ["RedeSociales", "RedesSociales", "Redes Sociales", "🌐 RedeSociales"],
        CH_LIVE: ["Avisos", "🔴 Avisos"],
        CH_ANNOUNCE: ["Anuncios", "📢 Anuncios"],
        CH_WARNS: ["Warns", "❌ Warns"],
    },
    CAT_COMMUNITY: {
        CH_CHAT: ["Chat", "💬 Chat"],
        CH_BIRTHDAY: ["Cumpleaños", "🎂 Cumpleaños"],
        CH_LEVELS: ["Niveles", "💯 Niveles"],
        VOICE_COMMUNITY: ["VOZ", "Voz", "voz"],
    },
    CAT_ENT: {
        CH_DRAWINGS: ["Dibujos", "🎨 Dibujos"],
        CH_MEMES: ["Memes", "😜 Memes"],
        CH_CLIPS: ["Clips", "🎬 Clips"],
    },
    CAT_FRIENDS: {
        CH_FRIENDS_CHAT: ["ChatAmigos", "Chat Amigos", "💬 ChatAmigos"],
        CH_FRIENDS_MUSIC: ["Musica2", "Música2", "Musica", "Música"],
        VOICE_FRIENDS: ["VozAmigos", "Voz Amigos", "🔊 VozAmigos"],
    },
    CAT_MC: {
        CH_MC_MODS: ["mods", "Mods"],
        CH_MC_IP: ["ip", "IP"],
        CH_MC_CHAT: ["texto", "Texto"],
        VOICE_MC: ["voz", "Voz"],
    },
    CAT_ARK: {
        CH_ARK_CHAT: ["ark", "ARK", "💬 ark"],
        CH_ARK_PATCHES: ["ark-parches", "ark patches", "ARK-parches"],
        CH_ARK_MUSIC: ["Musica2", "Música2", "Musica", "Música"],
        VOICE_ARK: ["Voz", "voz", "🔊 Voz"],
    },
    CAT_STAFF: {
        CH_STAFF_CHAT: ["ChatAdmins", "Chat Admins", "💬 ChatAdmins"],
        CH_STAFF_CONTROL: ["ControlStaff", "Control Staff"],
        VOICE_STAFF: ["VozStaff", "Voz Staff", "🔊 VozStaff"],
    },
}


# =========================================================
# HELPERS
# =========================================================

def role_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.roles, name=name)

def category_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.categories, name=name)

def channel_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.channels, name=name)

def text_by_name(guild: discord.Guild, name: str):
    return discord.utils.get(guild.text_channels, name=name)

def is_staff(member: discord.Member):
    return member.guild_permissions.administrator or any(r.name in STAFF_ROLES for r in member.roles)

def staff_overwrites(guild):
    ow = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
    }
    if guild.me:
        ow[guild.me] = discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, manage_messages=True,
            connect=True, speak=True, move_members=True,
        )
    for name in STAFF_ROLES:
        role = role_by_name(guild, name)
        if role:
            ow[role] = discord.PermissionOverwrite(
                view_channel=True, read_message_history=True,
                send_messages=True, manage_messages=True,
                connect=True, speak=True, move_members=True,
            )
    return ow

def readonly_overwrites(guild):
    ow = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=False,
            add_reactions=True,
        )
    }
    if guild.me:
        ow[guild.me] = discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, manage_messages=True,
            embed_links=True, attach_files=True,
        )
    for name in STAFF_ROLES:
        role = role_by_name(guild, name)
        if role:
            ow[role] = discord.PermissionOverwrite(
                view_channel=True, read_message_history=True,
                send_messages=True, manage_messages=True,
                add_reactions=True, embed_links=True, attach_files=True,
            )
    return ow

def public_chat_overwrites(guild):
    ow = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, add_reactions=True,
            attach_files=True, embed_links=True,
            connect=True, speak=True,
        )
    }
    if guild.me:
        ow[guild.me] = discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, manage_messages=True,
            attach_files=True, embed_links=True,
            connect=True, speak=True, move_members=True,
        )
    return ow

def role_gate_overwrites(guild, access_role_name):
    ow = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False, read_message_history=False,
            send_messages=False, connect=False, speak=False,
        )
    }
    if guild.me:
        ow[guild.me] = discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, manage_messages=True,
            connect=True, speak=True, move_members=True,
            attach_files=True, embed_links=True,
        )

    access_role = role_by_name(guild, access_role_name)
    if access_role:
        ow[access_role] = discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, add_reactions=True,
            attach_files=True, embed_links=True,
            connect=True, speak=True,
        )

    for name in STAFF_ROLES:
        role = role_by_name(guild, name)
        if role:
            ow[role] = discord.PermissionOverwrite(
                view_channel=True, read_message_history=True,
                send_messages=True, manage_messages=True,
                connect=True, speak=True, move_members=True,
            )
    return ow

def data_overwrites(guild):
    ow = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False, read_message_history=False, send_messages=False
        )
    }
    if guild.me:
        ow[guild.me] = discord.PermissionOverwrite(
            view_channel=True, read_message_history=True,
            send_messages=True, manage_messages=True
        )
    for name in STAFF_ROLES:
        role = role_by_name(guild, name)
        if role:
            ow[role] = discord.PermissionOverwrite(
                view_channel=True, read_message_history=True,
                send_messages=True, manage_messages=True
            )
    return ow


# =========================================================
# MIGRACIÓN
# =========================================================

async def migrate_existing(guild):
    print("[1/6] Migrando estructura actual...")

    # Categorías
    for target, aliases in CATEGORY_ALIASES.items():
        if category_by_name(guild, target):
            continue
        for old in aliases:
            cat = category_by_name(guild, old)
            if cat:
                try:
                    await cat.edit(name=target, reason="ARMENKR V1 migration")
                    break
                except discord.HTTPException:
                    pass

    # Canales dentro de sus categorías para evitar conflictos como Musica2.
    for cat_target, mappings in CHANNEL_ALIASES.items():
        cat = category_by_name(guild, cat_target)
        if not cat:
            continue

        for target_name, aliases in mappings.items():
            if discord.utils.get(cat.channels, name=target_name):
                continue

            for ch in list(cat.channels):
                if ch.name in aliases:
                    try:
                        await ch.edit(name=target_name, reason="ARMENKR V1 migration")
                        break
                    except discord.HTTPException:
                        pass

    # Warns antes estaba en Servidor; moverlo a Staff.
    server = category_by_name(guild, CAT_SERVER)
    staff = category_by_name(guild, CAT_STAFF)
    if server and staff:
        warns = discord.utils.get(server.text_channels, name=CH_WARNS)
        if warns:
            try:
                await warns.edit(category=staff, reason="ARMENKR V1: warns privado")
            except discord.HTTPException:
                pass


# =========================================================
# CREACIÓN
# =========================================================

async def ensure_role(guild, name, color, hoist):
    role = role_by_name(guild, name)
    if role:
        return role
    try:
        return await guild.create_role(
            name=name,
            colour=discord.Colour(color),
            hoist=hoist,
            reason="ARMENKR V1 setup"
        )
    except discord.HTTPException:
        return None

async def ensure_roles(guild):
    print("[2/6] Verificando roles...")
    for name, color, hoist in BASE_ROLES:
        await ensure_role(guild, name, color, hoist)
        await asyncio.sleep(0.05)

async def ensure_category(guild, name):
    cat = category_by_name(guild, name)
    if cat:
        return cat

    if name == CAT_STAFF:
        ow = staff_overwrites(guild)
    elif name == CAT_FRIENDS:
        ow = role_gate_overwrites(guild, ROLE_FRIENDS)
    elif name == CAT_MC:
        ow = role_gate_overwrites(guild, ROLE_MC)
    elif name == CAT_ARK:
        ow = role_gate_overwrites(guild, ROLE_ARK)
    elif name == CAT_GTA:
        ow = role_gate_overwrites(guild, ROLE_GTA)
    else:
        ow = public_chat_overwrites(guild)

    return await guild.create_category(name=name, overwrites=ow, reason="ARMENKR V1 setup")

async def ensure_channel(guild, cat, kind, name):
    if kind == "text":
        existing = discord.utils.get(cat.text_channels, name=name)
        if existing:
            return existing

        kwargs = dict(name=name, category=cat, reason="ARMENKR V1 setup")

        if name in {CH_WELCOME, CH_RULES, CH_SOCIALS, CH_LIVE, CH_ANNOUNCE}:
            kwargs["overwrites"] = readonly_overwrites(guild)
        elif name == CH_DATA:
            kwargs["overwrites"] = data_overwrites(guild)

        return await guild.create_text_channel(**kwargs)

    existing = discord.utils.get(cat.voice_channels, name=name)
    if existing:
        return existing

    return await guild.create_voice_channel(
        name=name, category=cat, reason="ARMENKR V1 setup"
    )

async def ensure_structure(guild):
    print("[3/6] Verificando categorías y canales...")
    for cat_name, channels in BLUEPRINT:
        cat = await ensure_category(guild, cat_name)
        for kind, channel_name in channels:
            await ensure_channel(guild, cat, kind, channel_name)
            await asyncio.sleep(0.04)


# =========================================================
# PERMISOS / ORDEN
# =========================================================

async def enforce_permissions(guild):
    print("[4/6] Aplicando permisos...")

    # Información oficial
    for name in [CH_WELCOME, CH_RULES, CH_SOCIALS, CH_LIVE, CH_ANNOUNCE]:
        ch = text_by_name(guild, name)
        if ch:
            try:
                await ch.edit(overwrites=readonly_overwrites(guild), reason="ARMENKR V1 permissions")
            except discord.HTTPException:
                pass

    # Elige roles: todos pueden ver y usar apps/components, pero no escribir.
    roles_ch = text_by_name(guild, CH_ROLES)
    if roles_ch:
        ow = readonly_overwrites(guild)
        ow[guild.default_role] = discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=False,
            use_application_commands=True,
        )
        try:
            await roles_ch.edit(overwrites=ow, reason="ARMENKR V1 role selector")
        except discord.HTTPException:
            pass

    # Público
    for name in [CH_CHAT, CH_BIRTHDAY, CH_LEVELS, CH_DRAWINGS, CH_MEMES, CH_CLIPS,
                 CH_BOT_COMMANDS, CH_BOT_MUSIC, CH_BOT_LEVELS]:
        ch = text_by_name(guild, name)
        if ch:
            try:
                await ch.edit(overwrites=public_chat_overwrites(guild), reason="ARMENKR V1 public")
            except discord.HTTPException:
                pass

    # Categorías con rol
    for cat_name, role_name in [
        (CAT_FRIENDS, ROLE_FRIENDS),
        (CAT_MC, ROLE_MC),
        (CAT_ARK, ROLE_ARK),
        (CAT_GTA, ROLE_GTA),
    ]:
        cat = category_by_name(guild, cat_name)
        if cat:
            try:
                await cat.edit(overwrites=role_gate_overwrites(guild, role_name), reason="ARMENKR V1 gated")
            except discord.HTTPException:
                pass
            for ch in cat.channels:
                try:
                    await ch.edit(sync_permissions=True, reason="ARMENKR V1 sync")
                except discord.HTTPException:
                    pass

    # Staff
    staff = category_by_name(guild, CAT_STAFF)
    if staff:
        try:
            await staff.edit(overwrites=staff_overwrites(guild), reason="ARMENKR V1 staff")
        except discord.HTTPException:
            pass
        for ch in staff.channels:
            if isinstance(ch, discord.TextChannel) and ch.name == CH_DATA:
                try:
                    await ch.edit(overwrites=data_overwrites(guild), reason="ARMENKR V1 data")
                except discord.HTTPException:
                    pass
            else:
                try:
                    await ch.edit(sync_permissions=True, reason="ARMENKR V1 staff sync")
                except discord.HTTPException:
                    pass

async def organize(guild):
    desired = [
        CAT_SERVER, CAT_COMMUNITY, CAT_ENT, CAT_FRIENDS,
        CAT_MC, CAT_ARK, CAT_GTA, CAT_BOTS, CAT_STAFF,
    ]
    for pos, name in enumerate(desired):
        cat = category_by_name(guild, name)
        if cat:
            try:
                await cat.edit(position=pos, reason="ARMENKR V1 organization")
            except discord.HTTPException:
                pass

    for cat_name, channels in BLUEPRINT:
        cat = category_by_name(guild, cat_name)
        if not cat:
            continue
        for pos, (_, name) in enumerate(channels):
            ch = discord.utils.get(cat.channels, name=name)
            if ch:
                try:
                    await ch.edit(position=pos, reason="ARMENKR V1 order")
                except discord.HTTPException:
                    pass


# =========================================================
# PANEL HELPERS
# =========================================================

async def upsert_embed(channel, marker, embed, view=None):
    async for msg in channel.history(limit=50):
        if msg.author == channel.guild.me and msg.content == marker:
            try:
                await msg.edit(content=marker, embed=embed, view=view)
                return msg
            except discord.HTTPException:
                pass

    return await channel.send(content=marker, embed=embed, view=view)


# =========================================================
# SELECTOR DE ROLES
# =========================================================

class GameRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Avisos de directo",
                value="live",
                emoji="🔔",
                description="Recibe aviso cuando ARMENKR está en vivo."
            ),
            discord.SelectOption(
                label="Minecraft",
                value="minecraft",
                emoji="⛏️",
                description="Desbloquea la zona de Minecraft."
            ),
            discord.SelectOption(
                label="ARK",
                value="ark",
                emoji="🦖",
                description="Desbloquea Dodófilos / ARK."
            ),
            discord.SelectOption(
                label="GTA",
                value="gta",
                emoji="🚗",
                description="Desbloquea la zona de GTA."
            ),
        ]
        super().__init__(
            placeholder="Selecciona tus intereses...",
            min_values=0,
            max_values=len(options),
            options=options,
            custom_id="armenkr:v1:selfroles",
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return

        member = interaction.user
        selected = set(self.values)

        add_roles = []
        remove_roles = []

        for key, role_name in SELF_ROLES.items():
            role = role_by_name(interaction.guild, role_name)
            if not role:
                continue

            if key in selected and role not in member.roles:
                add_roles.append(role)
            elif key not in selected and role in member.roles:
                remove_roles.append(role)

        try:
            if add_roles:
                await member.add_roles(*add_roles, reason="ARMENKR self roles")
            if remove_roles:
                await member.remove_roles(*remove_roles, reason="ARMENKR self roles")

            chosen = [SELF_ROLES[k] for k in selected]
            await interaction.response.send_message(
                "✅ Roles actualizados."
                + (f"\n\nSeleccionados:\n" + "\n".join(f"• {x}" for x in chosen) if chosen else "\n\nNo tienes roles opcionales seleccionados."),
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No puedo cambiar esos roles. Pon el rol del bot por encima de los roles de juegos.",
                ephemeral=True,
            )

class RolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GameRoleSelect())


# =========================================================
# REDES SOCIALES
# =========================================================

SOCIAL_MARKER = "ARMENKR_SOCIALS:"
SOCIAL_KEYS = ["instagram", "tiktok", "twitch", "youtube", "x", "discord"]

def clean_url(value):
    if value is None:
        return None
    value = value.strip()
    if value.lower() in {"none", "ninguna", "quitar", "remove", "-"}:
        return ""
    if not (value.startswith("https://") or value.startswith("http://")):
        return None
    return value

async def load_socials(guild):
    ch = text_by_name(guild, CH_DATA)
    if not ch:
        return {}

    async for msg in ch.history(limit=100):
        if msg.author == guild.me and msg.content.startswith(SOCIAL_MARKER):
            raw = msg.content[len(SOCIAL_MARKER):]
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return {}

async def save_socials(guild, data):
    ch = text_by_name(guild, CH_DATA)
    if not ch:
        return

    payload = SOCIAL_MARKER + json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    async for msg in ch.history(limit=100):
        if msg.author == guild.me and msg.content.startswith(SOCIAL_MARKER):
            await msg.edit(content=payload)
            return
    await ch.send(payload)

def social_view(data):
    view = discord.ui.View(timeout=None)
    buttons = [
        ("Instagram", "📸", data.get("instagram")),
        ("TikTok", "🎵", data.get("tiktok")),
        ("Twitch", "🟣", data.get("twitch")),
        ("YouTube", "▶️", data.get("youtube")),
        ("X", None, data.get("x")),
        ("Discord", "💬", data.get("discord")),
    ]

    for label, emoji, url in buttons:
        if not url:
            continue
        kwargs = dict(label=label, style=discord.ButtonStyle.link, url=url)
        if emoji:
            kwargs["emoji"] = emoji
        view.add_item(discord.ui.Button(**kwargs))

    return view


# =========================================================
# PANELES
# =========================================================

async def refresh_panels(guild):
    # Bienvenida
    ch = text_by_name(guild, CH_WELCOME)
    if ch:
        roles = text_by_name(guild, CH_ROLES)
        chat = text_by_name(guild, CH_CHAT)
        embed = discord.Embed(
            title="👑 𝐁𝐈𝐄𝐍𝐕𝐄𝐍𝐈𝐃𝐎 𝐀 𝐋𝐀 𝐂𝐎𝐌𝐔𝐍𝐈𝐃𝐀𝐃 𝐃𝐄 𝐀𝐑𝐌𝐄𝐍𝐊𝐑",
            description=(
                "Gaming • Streams • Clips • Comunidad\n\n"
                "Este servidor mantiene la esencia que ya tenía, pero ahora está organizado "
                "para crecer como comunidad oficial de streamer."
            ),
            color=ACCENT,
        )
        embed.add_field(
            name="🚀 Empieza aquí",
            value=(
                f"1. Lee {text_by_name(guild, CH_RULES).mention if text_by_name(guild, CH_RULES) else 'las normativas'}\n"
                f"2. Elige tus juegos en {roles.mention if roles else 'elige-tus-roles'}\n"
                f"3. Pásate por {chat.mention if chat else 'el chat'}"
            ),
            inline=False,
        )
        embed.set_footer(text="ARMENKR • MÁS QUE UN STREAM. UNA COMUNIDAD.")
        await upsert_embed(ch, "ARMENKR_PANEL_WELCOME", embed)

    # Normativas
    ch = text_by_name(guild, CH_RULES)
    if ch:
        embed = discord.Embed(
            title="📕 𝐍𝐎𝐑𝐌𝐀𝐓𝐈𝐕𝐀𝐒",
            description="Reglas simples para mantener una comunidad sana y divertida.",
            color=ACCENT,
        )
        rules = [
            ("01 • Respeto", "Nada de acoso, discriminación, amenazas ni ataques personales."),
            ("02 • Spam", "Evita flood, spam de links y menciones innecesarias."),
            ("03 • Contenido", "Nada de contenido NSFW, ilegal o que ponga en riesgo a otros."),
            ("04 • Canales", "Usa cada canal para su tema para que el servidor siga ordenado."),
            ("05 • Staff", "Las decisiones de moderación se discuten en privado, no montando drama en el chat."),
            ("06 • Comunidad", "Bromear está bien; convertirlo en toxicidad constante no."),
        ]
        for title, value in rules:
            embed.add_field(name=title, value=value, inline=False)
        embed.set_footer(text="ARMENKR • Respeta. Comparte. Disfruta.")
        await upsert_embed(ch, "ARMENKR_PANEL_RULES", embed)

    # Roles
    ch = text_by_name(guild, CH_ROLES)
    if ch:
        embed = discord.Embed(
            title="🎭 𝐄𝐋𝐈𝐆𝐄 𝐓𝐔𝐒 𝐑𝐎𝐋𝐄𝐒",
            description=(
                "Selecciona lo que te interesa. Puedes cambiarlo cuando quieras.\n\n"
                "⛏️ Minecraft → desbloquea Minecraft\n"
                "🦖 ARK → desbloquea Dodófilos / ARK\n"
                "🚗 GTA → desbloquea GTA\n"
                "🔔 Directos → avisos cuando ARMENKR esté en vivo"
            ),
            color=ACCENT,
        )
        await upsert_embed(ch, "ARMENKR_PANEL_ROLES", embed, RolePanelView())

    # Redes
    ch = text_by_name(guild, CH_SOCIALS)
    if ch:
        data = await load_socials(guild)
        embed = discord.Embed(
            title="🌐 𝐑𝐄𝐃𝐄𝐒 𝐎𝐅𝐈𝐂𝐈𝐀𝐋𝐄𝐒",
            description=(
                "Sigue a **ARMENKR** y no te pierdas streams, clips y contenido.\n\n"
                + ("Usa los botones de abajo." if any(data.values()) else "⚙️ Configuración pendiente: usa `/configurarredes`.")
            ),
            color=ACCENT,
        )
        await upsert_embed(ch, "ARMENKR_PANEL_SOCIALS", embed, social_view(data))

    # Live
    ch = text_by_name(guild, CH_LIVE)
    if ch:
        embed = discord.Embed(
            title="🔴 𝐀𝐑𝐌𝐄𝐍𝐊𝐑 𝐄𝐍 𝐕𝐈𝐕𝐎",
            description=(
                "Aquí aparecen los avisos oficiales de stream.\n\n"
                "Activa `🔔・DIRECTOS` en **elige-tus-roles** si quieres recibir la notificación."
            ),
            color=0xE53935,
        )
        await upsert_embed(ch, "ARMENKR_PANEL_LIVE", embed)

    # Control staff
    ch = text_by_name(guild, CH_STAFF_CONTROL)
    if ch:
        embed = discord.Embed(
            title="⚙️ 𝐂𝐎𝐍𝐓𝐑𝐎𝐋 𝐒𝐓𝐀𝐅𝐅",
            description=(
                "`/organizar` — estructura + permisos\n"
                "`/paneles` — refresca paneles\n"
                "`/envivo` — publica un stream\n"
                "`/configurarredes` — configura enlaces\n"
                "`/testbienvenida` — prueba bienvenida"
            ),
            color=ACCENT,
        )
        await upsert_embed(ch, "ARMENKR_PANEL_STAFF", embed)


# =========================================================
# BOT
# =========================================================

class ArmenBot(commands.Bot):
    def __init__(self, guild_id):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_id = guild_id

    async def setup_hook(self):
        self.add_view(RolePanelView())

        guild_obj = discord.Object(id=self.guild_id)
        try:
            self.tree.copy_global_to(guild=guild_obj)
            synced = await self.tree.sync(guild=guild_obj)
            print(f"✅ Slash commands sincronizados: {len(synced)}")
        except Exception as exc:
            print(f"❌ Error sincronizando comandos: {exc}")


TOKEN, GUILD_ID = get_config()
bot = ArmenBot(GUILD_ID)


# =========================================================
# COMANDOS
# =========================================================

@app_commands.guild_only()
@app_commands.command(name="organizar", description="Organiza y mejora el servidor de ARMENKR.")
async def organizar_cmd(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⛔ Solo administrador.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild

    await migrate_existing(guild)
    await ensure_roles(guild)
    await ensure_structure(guild)
    await migrate_existing(guild)  # segunda pasada para mover Warns si Staff se creó ahora
    await enforce_permissions(guild)
    await organize(guild)
    await refresh_panels(guild)

    await interaction.followup.send(
        "✅ **Servidor organizado.**\n\n"
        "Mantuve la estructura original y añadí GTA, roles de juegos, paneles de streamer, "
        "avisos de directo, redes y permisos privados de Staff.",
        ephemeral=True,
    )

@app_commands.guild_only()
@app_commands.command(name="paneles", description="Actualiza los paneles oficiales.")
async def paneles(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⛔ Solo administrador.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    await refresh_panels(interaction.guild)
    await interaction.followup.send("✅ Paneles actualizados.", ephemeral=True)

@app_commands.guild_only()
@app_commands.command(name="envivo", description="Publica un aviso de stream.")
@app_commands.describe(
    plataforma="Ej: TikTok, Twitch, YouTube",
    enlace="URL completa del directo",
    titulo="Título o descripción del stream"
)
async def envivo(
    interaction: discord.Interaction,
    plataforma: str,
    enlace: str,
    titulo: Optional[str] = None,
):
    if not isinstance(interaction.user, discord.Member) or not is_staff(interaction.user):
        await interaction.response.send_message("⛔ Solo staff.", ephemeral=True)
        return

    if not enlace.startswith(("https://", "http://")):
        await interaction.response.send_message("⛔ El enlace debe empezar por https://", ephemeral=True)
        return

    channel = text_by_name(interaction.guild, CH_LIVE)
    if not channel:
        await interaction.response.send_message("❌ No encontré el canal En Vivo. Ejecuta `/organizar`.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    role = role_by_name(interaction.guild, ROLE_LIVE)
    embed = discord.Embed(
        title=f"🔴 ARMENKR ESTÁ EN VIVO — {plataforma.upper()}",
        description=(
            (f"**{titulo}**\n\n" if titulo else "")
            + "Caigan al directo y únanse a la comunidad. 🔥"
        ),
        color=0xE53935,
        url=enlace,
    )
    embed.add_field(name="🔗 Ver directo", value=f"[ENTRAR AHORA]({enlace})", inline=False)
    embed.set_footer(text="ARMENKR • MÁS QUE UN STREAM. UNA COMUNIDAD.")

    await channel.send(
        content=role.mention if role else None,
        embed=embed,
        allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
    )

    await interaction.followup.send("✅ Aviso de directo publicado.", ephemeral=True)

@app_commands.guild_only()
@app_commands.command(name="configurarredes", description="Configura las redes sociales oficiales.")
@app_commands.rename(discord_link="discord")
async def configurarredes(
    interaction: discord.Interaction,
    instagram: Optional[str] = None,
    tiktok: Optional[str] = None,
    twitch: Optional[str] = None,
    youtube: Optional[str] = None,
    x: Optional[str] = None,
    discord_link: Optional[str] = None,
):
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("⛔ Solo administrador.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    data = await load_socials(interaction.guild)
    updates = {
        "instagram": instagram,
        "tiktok": tiktok,
        "twitch": twitch,
        "youtube": youtube,
        "x": x,
        "discord": discord_link,
    }

    invalid = []
    changed = False

    for key, value in updates.items():
        if value is None:
            continue
        parsed = clean_url(value)
        if parsed is None:
            invalid.append(key)
            continue
        data[key] = parsed
        changed = True

    if invalid:
        await interaction.followup.send(
            "⛔ URLs inválidas: " + ", ".join(invalid) + ". Usa enlaces completos con `https://`.",
            ephemeral=True
        )
        return

    if not changed:
        await interaction.followup.send("ℹ️ No enviaste ningún enlace.", ephemeral=True)
        return

    await save_socials(interaction.guild, data)
    await refresh_panels(interaction.guild)
    await interaction.followup.send("✅ Redes actualizadas.", ephemeral=True)

@app_commands.guild_only()
@app_commands.command(name="testbienvenida", description="Prueba la bienvenida pública.")
@app_commands.describe(jugador="Miembro para simular la bienvenida")
async def testbienvenida(
    interaction: discord.Interaction,
    jugador: Optional[discord.Member] = None,
):
    if not isinstance(interaction.user, discord.Member) or not is_staff(interaction.user):
        await interaction.response.send_message("⛔ Solo staff.", ephemeral=True)
        return

    target = jugador or interaction.user
    await interaction.response.defer(ephemeral=True)

    ch = text_by_name(interaction.guild, CH_WELCOME)
    if not ch:
        await interaction.followup.send("❌ No existe el canal Bienvenidas.", ephemeral=True)
        return

    roles_ch = text_by_name(interaction.guild, CH_ROLES)
    embed = discord.Embed(
        title="👋 ¡NUEVO MIEMBRO!",
        description=(
            f"Bienvenido {target.mention} a **ARMENKR | Comunidad**.\n\n"
            f"Empieza por {roles_ch.mention if roles_ch else 'elige-tus-roles'} para desbloquear los juegos que te interesan."
        ),
        color=ACCENT,
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    await ch.send(embed=embed)
    await interaction.followup.send("✅ Bienvenida de prueba enviada.", ephemeral=True)


bot.tree.add_command(organizar_cmd)
bot.tree.add_command(paneles)
bot.tree.add_command(envivo)
bot.tree.add_command(configurarredes)
bot.tree.add_command(testbienvenida)


# =========================================================
# EVENTOS
# =========================================================

@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        bot_role = role_by_name(member.guild, ROLE_BOTS)
        if bot_role:
            try:
                await member.add_roles(bot_role, reason="ARMENKR bot grouping")
            except discord.HTTPException:
                pass
        return

    community = role_by_name(member.guild, ROLE_COMMUNITY)
    if community:
        try:
            await member.add_roles(community, reason="ARMENKR new member")
        except discord.HTTPException:
            pass

    ch = text_by_name(member.guild, CH_WELCOME)
    if not ch:
        return

    roles_ch = text_by_name(member.guild, CH_ROLES)
    chat = text_by_name(member.guild, CH_CHAT)

    embed = discord.Embed(
        title="👑 𝐁𝐈𝐄𝐍𝐕𝐄𝐍𝐈𝐃𝐎 𝐀 𝐋𝐀 𝐂𝐎𝐌𝐔𝐍𝐈𝐃𝐀𝐃",
        description=(
            f"Qué más, {member.mention}. Bienvenido a la comunidad oficial de **ARMENKR**. 🔥\n\n"
            "Aquí encontrarás streams, clips, gaming y gente para jugar."
        ),
        color=ACCENT,
    )
    embed.add_field(
        name="🚀 Empieza así",
        value=(
            f"🎭 {roles_ch.mention if roles_ch else 'Elige tus roles'}\n"
            f"💬 {chat.mention if chat else 'Pásate por el chat'}"
        ),
        inline=False,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="ARMENKR • MÁS QUE UN STREAM. UNA COMUNIDAD.")

    try:
        await ch.send(
            content=member.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
    except discord.HTTPException:
        pass


@bot.event
async def on_ready():
    print("=" * 60)
    print(f"👑 ARMENKR BOT conectado como {bot.user}")
    print("=" * 60)

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ No encontré el servidor configurado.")
        return

    print(f"Servidor: {guild.name}")

    try:
        await migrate_existing(guild)
        await ensure_roles(guild)
        await ensure_structure(guild)
        await migrate_existing(guild)
        await enforce_permissions(guild)
        await organize(guild)
        await refresh_panels(guild)
        print("✅ ARMENKR STREAMER SERVER V1 listo.")
    except Exception as exc:
        print(f"❌ Error de setup: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    bot.run(TOKEN)
