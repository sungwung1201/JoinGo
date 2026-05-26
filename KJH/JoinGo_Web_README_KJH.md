# JoinGo Web Dashboard 개발 README

## KJH 담당 웹페이지 개발 작업 타임라인

| 작업명 | 날짜 | 담당자 | 파트 | 단계 | 완료 여부 |
| --- | --- | --- | --- | --- | --- |
| JoinGo 웹 대시보드 개발 방향 설정 | 2026년 5월 20일 | KJH | Web / Integration | 기획 | 완료 |
| Firebase Realtime Database와 웹 GUI 연동 방식 검토 | 2026년 5월 20일 | KJH | Web / DB 연동 | 구조 검토 | 완료 |
| 검사 결과를 웹 화면에서 실시간으로 표시하기 위한 DB 경로 검토 | 2026년 5월 20일 | KJH | Web / DB 연동 | 데이터 구조 확인 | 완료 |
| 초기 JoinGo 모니터링 웹페이지 UI 제작 | 2026년 5월 20일 | KJH | Web UI | 초기 구현 | 완료 |
| Firebase config 적용 및 Realtime Database 읽기 기능 구현 | 2026년 5월 20일 | KJH | Firebase / Web | DB 연결 | 완료 |
| 검사 상태, 나사 상태, 불량 로그를 웹 카드 형태로 표시 | 2026년 5월 20일 | KJH | Web UI | 상태 표시 | 완료 |
| 웹에서 Firebase로 명령을 전송하는 구조 검토 | 2026년 5월 20일 | KJH | Web / Command | 명령 연동 | 완료 |
| viewer HTML을 메인 웹에 통합하는 방식 검토 | 2026년 5월 21일 | KJH | Web / 3D Viewer | 통합 검토 | 완료 |
| Plotly 기반 3D Point Cloud 표시 구조 확인 | 2026년 5월 21일 | KJH | 3D Scan / Web | 렌더링 구조 분석 | 완료 |
| 3D 작업대 배경과 나사 marker를 웹에서 함께 표시 | 2026년 5월 21일 | KJH | 3D Scan / Web | 3D 렌더링 | 완료 |
| 나사 상태 normal / defect에 따라 초록색·빨간색 marker로 구분 표시 | 2026년 5월 21일 | KJH | 3D Scan / Web | 상태 시각화 | 완료 |
| 나사 선택 시 상세 정보 표시 구조 설계 | 2026년 5월 21일 | KJH | Web UI | 상세 로그 설계 | 완료 |
| 불량 나사 해결 완료 버튼으로 DB status 값을 normal로 갱신 | 2026년 5월 21일 | KJH | Web / DB 쓰기 | 상태 업데이트 | 완료 |
| 예외 상황 처리 GUI 기능 기획 | 2026년 5월 22일 | KJH | Web / Exception | 기능 기획 | 완료 |
| 비상정지, 일시정지, 안전정지 상태를 웹에서 표시하는 구조 추가 | 2026년 5월 22일 | KJH | Web / Exception | 예외 상태 표시 | 완료 |
| exceptionstatus/current 경로를 통해 현재 예외 상태 구독 | 2026년 5월 22일 | KJH | Firebase / Exception | DB 읽기 | 완료 |
| 예외 상황 발생 시 팝업 알림 표시 | 2026년 5월 22일 | KJH | Web UI / Exception | 팝업 구현 | 완료 |
| 조치 완료 후 exceptioncommand에 RESUME 명령을 전송하는 기능 구현 | 2026년 5월 22일 | KJH | Web / Command | 재개 신호 전송 | 완료 |
| exceptionstatus/history에 예외 발생 및 재개 이력 저장 구조 반영 | 2026년 5월 22일 | KJH | Firebase / Log | 이력 기록 | 완료 |
| DB export 기반 웹 연동 데이터 선별 | 2026년 5월 23일 | KJH | Web / DB 설계 | 데이터 선별 | 완료 |
| 웹에서 직접 사용하지 않는 legacy, external_exports, raw stream 데이터 제외 | 2026년 5월 23일 | KJH | Web / DB 설계 | 데이터 정리 | 완료 |
| inspections, events, exceptionstatus, exceptioncommand 중심의 웹 연동 구조 정리 | 2026년 5월 23일 | KJH | Web / DB 설계 | 연동 구조 정리 | 완료 |
| 3D Scan 결과와 웹 화면을 직접 통합하는 방식으로 iframe 의존도 감소 | 2026년 5월 23일 | KJH | Web / 3D Viewer | 구조 개선 | 완료 |
| 3D Scan 실시간 렌더링으로 인한 웹 렉 문제 확인 | 2026년 5월 24일 | KJH | Web / 성능 개선 | 문제 분석 | 완료 |
| 3d_scan_done 완료 신호 기반 렌더링 방식으로 변경 | 2026년 5월 24일 | KJH | Web / 성능 개선 | 렌더링 게이트 적용 | 완료 |
| 스캔 중에는 3D 화면을 갱신하지 않고 완료 후 한 번만 결과 로드하도록 수정 | 2026년 5월 24일 | KJH | 3D Scan / Web | 렌더링 최적화 | 완료 |
| 3D 스캔 미완료 상태에서 작업대 및 샘플링 선택을 막는 조건 추가 | 2026년 5월 24일 | KJH | Web UX | 사용 조건 제어 | 완료 |
| 스캔 미완료 시 3D 스캔중 팝업 로그 표시 | 2026년 5월 24일 | KJH | Web UX | 상태 안내 | 완료 |
| Point Cloud 색상 제거를 통한 1차 경량화 적용 | 2026년 5월 25일 | KJH | Web / 성능 개선 | 렌더링 경량화 | 완료 |
| 색상 제거 후 가독성 문제 확인 및 색상 샘플링 방식으로 롤백 | 2026년 5월 25일 | KJH | Web / 3D Viewer | 시각화 보완 | 완료 |
| Point Cloud 포인트 수를 선택적으로 제한하는 샘플링 기능 추가 | 2026년 5월 25일 | KJH | Web / 성능 개선 | 샘플링 기능 | 완료 |
| 배경 포인트 수 선택 옵션을 1만점부터 5만점까지 1만 단위로 구성 | 2026년 5월 25일 | KJH | Web UI / 3D Viewer | 옵션 UI 구현 | 완료 |
| viewer_06 구조 반영 및 live_scan/workstations 기준으로 웹 통합 | 2026년 5월 26일 | KJH | Web / 3D Viewer | viewer 업데이트 | 완료 |
| 작업대별 section_name, timestamp, background_url, screws 데이터 로드 구조 반영 | 2026년 5월 26일 | KJH | Web / DB 연동 | 데이터 구조 반영 | 완료 |
| 작업대 선택 드롭다운 기능 유지 및 최신 작업대 자동 선택 처리 | 2026년 5월 26일 | KJH | Web UI | 작업대 선택 | 완료 |
| 나사 인덱스를 화면에서 1번부터 표시하도록 수정 | 2026년 5월 26일 | KJH | Web UI / 3D Viewer | 표시 번호 보정 | 완료 |
| DB key는 유지하고 화면 표시 번호만 1번부터 시작하도록 분리 처리 | 2026년 5월 26일 | KJH | Web / DB 호환성 | 호환성 유지 | 완료 |
| 실시간 RGB 영상 탭 구조 기획 | 2026년 5월 26일 | KJH | Web / RGB Stream | 기능 기획 | 완료 |
| RGB Stream URL을 통해 웹에서 영상을 선택적으로 표시하는 구조 추가 | 2026년 5월 26일 | KJH | Web / RGB Stream | 탭 구조 추가 | 완료 |
| 3D Scan 화면과 RGB 영상 화면을 상단 탭으로 분리 | 2026년 5월 26일 | KJH | Web UI / UX | 화면 구조 개선 | 완료 |
| 메인 화면에 모든 기능을 배치하지 않고 탭 기반 화면 전환 구조로 재설계 | 2026년 5월 26일 | KJH | Web UI / UX | 메인 화면 개선 | 완료 |
| 메인 화면 문구를 체결 공정의 점검, 대응 자동화 시스템 : JoinGo로 변경 | 2026년 5월 26일 | KJH | Web Design | 카피 수정 | 완료 |
| JoinGo 로고와 중앙 상단 탭 중심의 화면 구성으로 디자인 개선 | 2026년 5월 26일 | KJH | Web Design | 레이아웃 개선 | 완료 |
| 메인 화면 하단 지표 카드를 제거하여 화면 단순화 | 2026년 5월 26일 | KJH | Web Design | 메인 정리 | 완료 |
| 나사 조임/풀림 백그라운드 애니메이션 제작 | 2026년 5월 26일 | KJH | Web Animation | 메인 애니메이션 | 완료 |
| 나사 4개를 규칙적으로 배열하고 독립 시퀀스로 회전하도록 수정 | 2026년 5월 26일 | KJH | Web Animation | 애니메이션 개선 | 완료 |
| 풀림 상태에서는 불량감지, 조임 중에는 조치중, 완전 체결 시 정상체결 말풍선 표시 | 2026년 5월 26일 | KJH | Web Animation | 상태 말풍선 | 완료 |
| 정상체결에서 불량감지로 전환될 때 나사가 풀리는 방향으로 회전하도록 수정 | 2026년 5월 26일 | KJH | Web Animation | 회전 방향 수정 | 완료 |
| 나사 클릭 시 우측 패널 대신 별도 상세 로그 팝업 표시 | 2026년 5월 26일 | KJH | Web UI / Log | 팝업 개선 | 완료 |
| 나사 상세 팝업에 좌표, 상태, 시간, raw log 정보를 표시 | 2026년 5월 26일 | KJH | Web UI / Log | 로그 표시 | 완료 |
| 불량 나사 상세 팝업에서 해결 완료 처리 가능하도록 기능 유지 | 2026년 5월 26일 | KJH | Web / DB 쓰기 | 불량 처리 | 완료 |
| JoinGo Web Dashboard 동작 플로우차트 제작 | 2026년 5월 26일 | KJH | 문서화 / Web | 플로우차트 | 완료 |
| draw.io 붙여넣기용 mxGraph XML 형식 플로우차트 작성 | 2026년 5월 26일 | KJH | 문서화 / Web | 자료 제작 | 완료 |
| 웹페이지 개발 README 작성 | 2026년 5월 26일 | KJH | 문서화 / README | 문서화 | 완료 |

