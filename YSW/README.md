## 성웅 담당 작업 타임라인

| 작업명 | 날짜 | 담당자 | 파트 | 단계 | 완료 여부 |
|---|---|---|---|---|---|
| 협동2 전체 시스템 구조 및 역할 분담 조율 | 2026년 5월 13일 | 성웅 | 팀장/통합 관리 | 기획/조율 | 완료 |
| 비전 검사 시스템에서 YOLO 적용 가능성 검토 | 2026년 5월 13일 | 성웅 | AI/비전 | 모델 검토 | 완료 |
| Roboflow 기반 데이터셋 구성 및 초기 학습 방향 검토 | 2026년 5월 13일 | 성웅 | AI/비전 | 데이터셋 준비 | 완료 |
| Roboflow credit 및 모델 업로드 문제 분석 | 2026년 5월 14일 | 성웅 | AI/비전 | 디버깅 | 완료 |
| 로컬 LabelImg 기반 라벨링 환경 구축 방향 정리 | 2026년 5월 14일 | 성웅 | AI/비전 | 라벨링 환경 | 완료 |
| LabelImg 실행 오류 및 PyQt float 타입 오류 해결 방향 정리 | 2026년 5월 14일 | 성웅 | AI/비전 | 디버깅 | 완료 |
| YOLOv8n 초기 학습 결과 분석 | 2026년 5월 15일 | 성웅 | AI/비전 | 모델 학습 | 완료 |
| good/ng 데이터 불균형 문제 분석 | 2026년 5월 15일 | 성웅 | AI/비전 | 데이터 분석 | 완료 |
| 추가 good 데이터 반영 및 데이터셋 균형 개선 방향 정리 | 2026년 5월 15일 | 성웅 | AI/비전 | 데이터셋 개선 | 완료 |
| YOLOv8n에서 YOLO11x img960으로 모델 개선 방향 검토 | 2026년 5월 16일 | 성웅 | AI/비전 | 모델 개선 | 완료 |
| 실제 환경에서 ng를 good으로 오판하는 문제 분석 | 2026년 5월 16일 | 성웅 | AI/비전 | 실환경 디버깅 | 완료 |
| 한 객체에 good/ng 박스가 동시에 뜨는 문제 분석 | 2026년 5월 16일 | 성웅 | AI/비전 | 실환경 디버깅 | 완료 |
| agnostic_nms 적용을 통한 중복 클래스 박스 완화 방향 정리 | 2026년 5월 16일 | 성웅 | AI/비전 | 추론 옵션 개선 | 완료 |
| detector + classifier 2단계 구조 검토 | 2026년 5월 17일 | 성웅 | AI/비전 | 모델 구조 검토 | 완료 |
| good/ng 분류 방식의 한계 판단 및 최종 적용 범위 재정리 | 2026년 5월 17일 | 성웅 | AI/비전 | 기술 의사결정 | 완료 |
| 최종 YOLO 사용 목적을 볼트 존재 여부 및 위치 확인 중심으로 조정 | 2026년 5월 18일 | 성웅 | AI/비전 | 적용 방향 확정 | 완료 |
| RealSense 기반 실시간 YOLO 모델 로딩 및 동작 로그 확인 | 2026년 5월 18일 | 성웅 | AI/비전 | 실행 테스트 | 완료 |
| 3D 작업 공간 맵 생성 구조 확인 | 2026년 5월 19일 | 성웅 | 3D 매핑 | 기능 구현 | 완료 |
| 여러 장의 캡처 데이터를 이용한 3D 환경 구성 방식 정리 | 2026년 5월 19일 | 성웅 | 3D 매핑 | 기능 구현 | 완료 |
| 작업 공간 내 볼트 위치 확인 구조 정리 | 2026년 5월 20일 | 성웅 | 비전/3D 매핑 | 검사 로직 | 완료 |
| 높이 기반 볼트 상태 측정 방식 적용 | 2026년 5월 20일 | 성웅 | 비전/알고리즘 | 검사 로직 | 완료 |
| 검사 결과 Firebase Realtime Database 저장 구조 연동 | 2026년 5월 20일 | 성웅 | Firebase/DB | DB 연동 | 완료 |
| Firebase 검사 결과와 웹 화면 연동 구조 확인 | 2026년 5월 20일 | 성웅 | 웹/DB 연동 | 통합 테스트 | 완료 |
| KJH 웹 화면의 실시간 검사 데이터 기준 검토 | 2026년 5월 21일 | 성웅 | 웹/DB 연동 | 구조 검토 | 완료 |
| 실시간 화면은 live_scan 기준으로 처리하도록 방향 정리 | 2026년 5월 21일 | 성웅 | 웹/DB 연동 | 데이터 기준 정리 | 완료 |
| 검사 이력 화면은 indexes → sessions 기준으로 조회하도록 방향 정리 | 2026년 5월 21일 | 성웅 | 웹/DB 연동 | 데이터 기준 정리 | 완료 |
| defect / defective / ng / failed 상태값을 모두 불량으로 처리하는 조건 정리 | 2026년 5월 21일 | 성웅 | 웹/DB 연동 | 상태값 정규화 | 완료 |
| DB 필드를 추가하지 않고 기존 구조를 유지하는 수정 방향 조율 | 2026년 5월 21일 | 성웅 | 팀장/DB 조율 | 코드 수정 방향 | 완료 |
| 팀원 KJH 화면 수정 방향 피드백 및 반영 기준 정리 | 2026년 5월 21일 | 성웅 | 팀장/웹 조율 | 피드백 | 완료 |
| 법선 벡터 기반 로봇 자세 제어 방향 정리 | 2026년 5월 22일 | 성웅 | 로봇 제어 | 자세 계산 | 완료 |
| 로봇 제어와 연동하기 위한 실시간 DB 구조 live_scan 추가 방향 정리 | 2026년 5월 24일 | 성웅 | 로봇/DB 연동 | 실시간 DB | 완료 |
| live_scan/workstations 기반 실시간 3D 검사 화면 연동 구조 확인 | 2026년 5월 24일 | 성웅 | 3D 매핑/웹 | 실시간 연동 | 완료 |
| 실시간 렌더링 페이지 초기화 및 갱신 방식 검토 | 2026년 5월 24일 | 성웅 | 웹/3D 시각화 | 렌더링 개선 | 완료 |
| PointCloud 데이터를 웹으로 전달할 때 발생하는 렉 원인 분석 | 2026년 5월 25일 | 성웅 | 3D 매핑/웹 | 성능 분석 | 완료 |
| Plotly 기반 3D 렌더링 최적화 방향 검토 | 2026년 5월 25일 | 성웅 | 3D 매핑/웹 | 성능 개선 | 완료 |
| 포인트클라우드 다운샘플링 및 렌더링 부하 감소 방향 정리 | 2026년 5월 25일 | 성웅 | 3D 매핑/웹 | 최적화 검토 | 완료 |
| 나사 중심점 검출 정확도 개선 방향 정리 | 2026년 5월 26일 | 성웅 | 비전/3D 매핑 | 알고리즘 개선 | 완료 |
| 나사 불량 판단 기준 수정 및 높이 기반 검사 로직 보완 | 2026년 5월 26일 | 성웅 | 비전/알고리즘 | 검사 로직 개선 | 완료 |
| 3D 맵에서 나사를 제외한 영역 평탄화 처리 방향 정리 | 2026년 5월 26일 | 성웅 | 3D 매핑 | 맵 후처리 | 완료 |
| Firebase DB 구조를 captures 중심에서 session 기반 구조로 재설계 | 2026년 5월 26일 | 성웅 | Firebase/DB | DB 구조 개선 | 완료 |
| inspections/{site_id}/sessions/{session_id}/workstations/{workstation_id}/captures 구조 적용 | 2026년 5월 26일 | 성웅 | Firebase/DB | DB 구조 개선 | 완료 |
| session_id를 노드 실행 시점이 아닌 실제 검사 시작 시점 기준으로 생성하도록 수정 | 2026년 5월 26일 | 성웅 | Firebase/DB | 세션 관리 | 완료 |
| ensure_session_started 로직 추가 및 세션 누적 관리 구조 정리 | 2026년 5월 26일 | 성웅 | Firebase/DB | 세션 관리 | 완료 |
| session_total_captures / session_total_markers / normal_count / defect_count 누적 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 통계 관리 | 완료 |
| workstation_id 자동 생성 및 작업대별 capture 분리 저장 구조 적용 | 2026년 5월 26일 | 성웅 | Firebase/DB | 작업대 관리 | 완료 |
| capture metadata에 session_id / workstation_id / robot_id / camera_id 포함 | 2026년 5월 26일 | 성웅 | Firebase/DB | 메타데이터 개선 | 완료 |
| 기존 flat captures 경로 mirror 저장 유지로 구형 GUI 호환성 확보 | 2026년 5월 26일 | 성웅 | Firebase/DB | 하위 호환성 | 완료 |
| Firebase Storage 경로를 session/workstation/capture 기준으로 변경 | 2026년 5월 26일 | 성웅 | Firebase Storage | 파일 경로 개선 | 완료 |
| indexes/latest 포인터 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 조회 최적화 | 완료 |
| indexes/capture_lookup 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 조회 최적화 | 완료 |
| indexes/captures_by_date 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 날짜별 조회 | 완료 |
| indexes/captures_by_workstation 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 작업대별 조회 | 완료 |
| indexes/defects_by_status/unresolved 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 불량 추적 | 완료 |
| sites/latest_session_id 및 latest_capture_id 업데이트 구조 추가 | 2026년 5월 26일 | 성웅 | Firebase/DB | 사이트 상태 관리 | 완료 |
| robots/current_session_id / current_workstation_id / current_capture_id 업데이트 구조 추가 | 2026년 5월 26일 | 성웅 | 로봇/DB 연동 | 로봇 상태 연동 | 완료 |
| twin_state/current_session 업데이트 구조 추가 | 2026년 5월 26일 | 성웅 | 디지털트윈/DB | 현재 세션 표시 | 완료 |
| twin_state/current_inspection 업데이트 구조 추가 | 2026년 5월 26일 | 성웅 | 디지털트윈/DB | 최신 검사 표시 | 완료 |
| Firebase DB 연결 및 Storage bucket 연결 상태 확인 | 2026년 5월 26일 | 성웅 | Firebase/DB | 디버깅 | 완료 |
| markers가 None으로 저장되는 문제 원인 분석 | 2026년 5월 26일 | 성웅 | Firebase/DB | 디버깅 | 완료 |
| markers None 문제가 DB 오류가 아니라 YOLO 감지 결과 0개 때문임을 확인 | 2026년 5월 26일 | 성웅 | Firebase/DB | 디버깅 | 완료 |
| session 구조 도입 중 SyntaxError 발생 후 Git restore로 정상 버전 복구 | 2026년 5월 26일 | 성웅 | 코드 통합/DB | 디버깅 | 완료 |
| py_compile / import 테스트 / 경로 생성 테스트로 DB 코드 정적 검증 | 2026년 5월 26일 | 성웅 | 코드 통합/DB | 검증 | 완료 |
| GUI/API/Robot이 session 구조를 우선 조회하고 flat 구조를 fallback으로 사용하도록 방향 정리 | 2026년 5월 26일 | 성웅 | 통합 관리/DB | 호환성 설계 | 완료 |
| 팀원별 폴더 구조 CEY / KJH / YJH / YSW 확인 및 통합 기준 정리 | 2026년 5월 26일 | 성웅 | 팀장/GitHub | 협업 관리 | 완료 |
| GitHub collaborator main push 권한 및 VS Code push 오류 해결 지원 | 2026년 5월 26일 | 성웅 | 팀장/GitHub | 협업 관리 | 완료 |
| 팀원별 구현 파트 충돌 여부 확인 및 수정 방향 피드백 | 2026년 5월 26일 | 성웅 | 팀장/통합 관리 | 코드 리뷰 | 완료 |
