import disnake
from disnake.ext import commands
import variables
import regex as re
import json


class OnMessage(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if (
            type(message.channel) is disnake.Thread
            and message.channel.parent.get_tag_by_name("RESOLVED")
            in message.channel.applied_tags
            and not (message.author.id == self.bot.user.id)
        ):
            await message.channel.remove_tags(
                message.channel.parent.get_tag_by_name("RESOLVED")
            )
            await message.reply(
                "**Re-opened the channel.** Make sure to close it again once you're done.",
                components=[
                    disnake.ui.Button(
                        label="Close Question", custom_id="resolve_question_button"
                    )
                ],
            )
        if (
            type(message.channel) is disnake.Thread
            and message.channel.parent.id in variables.help_channels
            and message.author.id == message.channel.owner_id
        ):
            c = message.content.lower()
            if not (
                "thanks" in c
                or "thank you" in c
                or "thx" in c
                or "ty" in c
                or "tysm" in c
            ):
                return

            mention = re.findall("<@([0-9]*)>", c)
            if not mention:
                await message.reply(
                    "If someone has helped you resolve your question, make sure to thank them by typing `thanks @user` 🤝"
                )
            else:
                with open("/root/dph_bot/discord/points.json", "r+") as fp:
                    fp.seek(0)
                    data = json.loads(fp.read())
                    if str(mention[0]) in data:
                        data[str(mention[0])] += 1
                    else:
                        data[str(mention[0])] = 1
                    fp.seek(0)
                    fp.write(json.dumps(data))
                    fp.close()

                await message.add_reaction("🤝")
                await message.reply(
                    embed=disnake.Embed(
                        title="Is your question done?",
                        description=f"We're happy that <@{mention[0]!s}> helped you with your question!\n\nIf your question is now done, please don't forget to close the question with /resolve.",
                        color=disnake.Color.dark_green(),
                    ),
                    components=[
                        disnake.ui.Button(
                            style=disnake.ButtonStyle.green,
                            label="Close Question",
                            custom_id="resolve_question_button",
                        ),
                        disnake.ui.Button(
                            style=disnake.ButtonStyle.red,
                            label="I'm not done yet!",
                            custom_id="del_this_button",
                        ),
                    ],
                )