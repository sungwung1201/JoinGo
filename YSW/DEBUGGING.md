# DEBUGGING.md

# JoinGo / 협동2 디버깅 및 구현 정리

> 담당자: 윤성웅  
> 역할: 팀장 / 프로젝트 기획 / 통합 관리 / YOLO 디버깅 / Firebase DB 구조 개선 / 로봇-DB 연동 검토 / 시스템 아키텍처 및 플로우차트 제작  
> 기간: 2026년 5월 13일 ~ 2026년 5월 28일  
> 대상 프로젝트: JoinGo 협동2 스마트팩토리형 볼트 검사 자동화 시스템

---

## 1. 전체 개요

JoinGo 프로젝트는 제조 현장의 볼트 체결 상태를 검사하고, 검사 결과를 Firebase DB와 웹 화면, 3D 시각화, 로봇 제어 흐름과 연결하는 스마트팩토리형 검사 자동화 시스템이다.

성웅은 팀장으로서 전체 프로젝트 기획, 일정 조율, 팀원별 역할 분담, 파트 간 통합 방향 검토, 구현 과정 피드백을 담당하였다. 직접적으로는 YOLO 기반 볼트 인식 디버깅, Firebase DB 구조 개선, 로봇 제어와 DB 연동 구조 검토, 시스템 아키텍처 및 플로우차트 제작을 수행하였다.

3D 매핑 파트는 팀원이 주도적으로 구현하였고, 성웅은 구현 과정을 확인하면서 구조 검토, 디버깅 조언, 웹/DB/검사 로직과의 연동 방향 피드백을 수행하였다.

---

## 2. 초기 설계

### 2.1 초기 프로젝트 방향

초기에는 단순히 카메라로 볼트를 감지하고 결과를 확인하는 수준이 아니라, 다음과 같은 흐름을 목표로 했다.

```text
RealSense / 웹캠 입력
→ YOLO 기반 볼트 감지
→ 3D 작업 공간 구성
→ 볼트 위치 및 상태 계산
→ Firebase DB 저장
→ 웹 화면 표시
→ 로봇 제어 또는 후속 작업 연동
```

초기 설계에서 고려한 주요 구성 요소는 다음과 같다.

| 구성 요소 | 역할 |
|---|---|
| YOLO | 볼트 또는 볼트-너트 결합부 감지 |
| RealSense D435i | RGB / Depth 기반 검사 데이터 입력 |
| 3D Mapping | 작업 공간 및 볼트 위치 시각화 |
| Firebase Realtime DB | 검사 결과, 상태, 세션 정보 저장 |
| Firebase Storage | 3D 배경 파일, HTML/JS 결과 파일 저장 |
| Web Dashboard | 실시간 검사 결과 및 이력 표시 |
| Robot Control | DB의 검사 결과를 기반으로 로봇 작업 대상 판단 |
| GitHub | 팀원별 코드 통합 및 협업 관리 |

### 2.2 초기 설계상 핵심 문제

초기 설계에서 바로 드러난 문제는 다음과 같았다.

1. YOLO가 단순히 볼트를 찾는 것인지, good/ng 상태까지 판단해야 하는지 범위가 불명확했다.
2. Firebase DB에 검사 결과를 단순 저장할지, 세션/작업대/검사 이력 단위로 구조화할지 결정이 필요했다.
3. 팀원별로 앱/웹/DB/비전/로봇 파트가 나뉘어 있어 데이터 기준을 통일해야 했다.
4. 3D 매핑 결과와 YOLO 결과, 웹 표시, DB 저장 구조가 서로 맞아야 했다.
5. 발표 자료를 각자 만들더라도 시스템 흐름과 용어는 일관되어야 했다.

---

## 3. 디버깅 방식

전체 디버깅은 다음 원칙으로 진행하였다.

```text
1. 문제 발생 위치 확인
2. 입력 데이터 / 코드 / 환경 / DB 중 원인 분리
3. 기존 정상 동작 상태 확인
4. 최소 단위로 수정
5. 실행 또는 정적 검증
6. Git diff / py_compile / import test로 확인
7. 팀원 구현 파트와 충돌 여부 검토
8. README / 문서 / 발표 자료에 최종 구조 반영
```

특히 DB 구조 수정 중 SyntaxError가 발생했을 때는 바로 추가 수정을 이어가지 않고, Git으로 정상 버전을 복구한 뒤 짧은 단위로 다시 적용했다.

```bash
git restore common/db_paths.py YJH/realtime/realtime_3d_mapper_multi_04.py
python3 -m py_compile 대상파일.py
```

이 방식으로 파일이 깨진 상태에서 계속 누적 수정되는 문제를 방지했다.

---

# 4. YOLO 디버깅 과정

## 4.1 초기 목표

처음 YOLO 작업의 목표는 단순한 볼트 검출이 아니라, 볼트와 너트의 체결 상태를 good/ng로 구분하는 것이었다.

```text
good = 볼트와 너트가 완전히 붙어 있는 정상 체결 상태
ng   = 볼트와 너트 사이가 떨어져 있는 불량 체결 상태
```

