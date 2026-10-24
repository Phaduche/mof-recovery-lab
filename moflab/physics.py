import math

P_MASS = 30.973761998
PO4_TO_P = (P_MASS + 4*15.999)/P_MASS

def _number(value, name, positive=False):
    v = float(value)
    if not math.isfinite(v) or v < 0 or (positive and v == 0):
        raise ValueError(f'{name}: 유한한 '+('양수' if positive else '0 이상의 값')+'가 필요합니다.')
    return v

def concentration_as_p(value, unit='mg P/L'):
    v = _number(value,'농도')
    if unit == 'mg P/L': return v
    if unit == 'mg PO4/L': return v/PO4_TO_P
    raise ValueError('농도 단위는 mg P/L 또는 mg PO4/L여야 합니다.')

def mass_balance(initial_mgP_L, residual_mgP_L, initial_ml, residual_ml,
                 dry_mof_mg, desorb_mgP_L=None, desorb_ml=None,
                 sampled_p_mg=0., blank_loss_p_mg=0., wash_loss_p_mg=0.):
    c0=_number(initial_mgP_L,'초기 농도',True)
    ce=_number(residual_mgP_L,'잔류 농도')
    v0=_number(initial_ml,'초기 부피',True)
    ve=_number(residual_ml,'잔류 부피',True)
    m=_number(dry_mof_mg,'건조 MOF 질량',True)
    sampled=_number(sampled_p_mg,'채취된 인 질량')
    blank=_number(blank_loss_p_mg,'공시험 손실')
    wash=_number(wash_loss_p_mg,'세척액 손실')
    initial=c0*v0/1000.
    residual=ce*ve/1000.
    captured=initial-residual-sampled-blank
    tolerance=max(initial*1e-9,1e-12)
    if captured < -tolerance:
        raise ValueError('질량수지 불일치: 잔류·채취·공시험 인 질량이 초기량을 넘습니다.')
    captured=max(0.,captured)
    recovered=None
    if (desorb_mgP_L is None) != (desorb_ml is None):
        raise ValueError('탈착 농도와 부피를 함께 입력하세요.')
    if desorb_mgP_L is not None:
        recovered=_number(desorb_mgP_L,'탈착 농도')*_number(desorb_ml,'탈착 부피',True)/1000.
        if recovered+wash > captured+tolerance:
            raise ValueError('질량수지 불일치: 회수액·세척액의 인이 포집량을 넘습니다. 단위·공시험·측정 오차를 확인하세요.')
    elif wash > captured+tolerance:
        raise ValueError('세척액 인 질량이 포집량을 넘습니다.')
    return {'initial_p_mg':initial, 'residual_p_mg':residual, 'captured_p_mg':captured,
            'recovered_p_mg':recovered, 'capture_pct':100*captured/initial,
            'capture_mgP_g':1000*captured/m,
            'desorption_pct':100*recovered/captured if recovered is not None and captured>0 else None,
            'overall_recovery_pct':100*recovered/initial if recovered is not None else None,
            'recovered_mgP_g':1000*recovered/m if recovered is not None else None,
            'unrecovered_captured_p_mg':captured-recovered-wash if recovered is not None else None,
            'concentration_factor':desorb_mgP_L/c0 if recovered is not None else None,
            'interpretation':'용액 질량수지상 겉보기 포집량; 침전·용출은 공시험과 고체 분석으로 구분해야 함'}

def scenario_recovery(flow_m3_day, concentration_mgP_L, recovery_fraction):
    flow=_number(flow_m3_day,'처리량')
    c=_number(concentration_mgP_L,'인 농도')
    eta=_number(recovery_fraction,'회수율')
    if eta>1: raise ValueError('회수율은 0~1입니다.')
    return flow*c/1000.*eta
