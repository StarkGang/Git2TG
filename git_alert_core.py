# Copyright (C) 2020-2021 by DevsExpo@Github, < https://github.com/DevsExpo >.
# This file is part of < https://github.com/DevsExpo/FridayAssistant > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/DevsExpo/FridayAssistant/blob/master/LICENSE >
# All rights reserved.

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from html import escape
import time
import aiohttp
from sys import getsizeof
from quart import jsonify, request
import hypercorn.asyncio
import pyrogram
from hypercorn import Config
from pyrogram import Client
from pyrogram import __version__ as ve
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from quart import Quart, jsonify, request

from config import Config as config

gitalertapi = Quart(__name__)

    
port_ = config.PORT
host = config.HOST
chat = config.CHAT_ID


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [FridayAssistant] - %(levelname)s - %(message)s",
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

if not config.BOT_TOKEN:
    logging.error("Who Will Give Me BOT_TOKEN? Don't You Want To Send Alerts?")
    quit(1)
    
if not config.API_ID:
    logging.error("Who Will Give Me API_ID? Telegram Will Kill me.")
    quit(1)
    
if not config.API_HASH:
    logging.error("Who Will Give Me API_ID? Telegram Will Kill me.")
    quit(1)
    
    
gitbot = Client(
    "gitbot_app",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)


async def ping_app():
    app_url = "https://{}.herokuapp.com/".format(config.HEROKU_APP_NAME)
    async with aiohttp.ClientSession() as session:
        async with session.get(app_url) as response:
            return response.status
    return 404



@gitalertapi.route("/", methods=["GET", "POST"])
async def root():
    bot_ = "@" + str(gitbot.me.username)
    response = {
        "server_alive": True,
        "bot": bot_,
        "host": host,
        "port": port_,
        "pyrogram_version": ve,
    }
    return jsonify(response)


