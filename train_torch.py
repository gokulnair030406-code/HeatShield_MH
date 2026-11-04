"""Train the HeatShield MH HVI proxy model using the single vulnerability CSV.
Run: python train_torch.py
The NumPy training implementation retains the 7-32-16-1 FNN, Adam, MSE and backpropagation.
"""
from pathlib import Path
from src import vulnerability as V
root = Path(__file__).parent
rows, features, metadata = V.load_rows(root)
net, metrics = V.train_model(root, rows, features)
print("Saved HVI proxy model:", {k: metrics.get(k) for k in ("MAE_proxy", "RMSE_proxy", "R2_proxy")})
print("Dataset:", V.CSV_NAME, "| rows:", len(rows), "| architecture:", net.SIZES)
