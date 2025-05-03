# evrmail/gui/log_panel.py
import flet as ft

def create_log_panel():
    """Create the logs panel with Flet"""
    
    log_output = ft.TextField(
        multiline=True,
        read_only=True,
        value="",
        min_lines=20,
        expand=True,
        text_size=13,
        color="#ccc",
        bgcolor="#121212",
        border_color="#333",
        border_radius=8,
    )
    
    def clear_logs(e):
        log_output.value = ""
        log_output.update()
    
    panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("📜 EvrMail Logs", size=24, color="white", weight="bold"),
                log_output,
                ft.Container(
                    content=ft.ElevatedButton(
                        "🧹 Clear Logs",
                        on_click=clear_logs,
                        bgcolor="#3c3c3c",
                        color="white",
                    ),
                    alignment=ft.alignment.bottom_right,
                ),
            ],
            spacing=16,
            expand=True,
        ),
        padding=32,
        expand=True,
    )
    
    # Attach the log output field to the panel for external access
    panel.log_output = log_output
    
    return panel