하지만 실제 환경에서 볼트-너트 사이 간격은 매우 작고, 카메라 각도, 조명, 반사, 거리의 영향을 많이 받았다. 따라서 detection 모델 하나로 위치 검출과 상태 판정을 동시에 수행하기에는 한계가 있었다.

## 4.2 Roboflow 데이터셋 다운로드 및 경로 오류

초기에는 Roboflow에서 데이터셋을 내려받아 YOLO 학습을 진행했다.

기준 작업 폴더:

```text
/home/yoon/yolo_train_ws
```

실제 데이터셋 위치:

```text
/home/yoon/yolo_train_ws/hyupdong2-1/data.yaml
```

초기에 잘못 사용한 경로:

```text
/home/yoon/yolo_train_ws/bolt-detection-1/data.yaml
```

발생 오류:

```text
FileNotFoundError:
'/home/yoon/yolo_train_ws/bolt-detection-1/data.yaml' does not exist
```

원인은 실제 데이터셋 폴더명이 `bolt-detection-1`이 아니라 `hyupdong2-1`이었기 때문이다. 실제 존재하는 `data.yaml` 경로를 사용하여 해결하였다.

## 4.3 Roboflow Python 실행 오류

처음 `download_dataset.py` 안에 Jupyter Notebook 문법이 포함되어 있었다.

```python
!pip install roboflow
```

터미널에서 일반 Python 파일로 실행하면 `!pip`는 Python 문법이 아니기 때문에 다음 오류가 발생했다.

```text
SyntaxError: invalid syntax
```

해결:

```bash
sed -i '/^!pip install roboflow/d' download_dataset.py
```

이후에도 `requests`, `urllib3`, `requests_toolbelt` 버전 충돌 문제가 발생했다.

```text
ImportError: cannot import name 'appengine' from 'urllib3.contrib'
```

해결 방식은 가상환경을 새로 만들고, Roboflow와 Ultralytics를 해당 환경 안에 맞춰 설치하는 것이었다.

```bash
source ~/yolo_train_ws/rf_env/bin/activate
```

## 4.4 Roboflow 모델 업로드 문제

초기 학습 모델을 Roboflow에 다시 업로드해서 Label Assist에 활용하려고 했으나 여러 제한이 있었다.

### 문제 1. 이미 해당 version에 trained model 존재

```text
This version already has a trained model.
Please generate and train a new version in order to upload model to Roboflow.
```

의미는 Roboflow dataset version에는 이미 학습된 모델이 연결되어 있어서 같은 version에 다시 업로드할 수 없다는 것이다.

### 문제 2. 존재하지 않는 version 사용

코드에서 `project.version(3)`을 사용했지만, Roboflow 웹에는 Version 3이 없었다.

```text
RuntimeError: Version number 3 is not found.
```

### 문제 3. model_type 오류

처음에는 다음처럼 사용했다.

```python
model_type="yolov8"
```

그러나 Roboflow는 size suffix가 붙은 형식을 요구했다.

```text
Model type "yolov8" is not recognized.
```

수정:

```python
model_type="yolov8n"
```

결국 Roboflow workspace credit 문제도 겹치면서, Roboflow 의존을 줄이고 로컬 라벨링/학습 구조로 전환하였다.

---

## 4.5 로컬 LabelImg 환경 구축

Roboflow Label Assist를 계속 쓰기 어렵다고 판단하고, 로컬에서 자동 라벨링 + LabelImg 수정 + Ultralytics 학습 구조로 전환했다.

설치:

```bash
python -m pip install labelImg pyqt5 lxml
```

YOLO 라벨 형식:

```text
class_id x_center y_center width height
```

클래스 구조:

```text
0 = good
1 = ng
```

LabelImg 사용 방식:

| 키 | 기능 |
|---|---|
| W | 새 박스 생성 |
| Delete | 선택 박스 삭제 |
| Ctrl + S | 저장 |
| D | 다음 이미지 |
| A | 이전 이미지 |

## 4.6 LabelImg PyQt float 타입 오류

Ubuntu / PyQt 환경에서 LabelImg 내부 함수에 float 값이 들어가면서 여러 오류가 발생했다.

### 스크롤 오류

```text
TypeError: setValue(self, a0: int): argument 1 has unexpected type 'float'
```

원인:

```python
bar.setValue(bar.value() + bar.singleStep() * units)
```

수정:

```python
bar.setValue(int(bar.value() + bar.singleStep() * units))
```

### 확대/축소 오류

문제 코드:

```python
self.zoom_widget.setValue(value)
```

수정:

```python
self.zoom_widget.setValue(int(value))
```

수평/수직 스크롤도 같은 방식으로 수정했다.

```python
h_bar.setValue(int(new_h_bar_value))
v_bar.setValue(int(new_v_bar_value))
```

### 박스 생성 시 drawLine 오류

```text
drawLine argument 1 has unexpected type 'float'
```

수정 방향:

