from discord.ext import commands, tasks
import discord
import time

FORUM_CHANNELS_COOLDOWN_MAP = {
    1023274993045471272: 3600,  # 🐸┃dank-memer
    1025640363811143710: 3600,  # 🤖┃all-bots
    1025637841608388608: 10800,  # 🔱┃premium-all-bots
    1025636802134028318: 21600,  # 🥉┃tier-3-all-bots¹
    1025636756709720144: 43200,  # 🥈┃tier-2-all-bots
    1025636171780468736: 86400,  # 🏆┃tier-1-all-bots
}


class ForumChannels(commands.Cog):
    """
    Archive and lock forum threads after a certain amount of time
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.archive_and_lock_threads.start()

    @commands.Cog.listener(name="on_raw_thread_update")
    async def forum_channel_archived(self, payload: discord.RawThreadUpdateEvent):
        data = payload.data
        if payload.parent_id not in FORUM_CHANNELS_COOLDOWN_MAP:
            return

        if payload.data["thread_metadata"]["archived"] is False or payload.data["thread_metadata"]["locked"] is False:
            return

        farm = self.bot.get_guild(645753561329696785)
        thread = payload.thread or await farm.fetch_channel(payload.thread_id)
        owner_id = int(data["owner_id"])

        async for entry in farm.audit_logs(
            limit=10, action=discord.AuditLogAction.thread_update
        ):
            if entry.target.id != thread.id:
                continue
                
            if entry.user.id == 855270214656065556:
                return
                
            else:
                hours_of_inactivity = (
                    FORUM_CHANNELS_COOLDOWN_MAP[payload.parent_id] // 3600
                )
                await thread.edit(
                        locked=False, archived=False, reason="User tried closing thread"
                    )
                return await thread.send(
                    f"You cannot archive or lock this thread. It has been unarchived and will be automatically archived after {hours_of_inactivity} hour{' s'[bool(hours_of_inactivity-1)]} of inactivity."
                )

    @tasks.loop(minutes=30)
    async def archive_and_lock_threads(self):
        for forum_id, auto_archive_duration in FORUM_CHANNELS_COOLDOWN_MAP.items():
            forum = self.bot.get_channel(forum_id) or await self.bot.fetch_channel(
                forum_id
            )

            for thread in reversed(forum.threads):
                timestamp = ((thread.last_message_id >> 22) + 1420070400000) / 1000
                if time.time() - timestamp >= auto_archive_duration:
                    await thread.send(
                        "Thread has been archived and locked due to inactivity. Please create a new thread if you wish to continue using the bot"
                    )
                    await thread.edit(
                        locked=True, archived=True, reason="Archived due to inactivity"
                    )


async def setup(bot: commands.Bot):
    await bot.add_cog(ForumChannels(bot))
