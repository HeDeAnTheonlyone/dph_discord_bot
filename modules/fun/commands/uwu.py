import json
from utils.uwufier import Uwuifier
import disnake
from disnake.ext import commands

class UwuCommand(commands.Cog, name="uwu"):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="uwu")
    async def uwu(self, inter: disnake.ApplicationCommandInteraction):
        return
    
    @uwu.sub_command("message","Send an uwufied message")
    async def message(self, inter: disnake.ApplicationCommandInteraction, text: str):
        hooks = await inter.channel.webhooks()

        for hook in hooks:
            if hook.name == "DPH":
                break
        else:
            hook = await inter.channel.create_webhook(name="DPH")
        uwu = Uwuifier()
        await hook.send(uwu.uwuify_sentence(text.lower()),wait=False,username=inter.author.display_name,avatar_url=inter.author.display_avatar.url,allowed_mentions=disnake.AllowedMentions.none())
    
    @uwu.sub_command("auto","Enable the auto uwufier")
    async def message(self, inter: disnake.ApplicationCommandInteraction):
        with open("uwufied.json","r+") as fp:
            data: list[int] = json.load(fp)
            if inter.author.id in data:
                data.remove(inter.author.id)
                await inter.response.send_message("**Disabled** auto uwufier for user " + inter.author.display_name)
            else:
                data.append(inter.author.id)
                await inter.response.send_message("**Enabled** auto uwufier for user " + inter.author.display_name)
            with open("uwufied.json","w") as fp:
                fp.seek(0)
                json.dump(data,fp)
                fp.close()
            fp.close()
            