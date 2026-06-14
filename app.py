"""试卷分析 Agent — Flask API 层"""
import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
load_dotenv()

from agent.orchestrator import ExamOrchestrator
from utils.file_utils import init_ocr

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

app = Flask(__name__)
agent = ExamOrchestrator()

# 预加载 EasyOCR 模型，避免首次请求下载模型导致超时
init_ocr()


@app.route("/")
def index():
    return render_template("index.html")


# ── API 1：上传试卷 → 分析 ─────────────────────────────

@app.route("/api/paper/upload", methods=["POST"])
def paper_upload():
    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400
    file = request.files["file"]
    paper_name = request.form.get("name", file.filename or "未命名")

    result = agent.analyze_paper(file, paper_name)
    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "paper_name": result["paper_name"],
        "analysis": result["analysis"],
        "question_count": result["question_count"]
    })


@app.route("/api/paper/download-docx/<path:paper_name>")
@app.route("/api/paper/download-docx")
def paper_download(paper_name=None):
    if not agent.last_analysis:
        return "请先分析试卷", 404
    path = agent.last_analysis.get("docx_path", "")
    name = agent.last_analysis.get("paper_name", "试卷")
    if not os.path.exists(path):
        return "文件未找到", 404
    return send_file(path, as_attachment=True, download_name=f"{name}_试卷分析.docx")


# ── API 2：错题归档 → 学生分析 ─────────────────────────

@app.route("/api/wrong/submit", methods=["POST"])
def wrong_submit():
    data = request.json
    student_name = data.get("student_name", "").strip()
    wrong_nums = data.get("wrong_nums", "").strip()
    paper_name = data.get("paper_name", "").strip()

    result = agent.archive_wrong(student_name, wrong_nums, paper_name)
    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "student_name": result["student_name"],
        "overview": result["overview"],
        "detail_analysis": result.get("detail_analysis", ""),
        "weakness": result["weakness"],
        "measures": result["measures"],
        "record_count": result["record_count"]
    })


@app.route("/api/wrong/download-docx/<student_name>")
def wrong_download(student_name):
    path = os.path.join(agent.output_dir, f"{student_name}_试卷分析.docx")
    if not os.path.exists(path):
        return "请先归档该学生的错题", 404
    return send_file(path, as_attachment=True, download_name=f"{student_name}_试卷分析.docx")


# ── API 3：生成错题练习卷 ──────────────────────────────

@app.route("/api/wrong/generate-paper", methods=["POST"])
def generate_paper():
    student_name = (request.json or {}).get("student_name", "").strip()
    if not student_name:
        return jsonify({"error": "请提供学生姓名"}), 400

    result = agent.generate_paper(student_name)
    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "student_name": result["student_name"],
        "exam_paper": result["exam_paper"]
    })


@app.route("/api/wrong/download-paper-docx/<student_name>")
def paper_download_docx(student_name):
    path = os.path.join(agent.output_dir, f"{student_name}_错题练习卷.docx")
    if not os.path.exists(path):
        return "请先生成练习卷", 404
    return send_file(path, as_attachment=True, download_name=f"{student_name}_错题练习卷.docx")


if __name__ == "__main__":
    import time, sys
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        # ModelScope 环境：保持进程存活，平台自动接管 Flask app 对象
        while True:
            time.sleep(3600)
