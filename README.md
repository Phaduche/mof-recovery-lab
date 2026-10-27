# MOF Recovery Lab

**AI로 찾는 인(P) 자원 회수용 MOF** — 옹기종기 · Korea Junior Water Prize 2026 본선 연구 웹사이트

하수처리장 반류수·소화 탈리액처럼 인이 농축된 흐름에서 인산염을 붙잡고 다시 떼어낼 수 있는 금속-유기 골격체(MOF)를
공개 구조 데이터베이스와 머신러닝으로 1차 선별하고, 실험으로 검증하는 과정을 보여주는 Streamlit 앱입니다.

## 흐름 (기본 화면: 파이프라인)

| 단계 | 내용 |
|---|---|
| A-1 | 데이터베이스에서 MOF 가져오기 — CoRE MOF 2025 (2,565) + MOFSimplify/WS24 (1,092) = 3,657개 |
| A-2 | 모든 MOF를 같은 AI 모델로 200점 만점 채점 |
| A-3 | 최고점 3개 = 최종 MOF (PCN-128W · Zr-MOF·xly (2017) · NPF-200) |
| B-1 | 최종 3개의 링커(작용기 7종) · 원소(Zr → 금속 6종)를 바꿈 |
| B-2 | 수정한 39개를 같은 AI 모델로 다시 채점 |
| Final | 가장 점수가 높은 MOF — **PCN-128W –OH (185.0 / 200)** |

**점수 (200점)**: 안정성 100 (절대평가: RF 물 안정성 확률 × 100) + 포집 40 · 탈착 35 · 재사용 25
(상대평가: A 단계 데이터베이스 기준 z-score → 배점 × Φ(z/2)). 동점이면 네 점수 불균형(z)이 낮은 MOF가 앞.
규칙은 `moflab/pipeline.py`에 있습니다.

위쪽 메뉴가 곧 단계입니다: **A-1 · A-2 · A-3 · B-1 · B-2 · Final** (각 단계 코드는 `moflab/steps.py`).
B-1에는 Zr를 12가지 금속(K 포함)으로 바꾼 CHGNet 교체 에너지가 함께 나옵니다.
**연구** 메뉴: 소개 · 방법 · 모델 · 데이터 출처.

**사용하는 AI**: 안정성 = ML(Random Forest 분류기) · 원소 교체 에너지 = DL(CHGNet 그래프 신경망) ·
포집/탈착/재사용 = 화학 규칙 + z-score. DFT는 직접 돌리지 않습니다(CHGNet은 DFT 결과로 학습한 근사).

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

- **A · B 단계 다시 계산**: WS24(Zenodo 12110918)를 받아 압축을 푼 뒤
  `python -m scripts.build_pipeline --ws24 <폴더>` → `python -m scripts.build_stage_b --ws24 <폴더>` (pymatgen 필요).
  결과는 `data/pipeline/`에 저장되고 사이트가 그대로 읽습니다.
- **변형체 목록 · 판정 규칙**: `scripts/build_variants.py` (WS24 데이터셋, Zenodo 12110918) 수정 후
  `python -m scripts.build_variants --ws24 <data_sets와 features가 있는 폴더>`.
- **문구·레이아웃**: 각 페이지는 `views/*.py`, 공통 스타일은 `moflab/ui.py`.
- **3D 뷰어**: `moflab/viewer.py` (3Dmol.js 2.4.2, cdnjs).
- **금속 교체 다시 계산**: `pip install chgnet` 후 `python -m scripts.metal_swap` (노트북에서 금속당 1–10분, 중간에 끊겨도 이어서 계산).
  웹앱은 `data/metal_swap/` 결과만 읽으므로 Streamlit Cloud에 chgnet을 설치하지 않습니다.
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
