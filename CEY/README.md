# 5월 21일 
## 1. voice_ppv(LLM 음성제어 pkg)
   ### get_keyword_screw.py
  - '전체 검사해' : 나사 전체를 다 보라고 robot_control에게 명령함
  - 'n번 위치로 이동해' : 나사 번호 좌표로 이동하라고 robot_control에게 명령함
## 2. robot_ppv(로봇 제어 pkg)
  ### 1) robot_control_test4.py
  - yolo에서 받은 좌표정보를 순서대로 번호 매김
  - 전체 조사 기능 + 번호 위치 이동 기능 포함
  ### 2) robot_driver_chech_test3_4.py
  - 나사 순응제어,토크 모니터링을 통한 불량검사 미포함
  ### 3) robot_driver_chech_test3_5~7 까지
  - 조건 반대(기준토크 이상이면 불량 >> 기준토크 이상이면 정상으로 변경 필요)
  - 토크값 모니터링 기능 추가 +

# 5월 22일
   1. 로봇의 gripper로 나사를 잡고 돌리는 코드 구현
   2. 나사를 돌리면서 토크값 모니터링하는 코드 구현
   3. 나사가 일정 토크값을 넘으면 정지

# 5월 23일
   1. 각 ws 탐색 모션 하면서 /vision_inspect srv와 연동 
   2. 나사 좌표면 이동 >> ws + 나사 좌표 명령 구현
   3. 나사 좌표를 이용한 법선 벡터를 통해 ws별 자세값 + 수직 축 인식

