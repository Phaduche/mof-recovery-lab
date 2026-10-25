"""Phosphate-recovery screening checklist: transparent rules of thumb, not a learned model."""
import math

# Metals whose oxo/hydroxo nodes are reported to bind phosphate (ligand exchange, M–O–P).
PHOSPHATE_METALS = {'Zr', 'Hf', 'Ce', 'La', 'Fe', 'Al', 'Ti'}
PHOSPHATE_DIAMETER_A = 4.8   # PO4^3- thermochemical radius ~2.4 Å, hydration shell ignored
WATER_INDEX_MIN = 70

def _ok(value):
    return value is not None and not (isinstance(value, float) and math.isnan(value))

def checklist(water_prob=None, in_domain=None, metal=None, pld_A=None, water_class=None, group_effect=None):
    """Return [(label, passed: True/False/None, detail)]; None means not enough data."""
    rows = []
    if _ok(water_class):
        rows.append(('물 안정성 (문헌)', water_class >= 3, f'{int(water_class)}등급 / 4'))
    elif _ok(water_prob):
        rows.append(('물 안정성 (AI)', 100 * water_prob >= WATER_INDEX_MIN, f'지수 {100*water_prob:.0f} (기준 {WATER_INDEX_MIN})'))
    else:
        rows.append(('물 안정성', None, '예측 없음'))
    if _ok(in_domain) and not _ok(water_class):
        rows.append(('AI 학습 범위', bool(in_domain), '안쪽' if in_domain else '바깥 · 외삽'))
    metals = {m.strip() for m in str(metal or '').replace(',', ' ').split()} if _ok(metal) else set()
    rows.append(('인산염 결합 금속', bool(metals & PHOSPHATE_METALS) if metals else None,
                 ', '.join(sorted(metals)) or '미상'))
    if _ok(pld_A):
        # Narrow pores don't rule a MOF out: phosphate also binds node defects and the outer surface.
        rows.append(('기공 통과', True, f'PLD {pld_A:.1f} Å ≥ {PHOSPHATE_DIAMETER_A}') if pld_A >= PHOSPHATE_DIAMETER_A
                    else ('기공 통과', None, f'PLD {pld_A:.1f} Å · 표면 · 결함 자리 흡착 위주'))
    if group_effect is not None:
        rows.append(('작용기 전하', group_effect != '-',
                     {'+': '결합 도움', '0': '중립', '-': '음전하 → 반발'}[group_effect]))
    return rows

def summary(rows):
    known = [p for _, p, _ in rows if p is not None]
    passed = sum(known)
    if any(p is False for _, p, _ in rows[:1]):
        return '부적합', passed, len(known)
    if known and passed == len(known):
        return '유망', passed, len(known)
    return '검토', passed, len(known)
