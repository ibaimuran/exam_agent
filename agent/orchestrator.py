"""Exam Orchestrator — 试卷分析 Agent 编排引擎"""
import os

from .paper_agent import PaperAgent
from .student_agent import StudentAgent
from .exam_generator import ExamGeneratorAgent


class ExamOrchestrator:
    """协调 PaperAgent、StudentAgent、ExamGeneratorAgent 三个 Agent"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = "https://api.deepseek.com"
        self.output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs"
        )
        self.data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "students"
        )
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        self.paper_agent = PaperAgent(self.api_key, self.base_url)
        self.student_agent = StudentAgent(self.api_key, self.base_url, self.data_dir)
        self.exam_generator = ExamGeneratorAgent(self.api_key, self.base_url, self.data_dir)

        self.last_analysis = None

    # ── 工具 1：试卷分析 ─────────────────────────────────

    def analyze_paper(self, file, paper_name: str) -> dict:
        result = self.paper_agent.analyze(file, paper_name, self.output_dir)
        if "error" not in result:
            self.last_analysis = result
        return result

    # ── 工具 2：错题归档 ─────────────────────────────────

    def archive_wrong(self, student_name: str, wrong_nums: str, paper_name: str) -> dict:
        if not self.last_analysis:
            return {"error": "请先上传并分析试卷", "step": "prerequisite"}

        return self.student_agent.archive(
            student_name,
            wrong_nums,
            paper_name,
            self.last_analysis.get("analysis", ""),
            self.last_analysis.get("questions", []),
            self.output_dir,
        )

    # ── 工具 3：生成练习卷 ───────────────────────────────

    def generate_paper(self, student_name: str) -> dict:
        raw = self.last_analysis.get("raw", "") if self.last_analysis else ""
        questions = self.last_analysis.get("questions", []) if self.last_analysis else []

        return self.exam_generator.generate(student_name, questions, raw, self.output_dir)