## 담당 역할 요약

- KJH는 JoinGo 프로젝트에서 Web / Integration 파트를 담당하여 Firebase Realtime Database와 3D Scan Viewer, RGB 영상 탭, 예외 상황 처리 GUI를 하나의 웹 대시보드로 통합하였다.
- 초기에는 Firebase 검사 결과를 웹 화면에 표시하는 단순 모니터링 구조에서 시작했으며, 이후 viewer_05와 viewer_06 구조 변화에 맞춰 3D Point Cloud, 작업대별 나사 상태, 정상/불량 marker, 나사 상세 로그 팝업을 통합하였다.
- 3D Scan 화면에서는 live_scan/workstations 경로를 기준으로 작업대별 section_name, timestamp, background_url, screws 데이터를 읽고, 포인트 수 샘플링 기능을 적용하여 웹 렌더링 부하를 줄였다. 또한 3d_scan_done 신호가 true일 때만 작업대 및 샘플링 레이트를 선택할 수 있도록 하여 스캔 중 불필요한 렌더링을 방지하였다.
- 예외 상황 처리 기능에서는 exceptionstatus/current를 구독하여 비상정지, 일시정지, 안전정지 상황을 감지하고, 사용자가 조치 완료 후 exceptioncommand에 RESUME 명령을 전송할 수 있도록 구현하였다.
- 최종 웹 UI는 메인 화면, 3D Scan 확인 탭, RGB 영상 확인 탭으로 분리하였다. 메인 화면은 JoinGo 로고와 체결 공정 자동화 메시지를 중심으로 단순화했으며, 백그라운드에는 나사 조임/풀림 애니메이션을 적용하여 프로젝트의 목적을 직관적으로 보여주도록 구성하였다.