```python
p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))
```

### 박스 미리보기 drawRect 오류

```text
drawRect argument 1 has unexpected type 'float'
```

수정 방향:

```python
p.drawRect(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))
```

이후 LabelImg에서 박스 생성, 확대, 스크롤이 정상 동작했다.

---

## 4.7 데이터셋 폴더 정리

초기에는 작업 폴더가 많이 나뉘어 있었다.

```text
todo_labeling
todo_labeling_after250
todo_labeling_remaining
local_labeling_unfinished
label_check_all
retrain_250_dataset
retrain_labelimg_250_dataset
merged_hyupdong2_train_dataset
final_hyupdong2_dataset
```

작업 중 실수 방지와 백업을 위해 분리했지만, 관리 복잡도가 커졌다. 최종적으로 하나의 기준 폴더로 통합하였다.

```text
/home/yoon/merged_hyupdong2_all
```

최종 구조:

```text
merged_hyupdong2_all
├── classes.txt
├── data.yaml
├── images
├── labels
├── dataset
├── runs
├── models
├── real_test
├── classify_dataset
└── tools
```

---

## 4.8 YOLOv8n 초기 학습

초기 학습은 `yolov8n.pt`를 사용했다.

```bash
yolo detect train \
  data=/home/yoon/yolo_train_ws/hyupdong2-1/data.yaml \
  model=yolov8n.pt \
  epochs=100 \
  imgsz=640 \
  batch=8
```

초기 모델 위치:

```text
/home/yoon/work/nkai/runs/detect/train-2/weights/best.pt
```

초기 validation 수치는 좋아 보였지만, 실제 환경에서는 충분하지 않았다.

```text
mAP50 ≈ 0.962
mAP50-95 ≈ 0.769
```

---

## 4.9 good/ng 데이터 불균형 문제

초기 class 수:

```text
good: 581
ng: 2541
total: 3122
```

비율:

```text
good : ng = 1 : 4.37
```

문제는 모델이 ng 중심으로 학습되거나 good의 다양한 상태를 충분히 못 배우는 것이었다. 특히 good/ng 차이는 단순 물체 차이가 아니라 미세한 체결 간격 차이였기 때문에 데이터 균형이 중요했다.

good 전용 이미지 447장을 추가했고, 최종적으로 데이터 비율이 개선되었다.

```text
good: 2514
ng: 2971
total: 5485
good : ng ≈ 1 : 1.18
```

---

## 4.10 YOLO11x img960 개선

정확도 우선 학습을 위해 YOLO11x + imgsz 960 조합을 검토했다.

```bash
yolo detect train \
  data=/home/yoon/merged_hyupdong2_all/data.yaml \
  model=yolo11x.pt \
  epochs=200 \
  imgsz=960 \
  batch=2 \
  patience=50
```

의도:

| 설정 | 이유 |
|---|---|
| yolo11x.pt | 큰 모델로 표현력 증가 |
| imgsz=960 | 작은 체결 틈을 더 크게 보고 학습 |
| batch=2 | GPU 메모리 안정성 확보 |
| 약한 augmentation | 체결 틈 정보 보존 |

---

## 4.11 실제 환경에서 발생한 YOLO 문제

Validation 수치는 좋았지만 실제 환경에서는 다음 문제가 발생했다.

```text
ng로 봐야 하는 볼트-너트 체결부를 good으로 판단함
```

원인:

1. 학습/검증 데이터와 실제 카메라 환경의 분포 차이
2. 조명 반사
3. 카메라 각도 차이
4. 볼트와 너트 사이의 틈이 작음
5. 박스가 틈을 충분히 포함하지 못함

따라서 validation 수치만으로 실제 성능을 판단하기 어렵다는 결론을 얻었다.

---

## 4.12 자동 라벨링 및 hardcase 재학습 검토

실제 환경 이미지에 YOLO11x 모델을 적용하여 자동 라벨링을 수행했다.

```bash
yolo detect predict \
  model=/home/yoon/merged_hyupdong2_all/runs/train_yolo11x_img960_best_accuracy/weights/best.pt \
  source=/home/yoon/merged_hyupdong2_all/real_test/images \
  conf=0.25 \
  iou=0.35 \
  agnostic_nms=True \
  imgsz=960 \
  save=True \
  save_txt=True \
  save_conf=False
```

중요 옵션:

| 옵션 | 의미 |
|---|---|
| save_txt=True | YOLO txt 라벨 저장 |
| save_conf=False | LabelImg가 읽을 수 있도록 5개 값만 저장 |
| agnostic_nms=True | good/ng 중복 박스 완화 |

자동 라벨 폴더를 LabelImg로 다시 열어 직접 수정했다.

```bash
labelImg \
  ~/merged_hyupdong2_all/real_test/images \
  ~/merged_hyupdong2_all/classes.txt \
  ~/merged_hyupdong2_all/real_test/auto_label_yolo11x/labels
```

---

## 4.13 한 객체에 good/ng가 동시에 뜨는 문제

