"""Build the final-candidate + UiO-66 variant table from the WS24 data set (Zenodo 12110918, CC BY 4.0).

    python -m scripts.build_variants --ws24 /path/to/unzipped   # folder holding data_sets/ and features/

Labels are literature values (Burtch et al. classes). The RF probability is in-sample here, because
these MOFs are part of the model's training data, and is kept only for reference.
"""
import argparse, shutil
from pathlib import Path
import joblib
import pandas as pd
from moflab.descriptors import FEATURES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/variants'

# name in WS24 -> (display name, functional group, effect on phosphate at pH ~7, short reason)
# effect: + helps binding, 0 neutral, - repels (negatively charged at pH 7). Team chemistry judgement.
VARIANTS = {
    'UiO-66':        ('UiO-66', '없음 (–H)', '0', '기준 구조'),
    'UiO-66-NH2':    ('UiO-66-NH₂', '아미노 –NH₂', '+', '수소결합 · 산성에서 양전하'),
    'MOF-804':       ('UiO-66-(OH)₂', '하이드록시 –OH ×2', '+', '수소결합'),
    'UiO-66-NO2':    ('UiO-66-NO₂', '나이트로 –NO₂', '0', '중성 · 전자 끌기'),
    'UiO-66-CO2H':   ('UiO-66-COOH', '카복실 –COOH', '-', 'pH 7에서 음전하 → 반발'),
    'UiO-66-CO2H_2': ('UiO-66-(COOH)₂', '카복실 –COOH ×2', '-', 'pH 7에서 음전하 → 반발'),
    'UiO-66-SO3H':   ('UiO-66-SO₃H', '설폰산 –SO₃H', '-', '항상 음전하 → 반발'),
    'UiO-66-F':      ('UiO-66-F', '플루오로 –F', '0', '중성'),
    'UiO-66-F2':     ('UiO-66-F₂', '플루오로 –F ×2', '0', '중성'),
    'UiO-66-Br':     ('UiO-66-Br', '브로모 –Br', '0', '중성 · 소수성'),
    'UiO-66-Br2':    ('UiO-66-Br₂', '브로모 –Br ×2', '0', '중성 · 소수성'),
    'UiO-66-Cl2':    ('UiO-66-Cl₂', '클로로 –Cl ×2', '0', '중성 · 소수성'),
    'UiO-66-I':      ('UiO-66-I', '아이오도 –I', '0', '중성 · 소수성'),
    'UiO-66-CF3':    ('UiO-66-CF₃', '트라이플루오로메틸', '0', '중성 · 소수성'),
    'UiO-66-MM':     ('UiO-66-CH₃', '메틸 –CH₃', '0', '중성 · 소수성'),
    'UiO-66-DM':     ('UiO-66-(CH₃)₂', '메틸 –CH₃ ×2', '0', '중성 · 소수성'),
    'UiO-66-OMe_2':  ('UiO-66-(OCH₃)₂', '메톡시 ×2', '0', '중성'),
    'MOF-801-SC':    ('MOF-801', '링커 교체 (푸마르산)', '0', '작은 기공 · 중성'),
    'mil-100-fe':    ('MIL-100(Fe)', '다른 계열 (Fe-BTC)', '+', 'Fe–OH 자리 · 철–인 친화'),
}
CLASS = {1: '불안정', 2: '낮은 동역학적 안정', 3: '높은 동역학적 안정', 4: '열역학적 안정'}

def verdict(row):
    if row.water_class <= 2:
        return '제외', '물에서 약함 (2등급 이하)'
    if row.effect == '-':
        return '제외', '인산염과 같은 음전하'
    if row.effect == '+':
        return '추천', '물 안정 + 인산염 결합 도움'
    return '비교군', '물 안정, 결합 효과 중립'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ws24', type=Path, required=True)
    ws = ap.parse_args().ws24
    feats = pd.read_csv(ws / 'features/features_and_labels.csv').set_index('MOF_name')
    labels = pd.read_csv(ws / 'data_sets/WS14s/labels.csv')
    labels['MOF_name'] = labels.filename.str.removesuffix('.cif')
    labels = labels.set_index('MOF_name')
    model = joblib.load(sorted((ROOT / 'models').glob('water_rf_*.joblib'))[0])
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, (name, group, effect, reason) in VARIANTS.items():
        f, lab = feats.loc[key], labels.loc[key]
        shutil.copyfile(ws / 'data_sets/WS14s/CIFs' / f'{key}.cif', OUT / f'{key}.cif')
        rows.append({'key': key, 'name': name, 'group': group, 'effect': effect, 'effect_reason': reason,
                     'water_class': int(f.water_label), 'water_class_label': CLASS[int(f.water_label)],
                     'label_confidence': lab.confidence, 'acid_stable': bool(f.acid_label),
                     'base_stable': bool(f.base_label), 'boiling_stable': bool(f.boiling_label),
                     'lcd_A': f.Di, 'pld_A': f.Df, 'gsa_m2_g': f.GSA,
                     'rf_in_sample': float(model['estimator'].predict_proba(f[FEATURES].to_numpy(float).reshape(1, -1))[0, 1]),
                     'cif': f'{key}.cif'})
    df = pd.DataFrame(rows)
    df[['verdict', 'verdict_reason']] = df.apply(lambda r: pd.Series(verdict(r)), axis=1)
    df.to_csv(OUT / 'variants.csv', index=False)
    print(df[['name', 'water_class', 'effect', 'verdict']].to_string())

if __name__ == '__main__':
    main()
