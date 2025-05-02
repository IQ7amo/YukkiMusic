#
# Copyright (C) 2024-2025 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import platform
from sys import version as pyver

import psutil
from pytgcalls.__version__ import __version__ as pytgver
from telethon import Button, events

import config
from strings import get_string
from YukkiMusic import tbot
from YukkiMusic.core import filters as flt
from YukkiMusic.core.userbot import assistants
from YukkiMusic.misc import BANNED_USERS, SUDOERS
from YukkiMusic.platforms import youtube
from YukkiMusic.utils.database import (
    get_global_tops,
    get_particulars,
    get_queries,
    get_served_chats,
    get_served_users,
    get_sudoers,
    get_top_chats,
    get_topp_users,
)
from YukkiMusic.utils.decorators.language import language
from YukkiMusic.utils.inline.stats import (
    back_stats_buttons,
    back_stats_markup,
    get_stats_markup,
    overallback_stats_markup,
    stats_buttons,
    top_ten_stats_markup,
)

loop = asyncio.get_event_loop()


@tbot.on_message(flt.command("STATS_COMMAND", True) & ~BANNED_USERS)
@language
async def stats_command(event, _):
    _ = get_string("en")
    upl = stats_buttons(_, event.sender_id in SUDOERS)
    await event.reply(
        _["gstats_11"].format(tbot.me.username), file=config.STATS_IMG_URL, buttons=upl
    )


@tbot.on_message(flt.command("GSTATS_COMMAND", True) & ~BANNED_USERS)
@language
async def gstats_command(event, _):
    mystic = await event.reply(_["gstats_1"])

    async def get_stats():
        stats = await get_global_tops()
        if not stats:
            return None, None

        results = {}
        for i in stats:
            results[str(i)] = stats[i]["spot"]

        list_arranged = dict(
            sorted(results.items(), key=lambda item: item[1], reverse=True)
        )

        for vidid, count in list_arranged.items():
            if vidid != "telegram":
                return vidid, count
        return None, None

    try:
        videoid, co = await get_stats()
        if not videoid:
            await mystic.edit(_["gstats_2"])
            return

        track_info = await youtube.track(videoid, True)
        title = track_info[0].title()
        thumbnail = track_info[3]
        final = f"Top played Tracks on {tbot.me.username}\n\n**Title:** {title}\n\nPlayed** {co} **times"
        upl = get_stats_markup(_, event.sender_id in SUDOERS)

        await tbot.send_file(event.chat_id, thumbnail, caption=final, buttons=upl)
        await mystic.delete()

    except Exception as e:
        await mystic.edit(f"Error: {str(e)}")
        raise


@tbot.on(events.CallbackQuery(pattern="GetStatsNow", func=~BANNED_USERS))
@language
async def handle_get_stats(event, _):
    what = event.pattern_match.group(1).decode()
    upl = back_stats_markup(_)

    try:
        await event.answer()
    except:
        pass

    chat_id = event.chat_id
    mystic = await event.edit(
        _["gstats_3"].format(f"ᴏғ {event.chat.title}" if what == "Here" else what)
    )

    if what == "Tracks":
        stats = await get_global_tops()
    elif what == "Chats":
        stats = await get_top_chats()
    elif what == "Users":
        stats = await get_topp_users()
    elif what == "Here":
        stats = await get_particulars(chat_id)

    if not stats:
        await mystic.edit(_["gstats_2"], buttons=upl)
        return

    queries = await get_queries()
    results = {}

    for i in stats:
        key = str(i)
        if what in ["Chats", "Users"]:
            results[key] = stats[i]
        else:
            results[key] = stats[i]["spot"]

    list_arranged = dict(
        sorted(results.items(), key=lambda item: item[1], reverse=True)
    )
    msg = ""
    limit = 0
    total_count = 0

    if what in ["Tracks", "Here"]:
        for items, count in list_arranged.items():
            total_count += count
            if limit >= 10:
                continue
            limit += 1
            details = stats.get(items, {})
            title = (details.get("title", "")[:35]).title()
            if items == "telegram":
                msg += f"🔗[Telegram Videos and media's](https://t.me/telegram) ** Played {count} Times**\n\n"
            else:
                msg += f"🔗 [{title}](https://www.youtube.com/watch?v={items}) ** Played {count} Times**\n\n"

        temp = (
            _["gstats_4"].format(
                queries, tbot.me.username, len(stats), total_count, limit
            )
            if what == "Tracks"
            else _["gstats_7"].format(len(stats), total_count, limit)
        )
        msg = temp + msg
    else:
        for items, count in list_arranged.items():
            if limit >= 10:
                break
            try:
                if what == "Users":
                    user = await tbot.get_entity(int(items))
                    name = user.first_name
                else:
                    chat = await tbot.get_entity(int(items))
                    name = chat.title
                msg += f"🔗`{name}` Played {count} Times on bot.\n\n"
                limit += 1
            except:
                continue

        temp = (
            _["gstats_5"].format(limit, tbot.me.username)
            if what == "Chats"
            else _["gstats_6"].format(limit, tbot.me.username)
        )
        msg = temp + msg

    await event.edit(msg, file=config.GLOBAL_IMG_URL, buttons=upl)


