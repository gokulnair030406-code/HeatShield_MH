"""HeatShield MH - model layer.

Same deep-learning concept as the original project:
    7 environmental inputs -> StandardScaler -> Dense(32,ReLU) -> Dropout(0.10)
    -> Dense(16,ReLU) -> Dense(1,Sigmoid) x 100  => heat-risk proxy 0-100
Trained with Adam (lr 0.006) on MSE.  This file implements the network (forward + back-prop)
in NumPy so the website runs anywhere; train_torch.py trains the identical network in PyTorch
and exports the weights to the same artifacts/model.npz file.
"""
import json
from pathlib import Path
import numpy as np

FEATURES = ["air_temp_c", "relative_humidity_pct", "built_up_pct", "green_cover_pct",
            "water_access_index", "vulnerable_population_pct", "night_cooling_index"]
META = {
    "air_temp_c": dict(label="Air temperature", unit="°C", min=20, max=48, step=0.5, hint="Hotter air raises the score."),
    "relative_humidity_pct": dict(label="Relative humidity", unit="%", min=10, max=100, step=1, hint="Humid heat is harder to shed."),
    "built_up_pct": dict(label="Built-up area", unit="%", min=0, max=100, step=1, hint="Concrete stores and re-radiates heat."),
    "green_cover_pct": dict(label="Green cover", unit="%", min=0, max=100, step=1, hint="Vegetation cools through shade and evapotranspiration."),
    "water_access_index": dict(label="Water access", unit="/100", min=0, max=100, step=1, hint="Better access lowers risk."),
    "vulnerable_population_pct": dict(label="Vulnerable population", unit="%", min=0, max=100, step=1, hint="Aggregate proxy, not individual data."),
    "night_cooling_index": dict(label="Night cooling", unit="", min=0, max=1, step=0.01, hint="Cooler nights allow recovery."),
}
MONTHS = {3: "March", 4: "April", 5: "May", 6: "June"}
BANDS = ["Low", "Moderate", "High", "Very high"]


def risk_band(s):
    return "Very high" if s >= 65 else "High" if s >= 45 else "Moderate" if s >= 25 else "Low"


# ----------------------------------------------------------------------------- data
# name: (lat, lon, zone, built-up %, green %)
STATIONS = {
 "Mumbai": (19.076, 72.878, "Konkan", 88, 12), "Thane": (19.218, 72.978, "Konkan", 78, 18),
 "Navi Mumbai": (19.033, 73.030, "Konkan", 70, 22), "Alibag": (18.641, 72.872, "Konkan", 35, 45),
 "Ratnagiri": (16.990, 73.312, "Konkan", 30, 50), "Kudal": (16.012, 73.689, "Konkan", 20, 60),
 "Pune": (18.520, 73.857, "Western Maharashtra", 75, 20), "Satara": (17.680, 74.018, "Western Maharashtra", 40, 40),
 "Kolhapur": (16.705, 74.243, "Western Maharashtra", 50, 38), "Sangli": (16.855, 74.564, "Western Maharashtra", 48, 30),
 "Solapur": (17.659, 75.906, "Western Maharashtra", 55, 15), "Ahmednagar": (19.095, 74.749, "Western Maharashtra", 45, 18),
 "Nashik": (19.998, 73.790, "North Maharashtra", 60, 25), "Dhule": (20.904, 74.774, "North Maharashtra", 45, 18),
 "Jalgaon": (21.007, 75.563, "North Maharashtra", 50, 16), "Nandurbar": (21.370, 74.240, "North Maharashtra", 30, 28),
 "Aurangabad": (19.876, 75.343, "Marathwada", 62, 14), "Jalna": (19.841, 75.880, "Marathwada", 48, 12),
 "Beed": (18.989, 75.756, "Marathwada", 40, 12), "Latur": (18.408, 76.560, "Marathwada", 50, 13),
 "Osmanabad": (18.186, 76.042, "Marathwada", 38, 14), "Nanded": (19.138, 77.321, "Marathwada", 52, 17),
 "Parbhani": (19.268, 76.771, "Marathwada", 42, 13),
 "Nagpur": (21.146, 79.088, "Vidarbha", 70, 18), "Amravati": (20.933, 77.752, "Vidarbha", 52, 16),
 "Akola": (20.709, 77.002, "Vidarbha", 50, 13), "Chandrapur": (19.962, 79.296, "Vidarbha", 45, 28),
 "Wardha": (20.745, 78.602, "Vidarbha", 40, 18), "Yavatmal": (20.390, 78.131, "Vidarbha", 35, 22),
 "Gadchiroli": (20.185, 80.003, "Vidarbha", 18, 55), "Bhandara": (21.167, 79.650, "Vidarbha", 38, 35),
 "Buldhana": (20.531, 76.184, "Vidarbha", 36, 18),
}
ZT = {  # monthly mean temperature (Mar..Jun) / humidity / water / night cooling base
 "Konkan": ([31, 33, 33, 31], [65, 68, 72, 82], 70, .55), "Western Maharashtra": ([34, 37, 36, 31], [35, 30, 40, 68], 62, .42),
 "North Maharashtra": ([36, 40, 39, 33], [28, 24, 34, 62], 50, .38), "Marathwada": ([37, 41, 40, 33], [27, 22, 33, 62], 38, .36),
 "Vidarbha": ([38, 43, 42, 35], [26, 21, 30, 58], 48, .34)}


