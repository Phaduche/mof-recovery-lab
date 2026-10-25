import pandas as pd
import streamlit as st
from moflab import data, ui, viewer
from moflab.cif import inspect_cif
from moflab.descriptors import FEATURES

ui.heading('Tool', '물 안정성 예측', 'MOFSimplify descriptor CSV → 우리 AI 모델의 예측')

samples = {f['name']: f for f in data.finalists() if f['descriptor_frame'] is not None}
step1, step2 = st.columns([1, 1.25])
with step1:
    st.markdown('**① 구조 특성 입력**')
    mode = st.radio('입력 방식', ['예시 구조', 'CSV 업로드'], horizontal=True, label_visibility='collapsed')
    if mode == '예시 구조':
        pick = st.selectbox('예시', list(samples))
        frame, cif_text, names = samples[pick]['descriptor_frame'], samples[pick]['cif_text'], [pick]
    else:
        up = st.file_uploader('descriptor CSV (MOFSimplify “Download descriptors”)', type='csv')
        cif_up = st.file_uploader('CIF (선택: 3D 표시와 문법 점검용)', type='cif')
        frame = pd.read_csv(up) if up else None
        names = frame['name'].astype(str).tolist() if frame is not None and 'name' in frame else None
        cif_text = None
        if cif_up:
            raw = cif_up.getvalue()
            try:
                st.json(inspect_cif(raw), expanded=False)
                cif_text = raw.decode('utf-8-sig', errors='replace')
            except ValueError as exc:
                st.error(str(exc))
    with st.expander('입력 특성 12개'):
        st.code('\n'.join(FEATURES))

with step2:
    st.markdown('**② 예측 결과**')
    if frame is None:
        st.info('CSV를 올리면 결과가 여기에 표시됩니다.')
    else:
        try:
            res = data.predict_water(frame)
        except ValueError as exc:
            st.error(str(exc))
        else:
            res.insert(0, 'name', names or [f'#{i+1}' for i in range(len(res))])
            if len(res) == 1:
                row = res.iloc[0]
                ui.confidence(float(row.water_prob))
                st.write('')
                ui.kv([('판정 (0.5 기준)', '물에 안정' if row.water_prob > 0.5 else '불안정 쪽'),
                       ('학습 범위', '안쪽' if row.in_domain else '바깥 — 외삽이므로 신뢰도 낮음'),
                       ('표준화 거리', f'{row.domain_distance:.3f}'),
                       ('트리 간 편차', f'{row.tree_sd:.3f}'),
                       ('가장 가까운 학습 MOF', row.nearest_training_name)])
            else:
                st.dataframe(res, hide_index=True, width='stretch',
                             column_config={'water_index': st.column_config.ProgressColumn(
                                 '물 안정성 지수', min_value=0, max_value=100, format='%.1f')})
            st.download_button('예측 결과 CSV', res.to_csv(index=False).encode('utf-8-sig'),
                               file_name='water_stability_predictions.csv')

if cif_text:
    st.markdown('**③ 구조 미리보기**')
    viewer.crystal(cif_text, '볼 & 스틱', 1, True, False, height=440)

st.divider()
ui.note('CSV 얻는 법: <a href="https://mofsimplify.mit.edu/water_stability_prediction.html" target="_blank">MOFSimplify</a>'
        '에 CIF 업로드 → “Download descriptors”. 예측은 물 안정성만 다룹니다.')
