# Explainable Mixer-Like Behavior Detection in Bitcoin via Transaction-Level Heuristics

This repository provides a reproducible pipeline for analyzing **mixer-like behavior in Bitcoin** using interpretable, transaction-level heuristics.  
It includes scripts for dataset extraction from a Bitcoin Core node, heuristic-based analysis, and evaluation through metrics and visualizations.  

---

## Dataset Extraction & Experimental Reproducibility 

## Dataset
In this folder, you will find the script `retrievedata.py`, which is used to extract the Bitcoin transaction dataset directly from a Bitcoin Core node.

---

## How to Run the Code

### Requirements
- Python 3.8+
- Bitcoin Core node (fully synced)
- RPC enabled in Bitcoin Core

---

### Bitcoin Core Configuration

Edit your `bitcoin.conf` file:

```ini
server=1
txindex=1
rpcuser=your_user
rpcpassword=your_password
rpcallowip=127.0.0.1
rpcport=8332
```

- `txindex=1` is mandatory (otherwise `getrawtransaction` won’t work)  
- Node must be fully synced  

---

### Configure the Script

Replace the placeholders in `retrievedata.py` with your local configuration:

```python
rpc_user = "xxxx"
rpc_pass = "xxxx"
rpc_host = "xxxx"   # usually 127.0.0.1
```

---

### Install Dependencies

```bash
pip install python-bitcoinrpc
```

---

### Run the Script

```bash
python retrievedata.py
```

---





## Feature Construction
Running the script generates CSV files packaged in a zipped Dataset folder. This folder also includes the 'BitcoinFog' dataset, which was retrieved from WalletExplorer:

Each row represents a **transaction pair context** and includes the following information:

### Previous Transaction
- `prev_txid`, `prev_timestamp`  
- `prev_amount_received`  

### Current Transaction
- `current_txid`, `current_timestamp`  
- `total_input`, `total_output`, `fee`  

### Sender / Receiver
- `sender_wallet`, `receiver_address`  
- `sender_balance_after`  
- `balance_receiver_before`  

### Future Behavior
- `future_txid`, `future_timestamp`  
- Used for delay-based heuristics  

### Labels
- `is_fog_sender`  
- `is_fog_receiver`  
- `is_fog_any`  

---

## Heuristics, Plots, and Metrics

In the folder **`Heuristics plots and metrics`**, you will find the implementation of all proposed heuristics, along with scripts for computing evaluation metrics and generating plots.

---

### Implemented Heuristics

1. **Balance After = 0**  
   Captures transactions where the remaining balance of an address becomes zero after spending.

2. **Delay Hours**  
   Computes the time interval in hours between two related transactions.

3. **Balance Dust**  
   Identifies transactions where the remaining balance is close to zero.

4. **Fee Shrinkage**  
   Measures the proportional reduction between the previously received value and the current output value.

5. **Temporal Balance Depletion**  
   Combines temporal and balance-based signals to model mixer-like execution patterns.

---

### Metrics and Plots

The scripts compute standard evaluation metrics, including:
- True Positives (TP), False Positives (FP)  
- False Negatives (FN), True Negatives (TN)  
- Recall, False Positive Rate (FPR), Specificity  

Additionally, they generate:
- Heatmaps  
- Temporal performance plots  
- Threshold comparison visualizations  

---

### Required Libraries

```bash
pip install pandas numpy matplotlib seaborn scikit-learn
```
