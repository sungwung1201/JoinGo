# ros2 service call /get_keyword std_srvs/srv/Trigger "{}"

import os
import rclpy
import pyaudio
from rclpy.node import Node

from ament_index_python.packages import get_package_share_directory
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate  # d2 이거를 langchain_core로 바꿈
# from langchain.chains import LLMChain

from std_srvs.srv import Trigger
from voice_ppv.MicController import MicController, MicConfig

from voice_ppv.wakeup_word import WakeupWord
from voice_ppv.stt import STT

############ Package Path & Environment Setting ############

#----------------------------------------------------------------
# current_dir = os.getcwd()
# package_path = get_package_share_directory("pick_and_place_voice")

# env_path = "/home/rokey/cobot_ws/src/cobot2_ws/pick_and_place_voice/resource/.env"
# load_dotenv(dotenv_path=env_path)
# is_load = load_dotenv(dotenv_path=os.path.join(f"{package_path}/resource/.env"))
# openai_api_key = os.getenv("OPENAI_API_KEY")
#-----------------------------------------------------------------

PACKAGE_NAME = "voice_ppv"
PACKAGE_PATH = get_package_share_directory(PACKAGE_NAME)
RESOURCE_PATH = os.path.join(PACKAGE_PATH, "resource")
# ENV_PATH = os.path.join(RESOURCE_PATH, ".env")
ENV_PATH = "/home/eycho/cobot_ws/src/voice_ppv/resource/.env"
load_dotenv(dotenv_path=ENV_PATH)
openai_api_key = os.getenv("OPENAI_API_KEY")

############ AI Processor ############
# class AIProcessor:
#     def __init__(self):



