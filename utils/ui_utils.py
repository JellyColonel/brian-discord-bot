# brian-discord-bot/utils/ui_utils.py

import disnake
from typing import Dict, List, Optional, Union, Any
import config

class UIComponents:
    """Utility class for creating UI components like embeds, buttons, and more."""
    
    @staticmethod
    def create_embed(
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[disnake.Color] = None,
        fields: Optional[List[Dict[str, Union[str, bool]]]] = None,
        author: Optional[Dict[str, str]] = None,
        footer: Optional[Dict[str, str]] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        timestamp: bool = False
    ) -> disnake.Embed:
        """
        Create a Discord embed with common parameters.
        
        Args:
            title: Title of the embed
            description: Description of the embed
            color: Color of the embed (defaults to the bot's default color)
            fields: List of field dictionaries with "name", "value", and optionally "inline" keys
            author: Dictionary with "name" and optionally "icon_url" keys
            footer: Dictionary with "text" and optionally "icon_url" keys
            thumbnail: URL for the thumbnail image
            image: URL for the main image
            timestamp: Whether to include the current timestamp
            
        Returns:
            A disnake.Embed object
        """
        # Use default color if none provided
        if color is None:
            color = config.EMBED_COLOR
            
        # Create embed with basic attributes
        embed = disnake.Embed(
            title=title,
            description=description,
            color=color
        )
        
        # Add timestamp if requested
        if timestamp:
            embed.timestamp = disnake.utils.utcnow()
        
        # Add fields
        if fields:
            for field in fields:
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
        
        # Add author
        if author:
            embed.set_author(
                name=author["name"],
                icon_url=author.get("icon_url")
            )
        
        # Add footer
        if footer:
            embed.set_footer(
                text=footer["text"],
                icon_url=footer.get("icon_url")
            )
        
        # Add thumbnail and image
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if image:
            embed.set_image(url=image)
            
        return embed
    
    @staticmethod
    def create_button_row(*buttons) -> disnake.ui.ActionRow:
        """
        Create a row of buttons.
        
        Args:
            *buttons: Button objects to include in the row
            
        Returns:
            A disnake.ui.ActionRow containing the buttons
        """
        row = disnake.ui.ActionRow()
        for button in buttons:
            row.append_item(button)
        return row
    
    @staticmethod
    def create_button(
        label: str,
        custom_id: str,
        style: disnake.ButtonStyle = disnake.ButtonStyle.primary,
        emoji: Optional[Union[str, disnake.Emoji, disnake.PartialEmoji]] = None,
        disabled: bool = False,
        url: Optional[str] = None
    ) -> disnake.ui.Button:
        """
        Create a Discord button.
        
        Args:
            label: Text label on the button
            custom_id: Custom ID for the button (not needed for URL buttons)
            style: Button style (primary, secondary, success, danger, link)
            emoji: Emoji to display on the button
            disabled: Whether the button is disabled
            url: URL for link buttons (style must be ButtonStyle.link)
            
        Returns:
            A disnake.ui.Button object
        """
        if style == disnake.ButtonStyle.link and url:
            return disnake.ui.Button(
                label=label,
                style=style,
                url=url,
                emoji=emoji,
                disabled=disabled
            )
        else:
            return disnake.ui.Button(
                label=label,
                custom_id=custom_id,
                style=style,
                emoji=emoji,
                disabled=disabled
            )
    
    @staticmethod
    def create_select_menu(
        custom_id: str,
        options: List[disnake.SelectOption],
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False
    ) -> disnake.ui.Select:
        """
        Create a Discord select menu (dropdown).
        
        Args:
            custom_id: Custom ID for the select menu
            options: List of select options
            placeholder: Placeholder text when nothing is selected
            min_values: Minimum number of values that must be selected
            max_values: Maximum number of values that can be selected
            disabled: Whether the select is disabled
            
        Returns:
            A disnake.ui.Select object
        """
        return disnake.ui.Select(
            custom_id=custom_id,
            options=options,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled
        )
    
    @staticmethod
    def create_select_option(
        label: str,
        value: str,
        description: Optional[str] = None,
        emoji: Optional[Union[str, disnake.Emoji, disnake.PartialEmoji]] = None,
        default: bool = False
    ) -> disnake.SelectOption:
        """
        Create an option for a select menu.
        
        Args:
            label: Option display text
            value: Value returned when this option is selected
            description: Additional description text
            emoji: Emoji to display with the option
            default: Whether this option is selected by default
            
        Returns:
            A disnake.SelectOption object
        """
        return disnake.SelectOption(
            label=label,
            value=value,
            description=description,
            emoji=emoji,
            default=default
        )
    
    @staticmethod
    def create_text_input(
        label: str,
        custom_id: str,
        style: disnake.TextInputStyle = disnake.TextInputStyle.short,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> disnake.ui.TextInput:
        """
        Create a text input for modals.
        
        Args:
            label: Label for the text input
            custom_id: Custom ID for the input
            style: Input style (short or paragraph)
            placeholder: Placeholder text
            value: Pre-filled value
            required: Whether the field is required
            min_length: Minimum input length
            max_length: Maximum input length
            
        Returns:
            A disnake.ui.TextInput object
        """
        return disnake.ui.TextInput(
            label=label,
            custom_id=custom_id,
            style=style,
            placeholder=placeholder,
            value=value,
            required=required,
            min_length=min_length,
            max_length=max_length
        )

class ButtonView(disnake.ui.View):
    """A base class for views with buttons."""
    
    def __init__(self, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        
    @staticmethod
    def add_buttons(
        view,
        buttons: List[Dict[str, Any]]
    ) -> None:
        """
        Add multiple buttons to a view using button data.
        
        Args:
            view: The view to add buttons to
            buttons: List of button data dictionaries with parameters for create_button
        """
        for button_data in buttons:
            # Extract callback if present
            callback = button_data.pop("callback", None)
            
            # Create the button
            button = UIComponents.create_button(**button_data)
            
            # Add callback if provided
            if callback:
                button.callback = callback
                
            # Add to view
            view.add_item(button)
    
    @staticmethod
    def create_paginator(
        embeds: List[disnake.Embed],
        user_id: Optional[int] = None,
        timeout: Optional[float] = 180
    ) -> 'Paginator':
        """
        Create a paginator for multiple embeds.
        
        Args:
            embeds: List of embeds to paginate
            user_id: User ID who can interact with the paginator (or None for anyone)
            timeout: Time in seconds before buttons are disabled
            
        Returns:
            A Paginator view
        """
        return Paginator(embeds, user_id, timeout)

class Paginator(disnake.ui.View):
    """A view for paginating through multiple embeds."""
    
    def __init__(
        self,
        embeds: List[disnake.Embed],
        user_id: Optional[int] = None, 
        timeout: Optional[float] = 180
    ):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        
        # Add page counter to embeds
        for i, embed in enumerate(self.embeds):
            embed.set_footer(
                text=f"Page {i+1}/{len(self.embeds)}" + 
                     (f" • {embed.footer.text}" if embed.footer and embed.footer.text else "")
            )
        
        # Update button states
        self._update_buttons()
    
    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        # If user_id is set, only allow that user to interact
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "You are not authorized to use these controls.", 
                ephemeral=True
            )
            return False
        return True
    
    def _update_buttons(self):
        # First page - disable previous buttons
        if self.current_page == 0:
            self.first_page.disabled = True
            self.prev_page.disabled = True
        else:
            self.first_page.disabled = False
            self.prev_page.disabled = False
            
        # Last page - disable next buttons
        if self.current_page == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        else:
            self.next_page.disabled = False
            self.last_page.disabled = False
    
    async def _update_message(self, interaction: disnake.MessageInteraction):
        self._update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page],
            view=self
        )
    
    @disnake.ui.button(
        emoji="⏪", 
        style=disnake.ButtonStyle.secondary, 
        custom_id="first_page"
    )
    async def first_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.current_page = 0
        await self._update_message(interaction)
    
    @disnake.ui.button(
        emoji="◀️", 
        style=disnake.ButtonStyle.primary, 
        custom_id="prev_page"
    )
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.current_page = max(0, self.current_page - 1)
        await self._update_message(interaction)
    
    @disnake.ui.button(
        emoji="▶️", 
        style=disnake.ButtonStyle.primary, 
        custom_id="next_page"
    )
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.current_page = min(len(self.embeds) - 1, self.current_page + 1)
        await self._update_message(interaction)
    
    @disnake.ui.button(
        emoji="⏩", 
        style=disnake.ButtonStyle.secondary, 
        custom_id="last_page"
    )
    async def last_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.current_page = len(self.embeds) - 1
        await self._update_message(interaction)
    
    @disnake.ui.button(
        emoji="🗑️", 
        style=disnake.ButtonStyle.danger, 
        custom_id="close"
    )
    async def close(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        # Remove the message or clear the view
        await interaction.response.edit_message(view=None)
        self.stop()

class ModalCreator:
    """A utility class for creating and working with modals."""
    
    @staticmethod
    def create_simple_modal(
        title: str,
        custom_id: str,
        *text_inputs
    ) -> disnake.ui.Modal:
        """
        Create a simple modal with text inputs.
        
        Args:
            title: Title of the modal
            custom_id: Custom ID for the modal
            *text_inputs: TextInput objects to add to the modal
            
        Returns:
            A disnake.ui.Modal object
        """
        modal = disnake.ui.Modal(title=title, custom_id=custom_id)
        
        for text_input in text_inputs:
            modal.add_components(text_input)
            
        return modal