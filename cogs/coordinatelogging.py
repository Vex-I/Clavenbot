
from discord.ext import commands
from discord.ext.commands import Context



class CoordinateLogging(commands.Cog, name="coordinatelogging"):
    """
    Handles user-created logs of coordinates, storing them in the database.
    Each CoordinateLog consists of Coordinate, author, creation date and description.
    """
    def __init__(self, bot) -> None:
        self.bot = bot

    

    @commands.hybrid_command(
        name="loglist",
        description="List all the logs created.",
    )
    async def loglist(self, context: Context) -> None:
        
        pass



async def setup(bot):
    await bot.add_cog(CoordinateLogging(bot))
