"""Syntax-level CIF inspection for uploaded structures (no synthesizability claims)."""
import math

def inspect_cif(cif_bytes):
    import gemmi
    if len(cif_bytes)>10*1024*1024:raise ValueError('CIF는 10 MB 이하로 업로드하세요.')
    try:
        text=cif_bytes.decode('utf-8-sig')
        doc=gemmi.cif.read_string(text)
        if len(doc)!=1:raise ValueError('단일 구조 data block이 필요합니다.')
        block=doc.sole_block();structure=gemmi.make_small_structure_from_block(block)
    except Exception as exc:raise ValueError('CIF 해석 실패: '+str(exc)) from exc
    cell=structure.cell
    parameters=[cell.a,cell.b,cell.c,cell.alpha,cell.beta,cell.gamma]
    if any(not math.isfinite(x) for x in parameters) or min(parameters[:3])<=0 or not all(0<x<180 for x in parameters[3:]) or not math.isfinite(cell.volume) or cell.volume<=0:
        raise ValueError('유효한 결정 격자 길이·각도·부피가 필요합니다.')
    if not structure.sites:raise ValueError('원자 좌표가 없습니다.')
    elements={};partial=False
    for site in structure.sites:
        if not all(math.isfinite(x) for x in (site.fract.x,site.fract.y,site.fract.z,site.occ)):
            raise ValueError('유한하지 않은 좌표 또는 점유율입니다.')
        if site.element.atomic_number<=0:raise ValueError('알 수 없는 원소입니다.')
        if not 0 < site.occ <= 1:raise ValueError('원자 점유율은 0 초과 1 이하여야 합니다.')
        partial=partial or site.occ<0.9999
        elements[site.element.name]=elements.get(site.element.name,0)+1
    return {'data_block':block.name,'cell_A_deg':parameters,'volume_A3':cell.volume,
            'asymmetric_unit_sites':len(structure.sites),'elements_site_counts':elements,
            'partial_occupancy':partial,'syntax_check_passed':True,
            'synthesizability_proven':False,'topology_charge_collision_checked':False,
            'note':'문법·격자·좌표 점검입니다. 결합·전하 균형·구조 최적화·합성 가능성의 검증이 아닙니다.'}