YOLO 기본 NMS는 class-aware 방식이기 때문에 같은 위치에 박스가 겹쳐도 클래스가 다르면 둘 다 남을 수 있다.

```text
good box
ng box
```

동일 객체에 두 개가 뜨는 문제가 발생했다.

완화 방법:

```text
agnostic_nms=True
iou=0.35
```

의미:

```text
클래스가 달라도 같은 위치에서 겹치면 하나만 남김
```

그러나 구조적으로는 detection 단독 방식의 한계가 있었다.

---

## 4.14 detector + classifier 구조 검토

최종적으로 정확도를 높이기 위한 구조로 detector + crop classifier를 검토했다.

```text
원본 이미지
→ Detector로 볼트-너트 결합부 위치 검출
→ crop
→ Classifier로 good/ng 판단
```

장점은 classifier가 전체 이미지가 아니라 결합부 crop만 보기 때문에 미세한 간격 판단에 더 유리하다는 것이다.

최종 모델 경로:

```text
/home/yoon/merged_hyupdong2_all/models/detector_yolo11x_img960_best.pt
/home/yoon/merged_hyupdong2_all/models/classifier_yolo11x_crop_best.pt
```

classifier 학습 결과:

```text
top1_acc: 0.969
top5_acc: 1.000
```

## 4.15 최종 프로젝트 적용 판단

디버깅 과정에서는 good/ng 분류까지 검토했고 detector+classifier 구조까지 판단했지만, 실제 프로젝트 적용 범위와 발표 안정성을 고려해 최종적으로는 다음처럼 정리하였다.

```text
YOLO 최종 활용 목적:
good/ng 최종 판정보다는 볼트 존재 여부 및 위치 확인 중심
```

이유:

1. 실제 환경에서 good/ng 오판 가능성이 남아 있었다.
2. 프로젝트 전체 구조에서는 볼트 위치와 DB/3D/로봇 연동 안정성이 더 중요했다.
3. 체결 상태 판단은 높이 기반 검사 로직과 3D 측정 결과를 함께 고려하는 방향이 더 적합했다.
4. 발표 데모에서는 불안정한 good/ng 분류보다 안정적인 볼트 검출이 더 유리했다.

---

# 5. Firebase DB 디버깅 및 구조 개선

## 5.1 기존 DB 구조 문제

기존 구조는 검사 결과가 바로 `captures` 또는 `linestatus` 아래에 저장되는 방식이었다.

```text
inspections/site_joingo_lab_001/captures/{capture_id}
```

또는 예전 구조:

```text
linestatus
```

문제점:

1. 검사 시작 시간 기준으로 묶기 어려움
2. 작업대별 검사 결과 구분이 어려움
3. 디지털트윈에서 시간 흐름 표현이 약함
4. 외부 API 공유 시 구조가 불명확함
5. GUI, 로봇, API가 서로 다른 방식으로 데이터를 읽을 가능성이 있음
6. 날짜별/작업대별/불량별 검색이 어려움

## 5.2 최종 DB 구조

최종 구조는 다음과 같이 재설계하였다.

```text
검사 세션
→ 작업대
→ 검사 결과
→ 나사별 marker
```

경로:

```text
inspections/{site_id}/sessions/{session_id}/workstations/{workstation_id}/captures/{capture_id}
```

예시:

```text
inspections/site_joingo_lab_001/sessions/session_20260522_150000/workstations/workstation_01/captures/capture_20260522_150010
```

의미:

| 항목 | 의미 |
|---|---|
| site_id | 현장 ID |
| session_id | 검사 시작 시간 기준 검사 묶음 |
| workstation_id | 검사 대상 작업대 |
| capture_id | 실제 검사 결과 1회 |
| markers | 나사별 정상/불량 결과 |

---

## 5.3 session_id 생성 시점 문제

기존에는 노드 실행 시점에 session_id가 생성될 수 있었다.

```text
노드 실행
→ session_id 생성
→ 실제 검사는 나중에 시작
```

이 경우 session 시간이 실제 검사 시작 시간과 달라지는 문제가 있었다.

변경:

```text
노드 실행
→ 대기
→ 실제 검사 시작
→ session_id 생성
```

이를 위해 `ensure_session_started(now_ms)` 개념을 추가하였다.

목적:

1. 세션이 없으면 새로 생성
2. 이미 세션이 있으면 기존 세션 유지
3. 여러 작업대 검사를 하나의 세션으로 묶음

---

## 5.4 세션 누적 카운트 추가

세션 전체 통계를 위해 다음 값을 누적하도록 설계했다.

```text
session_total_captures
session_total_markers
session_normal_count
session_defect_count
```

의미:

| 필드 | 의미 |
|---|---|
| session_total_captures | 세션 내 capture 수 |
| session_total_markers | 세션 전체 나사 marker 수 |
| session_normal_count | 세션 전체 정상 수 |
| session_defect_count | 세션 전체 불량 수 |

이를 통해 검사 세션 단위 리포트와 디지털트윈 표시가 가능해졌다.

---

