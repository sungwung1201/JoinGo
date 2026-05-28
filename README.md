# JoinGo

<p align="center">
  <b>Scan-First 기반 공간 적응형 로봇 검사 자동화 플랫폼</b><br>
  AI Computer Vision · ROS 2 Humble · Doosan M0609 · RealSense · Firebase · Web 3D Viewer · VR/Digital Twin Ready
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ROS2-Humble-22314E?style=for-the-badge&logo=ros&logoColor=white">
  <img src="https://img.shields.io/badge/Ubuntu-22.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/YOLO-Detection--Only-00FFFF?style=for-the-badge">
  <img src="https://img.shields.io/badge/Firebase-Realtime%20DB-FFCA28?style=for-the-badge&logo=firebase&logoColor=black">
</p>

<p align="center">
  <a href="#1-프로젝트-개요">프로젝트 개요</a> ·
  <a href="#3-주요-기능">주요 기능</a> ·
  <a href="#4-시스템-아키텍처">시스템 아키텍처</a> ·
  <a href="#6-firebase-db-구조">Firebase DB</a> ·
  <a href="#10-설치-및-실행-순서">실행 방법</a>
</p>

---

## 0. 프로젝트 한 줄 요약

**JoinGo**는 **Doosan M0609 협동로봇**, **Intel RealSense RGB-D 카메라**, **YOLO 기반 볼트 검출**, **Point Cloud 기반 3D 공간 인식**, **Firebase 운영 DB**, **웹 대시보드**, **VR/디지털 트윈 확장 구조**를 연동하여, 로봇이 작업공간을 먼저 스캔한 뒤 현재 설비 기준으로 볼트 위치를 검출하고 검사 결과를 구조화된 데이터로 저장하는 **Scan-First 기반 로봇 검사 자동화 플랫폼**입니다.