## 주요 구현 기능

| 기능 | 설명 | 사용 DB 경로 | 상태 |
| --- | --- | --- | --- |
| 작업대 선택 | live_scan/workstations 하위 작업대를 드롭다운으로 선택 | live_scan/workstations | 완료 |
| 3D Scan 완료 게이트 | 스캔 완료 신호가 true일 때만 3D 결과 로드 | live_scan/3d_scan_done | 완료 |
| Point Cloud 렌더링 | background_url의 3D 배경 데이터를 Plotly로 표시 | live_scan/workstations/{workstation}/background_url | 완료 |
| 샘플링 레이트 선택 | 배경 포인트 수를 1만~5만점 단위로 제한 | 클라이언트 옵션 | 완료 |
| 나사 marker 표시 | normal은 초록, defect는 빨강 marker로 표시 | live_scan/workstations/{workstation}/screws | 완료 |
| 나사 번호 보정 | DB key와 무관하게 화면에는 나사 1번부터 표시 | 클라이언트 표시 로직 | 완료 |
| 상세 로그 팝업 | 나사 클릭 시 좌표, 상태, 시간, raw log 표시 | live_scan/workstations/{workstation}/screws/{screw} | 완료 |
| 불량 해결 처리 | 해결 완료 클릭 시 해당 screw status를 normal로 업데이트 | live_scan/workstations/{workstation}/screws/{screw}/status | 완료 |
| RGB 영상 탭 | 추후 RGB Stream URL 수신을 위한 탭 구조 구성 | live_scan/rgb_stream/url | 기본 구조 완료 |
| 예외 상황 감지 | 비상정지, 일시정지, 안전정지 상황을 웹 팝업으로 표시 | exceptionstatus/current | 완료 |
| 재개 신호 전송 | 조치 완료 후 RESUME 명령을 DB로 전송 | exceptioncommand | 완료 |
| 예외 이력 기록 | 예외 발생 및 재개 요청 기록 저장 | exceptionstatus/history | 완료 |