## 5.5 workstation_id 자동 생성

작업대별 검사 결과를 분리하기 위해 `workstation_id` 자동 생성 구조를 적용했다.

```text
첫 번째 검사 → workstation_01
두 번째 검사 → workstation_02
세 번째 검사 → workstation_03
```

효과:

1. 작업대별 검사 이력 관리
2. 작업대별 불량률 분석
3. 디지털트윈에서 작업대 단위 표시
4. 로봇 작업 대상 구분

---

## 5.6 capture metadata 보강

각 capture 자체에도 소속 정보를 포함하도록 했다.

```text
metadata
├── session_id
├── workstation_id
├── capture_id
├── robot_id
└── camera_id
```

이렇게 하면 DB 경로에서 분리되어도 capture 단독 데이터만으로 소속 정보를 확인할 수 있다.

---

## 5.7 flat captures mirror 저장

새 구조를 적용하면 기존 GUI/API/로봇 코드가 깨질 수 있었다. 그래서 기존 flat 경로에도 동일 데이터를 mirror 저장하도록 했다.

메인 구조:

```text
inspections/site/sessions/session/workstations/workstation/captures/capture
```

호환 구조:

```text
inspections/site/captures/capture
```

장점:

1. 기존 GUI와 API 호환성 유지
2. 점진적 마이그레이션 가능
3. 테스트 중 안정성 확보

단점:

1. 데이터 중복 저장
2. 장기적으로는 한쪽만 업데이트될 경우 불일치 가능

현재는 안정 전환 단계라서 유지하는 것이 맞다고 판단했다.

---

## 5.8 Storage 경로 변경

DB 구조와 Firebase Storage 구조를 맞추기 위해 Storage 업로드 경로도 변경하였다.

기존 가능 구조:

```text
companies/company_joingo_001/sites/site_joingo_lab_001/inspections/{capture_id}/background/bg.js
```

변경 후:

```text
companies/company_joingo_001/sites/site_joingo_lab_001/inspections/sessions/{session_id}/workstations/{workstation_id}/captures/{capture_id}/background/bg.js
```

이렇게 DB와 Storage 경로가 서로 일치하게 되었다.

---

## 5.9 Index 구조 추가

Firebase Realtime Database는 SQL처럼 복잡한 조건 검색이 강하지 않다. 그래서 목적별 index 구조를 추가했다.

### latest

```text
indexes/{site_id}/latest
```

최신 session, workstation, capture를 빠르게 찾기 위한 포인터이다.

### capture_lookup

```text
indexes/{site_id}/capture_lookup/{capture_id}
```

capture_id만 알고 있을 때 원본 session 경로를 역추적하기 위한 구조이다.

### captures_by_date

```text
indexes/{site_id}/captures_by_date/{date}/{capture_id}
```

날짜별 검사 이력 조회를 위한 구조이다.

### captures_by_workstation

```text
indexes/{site_id}/captures_by_workstation/{workstation_id}/{capture_id}
```

작업대별 검사 이력 조회를 위한 구조이다.

### defects_by_status

```text
indexes/{site_id}/defects_by_status/unresolved/{capture_id}_{marker_id}
```

아직 해결되지 않은 불량 marker만 빠르게 찾기 위한 구조이다.

---

## 5.10 sites / robots / twin_state 업데이트

### sites

```text
sites/site_joingo_lab_001
├── latest_session_id
└── latest_capture_id
```

현장 단위 최신 검사 상태를 저장한다.

### robots

```text
robots/dsr01
├── current_session_id
├── current_workstation_id
└── current_capture_id
```

로봇이 현재 어떤 검사 결과를 기준으로 움직여야 하는지 알려준다.

### twin_state/current_session

```text
twin_state/site_joingo_lab_001/current_session
```

디지털트윈 화면에서 현재 진행 중인 session 상태를 보여준다.

### twin_state/current_inspection

```text
twin_state/site_joingo_lab_001/current_inspection
```

가장 최근 검사 결과 요약 상태를 보여준다.

---

## 5.11 markers None 문제

검사 결과 저장 중 `markers: None`처럼 보이는 문제가 있었다.

처음에는 DB 저장 오류처럼 보였지만, 실제 원인은 YOLO 감지 결과가 0개였기 때문이었다.

```text
YOLO 감지 결과 0개
→ marker 생성 없음
→ markers None
```

즉 DB 오류가 아니라 입력 감지 결과 문제였다.

실제 감지가 들어온 경우에는 다음처럼 marker가 생성되었다.

```text
screw_0 normal
screw_1 normal
screw_2 defect
screw_3 defect
```

---

## 5.12 session 구조 적용 중 SyntaxError

긴 스크립트를 한 번에 붙여넣는 과정에서 파일이 깨져 SyntaxError가 발생했다.

```text
SyntaxError: invalid syntax
```

해결 절차:

```text
1. Git restore로 정상 버전 복구
2. py_compile로 문법 확인
3. 짧은 단위로 다시 수정
4. 경로 생성 테스트
5. import 테스트
6. GUI/API fallback 테스트
```