@gitalertapi.route("/ghook/<chat>", methods=["GET", "POST"])
async def ghoo_k(chat):
    try:
        chat = int(chat)
    except ValueError:
        chat = str(chat)
    headers = request.headers
    if not headers.get("User-Agent").startswith("GitHub-Hookshot"):
        logging.warning("Data Not From Github.")
        return "Please Webhook This URL to your Repo & Updates Will Be Sent To Chat Given As Parameter. Please README before Doing So. Ktnxbye"
    if headers.get("Content-Type") != "application/json":
        logging.error(
            f"Content type - Json Expected But Got : {headers.get('Content-Type')}"
        )
        return "Invalid Data Type"
    data = await request.get_json()
    name = data.get("organization", {}).get("login") or data.get("repository", {}).get(
        "full_name"
    )
    if not name:
        logging.warning("`Invalid / No Organisation Or Repo Found!`")
        return "Invalid Data"
    siz_ = getsizeof(str(data))
    logging.info(f"Recieved : {siz_} Of Data.")
    try:
        msg_ = await gitbot.send_message(
        chat, f"`Received {siz_} Bytes Of Data. Now Verifying..`"
    )
    except BaseException as e:
        logging.critical(f"Unable To Send Message To Chat. \nError : {e} \nApi is Exiting")
        return f"Error : {e}"
    if data.get("hook"):
        web_hook_done = f"**Webhooked 🔗** [{data['repository']['name']}]({data['repository']['html_url']}) **By ✨** [{data['sender']['login']}]({data['sender']['html_url']})"
        await msg_.edit(web_hook_done)
        return "ok"
    if data.get("issue"):
        if data.get("comment"):
            issue_comment = f"""
**💬 New Comment :** `{data['repository']['name']}` 
`{data['comment']['body']}`
[#{data['issue']['number']}]({data['comment']['html_url']})
"""
            await msg_.edit(issue_comment)
            return "ok"
        else:
            issue_c = f"""
**⚠️ New {data['action']} Issue :** `{data['repository']['name']}` 
Title : {data['issue']['title']}
{data['issue']['body'] or "No Description"}
[{data['issue']['number']}]({data['issue']['html_url']})"""
            await msg_.edit(issue_c)
            return "ok"
    if data.get("forkee"):
        fork_ = f"""
🍴 {data['forkee']['svn_url']} Forked {data['repository']['html_url']}
Total forks count is now: __{data['repository']['forks_count']} ⚡️__
"""
        await msg_.edit(fork_)
        return "ok"
    if data.get("ref_type"):
        response = f"A new {data['ref_type']} on <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> was created by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>!"
        await msg_.edit(response, parse_mode="html")
        return "ok"
    if data.get("created"):
        response = f"Branch {data['ref'].split('/')[-1]} <b>{data['ref'].split('/')[-2]}</b> on <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> was created by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>!"
        await msg_.edit(response, parse_mode="html")
        return "ok"
    if data.get("deleted"):
        response = f"Branch {data['ref'].split('/')[-1]} <b>{data['ref'].split('/')[-2]}</b> on <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> was deleted by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>!"
        await msg_.edit(response, parse_mode="html")
        return "ok"
    if data.get("forced"):
        response = f"Branch {data['ref'].split('/')[-1]} <b>{data['ref'].split('/')[-2]}</b> on <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> was forced by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>!"
        await msg_.edit(response, parse_mode="html")
        return "ok"
    if data.get("pages"):
        text = f"<a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> wiki pages were updated by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>!\n\n"
        for x in data["pages"]:
            summary = ""
            if x["summary"]:
                summary = f"{x['summary']}\n"
            text += f"📝 <b>{escape(x['title'])}</b> ({x['action']})\n{summary}<a href='{x['html_url']}'>{x['page_name']}</a> - {x['sha'][:7]}"
            if len(data["pages"]) >= 2:
                text += "\n=====================\n"
            await msg_.edit(text, parse_mode="html")
        return "ok"
    if data.get("commits"):
        commits_text = ""
        rng = len(data["commits"])
        if rng > 10:
            rng = 10
        for x in range(rng):
            commit = data["commits"][x]
            if len(escape(commit["message"])) > 300:
                commit_msg = escape(commit["message"]).split("\n")[0]
            else:
                commit_msg = escape(commit["message"])
            commits_text += f"{commit_msg}\n<a href='{commit['url']}'>{commit['id'][:7]}</a> - {commit['author']['name']} {escape('<')}{commit['author']['email']}{escape('>')}\n\n"
            if len(commits_text) > 1000:
                text = f"""✨ <b>{escape(data['repository']['name'])}</b> - New {len(data['commits'])} commits ({escape(data['ref'].split('/')[-1])})
{commits_text}
"""
                await msg_.edit(text, parse_mode="html")
                commits_text = ""
        if not commits_text:
            return "tf"
        text = f"""✨ <b>{escape(data['repository']['name'])}</b> - New {len(data['commits'])} commits ({escape(data['ref'].split('/')[-1])})
{commits_text}
"""
        if len(data["commits"]) > 10:
            text += f"\n\n<i>And {len(data['commits']) - 10} other commits</i>"
        await msg_.edit(text, parse_mode="html")
        return "ok"
    if data.get("pull_request"):
        if data.get("comment"):
            text = f"""❗ There is a new pull request for <b>{escape(data['repository']['name'])}</b> ({data['pull_request']['state']})
{escape(data['comment']['body'])}
<a href='{data['comment']['html_url']}'>Pull request #{data['issue']['number']}</a>
"""
            await msg_.edit(text, parse_mode="html")
            return "ok"
        text = f"""❗  New {data['action']} pull request for <b>{escape(data['repository']['name'])}</b>
<b>{escape(data['pull_request']['title'])}</b> ({data['pull_request']['state']})
{escape(data['pull_request']['body'])}
<a href='{data['pull_request']['html_url']}'>Pull request #{data['pull_request']['number']}</a>
"""
        await msg_.edit(text, parse_mode="html")
        return "ok"
    if data.get("action"):
        if data.get("action") == "published" and data.get("release"):
            text = f"<a href='{data['sender']['html_url']}'>{data['sender']['login']}</a> {data['action']} <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a>!"
            text += f"\n\n<b>{data['release']['name']}</b> ({data['release']['tag_name']})\n{data['release']['body']}\n\n<a href='{data['release']['tarball_url']}'>Download tar</a> | <a href='{data['release']['zipball_url']}'>Download zip</a>"
            await msg_.edit(text, parse_mode="html")
            return "ok"
        if data.get("action") == "started":
            text = f"🌟 <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a> gave a star to <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a>!\n<b>Total StarGazers :</b> <i>{data['repository']['stargazers_count']} </i>"
            await msg_.edit(text, parse_mode="html")
            return "ok"
        if data.get("action") == "edited" and data.get("release"):
            text = f"<a href='{data['sender']['html_url']}'>{data['sender']['login']}</a> {data['action']} <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a>!"
            text += f"\n\n<b>{data['release']['name']}</b> ({data['release']['tag_name']})\n{data['release']['body']}\n\n<a href='{data['release']['tarball_url']}'>Download tar</a> | <a href='{data['release']['zipball_url']}'>Download zip</a>"
            await msg_.edit(text, parse_mode="html")
            return "ok"
    if data.get("context"):
        if data.get("state") == "pending":
            emo = "⏳"
        elif data.get("state") == "success":
            emo = "✔️"
        elif data.get("state") == "failure":
            emo = "❌"
        else:
            emo = "🌀"
        await msg_.edit(
            f"{emo} <a href='{data['target_url']}'>{data['description']}</a> on <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a> by <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a>! \nLatest commit:\n<a href='{data['commit']['commit']['url']}'>{escape(data['commit']['commit']['message'])}</a>",
            parse_mode="html",
        )
        return "ok"
    await msg_.delete()
    return "tf"
  

if config.HEROKU_APP_NAME:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(ping_app, 'interval', minutes=config.PING_TIME)
    scheduler.start()


@gitbot.on_message(filters.command(["start", "help"]))
async def bot_(client, message):
    key_board = [
        InlineKeyboardButton(
            text="Source Code", url="https://github.com/DevsExpo/GitAlertBot"
        ),
    ]
    file = "https://i.makeagif.com/media/2-18-2016/M3yKm-.gif"
    msg = f"__Hello__ {message.from_user.mention}. __I Am A Simple Git ALert Bot. I Notify In Chat When My Hook Gets Triggred From Github. You Can Find My Source Code on Github.com__"
    await message.reply_animation(
        file, caption=msg, quote=True, reply_markup=InlineKeyboardMarkup([key_board])
    )


async def run():
    logging.info("[Starting] [GitBot] - Bot & Server")
    await gitbot.start()
    gitbot.me = await gitbot.get_me()
    config_ = Config()
    config_.bind = [f"{host}:{port_}"]
    await hypercorn.asyncio.serve(gitalertapi, config_)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