def label_formula(X):
    t, h, b, g, w, v, n = X.T
    raw = 4.2 * (t - 30) + 0.10 * h * (t - 28) / 10 + 0.22 * b - 0.28 * g - 0.16 * w + 0.35 * v - 22 * n + 18
    return 100 / (1 + np.exp(-(raw - 50) / 20))


def make_dataset(seed=7):
    import csv
    rng = np.random.default_rng(seed)
    rows = []
    for name, (lat, lon, zone, built, green) in STATIONS.items():
        temps, hums, wbase, nbase = ZT[zone]
        vul = rng.uniform(15, 45)
        for mi, month in enumerate(MONTHS):
            built_ = float(np.clip(built + rng.normal(0, 2), 0, 100))
            green_ = float(np.clip(green + rng.normal(0, 2) - (3 if month in (5, 6) else 0), 0, 100))
            t = temps[mi] + (lat - 19.5) * -0.3 + rng.normal(0, .8) + built_ / 100 * 1.2
            hum = float(np.clip(hums[mi] + rng.normal(0, 4), 10, 100))
            water = float(np.clip(wbase + (6 if built > 60 else 0) - [0, 4, 10, 0][mi] + rng.normal(0, 4), 0, 100))
            night = float(np.clip(nbase - built_ / 300 + rng.normal(0, .03), 0, 1))
            rows.append(dict(place=name, zone=zone, latitude=lat, longitude=lon, month=month, air_temp_c=round(t, 1),
                             relative_humidity_pct=round(hum), built_up_pct=round(built_), green_cover_pct=round(green_),
                             water_access_index=round(water), vulnerable_population_pct=round(vul + rng.normal(0, 1)),
                             night_cooling_index=round(night, 2)))
    X = np.array([[r[f] for f in FEATURES] for r in rows], float)
    y = label_formula(X) + rng.normal(0, 1.5, len(rows))
    for r, s in zip(rows, y):
        r["simulated_risk_label"] = round(float(np.clip(s, 0, 100)), 1)
    return rows


def load_dataset(root: Path):
    import csv
    p = root / "data" / "maharashtra_heat_demo.csv"
    if not p.exists():
        rows = make_dataset()
        p.parent.mkdir(exist_ok=True)
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(p) as f:
        rd = list(csv.DictReader(f))
    out = []
    for r in rd:
        o = {k: (v if k in ("place", "zone") else float(v)) for k, v in r.items()}
        o["month"] = int(o["month"]); out.append(o)
    return out


# ----------------------------------------------------------------------------- network
def _sig(z): return 1 / (1 + np.exp(-np.clip(z, -40, 40)))


class HeatNet:
    SIZES = (7, 32, 16, 1)

    def __init__(self, P=None, mu=None, sd=None):
        self.P, self.mu, self.sd = P, mu, sd

    # inference (dropout off)
    def predict(self, X):
        X = np.atleast_2d(np.asarray(X, float))
        a = (X - self.mu) / self.sd
        a = np.maximum(0, a @ self.P["W1"] + self.P["b1"])
        a = np.maximum(0, a @ self.P["W2"] + self.P["b2"])
        return 100 * _sig(a @ self.P["W3"] + self.P["b3"])[:, 0]

    def n_params(self):
        return int(sum(v.size for v in self.P.values()))

    def save(self, path):
        np.savez(path, mu=self.mu, sd=self.sd, **self.P)

    @classmethod
    def load(cls, path):
        z = np.load(path)
        return cls({k: z[k] for k in ("W1", "b1", "W2", "b2", "W3", "b3")}, z["mu"], z["sd"])

    def fit(self, Xtr, ytr, Xte, yte, epochs=900, lr=0.006, drop=0.10, seed=3):
        rng = np.random.default_rng(seed)
        self.mu, self.sd = Xtr.mean(0), Xtr.std(0) + 1e-8
        A, B = (Xtr - self.mu) / self.sd, (Xte - self.mu) / self.sd
        y, yt = ytr / 100, yte / 100
        s = self.SIZES
        P = {}
        for i in range(3):
            P[f"W{i+1}"] = rng.normal(0, np.sqrt(2 / s[i]), (s[i], s[i + 1]))
            P[f"b{i+1}"] = np.zeros(s[i + 1])
        m = {k: np.zeros_like(v) for k, v in P.items()}; v2 = {k: np.zeros_like(v) for k, v in P.items()}
        hist = []
        for ep in range(1, epochs + 1):
            z1 = A @ P["W1"] + P["b1"]; a1 = np.maximum(0, z1)
            mask = (rng.random(a1.shape) > drop) / (1 - drop); a1d = a1 * mask
            z2 = a1d @ P["W2"] + P["b2"]; a2 = np.maximum(0, z2)
            out = _sig(a2 @ P["W3"] + P["b3"])[:, 0]
            n = len(y)
            dz3 = (2 * (out - y) / n * out * (1 - out))[:, None]
            G = {"W3": a2.T @ dz3, "b3": dz3.sum(0)}
            dz2 = (dz3 @ P["W3"].T) * (z2 > 0)
            G["W2"], G["b2"] = a1d.T @ dz2, dz2.sum(0)
            dz1 = (dz2 @ P["W2"].T) * mask * (z1 > 0)
            G["W1"], G["b1"] = A.T @ dz1, dz1.sum(0)
            for k in P:                                   # Adam
                m[k] = .9 * m[k] + .1 * G[k]; v2[k] = .999 * v2[k] + .001 * G[k] ** 2
                P[k] -= lr * (m[k] / (1 - .9 ** ep)) / (np.sqrt(v2[k] / (1 - .999 ** ep)) + 1e-8)
            if ep % 10 == 0 or ep == 1:
                self.P = P
                tr = float(np.mean((self.predict(Xtr) / 100 - y) ** 2)); te = float(np.mean((self.predict(Xte) / 100 - yt) ** 2))
                hist.append([ep, tr, te])
        self.P = P
        return hist


