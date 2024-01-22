from copy import copy

import discord
from discord.ext import commands
import reactionmenu
import typing

from menus import CustomSelectMenu
from utils.constants import blank_color


class CustomPage:
    embeds: list[discord.Embed]
    view: typing.Optional[discord.ui.View]
    identifier: typing.Optional[str]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class SelectPagination(discord.ui.View):
    def __init__(self, user_id: int, pages: list[CustomPage], start_at=0):
        super().__init__(timeout=None)
        self.pages = pages
        self.user_id = user_id
        self.current_index = start_at
        self.view = self
        self.preset_children = copy(self.children)
        self.page_children = []

        starting_page = self.pages[self.current_index]
        if starting_page.identifier:
            for item in self.children:
                if item.label == "TEMP":
                    item.label = starting_page.identifier

    def get_current_view(self) -> discord.ui.View:
        current_page = self.pages[self.current_index]
        new_page = self.pages[self.current_index]
        new_index = self.current_index

        view = self.view
        self.current_index = new_index

        page_view = getattr(new_page, 'view', None)
        for i in view.children:
            if i.label == current_page.identifier:
                i.label = new_page.identifier
        if page_view:
            # checks = [i.row in [None, 0] for i in page_view.children]
            # Remove all non-native components
            for child in view.children:
                if child not in self.preset_children:
                    view.children.remove(child)

            self.page_children = []
            # if any(checks):
            #     for index, child in enumerate(page_view.children):
            #         if child.row is None:
            #             child.row = 1
            #         else:
            #             child.row += 1
            #         page_view.children[index] = child
            #         self.page_children.append(child)
            # else:
            for index, child in enumerate(page_view.children):
                self.page_children.append(child)

            for item in self.page_children:
                # Sanity check validations
                if getattr(item, 'default', None) is not None:
                    if item.default > len(item.options):
                        item.default = 0
                        print(f'INVALID ::: {item}')
                elif getattr(item, 'default_values', None) is not None:
                    if len(item.default_values) > item.max_values:
                        item.default_values = []
                        print(f'INVALID ::: {item}')
                else:
                    print(item)
                    print(f'Somewhat valid ::: {item}')

                view.add_item(item)
        return view

    async def _paginate(self, interaction: discord.Interaction, increment_index: int,
                        mode: typing.Literal["set", "increment"]):
        current_page = self.pages[self.current_index]

        if mode == "set":
            new_index = increment_index
            new_page = self.pages[new_index]
        else:
            new_index = self.current_index + increment_index
            if new_index >= len(self.pages):
                new_index = 0
            new_page = self.pages[new_index]

        view = self.view
        self.current_index = new_index

        page_view = getattr(new_page, 'view', None)
        for i in view.children:
            if getattr(i, 'label', None):
                if i.label == current_page.identifier:
                    i.label = new_page.identifier

        if page_view:
            # Clear the items added by the previous page
            for item in self.page_children:
                view.remove_item(item)
            self.page_children.clear()

            # Add the items from the new page
            for item in page_view.children:
                if getattr(item, 'default', None) is not None:
                    if item.default > len(item.options):
                        item.default = 0
                elif getattr(item, 'default_values', None) is not None:
                    if len(item.default_values) > item.max_values:
                        item.default_values = []
                else:
                    print(item)
                view.add_item(item)
                self.page_children.append(item)

        await interaction.message.edit(
            embeds=new_page.embeds,
            view=view
        )

    @discord.ui.button(
        emoji="<:l_arrow:1169754353326903407>",
        row=4
    )
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(embed=discord.Embed(
                title="Not Permitted",
                description="You are not permitted to interact with these buttons.",
                color=blank_color
            ), ephemeral=True)
        await interaction.response.defer()
        await self._paginate(interaction, -1, "increment")

    @discord.ui.button(
        label="TEMP",
        row=4
    )
    async def set_current_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(embed=discord.Embed(
                title="Not Permitted",
                description="You are not permitted to interact with these buttons.",
                color=blank_color
            ), ephemeral=True)
    
        try:
            msg = await interaction.response.send_message(
                embed=discord.Embed(
                    title='<:log:1163524830319104171> Change Pages',
                    description="What page would you like to change to?",
                    color=blank_color
                ),
                view=(view := CustomSelectMenu(interaction.user.id, [
                    discord.SelectOption(
                        label=page.identifier,
                        value=str(index)
                    ) for index, page in enumerate(self.pages)
                ]))
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Unable to apply paginator',
                    description="We were unable to apply the paginator to this message; this is most likely because your leaderboard is too big.",
                    color=blank_color
                )
            )
                

        await view.wait()
        index = int(view.value or '1000')
        await msg.delete()
        if index != 1000:
            await self._paginate(interaction, index, "set")

    @discord.ui.button(
        emoji="<:arrow:1169695690784518154>",
        row=4
    )
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(embed=discord.Embed(
                title="Not Permitted",
                description="You are not permitted to interact with these buttons.",
                color=blank_color
            ), ephemeral=True)
        await interaction.response.defer()
        await self._paginate(interaction, 1, "increment")
