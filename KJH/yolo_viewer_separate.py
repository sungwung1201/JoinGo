#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YOLO RealSense viewer node for 협동2.

이 파일은 로봇 모션 코드와 분리해서 실행하는 전용 영상/YOLO 확인 노드입니다.
이렇게 분리하는 이유:
- Doosan DSR_ROBOT2 모션 함수는 내부적으로 rclpy service/wait를 사용합니다.
- 같은 프로세스 안에서 영상 구독 rclpy.spin을 별도 스레드로 돌리면
  wait set index too big 에러가 발생할 수 있습니다.
- 따라서 모션 노드와 영상 노드를 별도 프로세스로 분리하는 방식이 가장 안정적입니다.

실행:
    ros2 run robot_control yolo_viewer

종료:
    OpenCV 창에서 q 키 또는 Ctrl+C
"""

import os
import time
from pathlib import Path

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
from ultralytics import YOLO


# =========================
# 설정값
# =========================

PACKAGE_NAME = "robot_control"
MODEL_FILENAME = "hyupdong2_yolo11x_realtest_corrected_best.pt"

COLOR_TOPIC = "/camera/camera/color/image_raw"

YOLO_IMGSZ = 960
YOLO_CONF = 0.25

WINDOW_NAME = "YOLO Screw Viewer"

# 모델의 raw label이 good/ng이더라도 화면에서는 screw 상태로 표시
MERGE_LABEL_TO_SCREW = True


def find_model_path() -> str:
    candidates = []

    try:
        package_path = get_package_share_directory(PACKAGE_NAME)
        candidates.append(Path(package_path) / "resource" / MODEL_FILENAME)
    except Exception:
        pass

    candidates.extend([
        Path.home() / "cobot_ws/src/cobot2_ws/robot_control/resource" / MODEL_FILENAME,
        Path.home() / "cobot_ws/src/robot_control/resource" / MODEL_FILENAME,
        Path.cwd() / MODEL_FILENAME,
    ])

    for p in candidates:
        if p.exists():
            return str(p)

    msg = "YOLO model not found. Checked:\n" + "\n".join(str(p) for p in candidates)
    raise FileNotFoundError(msg)


def normalize_status(raw_label: str) -> str:
    label = str(raw_label).lower()

    if "good" in label or "ok" in label or "pass" in label or "normal" in label:
        return "GOOD"

    if "ng" in label or "bad" in label or "fail" in label or "defect" in label:
        return "NG"

    return "UNKNOWN"


def display_label(raw_label: str, conf: float) -> str:
    status = normalize_status(raw_label)

    if MERGE_LABEL_TO_SCREW:
        if status == "UNKNOWN":
            return f"screw/{raw_label} {conf:.2f}"
        return f"screw-{status} {conf:.2f}"

    return f"{raw_label} {conf:.2f}"


class YoloViewerNode(Node):
    def __init__(self):
        super().__init__("yolo_viewer_node")

        self.bridge = CvBridge()
        self.frame_count = 0
        self.last_log_time = time.time()

        model_path = find_model_path()
        self.get_logger().info(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.get_logger().info(f"YOLO model names: {self.model.names}")

        self.sub = self.create_subscription(
            Image,
            COLOR_TOPIC,
            self.image_callback,
            10
        )

        self.get_logger().info(f"Subscribed color topic: {COLOR_TOPIC}")
        self.get_logger().info("OpenCV viewer is running. Press 'q' in the image window to quit.")

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().warn(f"cv_bridge conversion failed: {e}")
            return

        try:
            results = self.model.predict(
                source=frame,
                imgsz=YOLO_IMGSZ,
                conf=YOLO_CONF,
                verbose=False
            )
        except Exception as e:
            self.get_logger().warn(f"YOLO predict failed: {e}")
            return

        vis = frame.copy()
        det_count = 0

        if results and results[0].boxes is not None:
            result = results[0]
            names = result.names

            for box in result.boxes:
                cls_id = int(box.cls.item())
                raw_label = names.get(cls_id, str(cls_id))
                conf = float(box.conf.item())

                x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                label_text = display_label(raw_label, conf)

                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)

                text_y = max(25, y1 - 8)
                cv2.putText(
                    vis,
                    label_text,
                    (x1, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )

                det_count += 1

        self.frame_count += 1
        now = time.time()
        if now - self.last_log_time >= 1.0:
            self.get_logger().info(f"frame={self.frame_count}, detections={det_count}")
            self.last_log_time = now

        cv2.putText(
            vis,
            f"detections: {det_count} | q: quit",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.imshow(WINDOW_NAME, vis)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self.get_logger().warn("q pressed. Shutting down viewer.")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = YoloViewerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        cv2.destroyAllWindows()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
