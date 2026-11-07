# MOF Recovery Lab

옹기종기 · 2026 대한민국 청소년 물 대상(KJWP) 본선

웹사이트: https://phaduche.github.io/mof-recovery-lab/

- 하수처리장 반류수처럼 인이 진한 물에서 인산염을 붙잡았다가 다시 떼어 쓸 수 있는 MOF를 AI로 찾았다.
- 공개 데이터베이스의 MOF 3,657개를 물 안정성, 인 포집, 탈착, 재사용을 합친 200점 만점으로 채점했다.
- 물 안정성은 논문 실험값으로 학습한 Random Forest로 예측했고, 나머지 세 항목은 화학 원리를 점수로 바꿔 계산했다.
- 상위 3개의 링커와 금속을 바꾼 구조 39개를 다시 채점해서 PCN-128W에 –OH를 붙인 구조(185.0점)를 골랐다.
- 웹사이트에서 A-1부터 Final까지 단계별 결과와 3D 구조를 볼 수 있다.

## 다시 실행

```bash
pip install -r requirements.txt
python run_ai.py       # 교차검증부터 외부 검증까지 다시 계산 (보고서 숫자와 같음)
streamlit run app.py   # AI 예측 앱
```

데이터 출처와 라이선스는 [DATA_SOURCES.md](DATA_SOURCES.md)에 있다.
