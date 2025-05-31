from evrmore_rpc import EvrmoreClient
from evrmail.wallet.script.decode import decode as decode_script
import sqlite3
import os
import time

rpc = EvrmoreClient()
conn = None
c = None

def get_database(delete_existing: bool = False):
    global conn, c
    if delete_existing and os.path.exists('evrmore_snapshot.db'):
        os.remove('evrmore_snapshot.db')
    if conn is None:
        conn = sqlite3.connect('evrmore_snapshot.db')
        c = conn.cursor()
    return conn, c

table_definitions = {
    "blocks": """CREATE TABLE IF NOT EXISTS blocks (
        height INTEGER PRIMARY KEY,
        hash TEXT UNIQUE,
        time INTEGER,
        previousblockhash TEXT,
        merkleroot TEXT,
        size INTEGER,
        strippedsize INTEGER,
        weight INTEGER,
        version INTEGER,
        nonce INTEGER
    );""",
    "transactions": """CREATE TABLE IF NOT EXISTS transactions (
        txid TEXT PRIMARY KEY,
        block_height INTEGER,
        block_hash TEXT,
        hex TEXT,
        FOREIGN KEY(block_height) REFERENCES blocks(height)
    );""",
    "vins": """CREATE TABLE IF NOT EXISTS vins (
        txid TEXT,
        vin_index INTEGER,
        prev_txid TEXT,
        prev_vout INTEGER,
        address TEXT,
        asset_name TEXT,
        sequence INTEGER,
        FOREIGN KEY(txid) REFERENCES transactions(txid)
    );""",
    "vouts": """CREATE TABLE IF NOT EXISTS vouts (
        txid TEXT,
        vout_index INTEGER,
        value REAL,
        scriptpubkey TEXT,
        address TEXT,
        type TEXT,
        asset_name TEXT,
        spent INTEGER DEFAULT 0,
        PRIMARY KEY(txid, vout_index),
        FOREIGN KEY(txid) REFERENCES transactions(txid)
    );"""
}

def create_tables(delete_existing: bool = False):
    conn, c = get_database(delete_existing)
    for _, ddl in table_definitions.items():
        c.execute(ddl)
    conn.commit()

def _get(d, key, default=None):
    return d[key] if key in d else default

def get_block(height: int):
    return rpc.getblock(rpc.getblockhash(height), True)

def format_block_row(block):
    return {
        "height": block['height'],
        "hash": block['hash'],
        "time": block['time'],
        "previousblockhash": block.get('previousblockhash'),
        "merkleroot": block['merkleroot'],
        "size": block['size'],
        "strippedsize": block['strippedsize'],
        "weight": block['weight'],
        "version": block['version'],
        "nonce": block['nonce']
    }

def insert_block(block):
    row = format_block_row(block)
    c.execute("INSERT INTO blocks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              tuple(row.values()))
    conn.commit()

def insert_transaction(tx):
    c.execute("INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?)",
              (tx['txid'], tx['height'], tx['blockhash'], tx.get('hex')))

def insert_vout(txid, vout):
    decoded = decode_script(vout['scriptPubKey']['hex'])
    address = decoded['addresses'][0] if 'addresses' in decoded and decoded['addresses'] else None
    # Handle asset_name extraction safely
    asset = decoded.get('asset_name') or decoded.get('asset', {}).get('name')
    if isinstance(asset, dict):
        asset = str(asset)
    asset_data = decoded.get('asset', {})
    type_ = decoded.get('type')
    if not asset_data:
        value = vout['value']
    else:
        value = asset_data['amount']
    # Ensure all fields are SQLite-safe
    if isinstance(type_, dict):
        type_ = str(type_)

    if type_ == "nulldata":
        address = decoded.get('p2sh')

    c.execute("""
        INSERT INTO vouts (txid, vout_index, value, scriptpubkey, address, type, asset_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        txid,
        vout['n'],
        value,
        vout['scriptPubKey']['hex'],
        address,
        str(type_) if type_ else None,
        asset
    ))


def insert_vin(txid, vin):
    if 'coinbase' in vin:
        return
    try:
        prev_tx = rpc.getrawtransaction(vin['txid'], True)
        prev_vout = prev_tx['vout'][vin['vout']]
        decoded = decode_script(prev_vout['scriptPubKey']['hex'])
        address = decoded['addresses'][0] if 'addresses' in decoded and decoded['addresses'] else None
        # Handle asset_name extraction safely
        asset = decoded.get('asset_name') or decoded.get('asset', {}).get('name')
        if isinstance(asset, dict):
            asset = str(asset)

        c.execute("""
            INSERT INTO vins (txid, vin_index, prev_txid, prev_vout, address, asset_name, sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (txid, vin['vout'], vin['txid'], vin['vout'], address, asset, vin['sequence']))

        # Mark previous vout as spent
        c.execute("UPDATE vouts SET spent = 1 WHERE txid = ? AND vout_index = ?",
                  (vin['txid'], vin['vout']))
    except Exception as e:
        print(f"[WARN] Could not resolve vin {vin}: {e}")

def get_last_height():
    c.execute("SELECT MAX(height) FROM blocks")
    row = c.fetchone()
    return row[0] if row and row[0] is not None else -1

def index_chain(start=0):
    tip = rpc.getblockcount()
    for height in range(start, tip):
        block = get_block(height)
        print(f"[+] Block {height} | txs: {len(block['tx'])}")
        insert_block(block)
        for txid in block['tx']:
            tx = rpc.getrawtransaction(txid, True)
            tx['height'] = height
            tx['blockhash'] = block['hash']
            insert_transaction(tx)
            for vout in tx['vout']:
                insert_vout(tx['txid'], vout)
            for vin in tx['vin']:
                insert_vin(tx['txid'], vin)
        conn.commit()

if __name__ == "__main__":
    create_tables(delete_existing=False)
    last = get_last_height()
    index_chain(start=last + 1)
    print("[DONE] Blockchain fully indexed.")