@tbot.on(events.CallbackQuery(pattern="TopOverall", func=~BANNED_USERS))
@language
async def handle_top_overall(event, _):
    what = event.pattern_match.group(1).decode()

    if what == "sudo":
        if event.sender_id not in SUDOERS:
            await event.answer("Only for sudo users", alert=True)
            return

        # Sudo stats implementation
        sc = platform.system()
        p_core = psutil.cpu_count(logical=False)
        t_core = psutil.cpu_count(logical=True)
        ram = f"{round(psutil.virtual_memory().total / (1024.0**3))} GB"

        try:
            cpu_freq = psutil.cpu_freq().current
            cpu_freq = (
                f"{round(cpu_freq / 1000, 2)}GHz"
                if cpu_freq >= 1000
                else f"{round(cpu_freq, 2)}MHz"
            )
        except:
            cpu_freq = "Unable to Fetch"

        hdd = psutil.disk_usage("/")
        total = f"{hdd.total / (1024.0**3):.2f}"
        used = f"{hdd.used / (1024.0**3):.2f}"
        free = f"{hdd.free / (1024.0**3):.2f}"

        served_chats = len(await get_served_chats())
        served_users = len(await get_served_users())
        blocked = len(BANNED_USERS)
        sudoers = len(await get_sudoers())
        total_queries = await get_queries()

        text = f"""**Bot Stats and Information:**

**Platform:** {sc}
**RAM:** {ram}
**Physical Cores:** {p_core}
**Total Cores:** {t_core}
**CPU Frequency:** {cpu_freq}

**Python Version:** {pyver.split()[0]}
**Py-tgcalls Version:** {pytgver}
**Total Storage:** {total} GiB
**Used Storage:** {used} GiB
**Free Storage:** {free} GiB

**Served Chats:** {served_chats}
**Served Users:** {served_users}
**Blocked Users:** {blocked}
**Sudo Users:** {sudoers}
**Total Queries:** `{total_queries}`"""

        await event.edit(
            text, file=config.STATS_IMG_URL, buttons=overallback_stats_markup(_)
        )

    else:
        # Normal stats implementation
        served_chats = len(await get_served_chats())
        served_users = len(await get_served_users())
        total_queries = await get_queries()
        blocked = len(BANNED_USERS)
        sudoers = len(SUDOERS)
        mod = len(assistants)
        playlist_limit = config.SERVER_PLAYLIST_LIMIT
        fetch_playlist = config.PLAYLIST_FETCH_LIMIT
        song = config.SONG_DOWNLOAD_DURATION
        play_duration = config.DURATION_LIMIT_MIN
        ass = "Yes" if config.AUTO_LEAVING_ASSISTANT else "No"

        text = f"""**Bot's Stats and Information:**

**Loaded Modules:** {mod}
**Served Chats:** {served_chats}
**Served Users:** {served_users}
**Blocked Users:** {blocked}
**Sudo Users:** {sudoers}

**Total Queries:** {total_queries}
**Total Assistants:** {len(assistants)}
**Auto Leaving Assistant:** {ass}

**Play Duration Limit:** {play_duration} mins
**Song Download Limit:** {song} mins
**Server Playlist Limit:** {playlist_limit}
**Playlist Fetch Limit:** {fetch_playlist}"""

        await event.edit(
            text, file=config.STATS_IMG_URL, buttons=overallback_stats_markup(_)
        )


@tbot.on(
    events.CallbackQuery(
        pattern="(TOPMARKUPGET|GETSTATS|GlobalStats)", func=~BANNED_USERS
    )
)
@language
async def handle_stats_buttons(event, _):
    command = event.pattern_match.group(1).decode()

    if command == "TOPMARKUPGET":
        await event.edit(
            _["gstats_9"], file=config.GLOBAL_IMG_URL, buttons=top_ten_stats_markup(_)
        )
    elif command == "GlobalStats":
        await event.edit(
            _["gstats_10"].format(tbot.me.username),
            file=config.GLOBAL_IMG_URL,
            buttons=get_stats_markup(_, event.sender_id in SUDOERS),
        )
    elif command == "GETSTATS":
        await event.edit(
            _["gstats_11"].format(tbot.me.username),
            file=config.STATS_IMG_URL,
            buttons=stats_buttons(_, event.sender_id in SUDOERS),
        )