명령 예:

```bash
git restore common/db_paths.py YJH/realtime/realtime_3d_mapper_multi_04.py
python3 -m py_compile 대상파일.py
```

이 방식이 최종적으로 가장 안정적이었다.

---

## 5.13 문서화

DB 구조 변경 후 다음 문서화를 정리하였다.

```text
DATABASE_STRUCTURE.md
API_USAGE.md
```

포함 내용:

1. session/index/fallback 정책
2. API 사용법
3. DB 경로 구조
4. GUI/API/Robot 조회 기준
5. 기존 flat 구조와 신규 session 구조의 관계

---

# 6. 웹 / GUI / KJH 파트 디버깅

## 6.1 상태값 불일치 문제

웹 화면에서 불량 상태를 표시할 때 여러 상태값이 혼재했다.

```text
defect
defective
ng
failed
```

팀원별 코드와 DB 저장 방식에서 상태값이 다를 수 있었기 때문에 화면에서는 이 값을 모두 불량으로 처리하도록 방향을 정리했다.

```text
defect / defective / ng / failed
→ 모두 불량 처리
```

## 6.2 실시간 화면과 검사 이력 화면 기준 분리

KJH 화면에서 어떤 DB 경로를 기준으로 읽어야 하는지 구분했다.

```text
실시간 화면
→ live_scan 기준

검사 이력 화면
→ indexes → sessions 기준
```

이 구분을 통해 실시간 렌더링과 과거 이력 조회가 서로 충돌하지 않도록 했다.

## 6.3 DB 필드 추가 제한

사용자가 요구한 조건은 DB 필드를 함부로 추가하지 않는 것이었다.

```text
DB 필드를 추가하지 말고 기존 구조 안에서 처리
```

따라서 KJH 파일 수정 방향은 다음처럼 정리했다.

1. DB 구조 자체를 새로 늘리지 않음
2. 기존 live_scan, sessions, indexes 구조 활용
3. 상태값 정규화는 화면 처리 로직에서 대응
4. 검사 이력은 indexes를 통해 session 원본으로 접근

---

# 7. 3D 매핑 파트 디버깅 지원

## 7.1 기여 범위

3D 매핑 파트는 팀원이 주도적으로 구현했다. 성웅은 직접 구현 담당자는 아니며, 팀장으로서 다음을 지원했다.

1. 구조 검토
2. 디버깅 조언
3. 웹/DB/검사 로직과의 연동 방향 피드백
4. RealSense 기반 3D 생성 과정 확인
5. PointCloud 렌더링 성능 문제에 대한 개선 방향 제안

## 7.2 RealSense 기반 3D 작업 공간 생성 검토

3D 매핑 과정에서 RealSense를 이용해 작업 공간을 구성하고, YOLO 결과가 3D 위치와 연결되는 흐름을 확인했다.

검토한 흐름:

```text
RealSense RGB / Depth
→ PointCloud 생성
→ YOLO 검출 결과와 매칭
→ 나사 위치 계산
→ Firebase 저장
→ 웹에서 3D 표시
```

## 7.3 PointCloud 웹 렌더링 렉 문제

웹에서 `.js` 형태의 PointCloud 데이터를 HTML로 불러오고 Plotly로 표시할 때 렉이 심한 문제가 있었다.

원인으로 판단한 항목:

1. PointCloud 데이터량이 많음
2. Plotly 렌더링 부하가 큼
3. 매번 전체 데이터를 다시 그림
4. 브라우저 메모리 사용량 증가
5. 3D scatter point 수가 많음

개선 방향:

1. PointCloud 다운샘플링
2. 표시 포인트 개수 제한
3. 전체 갱신 대신 필요한 데이터만 갱신
4. WebGL 기반 렌더링 고려
5. Three.js 같은 대안 검토
6. JS 파일 크기 축소
7. 배경과 검사 marker 분리 렌더링

## 7.4 3D 맵 후처리 조언

3D 맵에서 나사 영역과 작업대 영역이 구분되도록 후처리 방향을 조언했다.

검토한 방향:

1. 나사 영역은 marker로 분리
2. 작업대 평면은 배경 mesh 또는 point cloud로 유지
3. 나사를 제외한 평면 영역 평탄화
4. 볼트 위치는 DB marker와 연결
5. 웹에서는 검사 대상 marker만 강조

---

# 8. 로봇 / DB 연동 디버깅

## 8.1 로봇이 DB 전체를 탐색하면 안 되는 문제

로봇 제어 코드가 DB 전체를 매번 탐색하면 비효율적이고 불안정하다. 따라서 로봇이 현재 처리해야 할 검사 결과를 바로 알 수 있도록 포인터 구조를 추가했다.

```text
robots/dsr01/current_session_id
robots/dsr01/current_workstation_id
robots/dsr01/current_capture_id
```

## 8.2 unresolved defect index

로봇이 처리해야 할 불량 marker만 빠르게 찾기 위해 다음 index를 검토했다.

