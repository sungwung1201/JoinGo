# JoinGo

<p align="center">
  <img src="./docs/images/system_architecture.png" alt="JoinGo System Architecture" width="900">
</p>

<p align="center">
  <b>Scan-First 기반 공간 적응형 로봇 검사 자동화 플랫폼</b><br>
  AI Computer Vision · ROS 2 Humble · Doosan M0609 · RealSense · Firebase
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ROS2-Humble-22314E?style=flat-square&logo=ros&logoColor=white">
  <img src="https://img.shields.io/badge/Ubuntu-22.04-E95420?style=flat-square&logo=ubuntu&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/YOLO-Detection--Only-00FFFF?style=flat-square">
  <img src="https://img.shields.io/badge/Firebase-Realtime%20DB-FFCA28?style=flat-square&logo=firebase&logoColor=black">
</p>

---

## 목차

- [1. 프로젝트 개요](#1-프로젝트-개요)
- [2. 핵심 컨셉: Scan-First](#2-핵심-컨셉-scan-first)
- [3. 주요 기능](#3-주요-기능)
- [4. 시스템 아키텍처](#4-시스템-아키텍처)
- [5. 플로우차트](#5-플로우차트)
- [6. Firebase DB 구조](#6-firebase-db-구조)
- [7. 개발 환경](#7-개발-환경)
- [8. 사용 장비](#8-사용-장비)
- [9. 의존성](#9-의존성)
- [10. 설치 및 실행 순서](#10-설치-및-실행-순서)
- [11. 프로젝트 폴더 구조](#11-프로젝트-폴더-구조)
- [12. 실행 확인](#12-실행-확인)
- [13. Troubleshooting](#13-troubleshooting)
- [14. 팀 구성 및 역할](#14-팀-구성-및-역할)

---

## 1. 프로젝트 개요

**JoinGo**는 협동로봇, RGB-D 카메라, YOLO 객체 검출, 3D 공간 인식, Firebase 운영 DB, 웹 대시보드를 결합한 **공간 적응형 로봇 검사 자동화 플랫폼**입니다.

기존 고정형 검사 장비는 카메라 위치, 작업대 위치, 검사 대상 위치가 바뀌면 재설정이 필요합니다.  
JoinGo는 로봇을 어느 설비 앞에 배치하더라도 먼저 작업공간을 스캔하고, 현재 설비 기준으로 검사 대상과 좌표를 재구성하는 **Scan-First 구조**를 목표로 합니다.

```text
로봇 배치
→ 작업공간 스캔
→ YOLO 볼트 검출
→ 3D 좌표 및 marker 데이터 생성
→ Firebase DB 저장
→ Web / Robot Control / Digital Twin 확장
```

이 프로젝트의 핵심은 단순히 볼트를 검출하는 것이 아니라, 검출 결과를 **운영 가능한 데이터 구조**로 저장하여 웹, 로봇 제어, 디지털 트윈, 외부 협업 플랫폼이 같은 기준으로 활용할 수 있게 만드는 것입니다.

---

## 2. 핵심 컨셉: Scan-First

### 기존 방식의 문제

| 기존 고정형 검사 방식 | 한계 |
|---|---|
| 카메라와 설비 위치가 고정됨 | 작업대 위치가 바뀌면 재설정 필요 |
| 검사 기준이 특정 설비에 종속됨 | 다른 설비로 확장하기 어려움 |
| 결과가 이미지 또는 수기 기록 중심 | 불량 위치와 작업 문맥 추적이 어려움 |
| 외부 시스템과 데이터 공유가 어려움 | 디지털 트윈, 로봇 제어, API 연동에 추가 작업 필요 |

### JoinGo 방식

| JoinGo Scan-First 구조 | 효과 |
|---|---|
| 작업 전 공간을 먼저 스캔 | 현재 설비 기준으로 검사 기준 생성 |
| 작업대 단위로 검사 결과 분리 | 여러 작업대, 여러 설비로 확장 가능 |
| marker 단위로 볼트 위치 저장 | 불량 위치 추적과 후속 로봇 작업 가능 |
| session / workstation / capture 구조화 | 외부 회사와 협업할 때 데이터 해석이 쉬움 |

---

## 3. 주요 기능

### 3.1 YOLO 기반 볼트 유무 검출

최종 YOLO 구조는 **good / ng 체결 상태 분류가 아니라 볼트 존재 여부 검출**입니다.

초기에는 체결 상태를 good / ng로 판단하는 구조도 고려했지만, 실제 환경에서는 조명, 각도, 금속 반사, 거리 변화에 따라 상태 분류가 흔들릴 수 있었습니다.  
따라서 최종 운영 기준에서는 **볼트 위치와 존재 여부를 안정적으로 검출하는 Detection-only 구조**로 정리했습니다.

```text
RealSense RGB Image
→ YOLO Detector
→ Bolt bbox 생성
→ Confidence 생성
→ Marker 변환
→ Firebase DB 저장
```

| 데이터 | 설명 |
|---|---|
| `bbox` | YOLO가 검출한 볼트 bounding box |
| `confidence` | 볼트 검출 신뢰도 |
| `detected` | 볼트 검출 여부 |
| `marker_id` | screw_0, screw_1 형태의 볼트/나사 식별자 |
| `position` | 2D 또는 3D 좌표 |
| `capture_id` | 어떤 검사 결과에서 생성된 marker인지 추적 |

---

### 3.2 Point Cloud 기반 3D 공간 인식

Intel RealSense D435i 계열 RGB-D 카메라를 이용하여 RGB 이미지와 Depth 데이터를 수집하고, 이를 Point Cloud 형태로 변환하여 작업공간을 3D로 표현합니다.

주요 역할은 다음과 같습니다.

- 작업대와 볼트 위치의 공간 관계 파악
- 2D YOLO bbox와 Depth 데이터를 결합한 3D 좌표 계산
- 웹 대시보드 또는 디지털 트윈에서 3D 공간 확인
- 로봇 제어에 필요한 좌표 후보 제공

---

### 3.3 Firebase 기반 운영 DB

검사 결과는 단순히 이미지나 JSON 파일 하나로 저장하지 않고, 실제 운영 흐름에 맞게 계층적으로 저장합니다.

```text
site
└── session
    └── workstation
        └── capture
            └── marker
```

이 구조를 통해 다음 질문에 바로 답할 수 있습니다.

| 질문 | DB 구조상 답변 기준 |
|---|---|
| 어느 현장에서 검사했는가? | `site_id` |
| 언제 시작한 검사인가? | `session_id` |
| 어느 작업대 결과인가? | `workstation_id` |
| 어떤 촬영 결과인가? | `capture_id` |
| 어떤 볼트 결과인가? | `marker_id` |

---

### 3.4 Index 기반 빠른 조회

Firebase Realtime Database는 SQL처럼 복잡한 조건 검색에 강하지 않습니다.  
따라서 JoinGo는 자주 필요한 조회를 위해 별도 index 구조를 사용합니다.

```text
indexes
└── site_joingo_lab_001
    ├── latest
    ├── capture_lookup
    ├── captures_by_date
    ├── captures_by_workstation
    └── defects_by_status
```

| index | 목적 |
|---|---|
| `latest` | 최신 session, workstation, capture를 빠르게 조회 |
| `capture_lookup` | capture_id만으로 원본 session 경로 역추적 |
| `captures_by_date` | 날짜별 검사 결과 조회 |
| `captures_by_workstation` | 작업대별 검사 결과 조회 |
| `defects_by_status` | 미해결 불량 또는 후속 작업 대상 조회 |

---

## 4. 시스템 아키텍처

아래 그림은 JoinGo의 전체 시스템 아키텍처입니다.

<p align="center">
  <img src="./docs/images/system_architecture.png" alt="JoinGo System Architecture" width="900">
</p>

| 계층 | 구성 요소 | 역할 |
|---|---|---|
| Sensor / Robot | RealSense D435i, Doosan M0609, OnRobot RG2 | 작업공간 촬영 및 로봇 후속 작업 |
| Vision AI | YOLO Detector | 볼트 위치 및 존재 여부 검출 |
| 3D Processing | PointCloud, 좌표 변환 | 2D bbox를 3D 좌표와 연결 |
| Data Layer | Firebase RTDB, Storage, indexes | 검사 결과 및 산출물 저장 |
| Service Layer | API, GUI, robot pointer, twin_state | 외부 조회 및 상태 동기화 |
| External Consumers | Web, Robot Control, Digital Twin Platform | 검사 결과 확인 및 후속 활용 |

---

## 5. 플로우차트

아래 그림은 JoinGo의 전체 실행 플로우차트입니다.

<p align="center">
  <img src="./docs/images/flow_chart.png" alt="JoinGo Flow Chart" width="850">
</p>

```text
작업공간 촬영
→ RGB-D 데이터 획득
→ YOLO Detector로 볼트 검출
→ bbox / confidence 생성
→ 3D 좌표 매핑
→ marker 데이터 생성
→ Firebase session DB 저장
→ index 갱신
→ Web / Robot / Digital Twin에서 조회
```

---

## 6. Firebase DB 구조

### 6.1 검사 결과 원본 구조

```text
inspections
└── site_joingo_lab_001
    └── sessions
        └── session_YYYYMMDD_HHMMSS
            ├── metadata
            ├── summary
            └── workstations
                └── workstation_01
                    └── captures
                        └── capture_YYYYMMDD_HHMMSS
                            ├── metadata
                            ├── summary
                            ├── markers
                            ├── transform_snapshot
                            └── storage_refs
```

### 6.2 계층별 의미

| 계층 | 의미 |
|---|---|
| `site` | 검사 현장 또는 공장 단위 |
| `session` | 검사 시작부터 종료까지의 하나의 검사 흐름 |
| `workstation` | 작업대 또는 설비 단위 |
| `capture` | 촬영 1회 또는 검사 결과 1회 |
| `marker` | 볼트/나사 하나의 검출 결과 |

### 6.3 Robot Pointer

```text
robots
└── dsr01
    ├── current_session_id
    ├── current_workstation_id
    ├── current_capture_id
    ├── robot_id
    ├── robot_model
    └── status
```

로봇 제어 노드는 전체 DB를 탐색하지 않고 현재 검사 대상만 빠르게 확인할 수 있습니다.

### 6.4 Digital Twin State

```text
twin_state
└── site_joingo_lab_001
    ├── current_session
    └── current_inspection
```

디지털 트윈 또는 외부 플랫폼은 `twin_state`를 기준으로 현재 표시할 검사 상태를 조회할 수 있습니다.

---

## 7. 개발 환경

| 구분 | 내용 |
|---|---|
| OS | Ubuntu 22.04 LTS |
| Middleware | ROS 2 Humble |
| Language | Python 3.10 |
| Build Tool | colcon |
| AI Framework | Ultralytics YOLO |
| Vision Library | OpenCV, NumPy |
| 3D Processing | Open3D, SciPy |
| Camera SDK | Intel RealSense SDK / pyrealsense2 |
| Database | Firebase Realtime Database |
| Storage | Firebase Storage |
| Web | HTML5, CSS3, JavaScript, Plotly.js |
| IDE | VS Code |
| Shell | Bash |

---

## 8. 사용 장비

| 구분 | 장비 | 용도 |
|---|---|---|
| Robot Arm | Doosan Robotics M0609 | 협동로봇 기반 검사 및 후속 작업 수행 |
| Camera | Intel RealSense D435i / D400 계열 | RGB-D 이미지, Depth, PointCloud 데이터 획득 |
| Gripper | OnRobot RG2 Gripper | 나사 또는 작업 대상 파지 및 후속 작업 |
| PC | Ubuntu 개발 PC | ROS 2 노드 실행, YOLO 추론, Firebase 연동 |
| Cloud DB | Firebase Realtime Database | 검사 결과, session, marker, index 저장 |
| Cloud Storage | Firebase Storage | 3D 배경 파일, 이미지, 산출물 저장 |
| Web Client | Chrome / Chromium Browser | 웹 대시보드 및 3D 검사 결과 확인 |

---

## 9. 의존성

### 9.1 requirements.txt

```txt
rclpy
opencv-python
numpy
scipy
open3d
ultralytics
pyrealsense2
firebase-admin
requests
python-dotenv
matplotlib
pillow
plotly
```

### 9.2 시스템 패키지

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  ros-humble-tf2-ros \
  ros-humble-tf-transformations \
  ros-humble-realsense2-camera \
  python3-colcon-common-extensions \
  python3-pip \
  python3-venv
```

---

## 10. 설치 및 실행 순서

### 10.1 ROS 2 환경 설정

```bash
cd ~/joingo_ws

source /opt/ros/humble/setup.bash
source ~/cobot_ws/install/setup.bash

export ROS_DOMAIN_ID=66
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

### 10.2 워크스페이스 빌드

```bash
cd ~/joingo_ws

colcon build --symlink-install

source install/setup.bash
```

### 10.3 RealSense 카메라 실행

```bash
ros2 launch realsense2_camera rs_launch.py \
  enable_rgbd:=true \
  enable_sync:=true \
  align_depth.enable:=true
```

### 10.4 Doosan M0609 로봇 Bringup

```bash
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py \
  mode:=real \
  model:=m0609 \
  host:=192.168.1.100
```

### 10.5 YOLO / 3D Mapping 실행

```bash
python3 ~/joingo_ws/src/JoinGo/YJH/realtime_3d_mapper_multi_10_03_04__.py
```

### 10.6 Robot Control 실행

```bash
ros2 run robot_ppv robot_control_test_fin_9_3
```

### 10.7 Voice Control 실행

```bash
ros2 run voice_ppv get_keyword_screw2
```

### 10.8 Web Dashboard 실행

```bash
cd ~/joingo_ws/src/JoinGo/KJH

python3 -m http.server 8000
```

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:8000
```

---

## 11. 프로젝트 폴더 구조

```text
joingo_ws/
└── src/
    └── JoinGo/
        ├── CEY/
        │   ├── robot_ppv/
        │   └── voice_ppv/
        ├── KJH/
        ├── YJH/
        ├── YSW/
        ├── docs/
        │   └── images/
        │       ├── system_architecture.png
        │       └── flow_chart.png
        ├── README.md
        └── requirements.txt
```

---

## 12. 실행 확인

### 12.1 ROS 2 패키지 확인

```bash
cd ~/joingo_ws
colcon list
```

정상 예시:

```text
robot_ppv    src/JoinGo/CEY/robot_ppv
voice_ppv    src/JoinGo/CEY/voice_ppv
```

### 12.2 이미지 경로 확인

```bash
ls ~/joingo_ws/src/JoinGo/docs/images
```

정상 예시:

```text
flow_chart.png  system_architecture.png
```

### 12.3 README 이미지 경로 확인

```bash
grep -n "docs/images" ~/joingo_ws/src/JoinGo/README.md
```

정상 예시:

```text
![JoinGo System Architecture](./docs/images/system_architecture.png)
![JoinGo Flow Chart](./docs/images/flow_chart.png)
```

---

## 13. Troubleshooting

### 13.1 RealSense 토픽이 보이지 않는 경우

```bash
ros2 topic list | grep camera
```

확인 사항:

- RealSense USB 연결 확인
- `realsense2_camera` 패키지 설치 확인
- USB 3.0 포트 사용 여부 확인
- 카메라 권한 문제 확인

---

### 13.2 YOLO 모델이 로드되지 않는 경우

확인 사항:

- `.pt` 모델 파일 경로 확인
- `ultralytics` 설치 여부 확인
- GPU / CUDA 환경 여부 확인
- CPU 실행 시 속도 저하 가능

모델 로드 테스트:

```bash
python3 - <<'PY'
from ultralytics import YOLO

model = YOLO('/home/yoon/merged_hyupdong2_all/models/detector_yolo11x_img960_best.pt')
print(model)
PY
```

---

### 13.3 Firebase 연결 실패

확인 사항:

- 서비스 계정 JSON 경로 확인
- `GOOGLE_APPLICATION_CREDENTIALS` 환경 변수 확인
- Realtime Database URL 확인
- 네트워크 연결 확인
- `firebase-admin` 설치 확인

---

## 14. 팀 구성 및 역할

| 이름 | 역할 |
|---|---|
| 윤성웅 | Data / Firebase DB 구조 개선, YOLO Debugging, 시스템 통합 |
| 윤재현 | Vision / 3D Mapping, RealSense, PointCloud, 공간 인식 |
| 조의연 | Robot Control, 좌표 변환, 작업 시퀀스, 로봇 제어 |
| 김지홍 | Web Dashboard, API 연동, 시연 흐름, UI 구성 |

---

## 15. 최종 요약

JoinGo는 다음 흐름을 갖는 공간 적응형 로봇 검사 자동화 플랫폼입니다.

```text
Scan-First
→ 작업공간 인식
→ YOLO 볼트 검출
→ 3D 좌표 매핑
→ Firebase 운영 DB 저장
→ index 기반 빠른 조회
→ Web · Robot Control · Digital Twin 연동
```

본 프로젝트의 핵심은 단순히 볼트를 검출하는 것이 아니라, 검사 결과를 **session, workstation, capture, marker, index, pointer 구조**로 저장하여 다른 시스템이 쉽게 이해하고 활용할 수 있는 운영 데이터로 전환하는 것입니다.
