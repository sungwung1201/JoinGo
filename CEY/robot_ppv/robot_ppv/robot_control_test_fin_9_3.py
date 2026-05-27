##########################
"""
패치 노드:
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
fin_1. 통합! all_check>> 5방향 작업대 탐색>> DB에서 좌표계 가져오기
fin_2. workspace을 설정하고, 그 workspace의 나사를 불러오는 기능 추가
    - workspace1의 경우 tcp의 자세값에 의해 사용 불가
fin_3. workspace마다 초기 작업 좌표 설정
fin_4. 자세값으로 workspace의 접근축, 접근 방향 계산
fin_5. 작업대별 offset + 나사 채결 토크값 다른 문제 발견
    - 토크 정리 (workspace3 : -0.5, workspace1 : -0.7)
    - workspace1 : z축 -30 offset 필요 >> yolo로 빛 가렸을 때 어떻게 되는지 확인 필요
    .1 나사 좌표를 가져오는 경로 DB에 맞게 수정
fin_6. yolo로 나사 좌표 정밀 보정 + DB 경로 변경
fin_7. 'workspace준비' 명령 추가
fin_8. 나사 기준 적응형 토크 감지 >> workspace마다 나사 채결 토크 차이를 감수
fin_9. 나사 정밀검사 명령 추가
    1. 토크검사 추가
    2. 작업대별로 offset 추가 + 최소 토크 임계값 보정
    3. 실행 속도 최적화
"""
##########################

import os
import time
import sys
import numpy as np
import rclpy
from rclpy.node import Node
import DR_init

# Firebase Admin SDK import
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from std_srvs.srv import Trigger
from ament_index_python.packages import get_package_share_directory
from robot_control.onrobot import RG

package_path = get_package_share_directory("robot_ppv")

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
VELOCITY, ACC = 100, 80
JHOME_POS = [0, 0, 90, 0, 90, 0]
GRIPPER_NAME = "rg2"
TOOLCHARGER_IP = "192.168.1.1"
TOOLCHARGER_PORT = "502"


# ==========================================================
# 접근축(Approach Axis)별 좌표 보정 오프셋 (mm 단위)
# ==========================================================
AXIS_OFFSETS = {
    "-y": {"x": -2.0, "y": -5.0, "z": -2.0},
    "-z": {"x": -20.0, "y": 5.0, "z": 0.0},
}

# ==========================================================
# all_check 5방향 탐색 viewpoint (explore_environment_plane_normal.py 기준)
# ==========================================================
VIEWPOINTS = [
    {"id": 1, "name": "viewpoint_1", "joints": [0.0,  -0.0,  90.039, -90.0,   90.0,   0.0]},
    {"id": 2, "name": "viewpoint_2", "joints": [-0.006, -0.019, 89.985, -90.003, -0.003, -0.0]},
    {"id": 3, "name": "viewpoint_3", "joints": [-0.034, -0.019, 89.984,  90.003,  90.005,  0.0]},
    {"id": 4, "name": "viewpoint_4", "joints": [-0.034, -0.018, 89.984,  -0.004,  90.005,  0.0]},
    {"id": 5, "name": "viewpoint_5", "joints": [-0.034, -0.022, 89.983,  -0.004, -90.004, -0.0]},
]
CAMERA_STABILIZE_SEC = 1.5  # 카메라 안정화 대기 시간(초)

ROBOT_TOOL = "Tool Weight"
ROBOT_TCP = "GripperDA_v1"

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL


rclpy.init()
dsr_node = rclpy.create_node("robot_control_node", namespace=ROBOT_ID)
DR_init.__dsr__node = dsr_node

