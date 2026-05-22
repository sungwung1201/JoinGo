##########################
"""
1. 단일 객체 인식 됬을 때 그 좌표로 이동
2. 복수 의 객체 인식 됬을 때 순서대로 좌표 이동 후 노드 종료
2.1 음성 추가
3. 전체 조사 기능 추가(
    - 전체 조사 기능>> 높은 좌표에서 각 나사 확인
    - 각 나사 번호 메기기 >> 좌표 통해 규칙 정해서 순서
4. 번호 받고 이동 기능
    - 번호를 yolo에서 할당으로 수정 >> 
    - 사용자가 번호 부르면 그 나사로 이동 조사 후 귀환
5. yolo에서 받는것이 아니라 DB에서 모든 나사 좌표와 번호를 가져옴 (Firebase 연동)
    _1 >> DB 연동 수정 
    _2 나사 조이는 기능 추가
    _3 나사 조이면서 토크값 확인 :
    _4 나사 조이는 성공!!!
"""
##########################

import os
import time
import sys
from scipy.spatial.transform import Rotation
import numpy as np
import rclpy
from rclpy.node import Node
import DR_init

# Firebase Admin SDK import
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from od_msg.srv import SrvDepthPosition
from std_srvs.srv import Trigger
from ament_index_python.packages import get_package_share_directory
from robot_control.onrobot import RG

package_path = get_package_share_directory("robot_ppv")

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
VELOCITY, ACC = 80, 60
JHOME_POS = [0, 0, 90, 0, 90, 0]
GRIPPER_NAME = "rg2"
TOOLCHARGER_IP = "192.168.1.1"
TOOLCHARGER_PORT = "502"
DEPTH_OFFSET = -39.0
MIN_DEPTH = 2.0

# ==========================================================
# 나사 좌표 보정 오프셋 (mm 단위)
# 카메라/비전 좌표와 실제 나사 위치 차이를 측정하여 입력하세요.
# ==========================================================
SCREW_OFFSET_X = -10.0   # X축 오프셋 (mm): 양수 -> 로봇 앞 방향, 음수 -> 로봇 뒤 방향
SCREW_OFFSET_Y = -10.0   # Y축 오프셋 (mm): 양수 -> 로봇 왼쪽, 음수 -> 로봇 오른쪽
SCREW_OFFSET_Z =  +0.0   # Z축 오프셋 (mm): 양수 -> 위쪽, 음수 -> 아래쪽

ROBOT_TOOL = "Tool Weight"
ROBOT_TCP = "GripperDA_v1"

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL


rclpy.init()
dsr_node = rclpy.create_node("robot_control_node", namespace=ROBOT_ID)
DR_init.__dsr__node = dsr_node

try:
    from DSR_ROBOT2 import (
        movej, movel, get_current_posx, mwait, trans, posx,
        amovej, get_current_posj, check_motion
    )
except ImportError as e:
    sys.exit()

gripper = RG(GRIPPER_NAME, TOOLCHARGER_IP, TOOLCHARGER_PORT)


# ==========================================================
# 로봇 초기화
# ==========================================================

def initialize_robot():
    from DSR_ROBOT2 import (
        set_tool,
        set_tcp,
        get_tool,
        get_tcp,
        ROBOT_MODE_MANUAL,
        ROBOT_MODE_AUTONOMOUS,
        get_robot_mode,
        set_robot_mode
    )

    print("#" * 50, flush=True)
    print("[TENDERIZING_ONCE] Initializing robot", flush=True)
    print(f"ROBOT_ID: {ROBOT_ID}", flush=True)
    print(f"ROBOT_MODEL: {ROBOT_MODEL}", flush=True)
    print(f"ROBOT_TCP: {ROBOT_TCP}", flush=True)
    print(f"ROBOT_TOOL: {ROBOT_TOOL}", flush=True)
    print(f"VELOCITY: {VELOCITY}", flush=True)
    print(f"ACC: {ACC}", flush=True)
    print("#" * 50, flush=True)

    set_robot_mode(ROBOT_MODE_MANUAL)
    time.sleep(0.5)

    set_tool(ROBOT_TOOL)
    set_tcp(ROBOT_TCP)

    set_robot_mode(ROBOT_MODE_AUTONOMOUS)
    time.sleep(2.0)

    print("#" * 50, flush=True)
    print("[TENDERIZING_ONCE] Robot initialized", flush=True)
    print(f"ROBOT_TCP: {get_tcp()}", flush=True)
    print(f"ROBOT_TOOL: {get_tool()}", flush=True)
    print(f"ROBOT_MODE: {get_robot_mode()}", flush=True)
    print("#" * 50, flush=True)


