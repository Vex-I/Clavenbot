from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from discord import ui
from discord import TextStyle
from discord import Interaction
import discord
import aiosqlite

class LogModal(ui.Modal):
    def __init__(self, user_id: str, log_id: int = None):
        """
        user_id: the Discord user id
        log_id: optional, if provided, this modal will EDIT an existing log; 
                otherwise it will CREATE a new log
        """
        super().__init__(title="Minecraft Log")
        self.user_id = user_id
        self.log_id = log_id

        # Modal Inputs
        self.x = ui.TextInput(label="X Coordinate", placeholder="Enter coordinate", required=True)
        self.y = ui.TextInput(label="Y Coordinate", placeholder="Enter coordinate", required=True)
        self.z = ui.TextInput(label="Z Coordinate", placeholder="Enter coordinate", required=True)
        self.desc = ui.TextInput(label="Description", style=TextStyle.paragraph, placeholder="Describe what you did", required=True)

        self.add_item(self.x)
        self.add_item(self.y)
        self.add_item(self.z)
        self.add_item(self.desc)

    async def on_submit(self, interaction: discord.Interaction):
        async with aiosqlite.connect("database/database.db") as db:
            if self.log_id:
                # Edit existing log
                await db.execute(
                    "UPDATE mc_logs SET x=?, y=?, z=?, description=? WHERE id=? AND user_id=?",
                    (int(self.x.value), int(self.y.value), int(self.z.value), self.desc.value, self.log_id, self.user_id)
                )
                await db.commit()
                await interaction.response.send_message(f"Log #{self.log_id} updated!", ephemeral=True)
            else:
                # Add new log
                await db.execute(
                    "INSERT INTO mc_logs (user_id, x, y, z, description) VALUES (?, ?, ?, ?, ?)",
                    (self.user_id, int(self.x.value), int(self.y.value), int(self.z.value), self.desc.value)
                )
                await db.commit()
                await interaction.response.send_message(f"New log added!", ephemeral=True)


class CoordinateLogging(commands.Cog, name="coordinatelogging"):
    """
    Handles user-created logs of coordinates, storing them in the database.
    Each CoordinateLog consists of Coordinate, author, creation date and description.
    """
    def __init__(self, bot) -> None:
        self.bot = bot


    async def sendRows(self, context:Context, rows):
        message = "**Minecraft Logs:**\n" 
        for row in rows:
            id, user_id, x, y, z, desc, timestamp = row
            message += (
                f"{id} | {user_id}"
                f" | Coordinates: ({x}, {y}, {z})"
                f" | Edited at: {timestamp}"
                f" | {desc}\n\n"
            )
        
            if len(message) > 1800:
                await context.send(message)
                message = ""
    
        if message:
            await context.send(message)

    @commands.hybrid_command(
        name="loglist",
        description="List all the logs created.",
    )
    @app_commands.describe(
        param = "Options for displaying logs. Can be 'head', 'tail' or 'all'"
    )
    async def loglist(self, context: Context, param : str  = "tail") -> None:
        async with aiosqlite.connect("database/database.db") as db:
            parameter = param.lower()

            match parameter:
                case "head":
                    query = "SELECT id, user_id, x, y, z, description, created_at FROM mc_logs ORDER BY id ASC LIMIT 5"
                case "tail":
                    query ="SELECT id, user_id, x, y, z, description, created_at FROM mc_logs ORDER BY id DESC LIMIT 5"
                case "all":
                    query = "SELECT id, user_id, x, y, z, description, created_at FROM mc_logs ORDER BY id ASC"

            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
    
        if not rows:
            await context.send("No logs found in the database!")
            return
        #Chunking the message to bypass discord's 2000 char limit
        await self.sendRows(context, rows)
            
    
    @commands.hybrid_command(
        name="log",
        description="create a new log"
    )
    async def log(self, context: Context):
        modal = LogModal(user_id=str(context.author.id))
        if context.interaction:  # was triggered as slash
            await context.interaction.response.send_modal(modal)
        else:
            await context.send("Modals only work with slash commands.")
    

    @commands.hybrid_command(
        name="logbyname",
        description="search logs by the author"
    )
    @app_commands.describe(
        name = "The discord username of the log author"
    )
    async def logbyname(self, context: Context, name : str) -> None:
        author = name.lower()
        async with aiosqlite.connect("database/database.db") as db:
            async with db.execute(
            "SELECT id, user_id, x, y, z, description, created_at "
            "FROM mc_logs WHERE user_id = ? ORDER BY id ASC", 
            (author,)
            ) as cursor:
                rows = await cursor.fetchall()
        if not rows:
            await context.send(f"No logs by '{name}'")
        
        #Chunking the message to avoid char limit
        await self.sendRows(context, rows)
        
    @commands.hybrid_command(
        name="logbydate",
        description="Search logs by date of edit"
    )
    async def logbydate(self, context: Context, date : str) -> None:
        ## date is in datetime, with the format YYYY-MM-DD
        async with aiosqlite.connect("database/database.db") as db:
            async with db.execute(
            "SELECT id, user_id, x, y, z, description, created_at "
            "FROM mc_logs WHERE created_at = ? ORDER BY id ASC", 
            (date,)
            ) as cursor:
                rows = await cursor.fetchall()
        if not rows:
            await context.send(f"No logs made at '{date}'")
        
        #Chunking the message to avoid char limit
        await self.sendRows(context, rows)

    @commands.hybrid_command(
        name = "editlog", 
        description="Edit a log, specified by it's log_id")
    async def editlog(self, context: Context, log_id: int):
        modal = LogModal(user_id=str(context.author.id), log_id=log_id)
        if context.interaction:  # was triggered as slash
            await context.interaction.response.send_modal(modal)
        else:
            await context.send("Modals only work with slash commands.")


    @commands.hybrid_command(
        name="deletelog",
        description="Delete a Minecraft log by it's log_id"
    )
    async def deletelog(self, context: Context, log_id: int):
        user_id = str(context.author.id)

        async with aiosqlite.connect("database/database.db") as db:
            async with db.execute(
                "SELECT id FROM mc_logs WHERE id = ? AND user_id = ?",
                (log_id, user_id)
            ) as cursor:
                log = await cursor.fetchone()

            if not log:
                await context.send(f"No log found with ID {log_id} for you.")
                return
            await db.execute(
                "DELETE FROM mc_logs WHERE id = ? AND user_id = ?",
                (log_id, user_id)
            )
            await db.commit()
        await context.send(f"Log #{log_id} has been deleted.")
        
async def setup(bot):
    await bot.add_cog(CoordinateLogging(bot))