try:
    from DSR_ROBOT2 import (
        movej, movel, movejx, mwait,
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
    
    if ROBOT_TOOL:
        set_tool(ROBOT_TOOL)

    if ROBOT_TCP:
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

        # --- 음성 인식 서비스 ---
        self.get_keyword_client = self.create_client(Trigger, "/get_keyword")
        while not self.get_keyword_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().info("Waiting for get_keyword service...")
        self.get_keyword_request = Trigger.Request()

        # --- realtime_3d_mapper_multi_06 비전 검사 서비스 (all_check 전용) ---
        self.vision_client = self.create_client(Trigger, "/vision_inspect")
        while not self.vision_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().info("Waiting for /vision_inspect service...")
        self.vision_request = Trigger.Request()
        
        # workspace별 나사 좌표 저장: {"Workspace 1": {"1": [x,y,z,rx,ry,rz], ...}, ...}
        self.saved_positions = {}
        
        # workspace별 계산된 준비 위치 저장
        self.saved_prep_positions = {}
        
        # 현재 활성화된 워크스페이스 (음성 명령으로 변경 가능)
        self.current_workspace = "Workspace 3"

        # workspace별 무부하 토크 측정 임계값 저장 (대기 이동 시 자동 측정)
        # 예: {"Workspace 1": -0.7, "Workspace 3": -0.5}
        self.workspace_torque_threshold = {}

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

    def _compute_approach_euler(self, points_mm):
        """
        나사 xyz 좌표 리스트로부터 작업면 접근 방향을 계산하여
        Doosan ZYZ Euler 각도(rx, ry, rz)를 반환합니다.

        접근: N개의 나사좌표 → SVD 평면맞안법 → 법선벡터 n → 회전행렬화 → ZYZ Euler

        Args:
            points_mm: [(x1,y1,z1), ...] (mm 단위, 로봇 base frame)

        Returns:
            (rx, ry, rz): Doosan ZYZ Euler 각도 (도 단위)
        """
        DEFAULT = (0.0, 180.0, 0.0)  # 기본값: 그리퍼 수직 아래 향함

        pts = np.array(points_mm, dtype=float)  # (N, 3)
        N = len(pts)

        # --- 1. 평면 법선 계산 ---
        if N == 1:
            # 나사 1개만 있으면 기본값 사용
            self.get_logger().warn("[Pose] 나사 1개: 기본 자세값 사용")
            return DEFAULT

        centroid = pts.mean(axis=0)
        M = pts - centroid  # (N, 3)

        if N == 2:
            # 나사 2개: 두 점을 잇는 벡터와 임의 월드축의 외적으로 법선 계산
            v = M[1] - M[0]
            world_up = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(v / (np.linalg.norm(v) + 1e-12), world_up)) > 0.9:
                world_up = np.array([1.0, 0.0, 0.0])
            normal = np.cross(v, world_up)
        else:
            # N >= 3: SVD로 가장 작은 특이값에 대응하는 법선발견
            _, _, Vt = np.linalg.svd(M)
            normal = Vt[-1]  # 마지마 행 = 작업면 법선

        n = normal / (np.linalg.norm(normal) + 1e-12)  # 단위벡터화

        # --- 2. 접근 방향 부호 확정 ---
        # SVD로 구한 법선벡터 n은 방향이 임의적입니다.
        # 작업면의 지배적인 평면(X, Y, Z)에 따라 접근 방향을 결정합니다.
        dom_idx = int(np.argmax(np.abs(n)))
        
        if dom_idx == 2:
            # Z축이 지배적인 평면 (수평면, 바닥/책상):
            # 로봇은 위에서 아래로 접근해야 하므로, Z 성분은 항상 음수여야 합니다.
            approach = n if n[2] < 0 else -n
        else:
            # X 또는 Y축이 지배적인 평면 (수직면, 벽/옆면):
            # 로봇(원점)에서 작업물을 바라보고 접근해야 하므로,
            # 원점에서 작업물(centroid)을 향하는 벡터 방향과 부호가 같아야 합니다.
            # 예: 작업물이 Y=-700에 있으면 접근도 -Y 방향이어야 함.
            if (n[dom_idx] * centroid[dom_idx]) > 0:
                approach = n
            else:
                approach = -n

        # --- 지배 축 이름 판별 (나사 평면과 수직인 축 표시) ---
        _AXIS_NAMES = ['x', 'y', 'z']
        final_dom_idx = int(np.argmax(np.abs(approach)))
        dom_sign = '+' if approach[final_dom_idx] >= 0 else '-'
        dom_axis = f"{dom_sign}{_AXIS_NAMES[final_dom_idx]}"
        self.get_logger().info(
            f"[Pose] 면 법선={np.round(n, 3)}, 접근방향={np.round(approach, 3)} "
            f"→ 나사와 수직인 접근축: [{dom_axis}] (지배 성분 {approach[final_dom_idx]:+.3f})"
        )

        # --- 3. 기본 자세에서 최소 회전으로 방향 정렬 (Shortest Arc Rotation) ---
        # 기존: 임의의 x, y축을 생성해서 그립 방향이 틀어짐(twist)
        # 수정: 기본 자세(DEFAULT)의 Z축을 파악해, 이를 approach 방향으로 최소한만 회전시킴
        def zyz_to_R(rx, ry, rz):
            a, b, g = np.radians(rx), np.radians(ry), np.radians(rz)
            ca, sa = np.cos(a), np.sin(a)
            cb, sb = np.cos(b), np.sin(b)
            cg, sg = np.cos(g), np.sin(g)
            Rz1 = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
            Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
            Rz2 = np.array([[cg, -sg, 0], [sg, cg, 0], [0, 0, 1]])
            return Rz1 @ Ry @ Rz2
            
        R_def = zyz_to_R(*DEFAULT)
        v0 = R_def @ np.array([0, 0, 1])  # 기본 자세의 Z축
        v1 = approach
        
        # v0에서 v1으로의 최단 회전 행렬 (Rodrigues' rotation formula)
        axis = np.cross(v0, v1)
        s = np.linalg.norm(axis)
        c = np.dot(v0, v1)
        
        if s < 1e-6:
            if c > 0:
                R_align = np.eye(3)
            else:
                ortho = np.array([1, 0, 0]) if abs(v0[0]) < 0.9 else np.array([0, 1, 0])
                axis = np.cross(v0, ortho)
                axis = axis / np.linalg.norm(axis)
                K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
                R_align = np.eye(3) + 2 * (K @ K)
        else:
            axis = axis / s
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
            R_align = np.eye(3) + s * K + (1 - c) * (K @ K)
            
        R_new = R_align @ R_def

        # --- 4. ZYZ Euler 각도 연산 (도 단위) ---
        r22 = np.clip(R_new[2, 2], -1.0, 1.0)   # cos(beta)
        beta = np.degrees(np.arccos(r22))

        if abs(beta) < 1e-6 or abs(beta - 180.0) < 1e-6:
            # 특이점(gimbal lock)
            alpha = 0.0
            gamma = np.degrees(np.arctan2(R_new[1, 0], R_new[0, 0]))
        else:
            # 올바른 ZYZ 추출 공식 (이전 코드에서 alpha와 gamma 공식이 반대로 되어있었음)
            alpha = np.degrees(np.arctan2(R_new[1, 2], R_new[0, 2]))
            gamma = np.degrees(np.arctan2(R_new[2, 1], -R_new[2, 0]))

        rx, ry, rz = alpha, beta, gamma
        self.get_logger().info(
            f"[Pose] 자동 계산된 ZYZ Euler: rx={rx:.2f}, ry={ry:.2f}, rz={rz:.2f} (deg)"
        )
        return (rx, ry, rz)

    def get_workspace_vertical_axis(self, ws_name):
        """
        특정 워크스페이스의 나사 좌표들로부터 수직 성분(지배적인 법선축)의 인덱스와
        대표 자세값(rx, ry, rz)을 반환합니다.
        
        Args:
            ws_name: 워크스페이스 이름 (예: 'Workspace 1')
            
        Returns:
            dom_idx: 0 (X), 1 (Y), 2 (Z) 또는 None
            orientation: (rx, ry, rz) 튜플 또는 None
        """
        ws_positions = self.saved_positions.get(ws_name, {})
        if not ws_positions:
            return None, None

        pts = np.array([pos[:3] for pos in ws_positions.values()], dtype=float)
        N = len(pts)
        if N == 0:
            return None, None

        # 대표 자세값 (첫 번째 나사 좌표의 rx, ry, rz 사용)
        first_pos = next(iter(ws_positions.values()))
        orientation = first_pos[3:6]

        if N == 1:
            # 나사 1개인 경우 기본 Z축을 지배축으로 가정
            return 2, orientation

        centroid = pts.mean(axis=0)
        M = pts - centroid

        if N == 2:
            v = M[1] - M[0]
            world_up = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(v / (np.linalg.norm(v) + 1e-12), world_up)) > 0.9:
                world_up = np.array([1.0, 0.0, 0.0])
            normal = np.cross(v, world_up)
        else:
            _, _, Vt = np.linalg.svd(M)
            normal = Vt[-1]

        n = normal / (np.linalg.norm(normal) + 1e-12)
        
        # 접근 부호 및 지배 축 결정 ( _compute_approach_euler 로직 준수 )
        dom_idx = int(np.argmax(np.abs(n)))
        if dom_idx == 2:
            approach = n if n[2] < 0 else -n
        else:
            if (n[dom_idx] * centroid[dom_idx]) > 0:
                approach = n
            else:
                approach = -n
                
        final_dom_idx = int(np.argmax(np.abs(approach)))
        return final_dom_idx, orientation


    @staticmethod
    def _workspace_to_id(workspace_name: str) -> str:
        """
        'Workspace N' → 'workstation_0N' 변환.
        예: 'Workspace 1' → 'workstation_01', 'Workspace 12' → 'workstation_12'
        """
        import re
        m = re.search(r'(\d+)', workspace_name)
        if m:
            return f'workstation_{int(m.group(1)):02d}'
        return workspace_name.lower().replace(' ', '_')

    @staticmethod
    def _id_to_workspace(workstation_id: str) -> str:
        """
        'workstation_01' → 'Workspace 1' 변환.
        """
        import re
        m = re.search(r'(\d+)', workstation_id)
        if m:
            return f'Workspace {int(m.group(1))}'
        return workstation_id

    def _parse_screws(self, screws, workspace_name):
        """
        /live_scan/workstations/{id}/screws 데이터를 파싱하여
        {marker_id: [x,y,z,rx,ry,rz]} 딕셔너리로 반환.
        """
        result = {}
        raw_points = []

        items = screws.items() if isinstance(screws, dict) else enumerate(screws)
        for screw_id, data in items:
            if not (data and 'position' in data):
                continue
            pos_data = data['position']
            if not isinstance(pos_data, dict):
                continue
            x = float(pos_data.get('x', 0.0))
            y = float(pos_data.get('y', 0.0))
            z = float(pos_data.get('z', 0.0))
            # m 단위로 저장된 경우 mm 변환
            if abs(x) < 1.0 and abs(y) < 1.0 and abs(z) < 1.0 and not (x == 0 and y == 0 and z == 0):
                x *= 1000.0; y *= 1000.0; z *= 1000.0
            raw_points.append((x, y, z))

        # --- 작업면 접근 자세값 자동 계산 ---
        if raw_points:
            rx, ry, rz = self._compute_approach_euler(raw_points)
        else:
            rx, ry, rz = 0.0, 180.0, 0.0
        self.get_logger().info(
            f"[{workspace_name}] 적용 자세값: rx={rx:.2f}, ry={ry:.2f}, rz={rz:.2f}"
        )

        # --- 파싱 결과에 자세값 적용 ---
        items2 = screws.items() if isinstance(screws, dict) else enumerate(screws)
        for screw_id, data in items2:
            if not (data and 'position' in data):
                continue
            pos_data = data['position']
            if not isinstance(pos_data, dict):
                continue
            x = float(pos_data.get('x', 0.0))
            y = float(pos_data.get('y', 0.0))
            z = float(pos_data.get('z', 0.0))
            if abs(x) < 1.0 and abs(y) < 1.0 and abs(z) < 1.0 and not (x == 0 and y == 0 and z == 0):
                x *= 1000.0; y *= 1000.0; z *= 1000.0

            import re as _re
            m = _re.search(r'(\d+)', str(screw_id))
            if m:
                str_id = str(int(m.group(1)) + 1)
            else:
                try:
                    str_id = str(int(screw_id) + 1)
                except (ValueError, TypeError):
                    str_id = str(screw_id)

            target_coords = [x, y, z, rx, ry, rz]
            result[str_id] = target_coords
            self.get_logger().info(
                f"[DB 저장] [{workspace_name}] 나사 번호 {str_id} ({screw_id}): "
                f"{[round(v,2) for v in target_coords[:3]]} mm"
            )
        return result

    def fetch_positions_from_db(self, workspace_name):
        """Firebase DB에서 특정 워크스페이스의 나사 좌표를 가져와 saved_positions에 저장합니다."""
        try:
            workstation_id = self._workspace_to_id(workspace_name)
            ref = db.reference(f'/live_scan/workstations/{workstation_id}/screws')
            screws = ref.get()
            if not screws:
                self.get_logger().warn(
                    f"[{workspace_name}] DB에서 나사 데이터를 찾을 수 없습니다. "
                    f"(경로: /live_scan/workstations/{workstation_id}/screws)"
                )
                return False
            parsed = self._parse_screws(screws, workspace_name)
            if not parsed:
                return False
            self.saved_positions[workspace_name] = parsed
            self.get_logger().info(
                f"[{workspace_name}] {len(parsed)}개 나사 좌표 로드 완료."
            )
            return True
        except Exception as e:
            self.get_logger().error(f"[{workspace_name}] DB 데이터 불러오기 오류: {e}")
            return False

    def fetch_all_workspaces_from_db(self):
        """Firebase DB의 /live_scan/workstations 하위 모든 워크스페이스 좌표를 가져옵니다."""
        try:
            ref = db.reference('/live_scan/workstations')
            workstations = ref.get()
            if not workstations:
                self.get_logger().warn("DB /live_scan/workstations 에서 데이터를 찾을 수 없습니다.")
                return False
            self.saved_positions.clear()
            loaded_count = 0
            for ws_id, ws_data in workstations.items():
                if not isinstance(ws_data, dict) or 'screws' not in ws_data:
                    continue
                ws_name = self._id_to_workspace(ws_id)
                parsed = self._parse_screws(ws_data['screws'], ws_name)
                if parsed:
                    self.saved_positions[ws_name] = parsed
                    loaded_count += 1
            self.get_logger().info(
                f"전체 DB 동기화 완료: {loaded_count}개 워크스페이스, "
                f"워크스페이스 목록: {list(self.saved_positions.keys())}"
            )
            return loaded_count > 0
        except Exception as e:
            self.get_logger().error(f"전체 DB 데이터 불러오기 오류: {e}")
            return False

    def update_screw_status_to_normal(self, workspace_name, marker_key):
        """
        나사 체결 완료 후 Firebase DB에서 해당 나사의 status를 'normal'로 업데이트.
        예: workspace_name='Workspace 1', marker_key='1'
        -> /live_scan/workstations/workstation_01/screws/screw_00/status = 'normal'
        """
        try:
            workstation_id = self._workspace_to_id(workspace_name)
            # marker_key("1") -> screw_idx(0) -> "screw_00"
            screw_idx = int(marker_key) - 1
            screw_id = f"screw_{screw_idx:02d}"
            
            db_path = f'/live_scan/workstations/{workstation_id}/screws/{screw_id}'
            ref = db.reference(db_path)
            
            if ref.get() is not None:
                ref.update({'status': 'normal'})
                self.get_logger().info(f"[DB Update] {db_path}/status -> 'normal' 업데이트 완료")
                return True
            else:
                self.get_logger().warn(f"[DB Update] 대상 나사({db_path})가 DB에 존재하지 않습니다.")
                return False
        except Exception as e:
            self.get_logger().error(f"[DB Update] 상태 업데이트 실패: {e}")
            return False

    def update_screw_status_to_defect(self, workspace_name, marker_key):
        """
        토크 검사 실패 후 Firebase DB에서 해당 나사의 status를 'defect'로 업데이트.
        예: workspace_name='Workspace 1', marker_key='1'
        -> /live_scan/workstations/workstation_01/screws/screw_00/status = 'defect'
        """
        try:
            workstation_id = self._workspace_to_id(workspace_name)
            screw_idx = int(marker_key) - 1
            screw_id = f"screw_{screw_idx:02d}"

            db_path = f'/live_scan/workstations/{workstation_id}/screws/{screw_id}'
            ref = db.reference(db_path)

            if ref.get() is not None:
                ref.update({'status': 'defect'})
                self.get_logger().warn(
                    f"[DB Update] {db_path}/status -> 'defect' 업데이트 완료 (토크 미달)"
                )
                return True
            else:
                self.get_logger().warn(f"[DB Update] 대상 나사({db_path})가 DB에 존재하지 않습니다.")
                return False
        except Exception as e:
            self.get_logger().error(f"[DB Update] 상태(defect) 업데이트 실패: {e}")
            return False

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
        
        # 워크스페이스 정보 추출
        import re
        ws_match = re.search(r'workspace\s*(\d+)', target_obj)
        is_workspace_command = False
        if ws_match:
            ws_num = ws_match.group(1)
            self.current_workspace = f"Workspace {ws_num}"
            self.get_logger().info(f"작업 워크스페이스를 '{self.current_workspace}'(으)로 설정합니다.")
            # target_obj에서 workspace 부분 제거하여 번호 추출에 방해되지 않도록 함
            target_obj = re.sub(r'workspace\s*\d+', '', target_obj).strip()
            is_workspace_command = True
        
        # --- 1. 전체 조사(all_check) 기능: 5방향 순차 이동 + /vision_inspect Trigger ---
        if "all_check" in target_obj:
            self.get_logger().info(
                "전체 조사(all_check) 모드 진입. "
                f"5방향 viewpoint를 순차적으로 이동하며 비전 검사를 요청합니다."
            )

            for view in VIEWPOINTS:
                self.get_logger().info(
                    f"[all_check] Viewpoint {view['id']} ({view['name']}) 으로 이동 중..."
                )
                movej(view["joints"], vel=VELOCITY, acc=ACC)
                mwait()
                time.sleep(CAMERA_STABILIZE_SEC)  # 카메라 안정화 대기

                # /vision_inspect Trigger 서비스 호출
                self.get_logger().info(
                    f"[all_check] Viewpoint {view['id']}: /vision_inspect 요청 중..."
                )
                vision_future = self.vision_client.call_async(self.vision_request)
                rclpy.spin_until_future_complete(self, vision_future)

                vision_result = vision_future.result()
                if vision_result is not None:
                    self.get_logger().info(
                        f"[all_check] Viewpoint {view['id']} 검사 결과: "
                        f"success={vision_result.success}, message='{vision_result.message}'"
                    )
                else:
                    self.get_logger().warn(
                        f"[all_check] Viewpoint {view['id']}: /vision_inspect 응답 없음."
                    )

            self.get_logger().info(
                "[all_check] 5방향 검사 완료. Firebase DB에서 모든 워크스페이스 나사 좌표를 조회합니다."
            )
            # 비전 노드가 DB를 업데이트할 시간을 추가로 확보
            time.sleep(2.0)

            success = self.fetch_all_workspaces_from_db()

            if success:
                ws_list = list(self.saved_positions.keys())
                self.get_logger().info(
                    f"DB 동기화 완료 ({ws_list}). 다음 명령을 대기하기 위해 홈으로 복귀합니다."
                )
                # ── workspace별 자세값 요약 로그 ──────────────────────────────
                self.get_logger().info("=" * 55)
                self.get_logger().info("[all_check 완료] workspace별 자세값 요약")
                self.get_logger().info("=" * 55)
                for ws_name, ws_positions in self.saved_positions.items():
                    if not ws_positions:
                        continue
                    # 첫 번째 나사의 rx, ry, rz를 대표 자세값으로 사용
                    first_coords = next(iter(ws_positions.values()))
                    rx, ry, rz = first_coords[3], first_coords[4], first_coords[5]
                    screw_ids = sorted(ws_positions.keys(), key=lambda k: int(k) if k.isdigit() else k)

                    # ZYZ Euler → 회전행렬 → 접근축(Z열) 복원 → 지배 축 판별
                    def _zyz_col_z(rx_, ry_, rz_):
                        a, b, g = np.radians(rx_), np.radians(ry_), np.radians(rz_)
                        ca, sa = np.cos(a), np.sin(a)
                        cb, sb = np.cos(b), np.sin(b)
                        cg, sg = np.cos(g), np.sin(g)
                        Rz1 = np.array([[ca,-sa,0],[sa,ca,0],[0,0,1]])
                        Ry  = np.array([[cb,0,sb],[0,1,0],[-sb,0,cb]])
                        Rz2 = np.array([[cg,-sg,0],[sg,cg,0],[0,0,1]])
                        R   = Rz1 @ Ry @ Rz2
                        return R[:, 2]  # TCP Z축 방향 (= 접근 방향)
                    app_vec = _zyz_col_z(rx, ry, rz)
                    _AX = ['x', 'y', 'z']
                    di  = int(np.argmax(np.abs(app_vec)))
                    ds  = '+' if app_vec[di] >= 0 else '-'
                    approach_axis = f"{ds}{_AX[di]}"

                    self.get_logger().info(
                        f"  [{ws_name}] 자세값: rx={rx:.2f}, ry={ry:.2f}, rz={rz:.2f} deg "
                        f"| 접근축(나사⊥): [{approach_axis}] "
                        f"| 나사 번호: {screw_ids} ({len(screw_ids)}개)"
                    )
                self.get_logger().info("=" * 55)
                # ─────────────────────────────────────────────────────────────
            else:
                self.get_logger().warn("DB 동기화에 실패했습니다.")

            movej(JHOME_POS, vel=VELOCITY, acc=ACC)
            mwait()
            return True

        # --- 2. 나사 토크 검사 기능: 'inspect' 또는 '검사' 키워드 ---
        is_inspect_command = "inspect" in target_obj or "검사" in target_obj

        # --- 2-1. 작업대 대기 이동 기능: 'standby' / '대기' / '작업대' 키워드 ---
        # 예: '1번 작업대 대기', 'workspace3 standby', '3번 작업대로 가'
        is_standby_command = (
            "standby" in target_obj
            or "대기" in target_obj
            or ("작업대" in target_obj and not is_inspect_command)
        )

        # --- 3. 개별 번호 호출: current_workspace의 나사 좌표로 이동 ---
        # "1", "2" 같은 숫자 또는 "pos1" 형태에서 숫자만 추출
        marker_key = "".join(filter(str.isdigit, target_obj))

        # ── 대기 명령은 나사 번호보다 우선 처리 ────────────────────────────────
        # '1번 작업대 대기' 같은 명령에서 '1'이 marker_key로 추출되더라도
        # standby 의도가 감지되면 아래 나사 분기로 진입하지 않고 바로 준비 분기로 점프
        if is_standby_command:
            # is_workspace_command 여부와 무관하게 준비 분기를 직접 수행
            self.get_logger().info(
                f"[대기] '{self.current_workspace}' 준비 위치로 이동합니다."
            )
            if self.current_workspace not in self.saved_positions or not self.saved_positions[self.current_workspace]:
                self.get_logger().info(f"[{self.current_workspace}]의 좌표가 메모리에 없습니다. DB에서 가져옵니다.")
                self.fetch_positions_from_db(self.current_workspace)

            ws_positions_sb = self.saved_positions.get(self.current_workspace, {})
            if not ws_positions_sb:
                self.get_logger().error(f"[{self.current_workspace}]에 등록된 나사 좌표가 없습니다. 작업을 중단합니다.")
                return False

            dom_idx_sb, orientation_sb = self.get_workspace_vertical_axis(self.current_workspace)
            if dom_idx_sb is None:
                self.get_logger().error("수직 성분을 계산할 수 없습니다.")
                return False

            pts_sb = np.array([pos[:3] for pos in ws_positions_sb.values()], dtype=float)
            other_indices_sb = [i for i in range(3) if i != dom_idx_sb]
            avg_coords_sb = pts_sb[:, other_indices_sb].mean(axis=0)
            max_vert_sb = np.max(pts_sb[:, dom_idx_sb]) + 200.0

            prep_pos_sb = [0.0, 0.0, 0.0, orientation_sb[0], orientation_sb[1], orientation_sb[2]]
            prep_pos_sb[other_indices_sb[0]] = avg_coords_sb[0]
            prep_pos_sb[other_indices_sb[1]] = avg_coords_sb[1]
            prep_pos_sb[dom_idx_sb] = max_vert_sb

            self.saved_prep_positions[self.current_workspace] = prep_pos_sb

            self.get_logger().info(
                f"[{self.current_workspace}] 대기 위치: "
                f"X={prep_pos_sb[0]:.2f}, Y={prep_pos_sb[1]:.2f}, Z={prep_pos_sb[2]:.2f} mm | "
                f"rx={prep_pos_sb[3]:.2f}, ry={prep_pos_sb[4]:.2f}, rz={prep_pos_sb[5]:.2f}"
            )
            self.get_logger().info(f"[{self.current_workspace}] 대기 위치로 이동 중...")
            movel(prep_pos_sb, vel=VELOCITY, acc=ACC)
            mwait()
            self.get_logger().info(f"[{self.current_workspace}] 대기 위치 도착. 무부하 토크 측정을 시작합니다.")

            # ── 대기 위치 도착 후 무부하 토크 자동 측정 ────────────────────────
            self.measure_noload_torque(self.current_workspace)
            self.get_logger().info(f"[{self.current_workspace}] 무부하 측정 완료. 다음 명령을 대기합니다.")
            return True

        elif is_inspect_command and marker_key:
            # ── 나사 토크 검사 (특정 번호 지정) ──────────────────────────────
            ws_positions = self.saved_positions.get(self.current_workspace, {})
            if not ws_positions:
                self.get_logger().info(f"[{self.current_workspace}] 좌표 로딩 시도...")
                self.fetch_positions_from_db(self.current_workspace)
                ws_positions = self.saved_positions.get(self.current_workspace, {})

            if marker_key in ws_positions:
                target_pos = ws_positions[marker_key]
                self.get_logger().info(
                    f"[{self.current_workspace}] 나사 번호 '{marker_key}' 토크 검사를 시작합니다."
                )
                passed = self.inspect_screw_torque(target_pos)

                if passed:
                    self.get_logger().info(
                        f"[검사] 나사 '{marker_key}' 토크 정상 → DB status = normal"
                    )
                    self.update_screw_status_to_normal(self.current_workspace, marker_key)
                else:
                    self.get_logger().warn(
                        f"[검사] 나사 '{marker_key}' 토크 미달 → DB status = defect"
                    )
                    self.update_screw_status_to_defect(self.current_workspace, marker_key)

                # 준비 위치 또는 홈으로 복귀
                prep_pos = self.saved_prep_positions.get(self.current_workspace)
                if prep_pos:
                    self.get_logger().info(f"검사 완료. [{self.current_workspace}] 준비 위치로 복귀합니다.")
                    movel(prep_pos, vel=VELOCITY, acc=ACC)
                    mwait()
                else:
                    self.get_logger().info("검사 완료. 홈(JHOME_POS) 위치로 복귀합니다.")
                    movej(JHOME_POS, vel=VELOCITY, acc=ACC)
                    mwait()
                return True
            else:
                loaded_ws = list(self.saved_positions.get(self.current_workspace, {}).keys())
                self.get_logger().warn(
                    f"[{self.current_workspace}] 나사 번호 '{marker_key}'를 찾을 수 없습니다. "
                    f"로드된 번호: {loaded_ws}. "
                    "먼저 'all_check'를 실행하거나 올바른 workspace를 지정하세요."
                )
                return False

        elif is_inspect_command and not marker_key:
            self.get_logger().warn(
                "[검사] 나사 번호를 말씀해 주세요. 예: 'workspace 3 검사 1번'"
            )
            return False

        elif marker_key:
            ws_positions = self.saved_positions.get(self.current_workspace, {})
            if not ws_positions:
                self.get_logger().info(f"[{self.current_workspace}] 좌표 로딩 시도...")
                self.fetch_positions_from_db(self.current_workspace)
                ws_positions = self.saved_positions.get(self.current_workspace, {})

            if marker_key in ws_positions:
                target_pos = ws_positions[marker_key]
                self.get_logger().info(
                    f"[{self.current_workspace}] 나사 번호 '{marker_key}' 좌표로 이동합니다."
                )
                self.grip_and_tighten(target_pos)
                
                # DB 상태 업데이트 ('normal')
                self.update_screw_status_to_normal(self.current_workspace, marker_key)
                
                # 준비 위치가 미리 구해져 있다면 준비 위치로 복귀, 없으면 홈으로 복귀
                prep_pos = self.saved_prep_positions.get(self.current_workspace)
                if prep_pos:
                    self.get_logger().info(f"나사 조이기 완료. 다시 [{self.current_workspace}] 준비 위치로 복귀합니다.")
                    movel(prep_pos, vel=VELOCITY, acc=ACC)
                    mwait()
                else:
                    self.get_logger().info("나사 조이기 완료. 홈(JHOME_POS) 위치로 복귀합니다.")
                    movej(JHOME_POS, vel=VELOCITY, acc=ACC)
                    mwait()
                return True
            else:
                loaded_ws = list(self.saved_positions.get(self.current_workspace, {}).keys())
                self.get_logger().warn(
                    f"[{self.current_workspace}] 나사 번호 '{marker_key}'를 찾을 수 없습니다. "
                    f"로드된 번호: {loaded_ws}. "
                    "먼저 'all_check'를 실행하거나 올바른 workspace를 지정하세요."
                )
                return False

        # --- 4. 워크스페이스 준비 위치로 이동 (대기) ---
        # 조건: workspace 키워드 포함 OR '대기'/'standby'/'작업대' 키워드 포함
        elif is_workspace_command or is_standby_command:
            self.get_logger().info(f"[{self.current_workspace}] 준비 위치로 이동 명령을 수행합니다.")
            
            # DB에서 해당 워크스페이스의 나사 데이터를 가져오지 않았다면 가져옴
            if self.current_workspace not in self.saved_positions or not self.saved_positions[self.current_workspace]:
                self.get_logger().info(f"[{self.current_workspace}]의 좌표가 메모리에 없습니다. DB에서 가져옵니다.")
                self.fetch_positions_from_db(self.current_workspace)
            
            ws_positions = self.saved_positions.get(self.current_workspace, {})
            if not ws_positions:
                self.get_logger().error(f"[{self.current_workspace}]에 등록된 나사 좌표가 없습니다. 작업을 중단합니다.")
                return False
            
            # 수직 성분 축(접근축)과 회전값 계산
            dom_idx, orientation = self.get_workspace_vertical_axis(self.current_workspace)
            if dom_idx is None:
                self.get_logger().error("수직 성분을 계산할 수 없습니다.")
                return False
            
            pts = np.array([pos[:3] for pos in ws_positions.values()], dtype=float)
            
            # 수직 성분 이외의 축들
            other_indices = [i for i in range(3) if i != dom_idx]
            avg_coords = pts[:, other_indices].mean(axis=0)
            max_vert = np.max(pts[:, dom_idx]) + 200.0
            
            # 준비 위치 설정 및 저장
            prep_pos = [0.0, 0.0, 0.0, orientation[0], orientation[1], orientation[2]]
            prep_pos[other_indices[0]] = avg_coords[0]
            prep_pos[other_indices[1]] = avg_coords[1]
            prep_pos[dom_idx] = max_vert
            
            self.saved_prep_positions[self.current_workspace] = prep_pos
            
            self.get_logger().info(
                f"[{self.current_workspace}] 준비 위치 설정 완료: "
                f"X={prep_pos[0]:.2f}, Y={prep_pos[1]:.2f}, Z={prep_pos[2]:.2f} mm | "
                f"rx={prep_pos[3]:.2f}, ry={prep_pos[4]:.2f}, rz={prep_pos[5]:.2f} (수직축 인덱스: {dom_idx})"
            )
            
            # 준비 위치로 이동
            self.get_logger().info(f"[{self.current_workspace}] 준비 위치로 이동 중...")
            movel(prep_pos, vel=VELOCITY, acc=ACC)
            mwait()
            self.get_logger().info(f"[{self.current_workspace}] 대기 위치 도착. 무부하 토크 측정을 시작합니다.")

            # ── 대기 위치 도착 후 무부하 토크 자동 측정 ────────────────────────
            self.measure_noload_torque(self.current_workspace)
            self.get_logger().info(f"[{self.current_workspace}] 준비 완료. 다음 나사 명령을 대기합니다.")
            return True

        # --- 5. 인식 불가 명령 ---
        else:
            self.get_logger().warn(
                f"'{target_obj}'에 해당하는 명령을 인식하지 못했습니다. "
                "'all_check', '[workspace N] [번호]번 나사 조여', 또는 "
                "'[workspace N] 검사 [번호]번' 형태로 말씀해 주세요."
            )
            return False

    def init_robot(self):
        movej(JHOME_POS, vel=VELOCITY, acc=ACC)
        mwait()

    def measure_noload_torque(self, workspace_name):
        """
        무부하(그리퍼 공중 상태) J6 1회전으로 중력/축 영향에 의한 최대 토크를 측정합니다.
        측정된 최대 음수 토크값에 20% 여유를 더해 workspace별 임계값으로 저장합니다.

        동작:
          1. 그리퍼 열기 (빈 상태 확보)
          2. J6 +360도 비동기 회전 시작 (vel=15)
          3. 50ms 주기로 J6 외력 토크 샘플링
          4. 최솟값(가장 큰 음수) × 1.2 를 workspace 임계값으로 저장

        Returns:
            float: 측정된 임계값(음수, 예: -0.6). 측정 실패 시 기본값 -0.5 반환.
        """
        from DSR_ROBOT2 import (
            get_external_torque,
        )

        DEFAULT_THRESHOLD = 0.5  # 측정 실패 시 기본값 (절댓값)
        NOLOAD_ROTATE_DEG = 180.0  # 무부하 측정용 회전 각도
        TORQUE_POLL_SEC   = 0.05   # 샘플링 주기

        self.get_logger().info(
            f"[무부하 토크] '{workspace_name}' 무부하 토크 측정 시작 "
            f"(J6 {NOLOAD_ROTATE_DEG:.0f}도 회전, 50ms 주기)"
        )

        try:
            # 1. 그리퍼 열기 (무부하 상태)
            self.get_logger().info("[무부하 토크] 그리퍼 열기")
            gripper.open_gripper()
            time.sleep(0.8)

            # 2. 현재 관절각 읽기 → J6 목표각 설정
            curr_joint   = get_current_posj()
            target_joint = list(curr_joint)
            initial_j6   = curr_joint[5]
            target_joint[5] = initial_j6 + NOLOAD_ROTATE_DEG

            self.get_logger().info(
                f"[무부하 토크] J6 회전: {initial_j6:.1f}° → {target_joint[5]:.1f}° (vel=15)"
            )

            # 3. 비동기 회전 시작 (저속)
            amovej(target_joint, vel=15, acc=10)

            # 4. 토크 샘플링
            torque_samples = []
            while True:
                ext_torque = get_external_torque()
                if ext_torque == -1 or not isinstance(ext_torque, list) or len(ext_torque) < 6:
                    time.sleep(TORQUE_POLL_SEC)
                    continue

                j6_val = ext_torque[5]
                torque_samples.append(j6_val)
                motion_state = check_motion()

                self.get_logger().info(
                    f"[무부하 토크]   J6: {j6_val:+.3f} N·m | "
                    f"모션: {'동작중' if motion_state else '정지'}"
                )

                if motion_state == 0:
                    break
                time.sleep(TORQUE_POLL_SEC)

            # 5. J6 원위치 복귀
            curr_after = get_current_posj()
            back_joint = list(curr_after)
            back_joint[5] = initial_j6
            movej(back_joint, vel=60, acc=40)
            mwait()

            if not torque_samples:
                self.get_logger().warn("[무부하 토크] 샘플 없음 → 기본값 사용")
                self.workspace_torque_threshold[workspace_name] = DEFAULT_THRESHOLD
                return DEFAULT_THRESHOLD

            # 6. 토크 절댓값의 최댓값 추출 후 20% 여유 적용
            abs_max = max(abs(t) for t in torque_samples)
            threshold = round(abs_max * 1.2, 3)

            self.workspace_torque_threshold[workspace_name] = threshold
            self.get_logger().info(
                f"[무부하 토크] ★ 측정 완료 ── "
                f"샘플 수: {len(torque_samples)}, "
                f"절댓값 최댓값: {abs_max:+.3f} N·m, "
                f"적용 임계값(절댓값×1.2): {threshold:+.3f} N·m"
            )
            return threshold

        except Exception as e:
            self.get_logger().error(f"[무부하 토크] 측정 중 오류: {e} → 기본값 사용")
            self.workspace_torque_threshold[workspace_name] = DEFAULT_THRESHOLD
            return DEFAULT_THRESHOLD

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
        # 무부하 측정에서 구한 절댓값 기반 임계값 사용, 없으면 0.5
        base_threshold = self.workspace_torque_threshold.get(
            self.current_workspace, 0.5
        )
        # 나사 체결 토크의 절댓값은 최소 0.5 이상이 되도록 고정
        J6_TORQUE_THRESHOLD = max(base_threshold, 0.5)

        self.get_logger().info(
            f"[grip] 적용 임계값: {J6_TORQUE_THRESHOLD:+.3f} N·m "
            f"('{self.current_workspace}' 측정: {base_threshold:+.3f}, 최소 0.5 고정)"
        )
        # 한 파지 사이클에서 최대 회전 각도 (도)
        MAX_TIGHTEN_DEG     = 150.0
        # 토크 감시 주기 (초)
        TORQUE_POLL_SEC     = 0.05
        # 최대 파지 반복 횟수 (토크 미달 시 잡고→돌리고→놓고 반복 한계)
        MAX_CYCLE           = 10
        # ─────────────────────────────────────────────────────────────────────

        # ── 접근 방향 벡터 계산 (ZYZ Euler → R → TCP Z열) ──────────────────
        target_pos = list(target_pos)
        _rx, _ry, _rz = target_pos[3], target_pos[4], target_pos[5]
        _a, _b, _g = np.radians(_rx), np.radians(_ry), np.radians(_rz)
        _ca, _sa = np.cos(_a), np.sin(_a)
        _cb, _sb = np.cos(_b), np.sin(_b)
        _cg, _sg = np.cos(_g), np.sin(_g)
        _Rz1 = np.array([[_ca, -_sa, 0], [_sa, _ca, 0], [0, 0, 1]])
        _Ry  = np.array([[_cb,    0, _sb], [  0, 1,    0], [-_sb, 0, _cb]])
        _Rz2 = np.array([[_cg, -_sg, 0], [_sg, _cg, 0], [0, 0, 1]])
        _approach_vec = (_Rz1 @ _Ry @ _Rz2)[:, 2]  # TCP Z축 = 접근 방향

        _AX = ['x', 'y', 'z']
        _di = int(np.argmax(np.abs(_approach_vec)))
        _ds = '+' if _approach_vec[_di] >= 0 else '-'
        approach_axis = f"{_ds}{_AX[_di]}"

        # 오프셋 적용 (접근축 기준)
        offset_x, offset_y, offset_z = 0.0, 0.0, 0.0
        if approach_axis in AXIS_OFFSETS:
            axis_offsets = AXIS_OFFSETS[approach_axis]
            offset_x = axis_offsets.get("x", 0.0)
            offset_y = axis_offsets.get("y", 0.0)
            offset_z = axis_offsets.get("z", 0.0)

        target_pos[0] += offset_x
        target_pos[1] += offset_y
        target_pos[2] += offset_z
        self.get_logger().info(
            f"[grip] 오프셋 적용 [접근축 {approach_axis}]: "
            f"X{offset_x:+.1f}, Y{offset_y:+.1f}, Z{offset_z:+.1f} mm "
            f"-> 이동 목표: {target_pos[:3]}"
        )

        # 안전 위치 = 나사 위치에서 접근 방향 반대로 approach_height만큼 후퇴
        # (예) 접근=[-z]: z += height  /  접근=[-y]: y += height
        target_pos_up = list(target_pos)
        target_pos_up[0] -= approach_height * _approach_vec[0]
        target_pos_up[1] -= approach_height * _approach_vec[1]
        target_pos_up[2] -= approach_height * _approach_vec[2]
        # ─────────────────────────────────────────────────────────────────────

        # 1. 안전 위치로 이동
        self.get_logger().info(
            f"[grip] 1. 접근축=[{_ds}{_AX[_di]}], "
            f"안전 후퇴 위치({target_pos_up[:3]})로 이동 중..."
        )
        movel(target_pos_up, vel=VELOCITY, acc=ACC)
        mwait()
        time.sleep(1.0)

        # 2. 그리퍼 열기
        self.get_logger().info("[grip] 2. 그리퍼 열기")
        gripper.open_gripper()
        time.sleep(1.0)

        # 3. 나사 위치로 접근 (접근 축 방향으로 이동)
        self.get_logger().info(
            f"[grip] 3. 나사 위치 {target_pos[:3]} 으로 접근 (축=[{_ds}{_AX[_di]}])..."
        )
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
        current_target_pos = list(target_pos)

        for cycle in range(MAX_CYCLE):
            # ── 나사 삽입 깊이 보상 (헛잡음 방지) ──────────────────────────
            # 2 사이클마다 접근 방향 축으로 1.0mm씩 전진하여 나사 깊이를 따라감
            if cycle > 0 and cycle % 2 == 0:
                down_step = 1.0  # mm 단위
                self.get_logger().info(
                    f"[grip]   [사이클 {cycle+1}] 나사 깊이 보상: "
                    f"접근축=[{_ds}{_AX[_di]}] 방향으로 {down_step}mm 전진"
                )
                # 접근 방향(_approach_vec)으로 down_step만큼 추가 전진
                current_target_pos[0] += down_step * _approach_vec[0]
                current_target_pos[1] += down_step * _approach_vec[1]
                current_target_pos[2] += down_step * _approach_vec[2]
                movel(current_target_pos, vel=20, acc=20)
                mwait()
                time.sleep(0.5)
            # ─────────────────────────────────────────────────────────────

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
                    f"(임계: -{J6_TORQUE_THRESHOLD} N·m) | 모션: {'동작중' if motion_state else '정지'}"
                )

                # ── 나사 꽉 조여짐 감지 (음수 방향만 판별) ─────────────────────
                if j6_torque <= -J6_TORQUE_THRESHOLD:
                    cnt +=1
                    if cnt >= 5:
                        self.get_logger().info(
                            f"[grip]   ★ 나사 조임 완료! "
                            f"J6 토크 {j6_torque:+.3f} N·m ≤ -{J6_TORQUE_THRESHOLD} N·m"
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
                        f"({j6_torque:+.3f} N·m > -{J6_TORQUE_THRESHOLD} N·m) → 다음 사이클"
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
            movej(back_joint, vel=80, acc=60)  # 복귀는 빠르게
            mwait()
            time.sleep(0.3)

        if not tightened:
            self.get_logger().warn(
                f"[grip] ⚠ 최대 사이클({MAX_CYCLE}회) 도달 후에도 나사 조임 토크 미달. "
                f"나사 상태를 확인하세요."
            )

        # 5. 안전 위치로 복귀 (접근 방향 반대로 후퇴)
        self.get_logger().info(
            f"[grip] 5. 안전 위치로 복귀 (접근축=[{_ds}{_AX[_di]}] 반대 방향, {target_pos_up[:3]})"
        )
        movel(target_pos_up, vel=VELOCITY, acc=ACC)
        mwait()
        time.sleep(0.5)

    def inspect_screw_torque(self, target_pos, approach_height=150.0):
        """
        나사 토크 검사 시퀀스.
        나사 위치로 접근 후 J6 축을 180도 1회 회전시키며 J6 외력 토크를 감시합니다.
        기준 토크값(-0.5 N·m)을 초과하지 않으면 나사가 풀려 있다고 판단하고 False 반환.
        기준 토크값을 초과하면 정상 체결된 것으로 판단하고 True 반환.

        Returns:
            True  - 토크 정상 (나사 정상 체결 상태)
            False - 토크 미달 (나사 불량/풀림 상태) → DB status를 'defect'로 변경 필요
        """
        from DSR_ROBOT2 import (
            get_external_torque,
            drl_script_stop,
            DR_HOLD,
        )

        # ── 검사 파라미터 ─────────────────────────────────────────────────────
        # workspace별 무부하 측정 임계값(절댓값) 사용, 없으면 기본값 0.5 사용
        base_threshold = self.workspace_torque_threshold.get(self.current_workspace, 0.5)
        # 나사 검사 토크의 절댓값은 최소 0.5 이상이 되도록 고정
        effective_threshold = max(base_threshold, 0.5)
        INSPECT_TORQUE_THRESHOLD = -effective_threshold   # [N·m] 기준 토크값 (음수 방향, 이 값 미만이면 정상)

        self.get_logger().info(
            f"[inspect] 적용 임계값: {INSPECT_TORQUE_THRESHOLD:+.3f} N·m "
            f"('{self.current_workspace}' 측정: {base_threshold:+.3f}, 최소 0.5 고정)"
        )
        INSPECT_ROTATE_DEG       = 180.0  # [deg] 검사용 회전 각도 (1회)
        TORQUE_POLL_SEC          = 0.05   # [s]   토크 감시 주기
        # ─────────────────────────────────────────────────────────────────────

        # ── 접근 방향 벡터 계산 (ZYZ Euler → R → TCP Z열) ──────────────────
        target_pos = list(target_pos)
        _rx, _ry, _rz = target_pos[3], target_pos[4], target_pos[5]
        _a, _b, _g = np.radians(_rx), np.radians(_ry), np.radians(_rz)
        _ca, _sa = np.cos(_a), np.sin(_a)
        _cb, _sb = np.cos(_b), np.sin(_b)
        _cg, _sg = np.cos(_g), np.sin(_g)
        _Rz1 = np.array([[_ca, -_sa, 0], [_sa, _ca, 0], [0, 0, 1]])
        _Ry  = np.array([[_cb,    0, _sb], [  0, 1,    0], [-_sb, 0, _cb]])
        _Rz2 = np.array([[_cg, -_sg, 0], [_sg, _cg, 0], [0, 0, 1]])
        _approach_vec = (_Rz1 @ _Ry @ _Rz2)[:, 2]

        _AX = ['x', 'y', 'z']
        _di = int(np.argmax(np.abs(_approach_vec)))
        _ds = '+' if _approach_vec[_di] >= 0 else '-'
        approach_axis = f"{_ds}{_AX[_di]}"

        offset_x, offset_y, offset_z = 0.0, 0.0, 0.0
        if approach_axis in AXIS_OFFSETS:
            axis_offsets = AXIS_OFFSETS[approach_axis]
            offset_x = axis_offsets.get("x", 0.0)
            offset_y = axis_offsets.get("y", 0.0)
            offset_z = axis_offsets.get("z", 0.0)

        target_pos[0] += offset_x
        target_pos[1] += offset_y
        target_pos[2] += offset_z

        self.get_logger().info(
            f"[inspect] 오프셋 적용 [접근축 {approach_axis}]: "
            f"X{offset_x:+.1f}, Y{offset_y:+.1f}, Z{offset_z:+.1f} mm -> 이동 목표: {target_pos[:3]}"
        )

        # 안전 후퇴 위치
        target_pos_up = list(target_pos)
        target_pos_up[0] -= approach_height * _approach_vec[0]
        target_pos_up[1] -= approach_height * _approach_vec[1]
        target_pos_up[2] -= approach_height * _approach_vec[2]

        # 1. 안전 위치로 이동
        self.get_logger().info(
            f"[inspect] 1. 접근축=[{_ds}{_AX[_di]}], "
            f"안전 후퇴 위치({target_pos_up[:3]})로 이동 중..."
        )
        movel(target_pos_up, vel=VELOCITY, acc=ACC)
        mwait()
        time.sleep(1.0)

        # 2. 그리퍼 열기
        self.get_logger().info("[inspect] 2. 그리퍼 열기")
        gripper.open_gripper()
        time.sleep(1.0)

        # 3. 나사 위치로 접근
        self.get_logger().info(
            f"[inspect] 3. 나사 위치 {target_pos[:3]} 으로 접근 (축=[{_ds}{_AX[_di]}])..."
        )
        movel(target_pos, vel=40, acc=25)
        mwait()
        time.sleep(2.0)

        # 4. 그리퍼 닫기 (파지)
        self.get_logger().info("[inspect] 4. 그리퍼 닫기 (파지)")
        gripper.close_gripper()
        time.sleep(2.0)

        # 5. 180도 비동기 회전 + J6 토크 감시
        self.get_logger().info(
            f"[inspect] 5. 검사용 180도 회전 시작 "
            f"(기준 토크: {INSPECT_TORQUE_THRESHOLD} N·m, 이 값을 초과 시 정상 판정)"
        )
        curr_joint   = get_current_posj()
        target_joint = list(curr_joint)
        initial_j6   = curr_joint[5]
        target_joint[5] = initial_j6 + INSPECT_ROTATE_DEG

        self.get_logger().info(
            f"[inspect]   J6: {initial_j6:.1f}° → {target_joint[5]:.1f}° (vel=10)"
        )
        amovej(target_joint, vel=10, acc=10)

        # ── 토크 실시간 감시 ─────────────────────────────────────────────────
        torque_passed = False
        peak_torque   = 0.0

        while True:
            ext_torque = get_external_torque()

            if ext_torque == -1 or not isinstance(ext_torque, list) or len(ext_torque) < 6:
                self.get_logger().warn("[inspect]   외력 토크 읽기 실패, 재시도...")
                time.sleep(TORQUE_POLL_SEC)
                continue

            j6_torque    = ext_torque[5]
            motion_state = check_motion()  # 0: 정지, 1: 동작 중

            # 피크 토크 갱신 (가장 큰 음수값 추적)
            if j6_torque < peak_torque:
                peak_torque = j6_torque

            self.get_logger().info(
                f"[inspect]   J6 외력 토크: {j6_torque:+.3f} N·m "
                f"(기준: {INSPECT_TORQUE_THRESHOLD} N·m) | 피크: {peak_torque:+.3f} N·m "
                f"| 모션: {'동작중' if motion_state else '정지'}"
            )

            # 기준 토크 초과 → 정상 체결 판정, 모션 중단
            if j6_torque < INSPECT_TORQUE_THRESHOLD:
                self.get_logger().info(
                    f"[inspect]   ★ 토크 기준 초과! "
                    f"J6 토크 {j6_torque:+.3f} N·m < {INSPECT_TORQUE_THRESHOLD} N·m → 정상 판정"
                )
                drl_script_stop(DR_HOLD)
                mwait()
                torque_passed = True
                break

            # 180도 회전 완료 (토크 미달)
            if motion_state == 0:
                self.get_logger().warn(
                    f"[inspect]   180도 회전 완료, 토크 기준 미달 "
                    f"(피크: {peak_torque:+.3f} N·m, 기준: {INSPECT_TORQUE_THRESHOLD} N·m) "
                    f"→ 나사 불량(defect) 판정"
                )
                break

            time.sleep(TORQUE_POLL_SEC)

        # 6. 그리퍼 열기 → J6 원위치 복귀
        self.get_logger().info("[inspect] 6. 그리퍼 열기 → J6 원위치 복귀")
        gripper.open_gripper()
        time.sleep(0.5)

        curr_joint_after = get_current_posj()
        back_joint = list(curr_joint_after)
        back_joint[5] = initial_j6
        movej(back_joint, vel=40, acc=30)
        mwait()
        time.sleep(0.3)

        # 7. 안전 위치로 복귀
        self.get_logger().info(
            f"[inspect] 7. 안전 위치로 복귀 "
            f"(접근축=[{_ds}{_AX[_di]}] 반대 방향, {target_pos_up[:3]})"
        )
        movel(target_pos_up, vel=VELOCITY, acc=ACC)
        mwait()
        time.sleep(0.5)

        result_str = "정상(normal)" if torque_passed else "불량(defect)"
        self.get_logger().info(
            f"[inspect] 검사 완료 → 판정: {result_str} "
            f"| 피크 토크: {peak_torque:+.3f} N·m | 기준: {INSPECT_TORQUE_THRESHOLD} N·m"
        )
        return torque_passed


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