```text
indexes/{site_id}/defects_by_status/unresolved
```

이를 통해 로봇이 전체 capture를 뒤지지 않고 처리 대상만 확인할 수 있다.

## 8.3 법선 벡터 기반 자세 제어 검토

로봇이 나사 위치로 접근할 때 단순 좌표만 필요한 것이 아니라, 접근 방향과 자세가 필요하다. 이를 위해 법선 벡터 기반 자세 제어 방향을 정리했다.

검토한 흐름:

```text
3D 표면 또는 나사 주변 평면 추정
→ 법선 벡터 계산
→ 로봇 접근 방향 산출
→ 목표 pose 계산
→ 로봇 제어에 전달
```

---

# 9. GitHub / 협업 디버깅

## 9.1 collaborator main push 권한 확인

GitHub 레포지토리에 collaborator가 초대되어 있고, branch protection rule 또는 ruleset이 없으면 일반적으로 main 브랜치에 push 가능하다.

확인 조건:

```text
1. collaborator 초대 수락
2. Write 이상 권한
3. Ruleset 없음
4. Branch protection 없음
```

## 9.2 로컬 main이 원격 main과 연결되지 않은 문제

팀원이 push할 때 다음 메시지가 발생했다.

```text
The branch "main" has no remote branch.
Would you like to publish this branch?
```

의미:

```text
로컬 main 브랜치가 GitHub origin/main과 연결되어 있지 않음
```

해결 방향:

```bash
git branch --set-upstream-to=origin/main main
git pull --rebase origin main
git push origin main
```

또는 VS Code에서 새로 clone 후 작업하는 방법을 안내했다.

## 9.3 원격 main이 로컬보다 앞선 문제

다른 push 오류:

```text
Can't push refs to remote.
Try running "Pull" first to integrate your changes.
```

의미:

```text
GitHub 원격 main에 로컬에는 없는 커밋이 있음
→ 먼저 pull 필요
```

VS Code 기준 해결 순서:

```text
Source Control
→ Commit
→ Pull
→ Push
```

## 9.4 README HTML 표 표시 오류

README에 HTML 표를 넣을 때 코드블록 안에 넣으면 GitHub가 표로 렌더링하지 않고 그대로 보여준다.

잘못된 방식:

```text
```html
<table>
...
</table>
```
```

올바른 방식:

```html
<table>
...
</table>
```

즉 README에는 백틱 없이 HTML을 직접 넣어야 한다.

## 9.5 nowrap과 가로 스크롤 문제

HTML 표에 `nowrap`을 쓰면 줄바꿈은 줄어들지만 화면 폭보다 표가 길어져 가로 스크롤이 생긴다.

정리:

```text
줄바꿈 없이 한 줄 유지 → 가로 스크롤 발생
가로 스크롤 없이 표시 → 긴 문장은 줄바꿈 발생
```

따라서 GitHub README에서는 상황에 따라 두 가지 중 하나를 선택해야 한다.

1. 줄바꿈 최소화: HTML table + nowrap
2. 스크롤 최소화: Markdown table + 컬럼 축소

---

# 10. 시스템 아키텍처 및 플로우차트 문서화

## 10.1 시스템 아키텍처 제작

협동2 전체 구조를 보여주기 위해 시스템 아키텍처를 제작했다.

포함한 주요 요소:

1. Vision / YOLO
2. RealSense
3. 3D Mapping
4. Firebase Realtime DB
5. Firebase Storage
6. Web Dashboard
7. Robot Control
8. GitHub 협업 구조
9. 팀원별 파트

## 10.2 플로우차트 제작

프로젝트 동작 흐름을 단계별로 표현하기 위해 플로우차트를 제작했다.

기본 흐름:

```text
검사 시작
→ 카메라 데이터 수신
→ YOLO 볼트 검출
→ 3D 위치 계산
→ 높이/상태 검사
→ Firebase 저장
→ 웹 표시
→ 로봇 작업 대상 확인
→ 결과 업데이트
```

## 10.3 자료 보완

다이어그램 제작 중 다음을 보완했다.

1. 박스 간 간격 조정
2. 화살표 선이 박스를 관통하지 않도록 수정
3. 좌우 방향 화살표만 있는 문제 개선
4. 시스템 아키텍처와 플로우차트 역할 구분
5. 발표용으로 기술적 상세도 강화

---

# 11. 최종 구현 구조

## 11.1 최종 시스템 구조

최종적으로 JoinGo는 다음 구조로 정리되었다.

```text
RealSense / Vision Input
→ YOLO Bolt Detection
→ 3D Mapping / Position Calculation
→ Height-based Inspection Logic
→ Firebase Realtime Database
→ Firebase Storage
→ Web Dashboard
→ Robot/DB Integration
```

## 11.2 최종 YOLO 적용 범위

디버깅 중에는 good/ng 분류까지 검토했으나, 최종 적용은 다음에 집중했다.

```text
볼트 존재 여부 확인
볼트 위치 검출
3D 검사 로직과 연결
```

