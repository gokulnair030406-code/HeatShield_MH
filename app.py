"""HeatShield MH. Previous premium dashboard design, powered by one vulnerability CSV."""
import csv, io, json
from pathlib import Path
import numpy as np
from flask import Flask, jsonify, render_template, request, Response
from src import model as M, geo, vulnerability as V
ROOT=Path(__file__).parent
app=Flask(__name__); app.config["MAX_CONTENT_LENGTH"]=5*1024*1024
ROWS, FEATURES_RAW, V_META=V.load_rows(ROOT)
# One model only: the retained 7-32-16-1 FNN trained on generated HVI proxy labels.
artifact=ROOT/"artifacts"/"vulnerability_model.npz"
metrics_path=ROOT/"artifacts"/"vulnerability_metrics.json"
if artifact.exists() and metrics_path.exists():
    NET=M.HeatNet.load(artifact); METRICS=json.loads(metrics_path.read_text())
else:
    NET,METRICS=V.train_model(ROOT,ROWS,FEATURES_RAW)
BASE=np.mean([[r[f] for f in V.FEATURES] for r in ROWS],axis=0)
for r in ROWS: r["model_prediction"]=round(float(NET.predict([[r[f] for f in V.FEATURES]])[0]),2)
META={}
for f in V.FEATURES:
    vals=[float(r[f]) for r in ROWS]
    META[f]={"label":V.LABELS.get(f,f),"unit":"","min":float(min(vals)),"max":float(max(vals)),"step":max((max(vals)-min(vals))/100,0.01),"hint":"CSV-derived feature; estimates at unsampled places use IDW."}
MONTHS={1:"All records"}; BANDS=["Low","Moderate","High","Very high"]
def band(v): return M.risk_band(float(v))
def predict(x):
    score=float(np.clip(NET.predict([x])[0],0,100)); drivers=[]
    for i,f in enumerate(V.FEATURES):
        z=list(x); z[i]=BASE[i]; delta=score-float(NET.predict([z])[0])
        drivers.append({"name":f,"label":V.LABELS.get(f,f),"delta":round(delta,2)})
    return {"score":round(score,2),"hvi":round(score,2),"band":band(score),"risk_band":band(score),"drivers":drivers,"interventions":[],"guidance":"Formula-generated HVI proxy estimate. Not an official or measured vulnerability assessment."}
@app.context_processor
def inject(): return dict(meta=META,features=V.FEATURES,months=MONTHS,active=request.path)
@app.get("/")
def home(): return render_template("index.html")
@app.get("/map")
def map_page(): return render_template("vulnerability.html")
@app.get("/vulnerability")
def vuln_page(): return render_template("vulnerability.html")
@app.get("/simulator")
def simulator(): return render_template("simulator.html")
@app.get("/data")
def data(): return render_template("data.html")
@app.get("/model")
def model_page(): return render_template("model.html")
@app.get("/api/outline")
def outline(): return jsonify(geo.OUTLINE)
@app.get("/api/vulnerability")
def vulnerability_data():
    ordered=sorted(ROWS,key=lambda r:-r["heat_vulnerability_index"])
    return jsonify(total=len(ordered),rows=ordered,features=V.FEATURES,labels=V.LABELS,metadata=V_META,metrics=METRICS,correlations=V.correlation_matrix(ROWS),duplicate_profiles=int(len(ROWS)-len({tuple(round(r[f],4) for f in V.FEATURES[:-1]) for r in ROWS})))
@app.get("/api/vulnerability/surface")
def vulnerability_surface(): return jsonify(V.vulnerability_surface(ROWS,NET,geo))
@app.post("/api/vulnerability/probe")
def vulnerability_probe():
    d=request.get_json(silent=True) or {}
    try: lat,lon=float(d["lat"]),float(d["lon"])
    except Exception: return jsonify(error="Valid latitude and longitude are required."),400
    if not bool(geo.inside(lat,lon)): return jsonify(inside=False,error="Point is outside the Maharashtra demo region."),200
    X,scores,dist=V.predict_unsampled([lat],[lon],ROWS,NET); order=np.argsort(dist[0])[:3]; x=X[0]; sc=float(scores[0])
    return jsonify(inside=True,latitude=lat,longitude=lon,hvi=round(sc,2),score=round(sc,2),risk_band=band(sc),band=band(sc),features={k:round(float(v),3) for k,v in zip(V.FEATURES,x)},nearest=[{"location":ROWS[i]["District"],"place":ROWS[i]["District"],"distance_km":round(float(dist[0][i]),1),"source_hvi_proxy":ROWS[i]["heat_vulnerability_index"],"score":ROWS[i]["heat_vulnerability_index"]} for i in order],is_source_station=bool(dist[0,order[0]]<.01),guidance="IDW-estimated environmental inputs scored by the 7-32-16-1 neural network. HVI is a generated proxy.")
