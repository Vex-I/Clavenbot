
from discord.ext import commands
from discord.ext.commands import Context
import discord
import praw
import random
import os


class Template(commands.Cog, name="memeoftheday"):
    """
    A cog that retrieves a random meme from r/memes.
    """
    def __init__(self, bot) -> None:
        self.bot = bot
        self.reddit = praw.Reddit(
            client_id = os.getenv("CLIENT_ID"),
            client_secret = os.getenv("CLIENT_SECRET"),
            user_agent = os.getenv("USER_AGENT")
        )
    
    async def fetchMemes(self):
        """
        Fetches a list of 50 memes from reddit. Picks one at random
        """
        subreddit = self.reddit.subreddit("memes")
        posts = [post for post in subreddit.hot(limit=50) if not post.stickied]
        meme = random.choice(posts)
        return meme.title, meme.url





    @commands.hybrid_command(
        name="meme",
        description="This fetches a random top posts from r/memes.",
    )
    async def Meme(self, context: Context) -> None:
        title, url = self.fetchMemes()
        embed = discord.Embed(title=title, color=discord.Color.random())
        embed.set_image(url=url)
        await context.send(embed=embed)


async def setup(bot) -> None:
    await bot.add_cog(Template(bot))