## 최종 웹 구조

```text
JoinGo Web Dashboard
├─ Main 화면
│  ├─ JoinGo 로고
│  ├─ 체결 공정 자동화 메시지
│  └─ 나사 조임/풀림 백그라운드 애니메이션
│
├─ 3D Scan 확인 탭
│  ├─ 3d_scan_done 완료 신호 확인
│  ├─ 작업대 선택
│  ├─ 샘플링 레이트 선택
│  ├─ Point Cloud 렌더링
│  ├─ 나사 marker 표시
│  └─ 나사 상세 로그 팝업
│
├─ RGB 영상 확인 탭
│  ├─ RGB Stream URL 표시 영역
│  └─ 향후 실시간 영상 연동 대기 구조
│
└─ 예외 상황 처리
   ├─ exceptionstatus/current 구독
   ├─ 예외 팝업 표시
   ├─ 조치 완료 버튼
   └─ exceptioncommand RESUME 전송
```

## 실행 방법

파일이 있는 폴더에서 아래 명령어를 실행합니다.

```bash
python -m http.server 5500
```

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:5500/joingo_modern_tab_dashboard_v7_ko.html
```

## 사용 DB 경로 요약

| DB 경로 | 용도 | 읽기/쓰기 |
| --- | --- | --- |
| live_scan/3d_scan_done | 3D 스캔 완료 여부 판단 | 읽기 |
| live_scan/workstations | 작업대 목록 및 3D 검사 데이터 수신 | 읽기 |
| live_scan/workstations/{workstation}/background_url | Point Cloud 배경 데이터 URL | 읽기 |
| live_scan/workstations/{workstation}/screws | 나사별 위치, 상태, 시간 정보 | 읽기 |
| live_scan/workstations/{workstation}/screws/{screw}/status | 불량 해결 완료 시 normal로 변경 | 쓰기 |
| live_scan/rgb_stream/url | RGB 실시간 영상 주소 | 읽기 |
| exceptionstatus/current | 현재 예외 상황 확인 | 읽기/쓰기 |
| exceptionstatus/history | 예외 발생 및 재개 이력 기록 | 읽기/쓰기 |
| exceptioncommand | 웹에서 로봇/서버로 재개 명령 전송 | 쓰기 |

## 개발 결과 요약

JoinGo 웹페이지는 단순 표시용 UI에서 출발하여, Firebase DB와 연동되는 실시간 검사 관제 웹으로 확장되었다. 최종 구조는 3D Scan 결과 확인, RGB 영상 확인, 나사 상세 로그 확인, 불량 해결 처리, 예외 상황 대응을 모두 포함한다.

성능 측면에서는 실시간 Point Cloud 전체 렌더링으로 인한 렉 문제를 3d_scan_done 완료 게이트와 포인트 수 샘플링 방식으로 완화하였다. 사용성 측면에서는 메인 화면과 기능 화면을 분리하고, 나사 클릭 시 상세 로그 팝업을 제공하여 발표 및 시연에서 기능 흐름이 직관적으로 보이도록 구성하였다.