@app.get("/api/vulnerability.csv")
def vulnerability_csv():
    b=io.StringIO(); w=csv.DictWriter(b,fieldnames=list(ROWS[0])); w.writeheader(); w.writerows(ROWS)
    return Response(b.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=maharashtra_vulnerability_hvi_proxy.csv"})
# Compatibility endpoints used by the previous dashboard pages, now backed ONLY by the vulnerability CSV.
@app.get("/api/stations")
def stations(): return jsonify([{"place":r["District"],"zone":r["Zone"],"latitude":r["latitude"],"longitude":r["longitude"],"air_temp_c":r["max_temp_c"],"ai_risk_score":r["heat_vulnerability_index"],"risk_band":r["risk_band"]} for r in ROWS])
@app.get("/api/summary")
def summary():
    scores=[r["heat_vulnerability_index"] for r in ROWS]
    top=sorted(ROWS,key=lambda r:-r["heat_vulnerability_index"])[:6]
    return jsonify(month=1,avg=round(float(np.mean(scores)),1),avg_temp=round(float(np.mean([r["max_temp_c"] for r in ROWS])),1),counts={b:sum(band(x)==b for x in scores) for b in BANDS},n=len(ROWS),top=[{"place":r["District"],"zone":r["Zone"],"latitude":r["latitude"],"longitude":r["longitude"],"ai_risk_score":r["heat_vulnerability_index"],"risk_band":r["risk_band"],"air_temp_c":r["max_temp_c"]} for r in top],trend=[round(float(np.mean(scores)),1)])
@app.get("/api/surface")
def surface(): return jsonify(V.vulnerability_surface(ROWS,NET,geo))
@app.post("/api/probe")
def probe():
    d=request.get_json(silent=True) or {}; return vulnerability_probe()
@app.post("/api/predict")
def predict_api():
    d=request.get_json(silent=True) or {}
    try: x=[float(d[f]) for f in V.FEATURES]
    except Exception: return jsonify(error="All seven vulnerability input features are required."),400
    return jsonify(predict(x))
@app.post("/api/score_csv")
def score_csv():
    f=request.files.get("file")
    if not f:return jsonify(error="No CSV uploaded."),400
    try: rd=list(csv.DictReader(io.StringIO(f.read().decode("utf-8-sig"))))
    except Exception:return jsonify(error="Could not read CSV."),400
    if not rd:return jsonify(error="CSV is empty."),400
    good=[]
    for r in rd:
        try:
            x=[float(r[k]) for k in V.FEATURES]; r["predicted_hvi_proxy"]=round(float(NET.predict([x])[0]),2); good.append(r)
        except Exception: pass
    if not good:return jsonify(error="No rows contain all seven model features."),400
    buf=io.StringIO(); w=csv.DictWriter(buf,fieldnames=list(good[0])); w.writeheader();w.writerows(good)
    return jsonify(rows=good[:300],total=len(good),skipped=len(rd)-len(good),avg=round(float(np.mean([float(r["predicted_hvi_proxy"]) for r in good])),2),csv=buf.getvalue(),counts={})
@app.get("/api/dataset")
def dataset(): return Response((ROOT/"data"/V.CSV_NAME).read_text(encoding="utf-8-sig"),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=maharashtra_vulnerability.csv"})
@app.get("/api/template")
def template(): return Response(",".join(V.FEATURES)+"\n",mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=hvi_model_template.csv"})
@app.get("/api/model")
def model_info():
    return jsonify(note="Trained to approximate formula-generated HVI proxy labels, not real-world validated vulnerability.",params=NET.n_params(),sizes=list(NET.SIZES),importance=[{"label":V.LABELS.get(f,f),"value":0} for f in V.FEATURES],metrics={k:METRICS.get(k) for k in ("test_rows","train_rows","MAE_proxy","RMSE_proxy","R2_proxy","epochs")},history=METRICS.get("history",[]),scatter=[])
if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=False)
