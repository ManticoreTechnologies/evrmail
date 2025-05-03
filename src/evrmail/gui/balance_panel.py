"""
📬 EvrMail — Decentralized Email on the Evrmore Blockchain

A secure, blockchain-native messaging protocol powered by asset channels, 
encrypted IPFS metadata, and peer-to-peer message forwarding.

evrmail/gui/balance_panel.py

🔧 Developer: EQTL7gMLYkuu9CfHcRevVk3KdnG5JgruSE (Cymos)  
🏢 For: EfddmqXo4itdu2TbiFEvuDZeUvkFC7dkGD (Manticore Technologies, LLC)  
© 2025 Manticore Technologies, LLC
"""

import flet as ft
from evrmail.wallet.utils import calculate_balances

def create_balance_tab():
    """Create the wallet balance tab with Flet components"""
    
    # Get balances from wallet
    balances = calculate_balances()
    
    # Calculate total EVR balance
    total_evr = sum(balances["evr"].values()) / 1e8
    
    # Create total EVR balance display
    total_balance = ft.Container(
        content=ft.Text(
            f"Total EVR: {total_evr:.8f}",
            size=20,
            color="#4caf50",
            weight="bold",
        ),
        padding=10,
        margin=ft.margin.only(bottom=10),
    )
    
    # Create EVR balance table
    evr_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Address", weight="bold")),
            ft.DataColumn(ft.Text("EVR Balance", weight="bold"), numeric=True),
        ],
        border=ft.border.all(color="#333", width=1),
        border_radius=8,
        vertical_lines=ft.border.BorderSide(1, "#333"),
        horizontal_lines=ft.border.BorderSide(1, "#333"),
        column_spacing=50,
        heading_row_color=ft.colors.with_opacity(0.2, "#2c2c2c"),
        heading_row_height=50,
        data_row_min_height=40,
        width=10000,  # Force full width
    )
    
    # Add EVR balance rows
    evr_rows = list(balances["evr"].items())
    for address, amount in evr_rows:
        evr_table.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(address)),
                    ft.DataCell(ft.Text(f"{amount / 1e8:.8f}", text_align=ft.TextAlign.END)),
                ]
            )
        )
    
    # Create asset balance table
    asset_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Asset", weight="bold")),
            ft.DataColumn(ft.Text("Address", weight="bold")),
            ft.DataColumn(ft.Text("Amount", weight="bold"), numeric=True),
        ],
        border=ft.border.all(color="#333", width=1),
        border_radius=8,
        vertical_lines=ft.border.BorderSide(1, "#333"),
        horizontal_lines=ft.border.BorderSide(1, "#333"),
        column_spacing=50,
        heading_row_color=ft.colors.with_opacity(0.2, "#2c2c2c"),
        heading_row_height=50,
        data_row_min_height=40,
        width=10000,  # Force full width
    )
    
    # Add asset balance rows
    asset_rows = []
    for asset_name, addr_map in balances["assets"].items():
        for address, amount in addr_map.items():
            asset_rows.append((asset_name, address, amount / 1e8))
    
    for asset, address, amount in asset_rows:
        asset_table.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(asset)),
                    ft.DataCell(ft.Text(address)),
                    ft.DataCell(ft.Text(f"{amount:.8f}", text_align=ft.TextAlign.END)),
                ]
            )
        )
    
    # Create the complete layout
    balance_tab = ft.Container(
        content=ft.Column(
            [
                ft.Text("💰 Wallet Balances", size=24, color="white", weight="bold"),
                total_balance,
                ft.Text("🔵 EVR Balances", size=16, color="white"),
                ft.Container(
                    content=evr_table,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20),
                    border_radius=8,
                ),
                ft.Text("🟠 Asset Balances", size=16, color="white"),
                ft.Container(
                    content=asset_table,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(bottom=20),
                    border_radius=8,
                ),
            ],
            spacing=10,
            scroll="auto",
            expand=True,
        ),
        padding=20,
        expand=True,
    )
    
    # Add delayed_init method to handle table updates after panel is added to the page
    def delayed_init():
        """Update tables after the panel is added to the page"""
        # No need to do anything special since we're not calling update()
        pass
    
    balance_tab.delayed_init = delayed_init
    
    return balance_tab
