import os
import discord
import asyncio
import feedparser
import aiohttp

from discord.ext import tasks
from discord import app_commands
from server import stay_alive

# Umgebungsvariablen sicher lesen
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_STR = os.getenv("CHANNEL_ID")

if not DISCORD_TOKEN:
    raise ValueError(
        "❌ DISCORD_TOKEN ist nicht gesetzt! Bitte Umgebungsvariable hinzufügen."
    )

if not CHANNEL_ID_STR or not CHANNEL_ID_STR.isdigit():
    raise ValueError(
        "❌ CHANNEL_ID ist nicht gesetzt oder keine gültige Zahl! Bitte Umgebungsvariable hinzufügen."
    )

CHANNEL_ID = int(CHANNEL_ID_STR)

# YouTube-Kanäle
YOUTUBE_FEEDS = {
    "Olympic Foil":
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCCT4FI5gT5_uXuUdWZ_M8MQ",
    "FIE Fencing":
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCJEy8aBnqDymMIcJCh72gMw"
}

NEWS_FEED = "https://www.tsv-tettnang.de/news/fechten-news?type=9818"

last_video_ids = {}
last_news_title = ""

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"✅ Bot ist online als {client.user}")
    try:
        synced = await tree.sync()
        print(f"📡 Slash-Commands synchronisiert: {len(synced)} Befehle")
    except Exception as e:
        print(f"❌ Fehler beim Slash-Sync: {e}")

    check_youtube_updates.start()
    check_news_updates.start()


@tree.command(name="turniere", description="Zeigt die aktuelle Turnierliste")
async def turniere(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Hier findest du die aktuelle Turnierliste: https://www.tsv-tettnang.de/infos/fechten-infos/show/90-1"
    )


@tasks.loop(minutes=5)
async def check_youtube_updates():
    for name, url in YOUTUBE_FEEDS.items():
        feed = feedparser.parse(url)
        if not feed.entries:
            continue

        latest_video = feed.entries[0]
        video_id = latest_video.get("yt_videoid")

        if name not in last_video_ids:
            last_video_ids[name] = video_id
            continue

        if last_video_ids[name] != video_id:
            last_video_ids[name] = video_id
            title = latest_video.get("title")
            link = latest_video.get("link")
            channel = client.get_channel(CHANNEL_ID)
            # Nur wenn channel existiert und TextChannel ist
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(
                        f"🎥 Neues Video von **{name}**: **{title}**\n➡️ {link}"
                    )
                except Exception as e:
                    print(f"Fehler beim Senden der Nachricht: {e}")
            else:
                print(
                    f"⚠️ Channel mit ID {CHANNEL_ID} nicht gefunden oder kein TextChannel"
                )


@tasks.loop(minutes=10)
async def check_news_updates():
    global last_news_title

    async with aiohttp.ClientSession() as session:
        async with session.get(NEWS_FEED) as response:
            html = await response.text()
            feed = feedparser.parse(html)

            if not feed.entries:
                return

            latest_news = feed.entries[0]
            title = latest_news.get("title")
            link = latest_news.get("link")

            if last_news_title != title:
                last_news_title = title
                channel = client.get_channel(CHANNEL_ID)
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.send(
                            f"📰 Neuer Beitrag auf der Fechten-Startseite:\n**{title}**\n➡️ {link}"
                        )
                    except Exception as e:
                        print(f"Fehler beim Senden der Nachricht: {e}")
                else:
                    print(
                        f"⚠️ Channel mit ID {CHANNEL_ID} nicht gefunden oder kein TextChannel"
                    )


stay_alive()
client.run(DISCORD_TOKEN)
