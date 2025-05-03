import flet as ft
from pathlib import Path
import json

def create_utxo_panel():
    """Create the UTXO panel using Flet components"""
    
    # UTXO table
    utxo_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Spent", weight="bold")),
            ft.DataColumn(ft.Text("Status", weight="bold")),
            ft.DataColumn(ft.Text("Address", weight="bold")),
            ft.DataColumn(ft.Text("Asset", weight="bold")),
            ft.DataColumn(ft.Text("Amount", weight="bold")),
            ft.DataColumn(ft.Text("TXID", weight="bold")),
            ft.DataColumn(ft.Text("VOUT", weight="bold")),
            ft.DataColumn(ft.Text("Confirmations", weight="bold")),
        ],
        border=ft.border.all(color="#333", width=1),
        border_radius=8,
        vertical_lines=ft.border.BorderSide(1, "#333"),
        horizontal_lines=ft.border.BorderSide(1, "#333"),
        heading_row_color=ft.colors.with_opacity(0.2, "#202124"),
        heading_row_height=50,
        data_row_min_height=40,
        width=10000,  # Force full width
    )
    
    # Show spent checkbox
    show_spent_checkbox = ft.Checkbox(
        label="👁 Show Spent",
        value=False,
    )
    
    # Refresh button
    refresh_btn = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.REFRESH),
                ft.Text("🔄 Refresh UTXOs", size=14)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5,
        ),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        bgcolor="#3ea6ff",
        color="black",
    )
    
    # Container to hold all UTXOs for filtering
    all_utxos = []
    
    def load_utxos(e=None):
        """Load UTXOs from disk and populate the table"""
        utxo_dir = Path.home() / ".evrmail" / "utxos"
        confirmed_file = utxo_dir / "confirmed.json"
        mempool_file = utxo_dir / "mempool.json"
        
        # Clear existing data
        all_utxos.clear()
        
        # Load confirmed UTXOs
        if confirmed_file.exists():
            try:
                confirmed = json.loads(confirmed_file.read_text())
                for address, utxos in confirmed.items():
                    for utxo in utxos:
                        all_utxos.append({
                            "spent": utxo.get("spent", False),
                            "status": "✅ Confirmed",
                            "address": address,
                            "asset": utxo.get("asset", "EVR"),
                            "amount": utxo["amount"] / 1e8 if isinstance(utxo["amount"], int) else utxo["amount"],
                            "txid": utxo["txid"],
                            "vout": utxo["vout"],
                            "confirmations": utxo.get("confirmations", 1),
                            "color": "lightgreen" if not utxo.get("spent", False) else "red"
                        })
            except Exception as e:
                print(f"Error loading confirmed UTXOs: {e}")
        
        # Load mempool UTXOs
        if mempool_file.exists():
            try:
                mempool = json.loads(mempool_file.read_text())
                for address, utxos in mempool.items():
                    for utxo in utxos:
                        all_utxos.append({
                            "spent": utxo.get("spent", False),
                            "status": "⏳ Unconfirmed",
                            "address": address,
                            "asset": utxo.get("asset", "EVR"),
                            "amount": utxo["amount"] / 1e8 if isinstance(utxo["amount"], int) else utxo["amount"],
                            "txid": utxo["txid"],
                            "vout": utxo["vout"],
                            "confirmations": 0,
                            "color": "orange"
                        })
            except Exception as e:
                print(f"Error loading mempool UTXOs: {e}")
        
        # Update the table
        refresh_table()
    
    def refresh_table(e=None):
        """Refresh the UTXO table with the current filter settings"""
        # Filter UTXOs based on checkbox
        show_spent = show_spent_checkbox.value
        filtered_utxos = [utxo for utxo in all_utxos if show_spent or not utxo["spent"]]
        
        # Clear existing rows
        utxo_table.rows.clear()
        
        # Add filtered UTXOs to the table
        for utxo in filtered_utxos:
            # Create row with appropriate color
            color = utxo["color"]
            
            utxo_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("❌" if utxo["spent"] else "✅", color=color)),
                        ft.DataCell(ft.Text(utxo["status"], color=color)),
                        ft.DataCell(ft.Text(utxo["address"], color=color)),
                        ft.DataCell(ft.Text(utxo["asset"] if utxo["asset"] else "EVR", color=color)),
                        ft.DataCell(ft.Text(f"{utxo['amount']:.8f}", color=color)),
                        ft.DataCell(ft.Text(utxo["txid"], color=color)),
                        ft.DataCell(ft.Text(str(utxo["vout"]), color=color)),
                        ft.DataCell(ft.Text(str(utxo["confirmations"]), color=color)),
                    ],
                    on_select_changed=lambda e, txid=utxo["txid"]: copy_to_clipboard(txid),
                )
            )
        
        utxo_table.update()
    
    def copy_to_clipboard(text):
        """Copy the given text to clipboard"""
        page.clipboard.set_text(text)
        page.snack_bar = ft.SnackBar(ft.Text(f"Copied: {text}"))
        page.snack_bar.open = True
        page.update()
    
    # Set up event handlers
    refresh_btn.on_click = load_utxos
    show_spent_checkbox.on_change = refresh_table
    
    # Controls row
    controls_row = ft.Row(
        [
            refresh_btn,
            show_spent_checkbox,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    
    # Create the panel
    panel = ft.Column(
        [
            ft.Text("💎 UTXO Overview", size=22, weight="bold", color="white", text_align=ft.TextAlign.CENTER),
            controls_row,
            ft.Container(
                content=utxo_table,
                expand=True,
                margin=ft.margin.only(top=10),
            ),
        ],
        spacing=10,
        expand=True,
    )
    
    # Create a delayed initialization method
    def delayed_init():
        """Load UTXOs after the panel is added to the page"""
        load_utxos()
    
    # Add the delayed_init method to the panel
    panel.delayed_init = delayed_init
    
    return panel
