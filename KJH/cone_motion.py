#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import math
import numpy as np
from scipy.spatial.transform import Rotation

import rclpy
import DR_init


# ============================================================
# Doosan Robot 설정
# ============================================================

ROBOT_ID = "dsr01"
ROBOT_MODEL = "m0609"
ROBOT_TOOL = "Tool Weight"
ROBOT_TCP = "GripperDA_v1"

DR_init.__dsr__id = ROBOT_ID
DR_init.__dsr__model = ROBOT_MODEL

rclpy.init()
dsr_node = rclpy.create_node("cone_motion_quadrant_node", namespace=ROBOT_ID)
DR_init.__dsr__node = dsr_node

try:
    from DSR_ROBOT2 import movel, movej, mwait

    try:
        from DSR_ROBOT2 import release_force, release_compliance_ctrl
        HAS_RELEASE = True
    except Exception:
        HAS_RELEASE = False

except ImportError as e:
    print(f"Error importing DSR_ROBOT2: {e}")
    sys.exit(1)


# ============================================================
# 1사분면 원호 탐색 설정
# ============================================================

# 꼭짓점 좌표, base 좌표계 기준 mm
APEX_X = 420.864
APEX_Y = 53.716
APEX_Z = 0.0

# 이번 테스트는 z=200 고정
Z_LEVEL = 150.0

# z=200에서 원 반지름
RADIUS = 110.0

# 1사분면만 회전: 0도 -> 90도
START_ANGLE_DEG = -60.0
END_ANGLE_DEG = 180.0

# 0~90도를 몇 점으로 나눌지
# 10이면 0,10,20,...,90도 느낌
POINTS = 10

# TCP local Z축 방향 설정
# +1: TCP +Z축이 꼭짓점을 향함
# -1: TCP -Z축이 꼭짓점을 향함
# 자세가 뒤집히거나 unreachable 뜨면 -1로 바꿔보세요.
TCP_Z_SIGN = 1

# TCP local Z축 기준 roll offset
# 일단 태초마을 버전이므로 0으로 시작
TCP_LOCAL_Z_ROLL_OFFSET_DEG = 0.0

# 속도/가속도
VEL = 30
ACC = 10

# 각 지점 도착 후 대기
POINT_WAIT_SEC = 0.2

# 시작 전에 홈으로 보낼지
USE_HOME_BEFORE_START = True
JHOME = [0, 0, 90, 0, 90, 0]

# z축 방향으로 꼭짓점에 더 가까워지는 거리
APPROACH_TO_APEX_MM = 80.0


# ============================================================
# 유틸 함수
# ============================================================
def initialize_robot_setting():
    from DSR_ROBOT2 import set_tool, set_tcp, get_tool, get_tcp

    print("[INIT] set tool/tcp")
    set_tool(ROBOT_TOOL)
    set_tcp(ROBOT_TCP)

    print("[INIT] current tool:", get_tool())
    print("[INIT] current tcp :", get_tcp())

def normalize(v):
    norm = np.linalg.norm(v)
    if norm < 1e-9:
        raise ValueError("zero vector cannot be normalized")
    return v / norm


def release_modes():
    if not HAS_RELEASE:
        return

    try:
        release_force()
    except Exception:
        pass

    try:
        release_compliance_ctrl()
    except Exception:
        pass


def rotation_matrix_tcp_z_to_apex(tcp_pos):
    """
    현재 TCP 위치에서 TCP local Z축이 꼭짓점을 향하도록 회전행렬 생성.
    """

    tcp_pos = np.array(tcp_pos, dtype=float)
    apex_pos = np.array([APEX_X, APEX_Y, APEX_Z], dtype=float)

    direction_to_apex = normalize(apex_pos - tcp_pos)

    # TCP +Z 또는 -Z가 꼭짓점을 향하게 설정
    z_axis = TCP_Z_SIGN * direction_to_apex

    # 기준 벡터
    ref = np.array([0.0, 0.0, 1.0])

    # z_axis와 ref가 거의 평행하면 다른 기준 사용
    if abs(np.dot(z_axis, ref)) > 0.95:
        ref = np.array([1.0, 0.0, 0.0])

    # 오른손 좌표계 구성
    x_axis = normalize(np.cross(ref, z_axis))
    y_axis = normalize(np.cross(z_axis, x_axis))

    R = np.column_stack((x_axis, y_axis, z_axis))

    # TCP local Z축 기준 roll offset
    if abs(TCP_LOCAL_Z_ROLL_OFFSET_DEG) > 1e-9:
        R_offset = Rotation.from_euler(
            "Z",
            TCP_LOCAL_Z_ROLL_OFFSET_DEG,
            degrees=True
        ).as_matrix()
        R = R @ R_offset

    return R


