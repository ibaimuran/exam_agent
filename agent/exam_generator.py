"""错题练习卷生成 Agent — AI 出题 + Word 排版"""
import os
import json
import re

from .base import BaseAgent
from config import PAGE_LAYOUT, TYPOGRAPHY
from prompts import get_exam_generation_system, get_exam_generation_user
from utils.docx_utils import setup_page, set_default_font, add_title, add_body, add_docx_table


class ExamGeneratorAgent(BaseAgent):
    """错题练习卷生成 Agent"""

    def __init__(self, api_key: str = None, base_url: str = None, data_dir: str = None):
        super().__init__(api_key, base_url)
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "students"
        )

    def generate(self, student_name: str, questions: list, raw: str, output_dir: str) -> dict:
        student = self._load_student(student_name)
        if not student["records"]:
            return {"error": f"未找到 {student_name} 的错题记录", "step": "validate"}

        all_weakness = "\n".join(
            r.get("weakness", "") for r in student["records"]
        )
        all_details = []
        for r in student["records"]:
            all_details.extend(r.get("details", []))

        system_prompt = get_exam_generation_system()
        user_prompt = get_exam_generation_user(student_name, all_weakness, all_details)
        exam_text = self._call_ai(system_prompt, user_prompt, temp=0.3, max_tok=4000)

        docx_path = self._generate_docx(student_name, exam_text, output_dir)
        return {
            "student_name": student_name,
            "exam_paper": exam_text,
            "docx_path": docx_path,
            "step": "done",
        }

    def _load_student(self, name: str) -> dict:
        os.makedirs(self.data_dir, exist_ok=True)
        path = os.path.join(self.data_dir, f"{name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"name": name, "records": []}

    def _generate_docx(self, student_name: str, text: str, output_dir: str) -> str:
        from docx import Document
        from docx.shared import Pt, Cm

        doc = Document()
        setup_page(doc)
        set_default_font(doc)

        lines = text.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if line.startswith("---") or line.startswith("***"):
                i += 1
                continue

            if line.startswith("```") or line.startswith("paper_content") or line.startswith("error_history"):
                i += 1
                continue

            if line.startswith("# ") and not line.startswith("## "):
                add_title(doc, line[2:].strip(), Pt(18))
            elif line.startswith("## ") and not line.startswith("### "):
                add_body(doc, line[3:].strip(), Pt(12), bold=True)
            elif line.startswith("### "):
                add_body(doc, line[4:].strip(), Pt(12), bold=True)

            elif line.startswith("|") and line.endswith("|"):
                parts = [p.strip() for p in line.strip("|").split("|")]
                table_lines = [parts]
                j = i + 1
                while j < len(lines):
                    nl = lines[j].strip()
                    if nl.startswith("|") and nl.endswith("|"):
                        tp = [p.strip() for p in nl.strip("|").split("|")]
                        if not all(
                            c in "-:"
                            for c in "".join(tp).replace(" ", "").replace("-", "").replace(":", "")
                        ):
                            table_lines.append(tp)
                            j += 1
                        else:
                            j += 1
                    else:
                        break
                if len(table_lines) > 1:
                    add_docx_table(doc, table_lines[0], table_lines[1:])
                i = j
                continue

            elif re.match(r'^[A-D][.．]\s', line) or re.match(r'^[A-D]\s', line):
                add_body(doc, line, Pt(12), indent=True)

            elif re.match(r'^\d+[.．、]\s', line) or re.match(r'^\d+\s', line):
                add_body(doc, line, Pt(12))

            else:
                add_body(doc, line, Pt(12))

            i += 1

        path = os.path.join(output_dir, f"{student_name}_错题练习卷.docx")
        doc.save(path)
        return path
