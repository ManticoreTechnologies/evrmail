import flet as ft

def create_settings_panel():
    """Create the settings panel using Flet components"""
    
    # RPC URL field
    rpc_field = ft.TextField(
        label="Custom Node URL",
        hint_text="e.g. https://rpc.evrmore.exchange",
        prefix_icon=ft.icons.SETTINGS_ETHERNET,
        border_color="#3ea6ff",
        expand=True,
    )
    
    # Maximum addresses field
    max_addr_field = ft.TextField(
        label="Maximum Addresses",
        hint_text="e.g. 1000",
        prefix_icon=ft.icons.GRID_3X3,
        border_color="#3ea6ff",
        keyboard_type="number",
        expand=True,
    )
    
    # Theme selector
    theme_dropdown = ft.Dropdown(
        label="Theme",
        hint_text="Select application theme",
        options=[
            ft.dropdown.Option("dark", "Dark Theme"),
            ft.dropdown.Option("light", "Light Theme"),
            ft.dropdown.Option("system", "System Default"),
        ],
        value="dark",
        prefix_icon=ft.icons.PALETTE,
        expand=True,
    )
    
    # Start on boot option
    start_on_boot = ft.Checkbox(
        label="Start EvrMail on system boot",
        value=False,
    )
    
    # Save button
    save_button = ft.ElevatedButton(
        "Save Settings",
        icon=ft.icons.SAVE,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        bgcolor="#3ea6ff",
        color="black",
    )
    
    # Status text
    status_text = ft.Text(
        value="",
        color="#4caf50",
    )
    
    # Handle save button click
    def save_settings(e):
        # This would actually save settings to a config file
        status_text.value = "✅ Settings saved successfully"
        status_text.update()
    
    save_button.on_click = save_settings
    
    # Create the settings panel container
    panel = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(
                        "⚙️ Settings",
                        size=24, 
                        color="white", 
                        weight="bold"
                    ),
                    margin=ft.margin.only(bottom=20),
                ),
                ft.Text(
                    "Connection Settings",
                    size=16,
                    color="#ccc",
                    weight="medium",
                ),
                rpc_field,
                ft.Divider(height=1, color="#333"),
                ft.Text(
                    "Application Settings",
                    size=16,
                    color="#ccc",
                    weight="medium",
                ),
                max_addr_field,
                theme_dropdown,
                start_on_boot,
                ft.Container(height=10),
                status_text,
                ft.Container(
                    content=save_button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=20),
                ),
            ],
            spacing=15,
            expand=True,
        ),
        padding=32,
        expand=True,
    )
    
    # Add delayed_init method for consistency
    def delayed_init():
        """Method for delayed initialization (not needed for this panel)"""
        pass
    
    panel.delayed_init = delayed_init
    
    return panel