def pose_from_xy_angle(angle_deg):
    """
    apex 기준 원호 위의 pose 생성 후,
    TCP에서 꼭짓점 방향으로 APPROACH_TO_APEX_MM 만큼 더 근접시킨 pose 생성.
    """

    theta = math.radians(angle_deg)

    # 1. 원호 위의 기준 TCP 위치
    x = APEX_X + RADIUS * math.cos(theta)
    y = APEX_Y + RADIUS * math.sin(theta)
    z = Z_LEVEL

    tcp_pos = np.array([x, y, z], dtype=float)
    apex_pos = np.array([APEX_X, APEX_Y, APEX_Z], dtype=float)

    # 2. TCP에서 꼭짓점으로 향하는 방향 벡터
    direction_to_apex = apex_pos - tcp_pos
    direction_to_apex = direction_to_apex / np.linalg.norm(direction_to_apex)

    # 3. 꼭짓점 방향으로 60mm 더 근접
    tcp_pos = tcp_pos + direction_to_apex * APPROACH_TO_APEX_MM

    x, y, z = tcp_pos.tolist()

    # 4. 이동된 위치 기준으로 다시 꼭짓점을 바라보는 자세 계산
    R = rotation_matrix_tcp_z_to_apex([x, y, z])

    rx, ry, rz = Rotation.from_matrix(R).as_euler("ZYZ", degrees=True)

    return [
        float(x),
        float(y),
        float(z),
        float(rx),
        float(ry),
        float(rz),
    ]


def generate_quadrant_poses():
    poses = []

    if POINTS < 2:
        angles = [START_ANGLE_DEG]
    else:
        angles = [
            START_ANGLE_DEG + (END_ANGLE_DEG - START_ANGLE_DEG) * i / (POINTS - 1)
            for i in range(POINTS)
        ]

    print("========== Generated Quadrant Poses ==========")

    for idx, angle in enumerate(angles, start=1):
        pose = pose_from_xy_angle(angle)
        poses.append(pose)

        print(
            f"[{idx:02d}/{len(angles)}] "
            f"angle={angle:.1f} deg | "
            f"x={pose[0]:.3f}, y={pose[1]:.3f}, z={pose[2]:.3f}, "
            f"rx={pose[3]:.3f}, ry={pose[4]:.3f}, rz={pose[5]:.3f}"
        )

    return poses


def move_quadrant_path():
    initialize_robot_setting()
    print("========== 1st Quadrant Cone Motion Start ==========")
    print(f"APEX = [{APEX_X:.3f}, {APEX_Y:.3f}, {APEX_Z:.3f}]")
    print(f"Z_LEVEL = {Z_LEVEL}")
    print(f"RADIUS = {RADIUS}")
    print(f"ANGLE = {START_ANGLE_DEG} -> {END_ANGLE_DEG}")
    print(f"POINTS = {POINTS}")
    print(f"TCP_Z_SIGN = {TCP_Z_SIGN}")
    print(f"TCP_LOCAL_Z_ROLL_OFFSET_DEG = {TCP_LOCAL_Z_ROLL_OFFSET_DEG}")

    release_modes()

    if USE_HOME_BEFORE_START:
        print("[MOVE] Go home")
        movej(JHOME, vel=VEL, acc=ACC)
        mwait()

    poses = generate_quadrant_poses()

    print(f"\nGenerated poses: {len(poses)}")
    print("========== Motion Execute ==========")

    for idx, pose in enumerate(poses, start=1):
        print(
            f"[MOVE {idx:02d}/{len(poses)}] "
            f"x={pose[0]:.3f}, y={pose[1]:.3f}, z={pose[2]:.3f}, "
            f"rx={pose[3]:.3f}, ry={pose[4]:.3f}, rz={pose[5]:.3f}"
        )

        try:
            movel(pose, vel=VEL, acc=ACC)
            mwait()
        except Exception as e:
            print(f"[ERROR] move failed at pose #{idx}: {e}")
            break

        if POINT_WAIT_SEC > 0:
            time.sleep(POINT_WAIT_SEC)

    print("========== 1st Cone Motion Done ==========")


def main():
    try:
        move_quadrant_path()
    except KeyboardInterrupt:
        print("사용자 중단")
    finally:
        dsr_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()