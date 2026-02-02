import discord
from discord.ui import View, Button

class StockView(View):
    """
    A Discord UI View for shop stock with buttons per category.
    Clicking a button will show only that section of the stock.
    """

    def __init__(self, data: dict):
        super().__init__(timeout=None)  # persistent until bot restarts
        self.data = data
        self.build_buttons()

    def build_buttons(self):
        for category in self.data.keys():
            button = Button(
                label=category.title(),
                style=discord.ButtonStyle.primary,
                custom_id=f"stock_{category}"
            )
            # attach callback
            button.callback = self.make_callback(category)
            self.add_item(button)

    def make_callback(self, category):
        async def callback(interaction: discord.Interaction):
            # Create a new embed for the clicked category only
            IN_STOCK = "✅"
            OUT_STOCK = "❌"

            embed = discord.Embed(
                title=f"📦 {category.title()} Stock",
                description=f"Current availability in {category.title()}",
                color=0x57F287
            )

            lines = []
            for name, in_stock in self.data[category].items():
                icon = IN_STOCK if in_stock else OUT_STOCK
                lines.append(f"**{name.title()}** {icon}")

            embed.add_field(
                name=f"{category.title()}",
                value="\n".join(lines),
                inline=False
            )

            # edit the original message with the new embed
            await interaction.response.send_message(embed=embed, ephemeral=True)

        return callback
