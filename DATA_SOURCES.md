# 공개 데이터 출처와 사용 범위

실제 내려받아 정규화한 자료만 수록 건수에 포함했습니다. 출처 6개는 데이터 소유자·배포 컬렉션 기준이며 독립 실험 집단 6개라는 뜻이 아닙니다. 수집일은 2026-10-16 UTC입니다. 팀 입력은 별도 `team` 출처이며 공개 출처 수에 넣지 않습니다.

| ID | 원 출처·저자 | 고정한 버전 | 수록 | 이용 조건 |
|---|---|---|---:|---|
| core2025 | Zhao, Guobin et al., *Computation-Ready Experimental Metal-Organic Framework (CoRE MOF) 2025 Dataset* | Zenodo 15621349, v1.0 | 2,737 | CC BY 4.0 |
| core2019 | Chung, Yongchul G. et al., *CoRE MOF 2019 Dataset* | Zenodo 3370144, v1.1.0 | 12,020 | CC BY 4.0 |
| qmof | Rosen, Andrew et al., *QMOF Database* | Figshare article 13147324 v18; file 59573735 | 20,372 | CC BY 4.0 |
| mofsimplify | hjkgrp, *MOFSimplify* 공개 water/acid 자료 | Git commit 5693968b3e9b9e26eab3bdb1db908ae2877d4bb7 | 1,092 | 저장소 MIT 라이선스, 원 연구 자료 인용 필요 |
| arc | Burner, Jake et al., *ab initio REPEAT Charge MOF Database (ARC-MOF)* | Zenodo 16802743 | 500 | CC BY 4.0 |
| ultrastable | Nandy, Aditya et al., *A Database of Ultrastable MOFs Reassembled from Stable Fragments with Machine Learning Models* | Zenodo 7666081, v1.2.0 | 136 | CC BY 4.0 |

원 저자·배포 기록의 전체 메타데이터는 `data/source_metadata/`에 보존했습니다. SQLite의 각 자료에는 출처·원본 행/키·정규화 payload SHA-256이 있고, 내려받은 파일의 URL·SHA-256·크기·부분 수집 여부는 `data/source_inventory.json`에 있습니다. 원본의 MD5가 제공된 다운로드는 MD5도 확인했습니다. SQLite에 넣으면서 필드를 골랐거나 빈 값 표기를 통일한 변경을 아래에 설명합니다.

## CoRE MOF 2025

- 배포 기록: <https://zenodo.org/records/15621349>
- DOI: <https://doi.org/10.5281/zenodo.15621349>
- 사용 파일: `CR_meta_data_SI.json`, `CoREMOFDBSI_0613.zip`.
- 공개 CR 메타데이터 2,737개 전체와 이들의 CIF를 사용했습니다. ZIP의 NCR 등 나머지 구조나 전체 CoRE 데이터베이스를 모두 넣었다고 주장하지 않습니다.
- 자료의 `unknown`·`nan` 등의 빈 표기를 null로 정리했습니다. 기하·RAC·출처·구조·안정성 메타데이터는 후보 상세의 원자료에서 확인할 수 있습니다.
- 이 중 원시 12개 모델 입력 특성을 모두 갖춘 구조 2,565개에 별도 학습한 물 안정성 분류 모델을 적용했습니다. 입력이 부족한 나머지에 평균·0을 채우지 않았습니다.
- 출처의 stability 필드는 예측값으로 별도 저장했습니다. 물·용매 안정성 값이나 분해 온도를 정량적인 인산염 구조 유지율로 바꾸지 않았습니다.

## CoRE MOF 2019

- 배포 기록: <https://zenodo.org/records/3370144>
- DOI: <https://doi.org/10.5281/zenodo.3370144>
- 사용 파일: `2019-07-01-ASR-public_12020.csv` 전체.
- 12,020개 행의 공개 구조 메타데이터와 기하·금속 정보를 가져왔습니다. 이 출처의 대용량 CIF tar는 포함하지 않았습니다.
- 구조가 보고되었다는 근거와 기하 정보의 참고용입니다. 포집·회수·재사용의 실험 라벨을 제공하지 않습니다. 다른 출처의 같은 구조 이름과 자동 병합하지 않았습니다.

## QMOF

- 배포 기록: <https://figshare.com/articles/dataset/QMOF_Database/13147324>
- 이번 버전 DOI: <https://doi.org/10.6084/m9.figshare.13147324.v18>
- 공식 코드·설명: <https://github.com/Andrew-S-Rosen/QMOF>
- 사용 파일: file ID `59573735`의 `qmof_database.zip` 내부 `qmof.csv`.
- 20,372개 행에서 ID·이름·화학식·구조 기하·밀도·합성 보고 여부·출처·DOI·PBE bandgap/energy 등의 제한된 필드를 수록했습니다. 계산 JSON·전하·모든 최적화 CIF를 이 앱에 담지는 않았습니다.
- 합성 보고 플래그를 사용해 reported experimental과 hypothetical을 구분했습니다. 보고 플래그는 현재 팀의 합성 성공 증거가 아닙니다. 밴드갭이나 에너지를 인산염 흡착·탈착값으로 간주하지 않습니다.
- 데이터 재사용 시 공식 저장소가 요청한 두 연구를 함께 인용해야 합니다: Rosen et al., *Matter* (2021), DOI <https://doi.org/10.1016/j.matt.2021.02.015>; Rosen et al., *npj Computational Materials* (2022), DOI <https://doi.org/10.1038/s41524-022-00796-6>.