############ GetKeyword Node ############
class GetKeyword(Node):
    def __init__(self):

        print(PACKAGE_PATH, RESOURCE_PATH, ENV_PATH)

        self.llm = ChatOpenAI(
            model="gpt-4o", temperature=0.5, openai_api_key=openai_api_key
        )

        prompt_content = """
       당신은 사용자의 문장에서 로봇이 수행할 '명령(작업)'과 대상이 되는 '위치(나사 번호)'를 추출해야 합니다.

            <목표>
            - 문장에서 다음 리스트에 포함된 명령을 최대한 정확히 추출하세요.
            - 명령을 수행할 대상 위치(나사 번호)도 함께 추출하세요.

            <명령 리스트>
            - all_check        : 전체 조사. 로봇이 5방향으로 이동하며 모든 작업대의 나사를 카메라로 인식하고 좌표를 DB에 저장.
                                 예: "전체 조사해", "다 훑어봐", "전부 확인해"
            - prepare_workspace: 특정 workspace(작업대)로 이동해서 작업 준비 자세를 잡는 명령. 반드시 workspace 번호와 함께 사용.
                                 예: "workspace 3 준비해", "2번 작업대 준비"
            - torque_check     : 특정 나사를 드라이버로 잡고 조이는(체결) 명령. 나사 번호와 함께 사용.
                                 예: "3번 나사 조여봐", "단단히 고정해", "1번 나사 체결해"
            - inspect_check    : 특정 나사를 드라이버로 잡고 180도 회전하여 토크를 측정하는 검사 명령.
                                 토크가 기준값(-0.5 N*m)에 미달하면 DB의 나사 status를 defect로 변경함.
                                 예: "1번 나사 검사해", "3번 나사 토크 확인해", "2번 나사 불량 검사"

            <위치(나사 번호) 리스트>
            - pos1, pos2, pos3, pos4, ... (n번 나사는 posn으로 변환)
            - torque_check, inspect_check 명령에는 반드시 나사 번호(위치)가 필요합니다.
            - all_check, prepare_workspace 명령에는 나사 번호가 필요 없습니다.

            <출력 형식>
            - 다음 형식을 반드시 따르세요: [명령1 명령2 ... / 위치1 위치2 ... / 워크스페이스]
            - 명령과 위치는 각각 공백으로 구분합니다.
            - 워크스페이스는 "workspace1", "workspace2", "workspace3" 등과 같이 공백 없이 출력합니다.
            - 명령, 위치, 워크스페이스가 없으면 해당 항목의 '/' 앞뒤를 공백 없이 비웁니다.
            - 다수의 명령과 위치가 동시에 등장할 경우 각각에 대해 정확히 매칭하여 순서대로 출력하세요.

            <특수 규칙>
            - 명확한 명령 명칭이 없지만 문맥상 유추 가능한 경우 리스트 내 항목으로 최대한 추론해 반환하세요.
              예: "조여봐", "단단히 고정해", "체결해" → torque_check
              예: "검사해", "불량 확인해", "토크 확인해", "제대로 조여진 거 맞아?" → inspect_check
              예: "다 검사해", "전체 훑어봐", "전부 인식해" → all_check
              예: "준비해", "작업 자세 잡아" (workspace 번호 포함 시) → prepare_workspace
            - "1번 나사", "첫 번째 나사" 등 숫자로 지칭되는 위치는 모두 pos1, pos2 형식으로 변환하세요.
            - torque_check와 inspect_check의 구분:
              * torque_check  : 나사를 '조이는' 행위 (체결, 고정, 조임)
              * inspect_check : 나사가 제대로 조여져 있는지 '확인/검사'하는 행위 (검사, 확인, 불량 체크)

            <출력 예시>
            - 입력: "모두 검사 해줘"
            출력: all_check / /

            - 입력: "workspace 3 작업 준비해"
            출력: prepare_workspace / / workspace3

            - 입력: "workspace 2 준비"
            출력: prepare_workspace / / workspace2

            - 입력: "3번 나사 꽉 조여봐"
            출력: torque_check / pos3 /

            - 입력: "workspace 2에서 2번이랑 3번 나사 조여줘"
            출력: torque_check torque_check / pos2 pos3 / workspace2

            - 입력: "1번 나사 검사해"
            출력: inspect_check / pos1 /

            - 입력: "workspace 3에서 2번 나사 불량 검사해줘"
            출력: inspect_check / pos2 / workspace3

            - 입력: "workspace 1에서 1번이랑 3번 나사 토크 확인해"
            출력: inspect_check inspect_check / pos1 pos3 / workspace1

            <사용자 입력>
            "{user_input}"                
        """

        self.prompt_template = PromptTemplate(
            input_variables=["user_input"], template=prompt_content
        )
        self.lang_chain = self.prompt_template | self.llm
        # self.lang_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        self.stt = STT(openai_api_key=openai_api_key)


        super().__init__("get_keyword_node")
        # 오디오 설정
        mic_config = MicConfig(
            chunk=12000,
            rate=48000,
            channels=1,
            record_seconds=5,
            fmt=pyaudio.paInt16,
            device_index=10,
            buffer_size=24000,
        )
        self.mic_controller = MicController(config=mic_config)
        # self.ai_processor = AIProcessor()

        self.get_logger().info("MicRecorderNode initialized.")
        self.get_logger().info("wait for client's request...")
        self.get_keyword_srv = self.create_service(
            Trigger, "get_keyword", self.get_keyword
        )
        self.wakeup_word = WakeupWord(mic_config.buffer_size)

    def extract_keyword(self, output_message):
        response = self.lang_chain.invoke({"user_input": output_message})
        result = response.content

        # LLM 응답에 '/'가 포함되어 있는지 확인하여 안전하게 분리
        parts = result.strip().split("/")
        if len(parts) >= 3:
            object_str, target_str, workspace_str = parts[0].strip(), parts[1].strip(), parts[2].strip()
        elif len(parts) == 2:
            object_str, target_str = parts[0].strip(), parts[1].strip()
            workspace_str = ""
        else:
            object_str, target_str, workspace_str = result.strip(), "", ""

        objects = object_str.split()
        targets = target_str.split()
        workspaces = workspace_str.split()

        print(f"llm's raw response: {result}")
        print(f"commands (objects): {objects}")
        print(f"targets (positions): {targets}")
        print(f"workspaces: {workspaces}")
        
        # 가장 중요한 부분! 명령, 위치, 워크스페이스를 모두 합쳐서 반환해야 합니다.
        return objects + targets + workspaces
    
    def get_keyword(self, request, response):  # 요청과 응답 객체를 받아야 함    # d2 이 함수 일부 수정함
        try:
            print("open stream")
            self.mic_controller.open_stream()
            self.wakeup_word.set_stream(self.mic_controller.stream)
        except OSError:
            self.get_logger().error("Error: Failed to open audio stream")
            self.get_logger().error("please check your device index")
            return None

        while not self.wakeup_word.is_wakeup():
            pass

        # STT --> Keword Extract --> Embedding
        output_message = self.stt.speech2text()
        keyword = self.extract_keyword(output_message)

        self.get_logger().warn(f"Detected tools: {keyword}")

        # 응답 객체 설정
        response.success = True
        response.message = " ".join(keyword)  # 감지된 키워드를 응답 메시지로 반환
        return response


def main():  # d2 메인문 일부 수정
    rclpy.init()
    node = GetKeyword()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
