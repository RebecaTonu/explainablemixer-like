from bitcoinrpc.authproxy import AuthServiceProxy
import csv
from datetime import datetime


rpc_user = "xxxx" #to be replaced with actual info from bitcoin core config file
rpc_pass = "xxxx" #to be replaced with actual info from bitcoin core config file
rpc_host = "xxxx" #to be replaced with actual info from bitcoin core config file
rpc_client = AuthServiceProxy(
    f"http://{rpc_user}:{rpc_pass}@{rpc_host}:8332",
    timeout=120
)

START_DATE = "2011-01-01"
END_DATE   = "2012-01-01"
TARGET_ROWS = 1_000_000
rows_written = 0
FOG_FILE = r"xxxx" #to be replaced with actual path to the file containing the BitcoinFog addresses

START_TS = int(datetime.strptime(START_DATE, "%Y-%m-%d").timestamp())
END_TS   = int(datetime.strptime(END_DATE, "%Y-%m-%d").timestamp()) + 86400


def load_fog(path):
    with open(path, "r") as f:
        return {row.strip() for row in f if row.strip()}
FOG_SET = load_fog(FOG_FILE)
def utc(ts):
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S UTC")
def find_start_block(target):
    low, high = 0, rpc_client.getblockcount()
    while low <= high:
        mid = (low + high) // 2
        block = rpc_client.getblock(rpc_client.getblockhash(mid))
        if block["time"] < target:
            low = mid + 1
        else:
            high = mid - 1
    return low
tx_cache = {}
first_spend = {}
def get_tx(txid):
    if txid not in tx_cache:
        tx_cache[txid] = rpc_client.getrawtransaction(txid, True)
    return tx_cache[txid]
writers = {}
files = {}
def year_to_number(year):
    return year - 2010
def get_year_writer(block_time):
    year = datetime.utcfromtimestamp(block_time).year
    if year not in writers:
        file_number = year_to_number(year)
        file = open(f"{file_number}.csv", "w", newline="", encoding="utf-8")
        writer = csv.writer(file)
        writer.writerow([
            "prev_txid","prev_timestamp",
            "total_previous_input","total_previous_output","prev_amount_received",
            "current_txid","current_timestamp",
            "total_input","total_output","fee",
            "sender_wallet","receiver_address",
            "receiver_output","sent_to_other_wallets",
            "sender_balance_after","balance_receiver_before",
            "future_txid","future_timestamp",
            "future_total_input","future_total_output",
            "future_fee","future_spent",
            "is_fog_sender","is_fog_receiver","is_fog_any"
        ])
        writers[year] = writer
        files[year] = file
    return writers[year]
height = find_start_block(START_TS)
while rows_written < TARGET_ROWS:
    block_hash = rpc_client.getblockhash(height)
    block = rpc_client.getblock(block_hash, 2)
    if block["time"] >= END_TS:
        break
    writer = get_year_writer(block["time"])
    current_time = utc(block["time"])
    for tx in block["tx"]:
        if rows_written >= TARGET_ROWS:
            break
        if tx["vin"][0].get("coinbase"):
            continue
        total_input = sum(v.get("value", 0) for v in tx["vin"])
        total_output = sum(v["value"] for v in tx["vout"])
        fee = total_input - total_output
        vin0 = tx["vin"][0]
        if "txid" not in vin0:
            continue
        prev_tx = get_tx(vin0["txid"])
        prev_index = vin0["vout"]
        sender = prev_tx["vout"][prev_index]["scriptPubKey"].get("address")
        if not sender:
            continue
        prev_amount = prev_tx["vout"][prev_index]["value"]
        prev_time = utc(prev_tx["time"])
        prev_total_in = sum(v.get("value", 0) for v in prev_tx["vin"])
        prev_total_out = sum(v["value"] for v in prev_tx["vout"])
        outs = [
            (v["scriptPubKey"].get("address"), v["value"])
            for v in tx["vout"]
            if v["scriptPubKey"].get("address")
        ]
        if not outs:
            continue
        receiver, recv_amt = min(outs, key=lambda x: x[1])
        sent_other = total_output - recv_amt
        change = sum(
            v["value"] for v in tx["vout"]
            if v["scriptPubKey"].get("address") == sender
        )
        sender_after = max(prev_amount - (total_output - change), 0)
        for vin in tx["vin"]:
            if "txid" not in vin:
                continue
            ptx = get_tx(vin["txid"])
            idx = vin["vout"]
            addr = ptx["vout"][idx]["scriptPubKey"].get("address")
            if addr and addr not in first_spend:
                first_spend[addr] = tx
        future_tx = first_spend.get(receiver)
        if future_tx:
            f_txid = future_tx["txid"]
            f_time = utc(rpc_client.getblock(future_tx["blockhash"])["time"])
            f_in = sum(v.get("value", 0) for v in future_tx["vin"])
            f_out = sum(v["value"] for v in future_tx["vout"])
            f_fee = f_in - f_out
            f_spent = f_in
        else:
            f_txid = ""
            f_time = ""
            f_in = f_out = f_fee = f_spent = 0
        balance_receiver_before = f_spent - recv_amt
        is_fog_sender = 1 if sender in FOG_SET else 0
        is_fog_receiver = 1 if receiver in FOG_SET else 0
        is_fog_any = 1 if (is_fog_sender or is_fog_receiver) else 0
        writer.writerow([
            vin0["txid"], prev_time,
            f"{prev_total_in:.8f}", f"{prev_total_out:.8f}", f"{prev_amount:.8f}",
            tx["txid"], current_time,
            f"{total_input:.8f}", f"{total_output:.8f}", f"{fee:.8f}",
            sender, receiver,
            f"{recv_amt:.8f}", f"{sent_other:.8f}",
            f"{sender_after:.8f}", f"{balance_receiver_before:.8f}",
            f_txid, f_time,
            f"{f_in:.8f}", f"{f_out:.8f}", f"{f_fee:.8f}", f"{f_spent:.8f}",
            is_fog_sender, is_fog_receiver, is_fog_any
        ])
        rows_written += 1
    height += 1
for f in files.values():
    f.close()