#
# Copyright (C) 2024-2025 by TheTeamVivek@Github, < https://github.com/TheTeamVivek >.
#
# This file is part of < https://github.com/TheTeamVivek/YukkiMusic > project,
# and is released under the MIT License.
# Please see < https://github.com/TheTeamVivek/YukkiMusic/blob/master/LICENSE >
#
# All rights reserved.
#

import os
import re
from telethon import Button, events
from telethon.tl.types import InputMediaDocument, InputMediaPhoto

import yt_dlp
from config import SONG_DOWNLOAD_DURATION, SONG_DOWNLOAD_DURATION_LIMIT
from strings import command
from YukkiMusic import Platform, tbot
from YukkiMusic.core import filters as flt
from YukkiMusic.misc import BANNED_USERS
from YukkiMusic.platforms.Youtube import cookies
from YukkiMusic.utils.decorators import language
from YukkiMusic.utils.formatters import convert_bytes
from YukkiMusic.utils.inline.song import song_markup

@tbot.on(flt.command("SONG_COMMAND"), True) & flt.group & ~BANNED_USERS)
@language
async def song_command_group(event, _):
    buttons = [
        [Button.url(_["SG_B_1"], f"https://t.me/{tbot.me.username}?start=song")]
    ]
    await event.reply(_["song_1"], buttons=buttons)

@tbot.on(flt.command("SONG_COMMAND"), True) & flt.private & ~BANNED_USERS)
@language
async def song_command_private(event, _):
    try:
        await event.delete()
    except:
        pass

    url = await Platform.telegram.get_url_from_message(event)

    if url:
        if not await Platform.youtube.valid(url):
            return await event.reply(_["song_5"])

        mystic = await event.reply(_["play_1"])

        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await Platform.youtube.track(url)

        if str(duration_min) == "None":
            return await mystic.edit(_["song_3"])

        if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
            return await mystic.edit(
                _["play_4"].format(SONG_DOWNLOAD_DURATION, duration_min)
            )

        buttons = song_markup(_, vidid)
        await mystic.delete()

        if thumbnail:
            return await event.client.send_file(
                event.chat_id,
                thumbnail,
                caption=_["song_4"].format(title),
                buttons=buttons
            )
        else:
            return await event.reply(_["song_4"].format(title), buttons=buttons)
    else:
        if len(event.text.split()) < 2:
            return await event.reply(_["song_2"])

    mystic = await event.reply(_["play_1"])
    query = event.text.split(None, 1)[1]

    try:
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await Platform.youtube.track(query)
    except Exception:
        return await mystic.edit(_["play_3"])

    if str(duration_min) == "None":
        return await mystic.edit(_["song_3"])

    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit(
            _["play_6"].format(SONG_DOWNLOAD_DURATION, duration_min)
        )

    buttons = song_markup(_, vidid)
    await mystic.delete()

    if thumbnail:
        return await event.client.send_file(
            event.chat_id,
            thumbnail,
            caption=_["song_4"].format(title),
            buttons=buttons
        )
    else:
        return await event.reply(_["song_4"].format(title), buttons=buttons)

@tbot.on(events.CallbackQuery(pattern="song_back", func=~BANNED_USERS))
@language
async def songs_back_helper(event, _):
    callback_data = event.data.decode().strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    buttons = song_markup(_, vidid)
    await event.edit(buttons=buttons)

@tbot.on(events.CallbackQuery(pattern="song_helper", func=~BANNED_USERS))
@language
async def song_helper_cb(event, _):
    callback_data = event.data.decode().strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")

    if stype == "audio":
        try:
            formats_available, link = await Platform.youtube.formats(vidid, True)
        except Exception:
            return await event.edit(_["song_7"])

        buttons = []
        done = []

        for x in formats_available:
            check = x["format"]
            if "audio" in check:
                if x["filesize"] is None:
                    continue

                form = x["format_note"].title()
                if form not in done:
                    done.append(form)
                else:
                    continue

                sz = convert_bytes(x["filesize"])
                fom = x["format_id"]

                buttons.append(
                    [Button.inline(
                        f"{form} Quality Audio = {sz}",
                        data=f"song_download {stype}|{fom}|{vidid}"
                    )]
                )

        buttons.append([
            Button.inline(_["BACK_BUTTON"], data=f"song_back {stype}|{vidid}"),
            Button.inline(_["CLOSE_BUTTON"], data="close")
        ])

        await event.edit(buttons=buttons)
    else:
        try:
            formats_available, link = await Platform.youtube.formats(vidid, True)
        except Exception as e:
            print(e)
            return await event.edit(_["song_7"])

        buttons = []
        done = [160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266]

        for x in formats_available:
            check = x["format"]
            if x["filesize"] is None:
                continue
            if int(x["format_id"]) not in done:
                continue

            sz = convert_bytes(x["filesize"])
            ap = check.split("-")[1]
            to = f"{ap} = {sz}"

            buttons.append(
                [Button.inline(
                    to,
                    data=f"song_download {stype}|{x['format_id']}|{vidid}"
                )]
            )

        buttons.append([
            Button.inline(_["BACK_BUTTON"], data=f"song_back {stype}|{vidid}"),
            Button.inline(_["CLOSE_BUTTON"], data="close")
        ])

        await event.edit(buttons=buttons)

@tbot.on(events.CallbackQuery(pattern="song_download", func=~BANNED_USERS))
@language
async def song_download_cb(event, _):
    callback_data = event.data.decode().strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, format_id, vidid = callback_request.split("|")

    mystic = await event.edit(_["song_8"])
    yturl = f"https://www.youtube.com/watch?v={vidid}"

    with yt_dlp.YoutubeDL({"quiet": True, "cookiefile": f"{cookies()}"}) as ytdl:
        x = ytdl.extract_info(yturl, download=False)

    title = (x["title"]).title()
    title = re.sub(r"\W+", " ", title)

    try:
        thumb_image_path = await event.client.download_media(event.message.media)
    except:
        thumb_image_path = None

    duration = x["duration"]

    if stype == "video":
        try:
            file_path = await Platform.youtube.download(
                yturl,
                mystic,
                songvideo=True,
                format_id=format_id,
                title=title,
            )
        except Exception as e:
            return await mystic.edit(_["song_9"].format(e))

        try:
            await event.client.send_file(
                event.chat_id,
                file_path,
                supports_streaming=True,
                caption=title,
                thumb=thumb_image_path,
                attributes=[
                    types.DocumentAttributeVideo(
                        duration=duration,
                        w=event.message.media.width,
                        h=event.message.media.height
                    )
                ]
            )
            await mystic.delete()
        except Exception as e:
            print(e)
            return await mystic.edit(_["song_10"])
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            if thumb_image_path and os.path.exists(thumb_image_path):
                os.remove(thumb_image_path)

    elif stype == "audio":
        try:
            filename = await Platform.youtube.download(
                yturl,
                mystic,
                songaudio=True,
                format_id=format_id,
                title=title,
            )
        except Exception as e:
            return await mystic.edit(_["song_9"].format(e))

        try:
            await event.client.send_file(
                event.chat_id,
                filename,
                caption=title,
                thumb=thumb_image_path,
                attributes=[
                    types.DocumentAttributeAudio(
                        duration=duration,
                        title=title,
                        performer=x["uploader"]
                    )
                ]
            )
            await mystic.delete()
        except Exception as e:
            print(e)
            return await mystic.edit(_["song_10"])
        finally:
            if os.path.exists(filename):
                os.remove(filename)
            if thumb_image_path and os.path.exists(thumb_image_path):
                os.remove(thumb_image_path)
