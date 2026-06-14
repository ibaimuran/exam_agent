"""
提示词加载器 — 从 .txt 文件读取 system/user prompt 模板并格式化

每个 .txt 文件格式：
  system prompt 内容
  ---
  user prompt 内容（支持 {placeholder} 占位符）

{format_rules} 占位符：
  - system prompt 中：直接替换为 format_rules.txt 内容
  - user prompt 中：作为 .format() 参数传入（避免内容中的 {} 被误解析）
"""
import json
import os

_PROMPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_format_rules() -> str:
    """读取共享格式规则"""
    path = os.path.join(_PROMPT_DIR, "format_rules.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _load_template(name: str) -> tuple:
    """读取模板文件，返回 (system, user) — 不做任何替换"""
    path = os.path.join(_PROMPT_DIR, f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 1)
    system = parts[0].strip()
    user = parts[1].strip() if len(parts) > 1 else ""
    return system, user


# ── 试卷分析 ─────────────────────────────────


def get_paper_analysis_system() -> str:
    system, _ = _load_template("paper_prompts")
    return system.replace("{format_rules}", load_format_rules())


def get_paper_analysis_user(paper_name: str, paper_text: str) -> str:
    _, user = _load_template("paper_prompts")
    return user.format(
        paper_name=paper_name,
        paper_text=paper_text[:12000],
        format_rules=load_format_rules(),
    )


# ── 学生错题诊断 ──────────────────────────────


def get_student_analysis_system() -> str:
    system, _ = _load_template("student_prompts")
    return system.replace("{format_rules}", load_format_rules())


def get_student_analysis_user(
    student_name: str,
    paper_name: str,
    wrong_list: list,
    paper_analysis: str,
    wrong_details: list,
) -> str:
    _, user = _load_template("student_prompts")
    return user.format(
        student_name=student_name,
        paper_name=paper_name,
        wrong_list=", ".join(wrong_list),
        paper_analysis=paper_analysis[:5000],
        wrong_details_json=json.dumps(wrong_details, ensure_ascii=False),
        format_rules=load_format_rules(),
    )


# ── 错题练习卷生成 ────────────────────────────


def get_exam_generation_system() -> str:
    system, _ = _load_template("exam_prompts")
    return system.replace("{format_rules}", load_format_rules())


def get_exam_generation_user(
    student_name: str,
    all_weakness: str,
    all_details: list,
) -> str:
    _, user = _load_template("exam_prompts")
    return user.format(
        student_name=student_name,
        all_weakness=all_weakness[:3000],
        all_details_json=json.dumps(all_details[:15], ensure_ascii=False),
        format_rules=load_format_rules(),
    )
