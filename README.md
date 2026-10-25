# MOF Recovery Lab

**AI로 찾는 인(P) 자원 회수용 MOF** — 옹기종기 · Korea Junior Water Prize 2026 본선 연구 웹사이트

하수처리장 반류수·소화 탈리액처럼 인이 농축된 흐름에서 인산염을 붙잡고 다시 떼어낼 수 있는 금속-유기 골격체(MOF)를
공개 구조 데이터베이스와 머신러닝으로 1차 선별하고, 실험으로 검증하는 과정을 보여주는 Streamlit 앱입니다.

## 페이지

| 메뉴 | 내용 |
|---|---|
| 홈 | 한 줄 소개, 최종 선택 MOF 3D, 연구 흐름 |
| 결과 | 최종 후보 + UiO-66 변형체 19종 비교 → 선정 과정(퍼널), 전체 표, 3D 비교 |
| 실험 계획 | 고등학교 실험실용 2주 프로토콜, 준비물, 기록지 CSV |
| 후보 탐색 | CoRE MOF 2025 2,737개 구조를 물 안정성 지수·금속·기공 크기로 필터링 |
| 구조 상세 | 구조 하나의 3D 뷰어, 예측 신뢰도, Zeo++ 기공 특성 (AlphaFold DB 항목 페이지 스타일) |
| 물 안정성 예측 | MOFSimplify descriptor CSV를 넣으면 RF 모델이 확률·학습 범위를 계산 |
| 회수 성능 계산기 | 흡착–탈착 물질수지, 100점 평가(안정성 40·포집 20·탈착 25·재사용 15), 적용 시나리오 |
| 방법 · 모델 | ROC·신뢰도 곡선, 특성 중요도, 학습 범위, 평가 규칙, 한계 |
| 데이터 출처 | 6개 공개 출처의 버전·라이선스·역할 |

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 배포

1. <https://share.streamlit.io> 에 GitHub 계정으로 로그인
2. **Create app → Deploy a public app from GitHub**
3. Repository `Phaduche/mof-recovery-lab`, Branch `main`, Main file path `app.py`
4. Advanced settings에서 Python **3.12** 선택 → Deploy

`main`에 push하면 배포된 사이트가 자동으로 다시 빌드됩니다.

## 수정하는 법

- **최종 순위 바꾸기**: `data/variants/picks.json`.
- **변형체 목록 · 판정 규칙**: `scripts/build_variants.py` (WS24 데이터셋, Zenodo 12110918) 수정 후
  `python -m scripts.build_variants --ws24 <data_sets와 features가 있는 폴더>`.
- **문구·레이아웃**: 각 페이지는 `views/*.py`, 공통 스타일은 `moflab/ui.py`.
- **3D 뷰어**: `moflab/viewer.py` (3Dmol.js 2.4.2, cdnjs).
- **데이터 갱신**: 로컬 전체 연구 앱(SQLite, 약 100 MB)에서 스냅숏을 다시 만듭니다.

  ```bash
  python -m scripts.export_snapshot --lab ../mof_recovery_lab
  ```

## 구성

```
app.py                  내비게이션
views/                  페이지
moflab/                 데이터 로딩 · 3D 뷰어 · UI · 점수 규칙 · 물질수지
data/catalog.parquet    CoRE MOF 2025 후보 + 예측값
data/cifs/*.cif.gz      3D 구조 2,737개 (gzip)
data/variants/          UiO-66 변형체 19종 (문헌 라벨 + CIF) · 최종 순위
data/finalists/         MOFSimplify 실행 결과 · 예측 예시용 descriptor
models/                 물 안정성 RF 모델 · 검증 기록 · OOF 예측
```

## 모델에 대해 정직하게

- MOFSimplify 공개 물 안정성 라벨(1,081행)로 **독립 학습한** Random Forest입니다. MIT 공식 모델의 재현이 아닙니다.
- 그룹 5-fold 교차검증 OOF ROC-AUC 0.805, 균형 정확도 0.722. 외부 실험 검증과 확률 보정은 아직 없습니다.
- 예측은 문헌 클래스 기반 **물 안정성**입니다. 인산염 포집·탈착 성능이나 합성 가능성을 예측하지 않습니다.

데이터 출처와 라이선스는 [DATA_SOURCES.md](DATA_SOURCES.md)에 있습니다.
