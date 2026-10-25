import pandas as pd
import streamlit as st
from moflab import data, ui

ui.heading('Data', '데이터 출처', '모두 공개 데이터 · 버전 고정')
roles = {'core2025': '3D 구조(CIF)·기공 특성·AI 예측 대상', 'core2019': '구조 보고 근거·기하 메타데이터',
         'qmof': '전자구조 메타데이터·실험/가상 구분', 'mofsimplify': 'AI 학습용 문헌 물 안정성 라벨',
         'arc': '기하 특성 시범 부분집합 (앞 500행)', 'ultrastable': '노드·링커 구성 단위 참고'}
src = pd.DataFrame(data.sources())
src['역할'] = src.source_id.map(roles)
st.dataframe(src[['name', '역할', 'records', 'version', 'license', 'url']].rename(
    columns={'name': '출처', 'records': '수록 건수', 'version': '버전', 'license': '이용 조건', 'url': '링크'}),
    hide_index=True, width='stretch', column_config={'링크': st.column_config.LinkColumn(display_text='열기'),
                                                     '수록 건수': st.column_config.NumberColumn(format='%d')})
ui.note('UiO-66 변형체 19종: WS24 데이터셋 (Terrones et al., <i>JACS</i> 2024, Zenodo 12110918, CC BY 4.0)')

st.subheader('인용')
st.markdown('''
- Zhao, G. et al. *CoRE MOF 2025 Dataset*, Zenodo 15621349 (CC BY 4.0)
- Chung, Y. G. et al. *CoRE MOF 2019 Dataset*, Zenodo 3370144 (CC BY 4.0)
- Rosen, A. S. et al. *Matter* **4**, 1578 (2021); *npj Comput. Mater.* **8**, 112 (2022) — QMOF
- Nandy, A. et al. *Sci. Data* **9**, 74 (2022) — MOFSimplify
- Burner, J. et al. *ARC-MOF*, Zenodo 16802743 (CC BY 4.0)
- Nandy, A. et al. *Ultrastable MOF building blocks*, Zenodo 7666081 (CC BY 4.0)
- Terrones, G. et al. *J. Am. Chem. Soc.* (2024), doi:10.1021/jacs.4c05879 — WS24
- Burtch, N. C. et al. *Chem. Rev.* **114**, 10575 (2014) — 물 안정성 등급
- 3D 표시: 3Dmol.js (Rego & Koes, *Bioinformatics* 2015)
''')
st.caption('우리 RF 모델은 MOFSimplify 공개 라벨로 독립 학습한 것이며 MIT 공식 모델의 재현이나 공동 개발이 아닙니다.')