class RobotController(Node):
    def __init__(self):
        super().__init__("robot_integrated_controller")
        
        # 1. Firebase 초기화 설정
        self.init_firebase()
        
        self.init_robot()

        self.get_position_client = self.create_client(SrvDepthPosition, "/get_3d_position")
  
        while not self.get_position_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().info("Waiting for get_depth_position service...")

        self.get_keyword_client = self.create_client(Trigger, "/get_keyword")
        while not self.get_keyword_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().info("Waiting for get_keyword service...")
        self.get_keyword_request = Trigger.Request()
        
        # 번호별 위치 좌표를 기억하기 위한 딕셔너리 (DB에서 가져와 저장)
        self.saved_positions = {}

    def init_firebase(self):
        """Firebase Admin SDK 초기화"""
        # 제공된 JSON 인증 키 파일 경로 설정
        cred_path = os.path.join(package_path, "resource", "rokey-d-2-4c32a-firebase-adminsdk-fbsvc-3c31d8ba34.json")
        
        # Firebase 앱이 중복 초기화되지 않도록 확인
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(cred_path)
                # 데이터베이스 URL 설정
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://rokey-d-2-4c32a-default-rtdb.asia-southeast1.firebasedatabase.app'
                })
                self.get_logger().info("Firebase 초기화 완료")
            except Exception as e:
                self.get_logger().error(f"Firebase 초기화 실패: {e}")

    def fetch_positions_from_db(self, workspace_name="Workspace 1"):
        """Firebase DB에서 특정 워크스페이스의 마커 좌표와 할당 번호를 가져옵니다."""
        try:
            # 제공된 구조 이미지 기반: /linestatus/Workspace 1/markers 경로 참조
            ref = db.reference(f'/linestatus/{workspace_name}/markers')
            markers = ref.get()
            
            if not markers:
                self.get_logger().warn("DB에서 데이터를 찾을 수 없습니다.")
                return False
                
            self.saved_positions.clear() # 기존 저장소 초기화
            robot_posx = get_current_posx()[0] # 현재 로봇 자세 (Rx, Ry, Rz 기본값용)

            # markers가 리스트인지 딕셔너리인지에 따라 파싱
            items = markers.items() if isinstance(markers, dict) else enumerate(markers)
            
            for marker_id, data in items:
                if data and 'position' in data:
                    pos_data = data['position']
                    
                    # DB에 저장된 position 형태에 맞춰 파싱 (리스트 또는 딕셔너리 가정)
                    if isinstance(pos_data, dict):
                        x, y, z = pos_data.get('x', 0.0), pos_data.get('y', 0.0), pos_data.get('z', 0.0)
                        
                        # 미터(m) 단위로 들어오는 경우(값이 10 미만) 밀리미터(mm)로 변환
                        if abs(x) < 10.0 and abs(y) < 10.0 and abs(z) < 10.0:
                            x *= 1000.0
                            y *= 1000.0
                            z *= 1000.0
                            
                        target_coords = [x, y, z, robot_posx[3], robot_posx[4], robot_posx[5]]
                    elif isinstance(pos_data, (list, tuple)):
                        if len(pos_data) == 3:
                            target_coords = list(pos_data) + list(robot_posx[3:])
                        elif len(pos_data) == 6:
                            target_coords = list(pos_data)
                        else:
                            continue
                    else:
                        continue
                        
                    # 딕셔너리에 저장 (인덱스가 0부터 시작하므로 사람이 부르기 편하게 1을 더해 "1", "2" ... 로 저장)
                    try:
                        str_marker_id = str(int(marker_id) + 1)
                    except ValueError:
                        str_marker_id = str(marker_id)
                    self.saved_positions[str_marker_id] = target_coords
                    self.get_logger().info(f"[DB 저장 완료] 나사 번호 {str_marker_id}: {target_coords[:3]}")
                    
            return True
            
        except Exception as e:
            self.get_logger().error(f"DB 데이터 불러오기 오류: {e}")
            return False

    def get_robot_pose_matrix(self, x, y, z, rx, ry, rz):
        R = Rotation.from_euler("ZYZ", [rx, ry, rz], degrees=True).as_matrix()
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = [x, y, z]
        return T

    def transform_to_base(self, camera_coords, gripper2cam_path, robot_pos):
        gripper2cam = np.load(gripper2cam_path)
        coord = np.append(np.array(camera_coords), 1)
        x, y, z, rx, ry, rz = robot_pos
        base2gripper = self.get_robot_pose_matrix(x, y, z, rx, ry, rz)
        base2cam = base2gripper @ gripper2cam
        td_coord = np.dot(base2cam, coord)
        return td_coord[:3]

    def robot_control(self):
        self.get_logger().info("음성 명령을 기다립니다... (대상을 말해주세요)")
        
        get_keyword_future = self.get_keyword_client.call_async(self.get_keyword_request)
        rclpy.spin_until_future_complete(self, get_keyword_future)
        
        result = get_keyword_future.result()

        if not result or not result.success or not result.message:
            self.get_logger().warn("음성 인식 실패 또는 빈 메시지. 다시 시도합니다.")
            return False

        target_obj = result.message.strip().replace("'", "").replace('"', "").lower()
        self.get_logger().info(f"명령: '{target_obj}'")
        
        # --- 1. 전체 조사(all_check) 기능: 좌표 수집 및 DB 가져오기 ---
        if target_obj == "all_check":
            self.get_logger().info("전체 조사(all_check) 모드 진입. 지정된 높은 좌표로 이동합니다.")
            all_check_pos = [-7.997, 24.168, 48.78, -0.063, 107.244, -7.838]
            movej(all_check_pos, vel=VELOCITY, acc=ACC)
            mwait()
            time.sleep(1.0) # 카메라 안정화를 위한 대기

            # Detection 노드에 동작을 요청하여 DB를 업데이트 하도록 유도 (기존 서비스 호출 유지)
            self.get_logger().info("Detection 노드에 검사 요청 중...")
            _ = self.get_target_list("all") 
            
            # DB가 업데이트 될 수 있도록 약간의 시간 지연 대기
            time.sleep(2.0)
            
            self.get_logger().info("작업 완료 확인. Firebase DB에서 나사 좌표 및 할당 번호를 조회합니다.")
            success = self.fetch_positions_from_db(workspace_name="Workspace 3")
            
            if success:
                self.get_logger().info("DB 동기화 완료. 다음 명령을 대기하기 위해 홈으로 복귀합니다.")
            else:
                self.get_logger().warn("DB 동기화에 실패했습니다.")
                
            movej(JHOME_POS, vel=VELOCITY, acc=ACC)
            mwait()
            return True

        # --- 2. 개별 번호 호출 시 Firebase DB에 연동된 저장된 위치로 이동 ---
        # "1", "2" 와 같은 숫자 번호 또는 "pos1" 형태로 입력될 때 처리
        # 문자열에서 숫자 부분만 추출
        marker_key = "".join(filter(str.isdigit, target_obj))
        
        if marker_key in self.saved_positions:
            target_pos = self.saved_positions[marker_key]
            self.get_logger().info(f"DB에 할당된 번호 '{marker_key}' 좌표로 이동합니다.")
            self.grip_and_tighten(target_pos)
            
            self.get_logger().info("나사 조이기 완료. 홈(JHOME_POS) 위치로 복귀합니다.")
            movej(JHOME_POS, vel=VELOCITY, acc=ACC)
            mwait()
            return True

        # --- 3. 기존 일반 객체 탐색 ---
        else:
            if not marker_key and not target_obj.startswith("pos"):
                # "1" 같은 DB번호가 아닐 경우 일반 탐색 (생략 또는 기존 코드 유지)
                check_all_pos = [-7.997, 24.168, 48.78, -0.063, 107.244, -7.838]
                movel(check_all_pos, vel=VELOCITY, acc=ACC)
                mwait()
                
                target_pos_list = self.get_target_list(target_obj)
                
                if not target_pos_list:
                    self.get_logger().warn(f"[{target_obj}]의 좌표를 찾지 못했거나 DB 번호가 아닙니다.")
                    return False
                else:
                    self.get_logger().info(f"총 {len(target_pos_list)}개의 객체 발견. 작업을 시작합니다.")
                    for i, pos in enumerate(target_pos_list):
                        self.get_logger().info(f"--- {i+1}번째 나사 조이기 시작 ---")
                        self.grip_and_tighten(pos)
                    
                self.get_logger().info("모든 작업 완료. 홈(JHOME_POS) 위치로 복귀합니다.")
                movej(JHOME_POS, vel=VELOCITY, acc=ACC)
                mwait()
                return True
            else:
                self.get_logger().warn(f"'{target_obj}'(이)라는 번호로 DB에 할당된 좌표가 없습니다. 'all_check'를 먼저 실행했는지 확인하세요.")
                return False

    def get_target_list(self, target):
        """기존 Detection 서비스 호출 노드 로직"""
        new_request = SrvDepthPosition.Request()
        new_request.target = target
       
        future = self.get_position_client.call_async(new_request)
        rclpy.spin_until_future_complete(self, future)

        if future.result():
            result = future.result().depth_position.tolist()
            if not result or sum(result) == 0: return []

            path = os.path.join(package_path, "resource", "T_gripper2camera.npy")
            robot_posx = get_current_posx()[0]
            pos_list = []
            
            for i in range(0, len(result), 3):
                coord = result[i:i+3]
                if sum(coord) == 0: continue
                td = self.transform_to_base(coord, path, robot_posx)
                if td[2]:
                    td[2] = max(td[2] + DEPTH_OFFSET, MIN_DEPTH)
                    pos_list.append(list(td[:3]) + robot_posx[3:])
            return pos_list
        return []

    def init_robot(self):
        movej(JHOME_POS, vel=VELOCITY, acc=ACC)
        mwait()

    def grip_and_tighten(self, target_pos, approach_height=150.0):
        """
        그리퍼로 나사를 집고 J6 축을 회전시켜 조이는 시퀀스.
        get_external_torque()[5] (J6 외력 토크) 실시간 감시로 나사 조임 완료 판단.

        전략:
          - amovej 로 큰 각도(MAX_TIGHTEN_DEG) 비동기 회전 시작 (저속)
          - 50ms마다 get_external_torque()[5] 를 읽어 J6 토크 감시
          - |J6 토크| >= J6_TORQUE_THRESHOLD 이면 나사 꽉 조여짐으로 판단
            → drl_script_stop(DR_HOLD) 으로 즉시 모션 중단
          - 토크 미달로 MAX_TIGHTEN_DEG 다 돌면: 놓고 원위치 → 다음 사이클
        
        주의:
          - get_external_torque()는 컴플라이언스 제어 없이도 동작 중에 읽을 수 있음
          - task_compliance_ctrl + amovej 동시 사용은 제어 충돌 위험 → 사용 안 함
          - 모션 중단은 반드시 drl_script_stop(DR_HOLD)를 명시적으로 호출해야 함
        """
        from DSR_ROBOT2 import (
            get_external_torque,
            drl_script_stop,
            DR_HOLD,
        )

        # ── 토크 임계값 설정 ──────────────────────────────────────────────────
        # 나사가 꽉 조여졌다고 판단할 J6 외력 토크 임계값 (N·m)
        # 실제 나사 토크에 맞게 조정하세요 (일반적으로 1.0 ~ 3.0 N·m)
        J6_TORQUE_THRESHOLD = 0.5   # [N·m]
        # 한 파지 사이클에서 최대 회전 각도 (도)
        MAX_TIGHTEN_DEG     = 150.0
        # 토크 감시 주기 (초)
        TORQUE_POLL_SEC     = 0.05
        # 최대 파지 반복 횟수 (토크 미달 시 잡고→돌리고→놓고 반복 한계)
        MAX_CYCLE           = 10
        # ─────────────────────────────────────────────────────────────────────

        # 오프셋 적용
        target_pos = list(target_pos)
        target_pos[0] += SCREW_OFFSET_X
        target_pos[1] += SCREW_OFFSET_Y
        target_pos[2] += SCREW_OFFSET_Z
        self.get_logger().info(
            f"[grip] 오프셋 적용: "
            f"X+{SCREW_OFFSET_X:.1f}, Y+{SCREW_OFFSET_Y:.1f}, Z+{SCREW_OFFSET_Z:.1f} mm "
            f"-> 이동 목표: {target_pos[:3]}"
        )
        target_pos_up = list(target_pos)
        target_pos_up[2] += approach_height

        # 1. 안전 높이로 이동
        self.get_logger().info(f"[grip] 1. 안전 높이({target_pos_up[2]:.1f}mm)로 이동 중...")
        movel(target_pos_up, vel=VELOCITY, acc=ACC)
        mwait()
        time.sleep(1.0)

        # 2. 그리퍼 열기
        self.get_logger().info("[grip] 2. 그리퍼 열기")
        gripper.open_gripper()
        time.sleep(1.0)

        # 3. 나사 위치로 하강
        self.get_logger().info(f"[grip] 3. 나사 위치({target_pos[2]:.1f}mm)로 하강...")
        movel(target_pos, vel=40, acc=25)
        mwait()
        time.sleep(2.0)

        # 4. 토크 감시 기반 나사 조임 루프
        self.get_logger().info(
            f"[grip] 4. 토크 감시 나사 조임 시작 "
            f"(임계: ±{J6_TORQUE_THRESHOLD} N·m, 최대 회전: {MAX_TIGHTEN_DEG}°/사이클, "
            f"최대 {MAX_CYCLE}사이클)"
        )

        tightened = False

        for cycle in range(MAX_CYCLE):
            self.get_logger().info(f"[grip]   [사이클 {cycle+1}/{MAX_CYCLE}] 그리퍼 닫기 (파지)")
            gripper.close_gripper()
            time.sleep(2.0)

            # ── 현재 관절각 읽기 및 목표 관절각 설정 ─────────────────────────
            curr_joint   = get_current_posj()
            target_joint = list(curr_joint)
            initial_j6   = curr_joint[5]
            target_joint[5] = initial_j6 + MAX_TIGHTEN_DEG

            # ── 비동기 회전 시작 (amovej, 저속) ──────────────────────────────
            # vel=10, acc=10: 천천히 돌아야 토크 감지가 정확하고 안전함
            self.get_logger().info(
                f"[grip]   [사이클 {cycle+1}] 비동기 조임 회전 시작 "
                f"(J6: {initial_j6:.1f}° → {target_joint[5]:.1f}°, vel=10)"
            )
            amovej(target_joint, vel=10, acc=10)

            # ── J6 외력 토크 실시간 감시 ──────────────────────────────────────
            # get_external_torque()는 로봇 컨트롤러에 ROS2 서비스 쿼리
            # amovej로 비동기 모션 중에도 독립적으로 실시간 값을 읽을 수 있음
            tightened_this_cycle = False
            cnt = 0
            while True:
                ext_torque = get_external_torque()

                if ext_torque == -1 or not isinstance(ext_torque, list) or len(ext_torque) < 6:
                    self.get_logger().warn("[grip]   외력 토크 읽기 실패, 재시도...")
                    time.sleep(TORQUE_POLL_SEC)
                    continue

                j6_torque = ext_torque[5]  # J6 축 외력 토크 [N·m]
                motion_state = check_motion()  # 0: 모션 없음, 1: 동작 중

                self.get_logger().info(
                    f"[grip]   J6 외력 토크: {j6_torque:+.3f} N·m "
                    f"(임계: ±{J6_TORQUE_THRESHOLD} N·m) | 모션: {'동작중' if motion_state else '정지'}"
                )

                # ── 나사 꽉 조여짐 감지 ──────────────────────────────────────
                if abs(j6_torque) >= J6_TORQUE_THRESHOLD:
                    cnt +=1
                    if cnt >= 10:
                        self.get_logger().info(
                            f"[grip]   ★ 나사 조임 완료! "
                            f"J6 토크 {j6_torque:+.3f} N·m ≥ ±{J6_TORQUE_THRESHOLD} N·m"
                        )
                        # amovej 모션을 즉시 중단 (DR_HOLD: 현재 위치에서 감속 정지)
                        drl_script_stop(DR_HOLD)
                        mwait()  # 정지 완료 대기
                        tightened_this_cycle = True
                        tightened = True
                        break

                # ── 최대 각도 도달 (토크 미달) ───────────────────────────────
                if motion_state == 0:
                    self.get_logger().info(
                        f"[grip]   [사이클 {cycle+1}] 최대 각도 도달, 토크 미달 "
                        f"({j6_torque:+.3f} N·m < ±{J6_TORQUE_THRESHOLD} N·m) → 다음 사이클"
                    )
                    break

                time.sleep(TORQUE_POLL_SEC)

            if tightened_this_cycle:
                # 나사 조임 완료: 파지 해제 후 루프 종료
                self.get_logger().info("[grip]   나사 조임 완료. 그리퍼 열기")
                gripper.open_gripper()
                time.sleep(0.5)
                break

            # ── 토크 미달: 놓기 → 원위치 복귀 → 다음 사이클 ─────────────────
            self.get_logger().info(f"[grip]   [사이클 {cycle+1}] 그리퍼 열기 → J6 원위치 복귀")
            gripper.open_gripper()
            time.sleep(0.5)

            curr_joint_after = get_current_posj()
            back_joint = list(curr_joint_after)
            back_joint[5] = initial_j6
            movej(back_joint, vel=20, acc=20)
            mwait()
            time.sleep(0.3)

        if not tightened:
            self.get_logger().warn(
                f"[grip] ⚠ 최대 사이클({MAX_CYCLE}회) 도달 후에도 나사 조임 토크 미달. "
                f"나사 상태를 확인하세요."
            )

        # 5. 안전 높이로 상승
        self.get_logger().info("[grip] 5. 안전 높이로 수직 상승")
        curr_pos_up = list(target_pos)
        curr_pos_up[2] = target_pos_up[2]
        movel(curr_pos_up, vel=VELOCITY, acc=ACC)
        mwait()
        time.sleep(0.5)
        

def main(args=None):
    node = RobotController()
    try:
        initialize_robot()
        while rclpy.ok():
            node.robot_control()
            time.sleep(1.0) 
    except KeyboardInterrupt:
        node.get_logger().info("사용자에 의해 노드가 종료됩니다.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()