```text
로봇 배치
→ 작업공간 스캔
→ YOLO 볼트 검출
→ 3D 좌표 및 marker 생성
→ Firebase session DB 저장
→ Web Dashboard / Robot Control / VR·Digital Twin 확장
```

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
- [9. 의존성 및 설치 패키지](#9-의존성-및-설치-패키지)
- [10. 설치 및 실행 순서](#10-설치-및-실행-순서)
- [11. 프로젝트 폴더 구조](#11-프로젝트-폴더-구조)
- [12. 실행 확인](#12-실행-확인)
- [13. Troubleshooting](#13-troubleshooting)
- [14. 팀 구성 및 역할](#14-팀-구성-및-역할)
- [15. 보안 주의사항](#15-보안-주의사항)
- [16. 최종 요약](#16-최종-요약)

---

## 1. 프로젝트 개요

기존 제조 검사 방식은 작업자가 직접 볼트, 나사, 부품 체결 상태를 확인하는 경우가 많습니다. 이 방식은 반복 검사 인력이 계속 필요하고, 작업자의 피로도와 숙련도에 따라 검사 품질이 달라질 수 있습니다.

JoinGo는 이러한 문제를 해결하기 위해 **로봇이 현재 작업공간을 먼저 인식하고**, 그 결과를 바탕으로 검사 대상의 위치와 상태를 구조화하는 시스템을 목표로 합니다.

### 핵심 목표

| 목표 | 설명 |
|---|---|
| 공간 적응형 검사 | 고정 설비 기준이 아니라 현재 작업공간을 스캔한 뒤 검사 기준 구성 |
| 볼트 위치 검출 | YOLO Detection 기반으로 볼트 존재 여부와 bbox 검출 |
| 3D 좌표화 | RGB-D / Point Cloud를 이용해 2D 검출 결과를 3D 공간 정보와 연결 |
| 운영 DB화 | 검사 결과를 session, workstation, capture, marker 단위로 저장 |
| 통합 활용 | Web Dashboard, Robot Control, VR/Digital Twin에서 같은 데이터 기준 사용 |

---

## 2. 핵심 컨셉: Scan-First

### 2.1 기존 고정형 검사 방식의 한계

| 기존 방식 | 한계 |
|---|---|
| 카메라와 설비 위치가 고정됨 | 작업대 위치가 바뀌면 재설정 필요 |
| 검사 기준이 특정 설비에 종속됨 | 다른 설비로 확장하기 어려움 |
| 결과가 이미지 또는 수기 기록 중심 | 불량 위치와 작업 문맥 추적이 어려움 |
| 외부 시스템과 데이터 공유가 어려움 | 디지털 트윈, 로봇 제어, API 연동에 추가 작업 필요 |

### 2.2 JoinGo 방식

| JoinGo Scan-First 구조 | 효과 |
|---|---|
| 작업 전 공간을 먼저 스캔 | 현재 설비 기준으로 검사 기준 생성 |
| 작업대 단위로 검사 결과 분리 | 여러 작업대, 여러 설비로 확장 가능 |
| marker 단위로 볼트 위치 저장 | 불량 위치 추적과 후속 로봇 작업 가능 |
| session / workstation / capture 구조화 | 외부 회사와 협업할 때 데이터 해석이 쉬움 |

```text
로봇을 설비 앞에 배치
→ RealSense RGB-D 데이터 수집
→ Point Cloud 기반 작업공간 구성
→ YOLO 볼트 검출
→ 3D marker 생성
→ Firebase DB 저장
→ Web / Robot / VR·Digital Twin 연동
```

---

## 3. 주요 기능

### 3.1 YOLO 기반 볼트 위치 및 존재 여부 검출

최종 YOLO 운영 구조는 **good / ng 체결 상태 분류가 아니라 볼트 존재 여부와 위치 검출**입니다.

초기에는 체결 상태를 `good / ng`로 판단하는 구조도 검토했지만, 실제 환경에서는 조명, 각도, 금속 반사, 거리 변화에 따라 상태 분류가 흔들릴 수 있었습니다. 따라서 최종 운영 기준에서는 **볼트 위치와 존재 여부를 안정적으로 검출하는 Detection-only 구조**로 정리했습니다.

```text
RealSense RGB Image
→ YOLO Detector
→ Bolt bbox 생성
→ confidence 생성
→ marker 변환
→ Firebase DB 저장
```

| 데이터 | 설명 |
|---|---|
| `bbox` | YOLO가 검출한 볼트 bounding box |
| `confidence` | 볼트 검출 신뢰도 |
| `detected` | 볼트 검출 여부 |
| `marker_id` | `screw_0`, `screw_1` 등 볼트/나사 식별자 |
| `position` | 2D 또는 3D 좌표 |
| `capture_id` | 어떤 검사 결과에서 생성된 marker인지 추적 |

---

### 3.2 Point Cloud 기반 3D 공간 인식

Intel RealSense D435i 계열 RGB-D 카메라를 이용하여 RGB 이미지와 Depth 데이터를 수집하고, 이를 Point Cloud 형태로 변환하여 작업공간을 3D로 표현합니다.

| 역할 | 설명 |
|---|---|
| 작업공간 스캔 | 작업대와 검사 대상 위치를 3D 공간으로 구성 |
| 2D-3D 연결 | YOLO bbox와 Depth 데이터를 결합하여 3D 좌표 후보 생성 |
| 웹 시각화 | Plotly 기반 3D Viewer에서 작업공간과 marker 확인 |
| 로봇 연동 | 로봇 제어에 필요한 좌표 후보 및 상태 정보 제공 |
| VR/디지털 트윈 확장 | Point Cloud와 marker를 외부 3D/VR 환경에 전달 가능한 구조로 저장 |

> 3D 매핑 파트는 팀원이 주도적으로 구현했으며, 성웅은 팀장으로서 구조 검토, 디버깅 조언, 웹/DB/검사 로직과의 통합 방향 피드백을 수행했습니다.

---

### 3.3 Firebase 기반 운영 DB 저장

검사 결과는 단순 이미지나 JSON 파일 하나로 저장하지 않고, 실제 운영 흐름에 맞게 계층적으로 저장합니다.

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

| 계층 | 의미 |
|---|---|
| `site` | 검사 현장 또는 공장 단위 |
| `session` | 검사 시작부터 종료까지의 하나의 검사 흐름 |
| `workstation` | 작업대 또는 설비 단위 |
| `capture` | 촬영 1회 또는 검사 결과 1회 |
| `marker` | 볼트/나사 하나의 검출 결과 |

---

### 3.4 Index 기반 빠른 조회

Firebase Realtime Database는 SQL처럼 복잡한 조건 검색에 강하지 않기 때문에, 자주 필요한 조회를 위해 별도 index 구조를 구성했습니다.

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

### 3.5 웹 대시보드

웹 대시보드는 Firebase의 검사 결과를 읽어 상태를 표시하고, 3D Scan 결과와 나사 marker를 시각화합니다.

| 기능 | 설명 |
|---|---|
| 실시간 검사 상태 표시 | `live_scan/workstations` 기준 검사 결과 확인 |
| 3D Viewer | Point Cloud 배경과 screw marker 표시 |
| 상태 표시 | normal / defect 상태에 따라 marker 구분 |
| 작업대 선택 | 여러 workstation 데이터 선택 가능 |
| 성능 최적화 | 스캔 완료 후 3D 데이터 로드, 샘플링 옵션 적용 |
| 예외 상태 연동 | 비상정지, 일시정지, 안전정지 등 예외 상황 표시 구조 확장 가능 |

---

### 3.6 로봇 제어 연동

로봇 제어 파트는 Firebase에 저장된 marker 좌표와 검사 상태를 기반으로 후속 작업을 수행할 수 있도록 구성됩니다.

| 기능 | 설명 |
|---|---|
| M0609 제어 | Doosan M0609 기반 로봇 동작 수행 |
| OnRobot RG2 제어 | Gripper 동작 제어 |
| 법선 벡터 기반 자세 계산 | 작업면 방향에 따른 접근 자세 계산 |
| DB 기반 작업 대상 조회 | `robots/current_session_id`, `current_capture_id` 등을 기준으로 현재 작업 대상 확인 |
| 상태 피드백 | 작업 결과를 DB 상태값으로 되돌려 웹/로봇 상태 동기화 |

---

### 3.7 음성 명령 연동

CEY 파트에는 Wake word, STT, keyword extraction 기반 음성 명령 처리 구조가 포함되어 있습니다.

```text
Wake word
→ STT
→ Keyword extraction
→ 작업 명령 해석
→ 로봇 제어 노드 연동
```

| 구성 | 설명 |
|---|---|
| Wake word | `hello_rokey_8332_32.tflite`, `hey_jarvis.tflite` 기반 호출 감지 |
| STT | 음성 입력을 텍스트로 변환 |
| Keyword extraction | screw, tool, command 등 작업 명령 키워드 추출 |
| Robot Control 연동 | 추출된 명령을 로봇 제어 흐름에 전달 |

---

### 3.8 VR / 디지털 트윈 확장

JoinGo는 검사 결과를 단순한 2D 이미지나 표 형태로만 저장하지 않고, Point Cloud와 marker 데이터를 함께 구조화하여 저장합니다. 이를 통해 추후 VR 환경 또는 디지털 트윈 플랫폼에서 작업공간을 3D로 재현하고, 각 볼트의 위치와 검사 상태를 공간상에서 확인할 수 있습니다.

```text
RealSense RGB-D 데이터
→ Point Cloud 생성
→ 볼트 marker 좌표 생성
→ Firebase DB / Storage 저장
→ Web 3D Viewer 또는 VR Viewer에서 시각화
```

| 확장 항목 | 설명 |
|---|---|
| Web 3D Viewer | 웹에서 작업공간과 검사 결과를 3D로 확인 |
| Digital Twin | 실제 작업공간의 검사 상태를 가상 공간에 동기화 |
| VR Viewer | VR 환경에서 작업공간, 볼트 위치, 검사 결과를 몰입형으로 확인 |
| Remote Inspection | 현장에 가지 않고 원격으로 검사 결과 확인 |
| External Platform Export | 외부 디지털 트윈 또는 VR 플랫폼에 session/capture/marker 데이터 제공 |

> 현재 구현은 웹 3D Viewer와 Firebase 기반 데이터 구조가 중심이며, VR은 해당 데이터를 활용해 확장 가능한 구조로 설계되었습니다.

---

## 4. 시스템 아키텍처

아래 그림은 JoinGo의 전체 시스템 아키텍처입니다.

<p align="center">
  <img src="./docs/images/system_architecture.png" alt="JoinGo System Architecture" width="900">
</p>

| 계층 | 구성 요소 | 역할 | 핵심 데이터 |
|---|---|---|---|
| Sensor / Robot | RealSense D435i, Doosan M0609, OnRobot RG2 | 작업공간 촬영 및 로봇 후속 작업 | RGB, Depth, Robot Pose |
| Vision AI | YOLO Detector | 볼트 위치 및 존재 여부 검출 | bbox, confidence |
| 3D Processing | PointCloud, 좌표 변환 | 2D bbox를 3D 좌표와 연결 | x, y, z, transform |
| Data Layer | Firebase RTDB, Storage, indexes | 검사 결과 및 산출물 저장 | session, capture, marker |
| Service Layer | API, GUI, robot pointer, twin_state | 외부 조회 및 상태 동기화 | latest, current_capture |
| Web / Dashboard | HTML, JavaScript, Plotly.js | 검사 결과, 3D Scan, marker 시각화 | live_scan, workstations, background_url |
| Robot Control | ROS 2 Node, Doosan API, OnRobot RG2 | marker 기반 후속 작업 | target pose, normal vector, robot command |
| VR / Digital Twin | Web 3D Viewer, VR Viewer, External Twin Platform | 검사 결과를 3D/VR 환경에서 시각화 | PointCloud, marker, status |

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
→ Web / Robot / VR·Digital Twin에서 조회
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

### 6.2 보조 구조

```text
indexes
├── latest
├── capture_lookup
├── captures_by_date
├── captures_by_workstation
└── defects_by_status

robots
└── dsr01
    ├── current_session_id
    ├── current_workstation_id
    ├── current_capture_id
    └── status

twin_state
└── site_joingo_lab_001
    ├── current_session
    └── current_inspection
```

### 6.3 주요 설계 의도

| 구조 | 목적 |
|---|---|
| `sessions` | 검사 시작 시점 기준으로 검사 흐름을 묶음 |
| `workstations` | 작업대별 검사 결과 분리 |
| `captures` | 촬영/검사 1회 단위 저장 |
| `markers` | 볼트/나사 단위 검출 결과 저장 |
| `indexes` | 최신/날짜별/작업대별/불량별 빠른 조회 |
| `robots` | 로봇이 현재 처리해야 할 검사 결과 포인터 제공 |
| `twin_state` | 웹/VR/디지털 트윈이 현재 상태를 빠르게 표시 |
| `external_exports` | 외부 시스템 제공용 데이터 구조 확장 가능 |
| `legacy fallback` | 기존 flat captures 구조와의 호환성 유지 |

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
| 3D Processing | Open3D, SciPy, Plotly.js |
| Camera SDK | Intel RealSense SDK / pyrealsense2 |
| Database | Firebase Realtime Database |
| Storage | Firebase Storage |
| Robot | Doosan Robotics M0609 |
| Gripper | OnRobot RG2 |
| Voice | Wake word, STT, Keyword extraction |
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
| VR / Twin Client | VR Viewer 또는 외부 디지털 트윈 플랫폼 | 3D 공간 및 검사 결과 확장 시각화 |

---

## 9. 의존성 및 설치 패키지

### 9.1 Python requirements

```txt
numpy
scipy
opencv-python
ultralytics
pyrealsense2
open3d
firebase-admin
python-dotenv
requests
openai
langchain
langchain-openai
openwakeword
pyaudio
sounddevice
pymodbus
plotly
matplotlib
pillow
pytest
setuptools
```

설치:

```bash
python3 -m pip install -r requirements.txt
```

### 9.2 ROS 2 / System packages

`rclpy`, `sensor_msgs`, `geometry_msgs`, `tf2_ros`, `cv_bridge`, `std_srvs`, `ament_index_python` 등은 pip가 아니라 ROS 2 / apt 패키지로 설치합니다.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  ros-humble-cv-bridge \
  ros-humble-image-transport \
  ros-humble-tf2-ros \
  ros-humble-tf-transformations \
  ros-humble-realsense2-camera \
  ros-humble-sensor-msgs-py \
  ros-humble-geometry-msgs \
  ros-humble-std-srvs \
  python3-colcon-common-extensions \
  python3-pip \
  python3-venv \
  portaudio19-dev \
  python3-pyaudio
```

### 9.3 Doosan / OnRobot 관련

Doosan 관련 모듈은 pip 설치 대상이 아니라 기존 cobot workspace에서 제공되는 모듈입니다.

| 모듈 | 설치 기준 |
|---|---|
| `DR_init` | Doosan ROS 2 workspace 제공 |
| `DSR_ROBOT2` | Doosan ROS 2 workspace 제공 |
| `robot_control` | 사용자 ROS 2 패키지 내부 제공 |
| `onrobot.py` | `CEY/robot_ppv/robot_ppv/onrobot.py` |

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

브라우저 접속:

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
        │   │   ├── robot_ppv/
        │   │   │   ├── robot_control_test_fin_9_3.py
        │   │   │   └── onrobot.py
        │   │   ├── resource/
        │   │   │   └── T_gripper2camera.npy
        │   │   ├── package.xml
        │   │   └── setup.py
        │   ├── voice_ppv/
        │   │   ├── voice_ppv/
        │   │   │   ├── MicController.py
        │   │   │   ├── get_keyword_screw2.py
        │   │   │   ├── stt.py
        │   │   │   └── wakeup_word.py
        │   │   ├── resource/
        │   │   │   ├── hello_rokey_8332_32.tflite
        │   │   │   └── hey_jarvis.tflite
        │   │   ├── package.xml
        │   │   └── setup.py
        │   ├── README.md
        │   └── DEBUGGING.md
        ├── KJH/
        │   ├── joingo_modern_tab_dashboard_v6_ko.html
        │   ├── explore_environment_plane_normal.py
        │   └── README.md
        ├── YJH/
        │   ├── common/
        │   │   ├── db_paths.py
        │   │   ├── firebase_client.py
        │   │   └── settings.py
        │   ├── resource/
        │   │   └── hyupdong2_yolo11x_realtest_corrected_best.pt
        │   ├── realtime_3d_mapper_multi_10_03_04__.py
        │   ├── viewer_06.html
        │   └── README.md
        ├── YSW/
        │   └── README.md
        ├── docs/
        │   └── images/
        │       ├── system_architecture.png
        │       └── flow_chart.png
        ├── README.md
        ├── requirements.txt
        └── .gitignore
```

---

## 12. 실행 확인

### 12.1 ROS 2 패키지 확인

```bash
cd ~/joingo_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
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
./docs/images/system_architecture.png
./docs/images/flow_chart.png
```

### 12.4 Firebase 구조 확인

Firebase Console에서 다음 경로를 확인합니다.

```text
inspections/site_joingo_lab_001/sessions
indexes/site_joingo_lab_001/latest
robots/dsr01
twin_state/site_joingo_lab_001
```

---

## 13. Troubleshooting

### 13.1 RealSense 토픽이 보이지 않는 경우

```bash
ros2 topic list | grep -E "camera|depth|color|image"
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
- `.env` 또는 환경 변수 확인
- Realtime Database URL 확인
- 네트워크 연결 확인
- `firebase-admin` 설치 확인

---

### 13.4 pyaudio 설치 오류

```bash
sudo apt update
sudo apt install -y portaudio19-dev python3-pyaudio
python3 -m pip install pyaudio
```

---

### 13.5 ROS_DOMAIN_ID 불일치

JoinGo는 `ROS_DOMAIN_ID=66` 기준으로 정리되어 있습니다.

```bash
export ROS_DOMAIN_ID=66
```

---

## 14. 팀 구성 및 역할

| 이름 | 역할 |
|---|---|
| 윤성웅 | 팀장, 프로젝트 기획, 일정 조율, Firebase DB 구조 개선, YOLO 디버깅, 시스템 통합, 아키텍처/플로우차트 제작 |
| 윤재현 | Vision / 3D Mapping, RealSense, PointCloud, YOLO 연동, 공간 인식 |
| 조의연 | Robot Control, 좌표 변환, 작업 시퀀스, OnRobot RG2 제어, 음성 명령 연동 |
| 김지홍 | Web Dashboard, Firebase API 연동, 검사 화면, 시연 흐름, UI 구성 |

---

## 15. 보안 주의사항

GitHub에 업로드하기 전에 다음 파일은 반드시 제거하거나 `.gitignore`에 포함해야 합니다.

```text
*.json
.env
*firebase-adminsdk*.json
serviceAccountKey.json
```

특히 Firebase 서비스 계정 JSON과 OpenAI API Key가 포함된 `.env` 파일은 공개 저장소에 올리면 안 됩니다.

권장 `.gitignore` 예시:

```gitignore
.env
*.env
*.json
*firebase-adminsdk*.json
__pycache__/
*.pyc
runs/
models/
*.pt
*.bag
*.db3
```

> 단, YOLO 모델 `.pt` 파일을 GitHub에 포함할지 여부는 저장소 용량과 공개 범위를 고려해 결정해야 합니다.

---

## 16. 최종 요약

JoinGo는 다음 흐름을 갖는 공간 적응형 로봇 검사 자동화 플랫폼입니다.

```text
Scan-First
→ 작업공간 인식
→ YOLO 볼트 검출
→ 3D 좌표 매핑
→ Firebase 운영 DB 저장
→ index 기반 빠른 조회
→ Web · Robot Control · VR · Digital Twin 연동
```

본 프로젝트의 핵심은 단순히 볼트를 검출하는 것이 아니라, 검사 결과를 **session, workstation, capture, marker, index, robot pointer, twin_state 구조**로 저장하여 다른 시스템이 쉽게 이해하고 활용할 수 있는 운영 데이터로 전환하는 것입니다.

---

<p align="center">
  <b>JoinGo</b><br>
  Scan-First Robot Inspection Automation Platform
</p>