## MOFSimplify water labels

- 공식 사이트: <https://mofsimplify.mit.edu/>
- 공식 저장소: <https://github.com/hjkgrp/MOFSimplify>
- 고정 원자료: <https://raw.githubusercontent.com/hjkgrp/MOFSimplify/5693968b3e9b9e26eab3bdb1db908ae2877d4bb7/model/water_and_acid/features_and_labels.csv>
- 원본 라이선스: `data/source_metadata/MOFSimplify_LICENSE.txt`.
- 원시 물 안정성 자료 1,092행과 특성을 그대로 보존했습니다. 모델용 CSV에는 이름·water_label·고정한 12개 특성을 선택했습니다. 서로 같은 특성의 중복과 안정/불안정 라벨 충돌을 처리한 후 1,081개 학습 행을 사용했습니다.
- 클래스 3·4를 stable, 1·2를 unstable로 사용했습니다. 클래스는 정량 유지율이나 물에서 녹는 질량 백분율이 아닙니다. 산·염기·끓는 물 관련 라벨을 모델 입력으로 쓰지 않았습니다.
- 앱의 RF는 이 공개 자료로 별도 학습한 모델입니다. 공식 서버의 원 모델을 실행하거나 MIT와 공동 개발한 것으로 표시하지 않습니다. 정량 인산염 흡착·회수 모델이나 물리 시뮬레이터가 아닙니다.
- 고정한 12개 특성은 문헌 선정 특성입니다. 성능 검증에서 그 특성 선정 과정까지 nested CV로 다시 수행하지 않았다는 한계를 명시합니다.
- 공식 MOFSimplify 소개 연구: Nandy et al., *MOFSimplify, machine learning models with extracted stability data of three thousand metal–organic frameworks*, *Scientific Data* (2022). <https://www.nature.com/articles/s41597-022-01181-0>. 소개 논문의 전체 자료 수를 이 water 라벨 수와 혼동하지 않습니다. 개별 라벨 자료의 인용은 저장소와 원 데이터셋 출처도 확인해야 합니다.

## ARC-MOF

- 배포 기록: <https://zenodo.org/records/16802743>
- DOI: <https://doi.org/10.5281/zenodo.16802743>
- 사용 파일: `geometric_properties.csv`의 **원본 순서 앞 500행**.
- 대용량 전체 데이터베이스를 내려받아 학습한 것이 아닙니다. 무작위·층화 표본이 아니므로 데이터베이스 분포의 대표값이나 후보 성능의 통계적 비교에 사용하지 않습니다. 이 부분집합의 SHA-256을 기록하며 원본 전체 파일의 해시와 구분합니다.
- 실험·가상 구조가 혼재하므로 구조 상태를 mixed_or_unverified로 표시하고 최종 종합 순위의 구조 근거로 통과시키지 않습니다. 가스 흡착 자료를 인산염 실험으로 바꾸지 않습니다.

## Ultrastable MOF building blocks

- 배포 기록: <https://zenodo.org/records/7666081>
- DOI: <https://doi.org/10.5281/zenodo.7666081>
- 사용 파일: `building_blocks.zip`, `readme.txt`.
- 공개 CSV 3개의 노드·링커 구성 단위 136개와 ZIP의 XYZ 참고 파일을 수록했습니다. 대규모 가상 MOF 구조·특성 ZIP은 내려받아 수록하지 않았습니다.
- 각 행은 building_block입니다. 완성된 MOF 136종이 아니며 후보 검색에서 실제 MOF만 필터링할 때 제외됩니다. 안정한 구성 단위를 결합하면 완성 구조도 안정하거나 합성 가능하다는 보장은 없습니다.
- 새 소재 연구의 구성 단위 참고용으로 사용합니다. 임의의 조합에 기존 물 안정성 점수나 성능값을 복사하지 않습니다.

## 화면 글꼴

한국어가 설치되지 않은 운영체제에서도 읽을 수 있도록 Nanum Gothic 글꼴을 함께 제공합니다. 원본은 Google Fonts의 <https://github.com/google/fonts/tree/main/ofl/nanumgothic>에서 받았으며 배포 크기를 줄이기 위해 TTF를 WOFF2 형식으로 변환했습니다. 글리프 디자인은 바꾸지 않았습니다. 원본 저작권과 SIL Open Font License는 `static/fonts/OFL.txt`에 있습니다. 앱은 포함한 글꼴을 로컬에서 제공하며 실행 때 외부 글꼴 서버에 접속하지 않습니다.

## 출처가 있다고 말할 수 없는 것

이 자료들만으로 인산염 포집량·선택성·탈착 회수율·순환 재사용 성능을 동시에 학습하거나 새 MOF의 존재를 입증할 수 없습니다. 인산염용 문헌 수치나 실험 자료는 별도로 출처·단위·조건을 확인해야 합니다. 팀 실험과 수기 문헌 평가에는 원자료 파일·실험 번호 또는 DOI·쪽수·표 번호를 남깁니다.

코드는 원자료 수집과 정규화 과정을 재현하도록 포함했습니다. 공개 메타데이터를 별도 SQLite로 정리하고, 일부 자료는 위 범위로 제한했으며, 가상·미확인·예측의 구분을 추가한 것이 이 앱의 변경 사항입니다. 원 저자의 보증이나 프로젝트 참여를 암시하지 않습니다.
