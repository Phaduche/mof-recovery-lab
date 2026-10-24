"""Project decision rules, deliberately separate from learned predictions."""
from dataclasses import dataclass, field
import math
from statistics import mean, pstdev

CRITERIA = ('stability', 'capture', 'desorption', 'reuse')
LABELS = {'stability':'안정성', 'capture':'포집', 'desorption':'탈착 회수', 'reuse':'재사용'}

@dataclass(frozen=True)
class ScorePolicy:
    weights: dict = field(default_factory=lambda: dict(zip(CRITERIA, (40.,20.,25.,15.))))
    stability_floor: float = 70.
    tie_decimals: int = 2

    def __post_init__(self):
        if set(self.weights) != set(CRITERIA):
            raise ValueError('네 항목의 배점이 필요합니다.')
        w = self.weights
        if any(not math.isfinite(float(x)) or x <= 0 for x in w.values()):
            raise ValueError('배점은 유한한 양수여야 합니다.')
        if not math.isclose(sum(w.values()), 100., abs_tol=1e-9):
            raise ValueError('배점 합계는 100이어야 합니다.')
        if w['stability'] <= max(w[c] for c in CRITERIA[1:]):
            raise ValueError('안정성이 가장 큰 배점이어야 합니다.')
        if not math.isfinite(self.stability_floor) or not 0 < self.stability_floor <= 100:
            raise ValueError('안정성 통과 기준은 0 초과 100 이하여야 합니다.')
        if self.tie_decimals not in range(4):
            raise ValueError('동점 판정 소수 자릿수는 0~3입니다.')

def evaluate(profile, policy=None):
    policy = policy or ScorePolicy()
    values = {}
    for c in CRITERIA:
        v = profile.get(c)
        if v is not None:
            v = float(v)
            if not math.isfinite(v) or not 0 <= v <= 100:
                raise ValueError(f'{LABELS[c]} 점수는 0~100 또는 미확인이어야 합니다.')
        values[c] = v
    missing = [LABELS[c] for c,v in values.items() if v is None]
    reasons = []
    if not profile.get('structure_supported', False):
        reasons.append('실제 구조 근거 미확인')
    if values['stability'] is None:
        reasons.append('안정성 미확인')
    elif values['stability'] < policy.stability_floor:
        reasons.append('안정성 기준 미달')
    if missing:
        reasons.append('미확인: '+', '.join(missing))
    if not profile.get('comparable', False):
        reasons.append('동일 조건·측정 근거 검토 필요')
    if profile.get('evidence_type', 'experimental') != 'experimental':
        reasons.append('실험 검증 전 예측·가설')
    total = sum(values[c]*policy.weights[c]/100 for c in CRITERIA) if not missing else None
    avg = mean(values.values()) if not missing else None
    cv = pstdev(values.values())/avg if avg and avg > 0 else (0. if avg == 0 else None)
    return {**profile, **values, 'total_score':total, 'balance_cv':cv,
            'minimum_score':min(values.values()) if not missing else None,
            'available_weight':sum(policy.weights[c] for c,v in values.items() if v is not None),
            'eligible':not reasons, 'reason':' · '.join(reasons), 'rank':None, 'balance_z':None}

def rank_profiles(profiles, policy=None):
    """Never compare ranks across condition cohorts. No missing-value reweighting."""
    policy = policy or ScorePolicy()
    rows = [evaluate(p, policy) for p in profiles]
    cohorts = {}
    for r in rows:
        if r['eligible']:
            cohorts.setdefault(r.get('condition_key','unspecified'), []).append(r)
    for group in cohorts.values():
        mu = mean(r['balance_cv'] for r in group)
        sd = pstdev(r['balance_cv'] for r in group)
        for r in group:
            r['balance_z'] = (r['balance_cv']-mu)/sd if sd > 0 else 0.
        group.sort(key=lambda r:(-round(r['total_score'],policy.tie_decimals),
                                 r['balance_cv'], -r['minimum_score'], -r['stability'], r.get('name','')))
        for rank,r in enumerate(group,1):
            r['rank'] = rank
    return sorted(rows,key=lambda r:(not r['eligible'], r.get('condition_key',''), r['rank'] or 10**9, r.get('name','')))

def capacity_index(q_mgP_g, reference_mgP_g):
    q,ref = float(q_mgP_g),float(reference_mgP_g)
    if not all(math.isfinite(v) for v in (q,ref)) or q<0 or ref<=0:
        raise ValueError('흡착량은 0 이상, 사전 목표 흡착량은 0 초과의 유한한 값이어야 합니다.')
    return min(100., 100.*q/ref)