## 11.3 최종 DB 구조

```text
inspections/{site_id}/sessions/{session_id}/workstations/{workstation_id}/captures/{capture_id}
```

보조 구조:

```text
indexes
twin_state
sites
robots
external_exports
legacy fallback
```

## 11.4 최종 웹/DB 조회 기준

```text
실시간 화면:
live_scan 기준

검사 이력:
indexes → sessions 기준

호환성:
flat captures fallback 유지
```

## 11.5 최종 발표 준비

발표는 각자 PPT를 제작하되, 성웅은 다음 공통 구조를 조율했다.

1. 전체 프로젝트 목적
2. 시스템 아키텍처
3. 플로우차트
4. YOLO 디버깅
5. Firebase DB 구조 개선
6. 3D 매핑 파트 기여 범위 정리
7. 로봇/DB 연동 구조
8. 최종 구현 결과와 한계

---

# 12. 핵심 디버깅 요약표

| 구분 | 문제 | 원인 | 해결 |
|---|---|---|---|
| Roboflow | 모델 업로드 불가 | version 제약 / credit 부족 | 로컬 LabelImg + Ultralytics 전환 |
| Python | download_dataset.py 실행 오류 | Jupyter `!pip` 문법 포함 | 해당 줄 삭제 |
| Python 패키지 | Roboflow import 오류 | requests / urllib3 충돌 | 가상환경 재구성 |
| Dataset | data.yaml 경로 오류 | 잘못된 폴더명 사용 | 실제 경로로 수정 |
| LabelImg | setValue float 오류 | PyQt 함수 int 요구 | int 변환 패치 |
| LabelImg | drawLine/drawRect 오류 | float 좌표 전달 | int 변환 패치 |
| YOLO | good/ng 불균형 | good 데이터 부족 | good 데이터 추가 |
| YOLO | 실제 환경 오판 | 조명/각도/반사/분포 차이 | hardcase 검토 및 최종 적용 범위 조정 |
| YOLO | good/ng 중복 박스 | class-aware NMS | agnostic_nms 적용 |
| YOLO | detection 단독 한계 | 위치 검출과 상태 분류 동시 수행 | detector+classifier 구조 검토 |
| DB | captures 구조 한계 | 세션/작업대 개념 없음 | session/workstation 구조 도입 |
| DB | 최신/날짜/작업대 조회 어려움 | Firebase 조건 검색 한계 | indexes 구조 추가 |
| DB | 기존 GUI 깨질 가능성 | 기존 flat 경로 의존 | mirror/fallback 유지 |
| DB | markers None | YOLO 감지 결과 0개 | DB 오류가 아님을 확인 |
| DB 코드 | SyntaxError | 긴 코드 일괄 수정 | Git restore 후 단계별 재적용 |
| Web | 불량 상태값 혼재 | defect/defective/ng/failed 혼용 | 모두 불량으로 정규화 |
| Web | 실시간/이력 조회 혼재 | DB 기준 불명확 | live_scan / sessions 분리 |
| 3D Web | Plotly 렉 | PointCloud 데이터 과다 | 다운샘플링/렌더링 최적화 조언 |
| GitHub | push 실패 | 원격 main과 로컬 불일치 | Commit → Pull → Push |
| README | HTML이 그대로 보임 | 코드블록 안에 HTML 삽입 | 백틱 제거 |
| README | 가로 스크롤 | nowrap 사용 | 컬럼 축소 또는 줄바꿈 허용 |

---

# 13. 최종 결론

이번 프로젝트의 디버깅은 단순히 오류 하나를 고치는 과정이 아니라, 전체 시스템 구조를 안정적인 방향으로 바꿔가는 과정이었다.

YOLO 파트에서는 Roboflow 의존, 라벨링 환경 오류, 데이터 불균형, 실제 환경 오판, good/ng 분류 한계를 순서대로 확인했다. 그 결과 최종 데모와 시스템 안정성을 위해 YOLO는 볼트 존재 여부와 위치 확인 중심으로 활용하는 방향이 적합하다고 판단했다.

DB 파트에서는 단순 capture 저장 구조의 한계를 확인하고, session → workstation → capture → marker 구조로 재설계했다. 또한 indexes, twin_state, sites, robots, fallback 구조를 추가하여 GUI, 로봇 제어, 디지털트윈, 외부 API 공유까지 고려한 운영형 DB 구조로 개선했다.

팀장 역할에서는 각 파트의 구현 방향을 검토하고, 팀원별 작업 충돌을 줄이고, 발표 자료의 시스템 흐름을 통일했다. 특히 3D 매핑은 팀원이 주도적으로 구현했으며, 성웅은 구조 검토와 디버깅 조언, DB/웹/검사 로직과의 통합 방향을 지원했다.

최종적으로 JoinGo는 단순 검사 코드가 아니라, 비전 인식, 3D 시각화, Firebase DB, 웹 대시보드, 로봇 연동을 하나의 흐름으로 연결한 스마트팩토리형 검사 자동화 시스템으로 정리되었다.