def train(root: Path, rows, epochs=900):
    X = np.array([[r[f] for f in FEATURES] for r in rows], float)
    y = np.array([r["simulated_risk_label"] for r in rows], float)
    idx = np.random.default_rng(11).permutation(len(X)); cut = int(len(X) * .8)
    tr, te = idx[:cut], idx[cut:]
    net = HeatNet(); hist = net.fit(X[tr], y[tr], X[te], y[te], epochs=epochs)
    pred = net.predict(X[te]); err = pred - y[te]
    metrics = dict(test_rows=int(len(te)), MAE=round(float(np.abs(err).mean()), 2), RMSE=round(float(np.sqrt((err ** 2).mean())), 2),
                   R2=round(float(1 - (err ** 2).sum() / ((y[te] - y[te].mean()) ** 2).sum()), 3),
                   history=hist, scatter=[[round(float(a), 1), round(float(b), 1)] for a, b in zip(y[te], pred)],
                   train_rows=int(len(tr)), epochs=epochs, engine="numpy")
    (root / "artifacts").mkdir(exist_ok=True)
    net.save(root / "artifacts" / "model.npz")
    (root / "artifacts" / "experiment_metrics.json").write_text(json.dumps(metrics))
    return net, metrics


def load_or_train(root: Path, rows):
    p, mp = root / "artifacts" / "model.npz", root / "artifacts" / "experiment_metrics.json"
    if p.exists() and mp.exists():
        return HeatNet.load(p), json.loads(mp.read_text()), "Loaded saved model artifact"
    net, metrics = train(root, rows)
    return net, metrics, "Trained on first launch"


# ----------------------------------------------------------------------------- explanations
def drivers(net, x, baseline):
    """One-at-a-time counterfactual: score(x) - score(x with feature set to the statewide mean)."""
    x = np.asarray(x, float); s0 = float(net.predict(x)[0]); out = []
    for i, f in enumerate(FEATURES):
        z = x.copy(); z[i] = baseline[i]
        out.append(dict(name=f, label=META[f]["label"], delta=round(s0 - float(net.predict(z)[0]), 2)))
    return out


LEVERS = [("green_cover_pct", +15, "Add 15 pts of tree & green cover"), ("water_access_index", +15, "Improve drinking-water access by 15 pts"),
          ("night_cooling_index", +0.15, "Raise night cooling (+0.15): cool roofs, open ventilation corridors"),
          ("built_up_pct", -10, "Cut built-up / impervious surface by 10 pts"), ("vulnerable_population_pct", -8, "Reduce vulnerability by 8 pts via outreach & shelters")]


def interventions(net, x):
    x = np.asarray(x, float); s0 = float(net.predict(x)[0]); out = []
    for f, d, text in LEVERS:
        i = FEATURES.index(f); z = x.copy(); z[i] = np.clip(z[i] + d, META[f]["min"], META[f]["max"])
        out.append(dict(feature=f, change=float(z[i] - x[i]), text=text, new_value=round(float(z[i]), 2), gain=round(s0 - float(net.predict(z)[0]), 2)))
    return sorted(out, key=lambda r: -r["gain"])


def guidance(score):
    if score >= 65: return "Very high proxy: prioritise shade, drinking water and heat-safe work schedules. Check official advisories."
    if score >= 45: return "High proxy: add shade and hydration points and check on vulnerable groups during hot periods."
    if score >= 25: return "Moderate proxy: keep water and shaded rest areas available and watch the weather."
    return "Low proxy for these inputs. Continue normal heat-safety practice."
