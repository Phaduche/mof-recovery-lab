import pandas as pd
import streamlit as st
from moflab import data, ui

ui.heading('Data provenance', '데이터 출처',
           '모든 구조·특성·라벨은 공개 데이터베이스에서 가져왔고 버전을 고정했습니다. '
           '출처마다 역할이 다르며, 6개 출처는 독립적인 6개의 인산염 실험 데이터가 아닙니다.')
roles = {'core2025': '3D 구조(CIF)·기공 특성·AI 예측 대상', 'core2019': '구조 보고 근거·기하 메타데이터',
         'qmof': '전자구조 메타데이터·실험/가상 구분', 'mofsimplify': 'AI 학습용 문헌 물 안정성 라벨',
         'arc': '기하 특성 시범 부분집합 (앞 500행)', 'ultrastable': '노드·링커 구성 단위 참고'}
src = pd.DataFrame(data.sources())
src['역할'] = src.source_id.map(roles)
st.dataframe(src[['name', '역할', 'records', 'version', 'license', 'url']].rename(
    columns={'name': '출처', 'records': '수록 건수', 'version': '버전', 'license': '이용 조건', 'url': '링크'}),
    hide_index=True, width='stretch', column_config={'링크': st.column_config.LinkColumn(display_text='열기'),
                                                     '수록 건수': st.column_config.NumberColumn(format='%d')})
ui.note('웹 배포본에는 CoRE MOF 2025 공개 CR 구조 2,737개의 CIF와 예측값만 담았습니다. '
        '전체 36,857건 DB(약 100 MB)와 실험 기록 기능은 로컬 연구 앱에 있습니다.')

st.subheader('인용')
st.markdown('''
- Zhao, G. et al. *CoRE MOF 2025 Dataset*, Zenodo 15621349 (CC BY 4.0)
- Chung, Y. G. et al. *CoRE MOF 2019 Dataset*, Zenodo 3370144 (CC BY 4.0)
- Rosen, A. S. et al. *Matter* **4**, 1578 (2021); *npj Comput. Mater.* **8**, 112 (2022) — QMOF
- Nandy, A. et al. *Sci. Data* **9**, 74 (2022) — MOFSimplify
- Burner, J. et al. *ARC-MOF*, Zenodo 16802743 (CC BY 4.0)
- Nandy, A. et al. *Ultrastable MOF building blocks*, Zenodo 7666081 (CC BY 4.0)
- 3D 표시: 3Dmol.js (Rego & Koes, *Bioinformatics* 2015)
''')
st.caption('우리 RF 모델은 MOFSimplify 공개 라벨로 독립 학습한 것이며 MIT 공식 모델의 재현이나 공동 개발이 아닙니다.')
