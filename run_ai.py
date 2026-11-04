"""AI MOF 선별 파이프라인 재실행: 모델 검증 → A단계 채점 → B단계 재채점 → 외부 코호트 검증.

저장소를 내려받은 뒤 `python run_ai.py` 로 실행합니다. 저장된 모델(models/)과
data/ 아래 표만 읽으므로 인터넷이나 로컬 연구용 SQLite가 없어도 같은 숫자가 나옵니다.
"""
import sys, time, warnings
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, recall_score
warnings.filterwarnings('ignore')
REPO = Path(__file__).resolve().parent
VAL = REPO / 'data' / 'validation'   # MOFSimplify 물 안정성 라벨, CoRE MOF 2025 외부 코호트
sys.path.insert(0, str(REPO))
from moflab import pipeline
from moflab.descriptors import FEATURES

t0 = time.time()
art = joblib.load(next((REPO / 'models').glob('water_rf_*.joblib')))
rf = art['estimator']
print(f'[1] 물 안정성 모델: RandomForest  트리 {rf.n_estimators}개 · 깊이 {rf.max_depth} · 특성 {len(FEATURES)}개 · {rf.class_weight}')

# [2] 계열별 5-fold 교차검증을 처음부터 다시 학습
lab = pd.read_csv(VAL / 'water_labels.csv')
oof = pd.read_csv(REPO / 'models/water_oof_predictions.csv')[['name', 'group', 'fold']]
d = oof.merge(lab, on='name').drop_duplicates('name')
X = d[FEATURES].to_numpy(float); y = (d.water_label >= 3).astype(int).to_numpy()
p = np.zeros(len(d)); aucs = []
for k in range(1, 6):
    te = d.fold.to_numpy() == k
    m = RandomForestClassifier(**{**rf.get_params(), 'n_jobs': -1}).fit(X[~te], y[~te])
    p[te] = m.predict_proba(X[te])[:, 1]; aucs.append(roc_auc_score(y[te], p[te]))
overlap = sum(len(set(d.group[d.fold == k]) & set(d.group[d.fold != k])) for k in range(1, 6))
print(f'[2] 계열별 5-fold 교차검증 ({len(d):,}개, 겹치는 계열 {overlap})  ROC-AUC = {roc_auc_score(y, p):.3f}   '
      f'fold별 {min(aucs):.2f}~{max(aucs):.2f}')

# [3] A단계: 데이터베이스 전체 200점 채점
a = pd.read_parquet(REPO / 'data/pipeline/stage_a.parquet')[['name', 'metal', 'water_prob', 'capture_raw', 'desorption_raw', 'reuse_raw']]
stats = pipeline.reference_stats(a)
A = pipeline.rank(pipeline.score(a, stats))
print(f'[3] A단계 채점 완료: {len(A):,}개  (안정성 100 + 포집 40 + 탈착 35 + 재사용 25)')
for r in A.head(3).itertuples():
    print(f'      {r.rank}위  {r.name:<18} {r.metal}  {r.total:6.1f}점')

# [4] B단계: 상위 3개의 링커·금속을 바꾼 구조 재채점
b = pd.read_parquet(REPO / 'data/pipeline/stage_b.parquet')
B = pipeline.rank(pipeline.score(b[['name', 'change', 'water_prob', 'capture_raw', 'desorption_raw', 'reuse_raw']], stats))
print(f'[4] B단계 재채점 완료: 원본 3개 + 수정본 {len(B) - 3}개')
for r in B.head(3).itertuples():
    print(f'      {r.rank}위  {r.name:<22} {r.total:6.1f}점')
f = B.iloc[0]
print(f'      최종 MOF → {f["name"]}  안정성 {f.stability:.1f} · 포집 {f.capture:.1f} · 탈착 {f.desorption:.1f} · 재사용 {f.reuse:.1f}')

# [5] 외부 코호트: 학습에 안 쓴 CoRE MOF 2025 구조
ext = pd.read_csv(VAL / 'core2025_water_external.csv')   # 학습에 안 쓴 구조 497개와 CoRE의 물 안정성 값
xe = ext[FEATURES].apply(pd.to_numeric, errors='coerce').to_numpy(float)
ye = (ext.core_water >= 0.5).astype(int).to_numpy()
raw = lab[np.isfinite(lab[FEATURES].to_numpy(float)).all(1) & lab.water_label.isin([1, 2, 3, 4])]
p0 = RandomForestClassifier(n_estimators=180, random_state=42, n_jobs=-1).fit(raw[FEATURES].to_numpy(float), (raw.water_label >= 3).astype(int)).predict_proba(xe)[:, 1]
p1 = rf.predict_proba(xe)[:, 1]
print(f'[5] 외부 코호트 {len(ye)}개 (학습에 안 쓴 CoRE MOF 2025)')
for n, pp in [('처음 모델', p0), ('고친 모델', p1)]:
    print(f'      {n}: 정확도 {((pp >= .5) == ye).mean():.2f} · 불안정 맞춤 {recall_score(1 - ye, pp < .5):.2f} · 균형 정확도 {balanced_accuracy_score(ye, pp >= .5):.2f}')
print(f'완료 ({time.time() - t0:.1f}초)')
