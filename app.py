# # # app.py
# # import os
# # import json
# # import re
# # import logging
# # from typing import Optional, List, Any, Dict, Tuple

# # import requests
# # from flask import Flask, request, jsonify, render_template
# # from flask_cors import CORS
# # from openai import OpenAI
# # from dotenv import load_dotenv
# # from bs4 import BeautifulSoup

# # # ============
# # # Bootstrap
# # # ============
# # load_dotenv()

# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger("keyvoid-backend")

# # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# # if not OPENAI_API_KEY:
# #     logger.warning("OPENAI_API_KEY not set in environment.")
# # client = OpenAI(api_key=OPENAI_API_KEY)

# # CONFIG_PATH = os.getenv("CONFIG_PATH", "agents_config.json")

# # app = Flask(__name__, static_folder=".", template_folder=".")
# # CORS(app)

# # URL_PATTERN = re.compile(r"(https?://\S+)", re.IGNORECASE)
# # HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KeyVoidAgent/1.0)"}

# # # ============
# # # Utilities
# # # ============

# # def fetch_text(url: str, max_tokens: int = 140) -> str:
# #     """Lightweight HTML fetch → visible text (first ~N tokens)."""
# #     try:
# #         r = requests.get(url, timeout=8, headers=HEADERS)
# #         r.raise_for_status()
# #         soup = BeautifulSoup(r.text, "html.parser")
# #         for t in soup(["script", "style", "noscript", "iframe"]):
# #             t.decompose()
# #         tokens = list(soup.stripped_strings)
# #         return " ".join(tokens[:max_tokens])
# #     except Exception as e:
# #         logger.debug(f"fetch_text failed for {url}: {e}")
# #         return ""

# # def extract_all_json_from_text(text: str) -> List[Any]:
# #     """
# #     Extract ALL JSON blocks from model output.
# #     - First, parse ```json ... ``` blocks
# #     - Then, attempt balanced-brace parsing for standalone JSON
# #     """
# #     results: List[Any] = []

# #     # 1) fenced ```json blocks
# #     for m in re.finditer(r"```json\s*([\s\S]*?)```", text, flags=re.IGNORECASE):
# #         inner = m.group(1)
# #         try:
# #             results.append(json.loads(inner))
# #         except Exception:
# #             try:
# #                 cleaned = re.sub(r",\s*([\]}])", r"\1", inner)  # trailing commas
# #                 results.append(json.loads(cleaned))
# #             except Exception:
# #                 pass

# #     # 2) Balanced-brace fallback (excluding already-captured fenced blocks)
# #     stripped = re.sub(r"```json[\s\S]*?```", "", text, flags=re.IGNORECASE)

# #     def find_balanced_objects(s: str) -> List[Any]:
# #         out = []
# #         i = 0
# #         while i < len(s):
# #             if s[i] == "{":
# #                 depth = 0
# #                 start = i
# #                 for j in range(i, len(s)):
# #                     if s[j] == "{":
# #                         depth += 1
# #                     elif s[j] == "}":
# #                         depth -= 1
# #                         if depth == 0:
# #                             cand = s[start : j + 1]
# #                             try:
# #                                 out.append(json.loads(cand))
# #                                 i = j
# #                             except Exception:
# #                                 pass
# #                             break
# #             i += 1
# #         return out

# #     for obj in find_balanced_objects(stripped):
# #         if obj not in results:
# #             results.append(obj)

# #     return results

# # # ============
# # # Default knowledge (used if agent.py or agents_config.json don’t provide)
# # # ============

# # ONYX_GOLD_TONE = (
# #     "Onyx+Gold tone: crisp, confident, helpful. Prefer clarity over fluff. "
# #     "Be precise, practical, student-centered."
# # )

# # ELLER_MAJORS = [
# #     "MIS (Management Information Systems)",
# #     "Business Analytics",
# #     "Finance",
# #     "Accounting",
# #     "Business Management",
# #     "Marketing",
# #     "Entrepreneurship (senior-year sequence layered on a base major)"
# # ]

# # ELLER_ANCHORS = (
# #     "Eller sample plan anchors (append to https://eller.arizona.edu/programs/undergraduate/advising/sample-plans):\n"
# #     "- MIS: #management-information-systems\n"
# #     "- Business Analytics: #business-analytics\n"
# #     "- Finance: #finance\n"
# #     "- Accounting: #accounting\n"
# #     "- Business Management: #business-management\n"
# #     "- Marketing: #marketing\n"
# #     "- Entrepreneurship: #entrepreneurship-senior-year-program\n"
# # )

# # UA_ENGINEERING_MAJORS = [
# #     "Aerospace Engineering",
# #     "Biomedical Engineering",
# #     "Biosystems Engineering",
# #     "Chemical Engineering",
# #     "Civil Engineering",
# #     "Computer Engineering",
# #     "Electrical & Computer Engineering",
# #     "Environmental Engineering",
# #     "Industrial Engineering",
# #     "Materials Science & Engineering",
# #     "Mechanical Engineering",
# #     "Mining & Geological Engineering",
# #     "Optical Sciences & Engineering",
# #     "Systems Engineering"
# # ]

# # UA_ENGINEERING_ANCHORS = (
# #     "UArizona Engineering 4-year plans (append to https://engineering.arizona.edu/advising/4-year-degree-plans)"
# # )

# # MINING_CLUSTER = [
# #     "Mining & Geological Engineering",
# #     "Geosciences / Geological Sciences (BS)",
# #     "Earth & Environmental Sciences (relevant tracks)",
# #     "Materials Science & Metallurgy tracks",
# #     "Hydrology / Geohydrology (where offered at undergrad/bridge level)",
# #     "Energy Resources & Extractive Operations (related minors/certificates)"
# # ]

# # STEM_PATHWAYS = [
# #     "Computer Science & Software",
# #     "Data Science / Statistics",
# #     "Electrical / Computer / Robotics",
# #     "Mechanical / Aerospace",
# #     "Biomedical / Bioinformatics",
# #     "Chemistry / Chemical Engineering",
# #     "Mathematics / Applied Math",
# #     "Environmental / Earth Systems",
# #     "Materials / Nanoscience"
# # ]

# # # ============
# # # Markdown Formatters (agent-specific)
# # # ============

# # def _mk_header(title: str) -> str:
# #     return f"# {title}\n"

# # def _mk_section(title: str) -> str:
# #     return f"\n## {title}\n"

# # def format_eller_markdown(structured: Any) -> str:
# #     """
# #     Expects either:
# #     - dict with key 'recommendations' (list of majors) OR
# #     - list of {Major, Why it fits, Suggested Courses, Career Outcomes}
# #     Will render a six-section Eller report.
# #     """
# #     # Normalize recommendations list
# #     if isinstance(structured, dict):
# #         recs = structured.get("recommendations") or structured.get("majors") or structured.get("matches") or []
# #         profile = structured.get("profile") or {}
# #     elif isinstance(structured, list):
# #         recs = structured
# #         profile = {}
# #     else:
# #         recs, profile = [], {}

# #     md = []
# #     md.append(_mk_header("Eller Major Recommendation Report"))

# #     # 1) Snapshot
# #     md.append(_mk_section("1) Profile Snapshot"))
# #     if profile:
# #         for k, v in profile.items():
# #             if isinstance(v, list):
# #                 md.append(f"- **{k.title()}**: {', '.join(map(str, v))}")
# #             else:
# #                 md.append(f"- **{k.title()}**: {v}")
# #     else:
# #         md.append("_Profile details were not fully structured; results are based on your inputs._")

# #     # 2) Executive Summary
# #     md.append(_mk_section("2) Executive Summary"))
# #     if recs:
# #         names = [r.get("Major") or r.get("major") or "Unknown" for r in recs][:4]
# #         md.append(f"Top recommended Eller majors: **{', '.join(names)}**.")
# #     else:
# #         md.append("_No structured recommendations detected; see narrative below._")

# #     # 3) Ranked Major Options
# #     md.append(_mk_section("3) Ranked Major Options"))
# #     if recs:
# #         for i, r in enumerate(recs, start=1):
# #             major = r.get("Major") or r.get("major") or f"Option {i}"
# #             why = r.get("Why it fits") or r.get("why") or r.get("Reason", "")
# #             courses = r.get("Suggested Courses") or r.get("courses") or []
# #             outcomes = r.get("Career Outcomes") or r.get("outcomes") or "Strong career demand in related roles."
# #             md.append(f"### {i}. {major}")
# #             if why:
# #                 md.append(f"- **Why it fits:** {why}")
# #             if courses:
# #                 md.append("- **Suggested Courses:**")
# #                 for c in courses:
# #                     md.append(f"  - {c}")
# #             md.append(f"- **Career Outcomes & Demand:** {outcomes}\n")
# #     else:
# #         md.append("_No ranked items found._")

# #     # 4) Skills & Tools to Build
# #     md.append(_mk_section("4) Skills & Tools to Build"))
# #     md.append(
# #         "- Spreadsheet modeling, business writing/communication\n"
# #         "- SQL + one programming language (Python or R) for MIS/Analytics/Finance modeling\n"
# #         "- Research & consumer insights for Marketing; org behavior & PM for Management"
# #     )

# #     # 5) Sample 4-Year Sequence (Entrepreneurship senior-only)
# #     md.append(_mk_section("5) Sample 4-Year Sequence"))
# #     md.append(
# #         "**Year 1 – Discover & Foundations**\n"
# #         "- Business calc; micro/macro econ; intro info systems; spreadsheet modeling\n"
# #         "- Clubs & exploration; resume + LinkedIn; informational interviews\n\n"
# #         "**Year 2 – Core & First Projects**\n"
# #         "- Accounting I/II; business statistics; ops/management survey\n"
# #         "- Take an entry course in your top major or a tools course (SQL/Excel/Tableau)\n\n"
# #         "**Year 3 – Depth & Leadership**\n"
# #         "- 2–3 upper-division courses in your top major; build portfolio artifacts\n"
# #         "- Leadership in a club; summer internship in-field\n\n"
# #         "**Year 4 – Capstone & Launch**\n"
# #         "- Advanced major coursework; job-search sprints\n"
# #         "- **Entrepreneurship sequence in senior year** layered on the base major"
# #     )

# #     # 6) Links & Next Steps
# #     md.append(_mk_section("6) Links & Next Steps"))
# #     md.append(
# #         f"- Majors to consider at Eller: {', '.join(ELLER_MAJORS)}\n"
# #         f"- {ELLER_ANCHORS}\n"
# #         "- Meet with an academic advisor to confirm prerequisites and sample plans.\n"
# #         "- Draft a 1–2 project portfolio and attend two relevant club meetings this month."
# #     )

# #     return "\n".join(md)

# # def format_engineering_markdown(structured: Any) -> str:
# #     """Formatter for UArizona Engineering Major Selector."""
# #     if isinstance(structured, dict):
# #         recs = structured.get("recommendations") or structured.get("matches") or structured.get("majors") or []
# #         profile = structured.get("profile") or {}
# #     elif isinstance(structured, list):
# #         recs = structured
# #         profile = {}
# #     else:
# #         recs, profile = [], {}

# #     md = []
# #     md.append(_mk_header("UArizona – Engineering Major Selector"))

# #     md.append(_mk_section("1) Profile Snapshot"))
# #     if profile:
# #         for k, v in profile.items():
# #             md.append(f"- **{k.title()}**: {v if not isinstance(v, list) else ', '.join(map(str, v))}")
# #     else:
# #         md.append("_Profile not fully structured; using your inputs to infer fit._")

# #     md.append(_mk_section("2) Executive Summary"))
# #     if recs:
# #         names = [r.get("Major") or r.get("major") or "Unknown" for r in recs][:4]
# #         md.append(f"Top fit engineering majors: **{', '.join(names)}**.")
# #     else:
# #         md.append("_No structured recommendations detected._")

# #     md.append(_mk_section("3) Ranked Options & Why"))
# #     if recs:
# #         for i, r in enumerate(recs, start=1):
# #             major = r.get("Major") or r.get("major") or f"Option {i}"
# #             why = r.get("Why it fits") or r.get("why") or r.get("Reason", "")
# #             key_courses = r.get("Key Courses") or r.get("courses") or []
# #             md.append(f"### {i}. {major}")
# #             if why:
# #                 md.append(f"- **Why it fits:** {why}")
# #             if key_courses:
# #                 md.append("- **Key Courses to expect:**")
# #                 for c in key_courses:
# #                     md.append(f"  - {c}")
# #             md.append("")
# #     else:
# #         md.append("_No ranked items found._")

# #     md.append(_mk_section("4) Math/Science Core (common first two years)"))
# #     md.append(
# #         "- Calculus I–III, Differential Equations, Linear Algebra\n"
# #         "- Physics I–II (calculus-based), Chemistry I\n"
# #         "- Programming (Python/C/C++ as applicable); Intro to Engineering design"
# #     )

# #     md.append(_mk_section("5) Sample Plan & Prereq Notes"))
# #     md.append(
# #         f"- Typical 4-year plans: {UA_ENGINEERING_ANCHORS}\n"
# #         "- Prerequisites are strict — plan calculus/physics early to keep upper-division on track.\n"
# #         "- Lab scheduling can constrain semesters; meet with your SIE/department advisor each term."
# #     )

# #     md.append(_mk_section("6) Next Steps"))
# #     md.append(
# #         "- Visit two department info sessions from your top options.\n"
# #         "- Join 1–2 relevant engineering clubs (design/build teams are ideal).\n"
# #         "- Draft a 2-semester prerequisite map with an advisor."
# #     )

# #     return "\n".join(md)

# # def format_mining_markdown(structured: Any) -> str:
# #     """Formatter for Mining & Related Majors."""
# #     if isinstance(structured, dict):
# #         recs = structured.get("recommendations") or structured.get("matches") or []
# #         profile = structured.get("profile") or {}
# #     elif isinstance(structured, list):
# #         recs = structured
# #         profile = {}
# #     else:
# #         recs, profile = [], {}

# #     md = []
# #     md.append(_mk_header("Mining & Related Majors – Recommendation Report"))

# #     md.append(_mk_section("1) Profile Snapshot"))
# #     if profile:
# #         for k, v in profile.items():
# #             md.append(f"- **{k.title()}**: {v if not isinstance(v, list) else ', '.join(map(str, v))}")
# #     else:
# #         md.append("_Using your inputs to infer fit._")

# #     md.append(_mk_section("2) Executive Summary"))
# #     if recs:
# #         names = [r.get("Major") or r.get("major") or "Unknown" for r in recs][:4]
# #         md.append(f"Top fit programs in the mining/earth/energy cluster: **{', '.join(names)}**.")
# #     else:
# #         md.append("_No structured recommendations found._")

# #     md.append(_mk_section("3) Ranked Options & Why"))
# #     if recs:
# #         for i, r in enumerate(recs, start=1):
# #             major = r.get("Major") or r.get("major") or f"Option {i}"
# #             why = r.get("Why it fits") or r.get("Reason", "")
# #             focus = r.get("Focus Areas") or r.get("focus") or []
# #             md.append(f"### {i}. {major}")
# #             if why:
# #                 md.append(f"- **Why it fits:** {why}")
# #             if focus:
# #                 md.append("- **Focus areas / tracks:**")
# #                 for f in focus:
# #                     md.append(f"  - {f}")
# #             md.append("")
# #     else:
# #         md.append("_No ranked items found._")

# #     md.append(_mk_section("4) Skills & Field Readiness"))
# #     md.append(
# #         "- Geomechanics, mineral processing, rock mechanics, surveying (for Mining Eng)\n"
# #         "- Field methods & GIS; safety and environmental compliance\n"
# #         "- Data analysis & modeling (Python/Matlab); mine planning software exposure"
# #     )

# #     md.append(_mk_section("5) Programs & Adjacent Paths"))
# #     md.append(
# #         "- Primary: **Mining & Geological Engineering**\n"
# #         f"- Adjacent: {', '.join(MINING_CLUSTER[1:])}"
# #     )

# #     md.append(_mk_section("6) Next Steps"))
# #     md.append(
# #         "- Attend a department info session and tour lab facilities.\n"
# #         "- Map physics/chem/calc sequencing to hit junior-year core on time.\n"
# #         "- Explore a summer field camp or industry internship."
# #     )

# #     return "\n".join(md)

# # def format_stem_career_markdown(structured: Any) -> str:
# #     """Formatter for general STEM Career Recommender."""
# #     if isinstance(structured, dict):
# #         recs = structured.get("recommendations") or structured.get("matches") or []
# #         profile = structured.get("profile") or {}
# #     elif isinstance(structured, list):
# #         recs = structured
# #         profile = {}
# #     else:
# #         recs, profile = [], {}

# #     md = []
# #     md.append(_mk_header("STEM Career Recommender – Personalized Report"))

# #     md.append(_mk_section("1) Profile Snapshot"))
# #     if profile:
# #         for k, v in profile.items():
# #             md.append(f"- **{k.title()}**: {v if not isinstance(v, list) else ', '.join(map(str, v))}")
# #     else:
# #         md.append("_Inferred from your inputs._")

# #     md.append(_mk_section("2) Executive Summary"))
# #     if recs:
# #         names = [r.get("Path") or r.get("Major") or r.get("Track") or "Unknown" for r in recs][:5]
# #         md.append(f"Promising STEM pathways: **{', '.join(names)}**.")
# #     else:
# #         md.append("_No structured recommendations found._")

# #     md.append(_mk_section("3) Ranked Options & Why"))
# #     if recs:
# #         for i, r in enumerate(recs, start=1):
# #             title = r.get("Path") or r.get("Major") or r.get("Track") or f"Option {i}"
# #             why = r.get("Why it fits") or r.get("Reason", "")
# #             starter = r.get("Starter Courses") or r.get("courses") or []
# #             md.append(f"### {i}. {title}")
# #             if why:
# #                 md.append(f"- **Why it fits:** {why}")
# #             if starter:
# #                 md.append("- **Starter courses / certifications:**")
# #                 for c in starter:
# #                     md.append(f"  - {c}")
# #             md.append("")
# #     else:
# #         md.append("_No ranked items found._")

# #     md.append(_mk_section("4) Core Foundations"))
# #     md.append(
# #         "- Calculus sequence; statistics; programming (Python/Java/C++)\n"
# #         "- Physics and/or Chemistry depending on track\n"
# #         "- Version control (Git), Linux shell basics; technical communication"
# #     )

# #     md.append(_mk_section("5) Portfolio & Experience"))
# #     md.append(
# #         "- Build 2–3 small, outcome-oriented projects per year\n"
# #         "- Join 1 competition team or research lab; pursue internships each summer"
# #     )

# #     md.append(_mk_section("6) Next Steps"))
# #     md.append(
# #         f"- Explore: {', '.join(STEM_PATHWAYS)}\n"
# #         "- Schedule advising to map prerequisites and electives to your target roles."
# #     )

# #     return "\n".join(md)

# # # ============
# # # Agent loading & defaults
# # # ============

# # def default_agent_config_map() -> Dict[str, Dict[str, Any]]:
# #     """
# #     Provide defaults for the 4 agents if they’re missing from agent.py / agents_config.json.
# #     """
# #     def base_cfg(system_prompt: str, knowledge: List[str]) -> Dict[str, Any]:
# #         return {
# #             "model": "gpt-4o",
# #             "temperature": 0.4,
# #             "system_prompt": system_prompt,
# #             "knowledge_inputs": knowledge,
# #             "capabilities": {"scraping": True},
# #             "actions": []
# #         }

# #     return {
# #         "eller-major-recommender": base_cfg(
# #             system_prompt=(
# #                 "You are the Key-VΦid Eller Major Recommender. "
# #                 "Recommend Eller College BSBA majors and produce a polished Markdown report with six sections: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Major Options, "
# #                 "4) Skills & Tools to Build, 5) Sample 4-Year Sequence (Entrepreneurship senior-only), 6) Links & Next Steps. "
# #                 + ONYX_GOLD_TONE
# #             ),
# #             knowledge=[
# #                 f"Majors to consider: {', '.join(ELLER_MAJORS)}.",
# #                 ELLER_ANCHORS,
# #                 "Foundational themes (1–2 years): Business calc, micro/macro econ, Accounting I/II, Business Statistics, "
# #                 "Intro to Info Systems & Spreadsheet Modeling, Business Writing/Communication, Ops/Management survey.",
# #                 "Major-specific foundations: MIS→ Python/Java + SQL; Business Analytics→ Python/R + SQL + BI; "
# #                 "Finance→ Corporate finance & Excel modeling; Accounting→ Financial & Managerial sequence; "
# #                 "Management→ Org behavior & project management; Marketing→ Principles + consumer & research.",
# #                 "Treat Entrepreneurship as a senior-year sequence layered on top of a base major."
# #             ],
# #         ),
# #         "ua-engineering-major-selector": base_cfg(
# #             system_prompt=(
# #                 "You are the Key-VΦid UArizona Engineering Selector. "
# #                 "Recommend College of Engineering majors and produce a polished Markdown report with six sections: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Options & Why, "
# #                 "4) Math/Science Core, 5) Sample Plan & Prereq Notes, 6) Next Steps. "
# #                 + ONYX_GOLD_TONE
# #             ),
# #             knowledge=[
# #                 f"UArizona engineering majors include: {', '.join(UA_ENGINEERING_MAJORS)}.",
# #                 UA_ENGINEERING_ANCHORS,
# #                 "Common first/second year: Calculus sequence, Physics I–II, Chemistry I, Programming; intro design.",
# #                 "Prerequisites are strict; plan calculus/physics early to avoid delays."
# #             ],
# #         ),
# #         "mining-and-related-majors": base_cfg(
# #             system_prompt=(
# #                 "You are the Key-VΦid Mining & Related Majors Recommender. "
# #                 "Recommend Mining/Geological/Earth/Energy cluster majors and produce a polished Markdown report with six sections: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Options & Why, "
# #                 "4) Skills & Field Readiness, 5) Programs & Adjacent Paths, 6) Next Steps. "
# #                 + ONYX_GOLD_TONE
# #             ),
# #             knowledge=[
# #                 f"Mining cluster majors: {', '.join(MINING_CLUSTER)}.",
# #                 "Core skill themes: geomechanics, mineral processing, surveying, safety & environmental, data analysis/modeling."
# #             ],
# #         ),
# #         "stem-career-recommender": base_cfg(
# #             system_prompt=(
# #                 "You are the Key-VΦid STEM Career Recommender. "
# #                 "Recommend STEM pathways and produce a polished Markdown report with six sections: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Options & Why, "
# #                 "4) Core Foundations, 5) Portfolio & Experience, 6) Next Steps. "
# #                 + ONYX_GOLD_TONE
# #             ),
# #             knowledge=[
# #                 f"STEM pathways include: {', '.join(STEM_PATHWAYS)}.",
# #                 "Early foundations: Calculus, statistics, programming; physics/chemistry as appropriate."
# #             ],
# #         ),
# #     }
    

# # def load_agents() -> Dict[str, Any]:
# #     """
# #     Load agents from agent.py (preferred), else agents_config.json, then ensure the 4 agents exist.
# #     """
# #     agents: Dict[str, Any] = {}

# #     # Try agent.py
# #     try:
# #         from agent import AGENTS as AGENTS_FROM_MODULE  # user-provided registry
# #         if isinstance(AGENTS_FROM_MODULE, dict):
# #             agents.update(AGENTS_FROM_MODULE)
# #             logger.info("Loaded AGENTS from agent.py")
# #     except Exception as e:
# #         logger.info(f"No agent.py AGENTS found or import failed: {e}")

# #     # Try JSON config
# #     if not agents and os.path.exists(CONFIG_PATH):
# #         try:
# #             with open(CONFIG_PATH, encoding="utf-8") as f:
# #                 agents = json.load(f)
# #                 logger.info(f"Loaded AGENTS from {CONFIG_PATH}")
# #         except Exception as e:
# #             logger.warning(f"Failed to load {CONFIG_PATH}: {e}")

# #     # Ensure the 4 required agents exist; do not overwrite if present
# #     defaults = default_agent_config_map()
# #     for key, cfg in defaults.items():
# #         agents.setdefault(key, cfg)

# #     return agents

# # AGENTS = load_agents()

# # # ============
# # # Message Assembly
# # # ============

# # def build_messages_for_agent(agent_key: str, cfg: Dict[str, Any], msg: str, hist: List[dict]) -> List[dict]:
# #     """Compose OpenAI chat messages list for a given agent."""
# #     messages: List[dict] = []

# #     markdown_instruction = (
# #         "Final output: produce a polished, reader-friendly Markdown report. "
# #         "Do not present raw JSON as the primary output. If any structured data appears, "
# #         "wrap it in clearly labeled code blocks and keep narrative above it."
# #     )

# #     system_prompt = cfg.get("system_prompt") or cfg.get("instructions") or ""
# #     if system_prompt:
# #         messages.append({"role": "system", "content": f"{system_prompt}\n\n{markdown_instruction}"})
# #     else:
# #         messages.append({"role": "system", "content": markdown_instruction})

# #     # Knowledge inputs (from config)
# #     for ki in cfg.get("knowledge_inputs", []):
# #         if isinstance(ki, dict):
# #             val = ki.get("value", "")
# #         else:
# #             val = str(ki)
# #         if val:
# #             messages.append({"role": "system", "content": val})

# #     # Optional scraping of URLs in user message
# #     if cfg.get("capabilities", {}).get("scraping", False) and isinstance(msg, str):
# #         for u in URL_PATTERN.findall(msg):
# #             fetched = fetch_text(u, max_tokens=160)
# #             if fetched:
# #                 messages.append({"role": "system", "content": f"[Web scrape from {u}]: {fetched}"})

# #     # Conversation history
# #     if isinstance(hist, list):
# #         messages += hist

# #     # User message
# #     messages.append({"role": "user", "content": msg})

# #     return messages

# # # ============
# # # Routing formatter
# # # ============

# # def route_formatting(agent_key: str, raw_response: str) -> str:
# #     """
# #     Try to structure & pretty-print into our agent-specific Markdown.
# #     If JSON snippets are present, prefer them; otherwise, return the raw Markdown.
# #     """
# #     # Parse any JSON chunks
# #     try:
# #         snippets = extract_all_json_from_text(raw_response)
# #     except Exception:
# #         snippets = []

# #     structured: Optional[Any] = None
# #     # Prefer a dict with 'recommendations'/'matches'/etc., else take first snippet
# #     for s in snippets:
# #         if isinstance(s, dict) and any(k in s for k in ("recommendations", "matches", "majors", "profile")):
# #             structured = s
# #             break
# #     if structured is None and snippets:
# #         structured = snippets[0]

# #     key = agent_key.lower()
# #     try:
# #         if "eller" in key:
# #             if structured is not None:
# #                 return format_eller_markdown(structured)
# #         elif "engineering" in key:
# #             if structured is not None:
# #                 return format_engineering_markdown(structured)
# #         elif "mining" in key:
# #             if structured is not None:
# #                 return format_mining_markdown(structured)
# #         elif "stem" in key:
# #             if structured is not None:
# #                 return format_stem_career_markdown(structured)
# #     except Exception as e:
# #         logger.debug(f"Formatter error for {agent_key}: {e}")

# #     # Fallback: if no structured parse or agent not matched, return the original text
# #     return raw_response

# # # ============
# # # HTTP Endpoints
# # # ============

# # @app.route("/")
# # def index():
# #     return render_template("/templates/index.html")

# # @app.route("/api/config", methods=["GET"])
# # def get_config():
# #     return jsonify(AGENTS)

# # @app.route("/api/save-config", methods=["POST"])
# # def save_config():
# #     global AGENTS
# #     try:
# #         incoming = request.get_json(force=True)
# #         if not isinstance(incoming, dict):
# #             return jsonify({"status": "error", "message": "Config must be a JSON object"}), 400
# #         AGENTS = incoming
# #         with open(CONFIG_PATH, "w", encoding="utf-8") as f:
# #             json.dump(AGENTS, f, indent=2, ensure_ascii=False)
# #         return jsonify({"status": "ok"})
# #     except Exception as e:
# #         logger.exception("Failed to save config")
# #         return jsonify({"status": "error", "message": str(e)}), 500

# # @app.route("/api/<agent>/chat", methods=["POST"])
# # def chat(agent):
# #     if agent not in AGENTS:
# #         return jsonify({"error": f"Unknown agent: {agent}"}), 404

# #     cfg = AGENTS[agent]
# #     data = request.get_json(force=True) or {}
# #     msg = data.get("message", "")
# #     hist = data.get("history", [])
# #     structured_input = data.get("structured_input")

# #     # If structured_input is provided, wrap it in a user instruction tuned per agent
# #     if structured_input and isinstance(structured_input, dict):
# #         if "eller" in agent:
# #             msg = (
# #                 "Using the student profile below, recommend Eller BSBA majors. "
# #                 "Output a six-section Markdown report in this order: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Major Options, "
# #                 "4) Skills & Tools to Build, 5) Sample 4-Year Sequence, 6) Links & Next Steps. "
# #                 "Treat Entrepreneurship as a senior-year sequence layered on a base major.\n\n"
# #                 f"Student profile (JSON): ```json\n{json.dumps(structured_input, ensure_ascii=False)}\n```"
# #             )
# #         elif "engineering" in agent:
# #             msg = (
# #                 "Using the profile below, recommend UArizona College of Engineering majors. "
# #                 "Output a six-section Markdown report in this order: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Options & Why, "
# #                 "4) Math/Science Core, 5) Sample Plan & Prereq Notes, 6) Next Steps.\n\n"
# #                 f"Profile (JSON): ```json\n{json.dumps(structured_input, ensure_ascii=False)}\n```"
# #             )
# #         elif "mining" in agent:
# #             msg = (
# #                 "Using the profile below, recommend Mining & related majors. "
# #                 "Output a six-section Markdown report in this order: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Options & Why, "
# #                 "4) Skills & Field Readiness, 5) Programs & Adjacent Paths, 6) Next Steps.\n\n"
# #                 f"Profile (JSON): ```json\n{json.dumps(structured_input, ensure_ascii=False)}\n```"
# #             )
# #         elif "stem" in agent:
# #             msg = (
# #                 "Using the profile below, recommend STEM career pathways. "
# #                 "Output a six-section Markdown report in this order: "
# #                 "1) Profile Snapshot, 2) Executive Summary, 3) Ranked Options & Why, "
# #                 "4) Core Foundations, 5) Portfolio & Experience, 6) Next Steps.\n\n"
# #                 f"Profile (JSON): ```json\n{json.dumps(structured_input, ensure_ascii=False)}\n```"
# #             )

# #     messages = build_messages_for_agent(agent, cfg, msg, hist)

# #     functions = cfg.get("actions") or None
# #     function_call = "auto" if functions else None

# #     try:
# #         resp = client.chat.completions.create(
# #             model=cfg.get("model", "gpt-4o"),
# #             messages=messages,
# #             temperature=cfg.get("temperature", 0.4),
# #             functions=functions,
# #             function_call=function_call,
# #         )
# #     except Exception as e:
# #         logger.exception("OpenAI chat error")
# #         return jsonify({"error": f"LLM error: {e}"}), 500

# #     first = resp.choices[0].message

# #     # Optional function calling round-trip
# #     final_raw = first.content or ""
# #     function_response = None

# #     if getattr(first, "function_call", None) and cfg.get("actions"):
# #         fc = first.function_call
# #         action = next((a for a in cfg["actions"] if a.get("name") == fc.name), None)
# #         if action:
# #             try:
# #                 args = json.loads(fc.arguments or "{}")
# #             except json.JSONDecodeError:
# #                 args = {}
# #             try:
# #                 r = requests.request(
# #                     action.get("method", "GET"),
# #                     action.get("endpoint", ""),
# #                     json=args,
# #                     timeout=8,
# #                 )
# #                 result = r.json() if r.ok else {"error": r.text}
# #             except Exception as e:
# #                 result = {"error": f"action request failed: {e}"}

# #             function_response = result
# #             messages.append(first)
# #             messages.append({"role": "function", "name": fc.name, "content": json.dumps(result)})

# #             try:
# #                 follow = client.chat.completions.create(
# #                     model=cfg.get("model", "gpt-4o"),
# #                     messages=messages,
# #                     temperature=cfg.get("temperature", 0.4),
# #                 )
# #                 final_raw = follow.choices[0].message.content or json.dumps(result)
# #             except Exception as e:
# #                 logger.exception("Follow-up OpenAI call failed")
# #                 final_raw = json.dumps(result)

# #     # Post-format to agent-specific Markdown if we can
# #     markdown_report = route_formatting(agent, final_raw) if final_raw else ""

# #     return jsonify({
# #         "reply": final_raw,
# #         "markdown_report": markdown_report,
# #         "function_response": function_response,
# #     })

# # # ============
# # # Run
# # # ============

# # if __name__ == "__main__":
# #     port = int(os.getenv("PORT", "5000"))
# #     debug = os.getenv("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")
# #     app.run(host="0.0.0.0", port=port, debug=debug)
# # app.py
# import os
# import re
# import json
# import logging
# from typing import Any, Dict, List, Optional, Tuple

# import requests
# from flask import Flask, render_template, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv
# from bs4 import BeautifulSoup

# # Optional OpenAI polish (safe fallback to pure-Python if key missing)
# try:
#     from openai import OpenAI  # pip install openai>=1.0
# except Exception:
#     OpenAI = None  # type: ignore

# # =============================================================================
# # Bootstrap
# # =============================================================================
# load_dotenv()

# logging.basicConfig(level=logging.INFO)
# log = logging.getLogger("keyvoid-gold-backend")

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
# client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None

# app = Flask(__name__, static_folder=".", template_folder=".")
# CORS(app)

# HEADERS = {"User-Agent": "KeyVoid/1.0 (+https://keyvoid.local)"}
# URL_RE = re.compile(r"(https?://\S+)", re.I)

# # =============================================================================
# # Helpers: fetching (lightweight) + tokenization + scoring
# # =============================================================================
# def fetch_text(url: str, max_tokens: int = 140) -> str:
#     try:
#         r = requests.get(url, timeout=8, headers=HEADERS)
#         r.raise_for_status()
#         soup = BeautifulSoup(r.text, "html.parser")
#         for t in soup(["script", "style", "noscript", "iframe"]):
#             t.decompose()
#         tokens = list(soup.stripped_strings)
#         return " ".join(tokens[:max_tokens])
#     except Exception as e:
#         log.debug(f"fetch_text fail: {url} -> {e}")
#         return ""

# def tk(s: str) -> List[str]:
#     return re.sub(r"[^a-z0-9+\s]", " ", (s or "").lower()).split()

# def freq_map(text: str) -> Dict[str, int]:
#     f: Dict[str, int] = {}
#     for w in tk(text):
#         f[w] = f.get(w, 0) + 1
#     return f

# def weighted_count(words: Dict[str, int], keyword: str) -> int:
#     k = keyword.lower()
#     base = words.get(k, 0)
#     # heavier weight for rigor/skills that better signal fit
#     if re.search(r"(sql|python|r\b|statistics|statistical|model|machine|ml\b|coding|java|cloud|cyber|cfa|audit)", k):
#         return base * 2
#     return base

# def rank_items(intake_text: str, items: List[Dict[str, Any]], key: str = "keywords") -> List[Dict[str, Any]]:
#     words = freq_map(intake_text)
#     results: List[Dict[str, Any]] = []
#     for item in items:
#         score = 0
#         hits: List[str] = []
#         for kw in item.get(key, []):
#             w = weighted_count(words, kw)
#             if w > 0:
#                 score += w
#                 hits.append(kw.lower())
#         # name bonus
#         if item.get("id"):
#             score += len(re.findall(rf"\b{re.escape(item['id'].lower())}\b", intake_text.lower())) * 2
#         results.append({**item, "score": score, "hits": sorted(list(set(hits)))})
#     max_score = max([r["score"] for r in results] + [1])
#     for r in results:
#         r["match"] = int(round((r["score"] / max_score) * 100))
#     results.sort(key=lambda r: r["match"], reverse=True)
#     return results

# # =============================================================================
# # Domain catalogs (majors/tracks)
# # =============================================================================
# ELLER = [
#     {
#         "id": "mis",
#         "name": "Management Information Systems (MIS)",
#         "keywords": [
#             "mis","information systems","systems","database","databases","sql","python","java","coding",
#             "software","product","cloud","cyber","cybersecurity","ai","ml","data","analytics","it",
#             "technology","architecture","api","erp"
#         ],
#         "clubs": ["Cyber Cats","Data Cats","Product Club","Coding Clubs"],
#         "roles": ["Business Systems Analyst","Product Analyst","Data Analyst","IT Analyst"],
#         "companies": ["Intuit","American Express","Raytheon","Deloitte","Amazon"]
#     },
#     {
#         "id": "ba",
#         "name": "Business Analytics",
#         "keywords": [
#             "analytics","data","statistics","statistical","modeling","machine learning","ml","tableau",
#             "power bi","experiments","ab testing","sql","python","r","forecast","quant"
#         ],
#         "clubs": ["Analytics Club","Data Cats","Kaggle/ML"],
#         "roles": ["Data Analyst","Growth Analyst","Ops Analytics"],
#         "companies": ["Intuit","Adobe","Meta","Uber","DoorDash"]
#     },
#     {
#         "id": "fin",
#         "name": "Finance",
#         "keywords": [
#             "finance","investment","banking","ib","valuation","equity research","portfolio","trading",
#             "discounted cash flow","dcf","markets","hedge","risk","financial modeling","cfa"
#         ],
#         "clubs": ["Investments Club","Wall Street Scholars"],
#         "roles": ["Financial Analyst","IB Analyst (prep)","Corporate Finance","FP&A"],
#         "companies": ["JPMorgan","Goldman Sachs","Charles Schwab","Honeywell"]
#     },
#     {
#         "id": "acc",
#         "name": "Accounting",
#         "keywords": [
#             "accounting","audit","auditing","tax","cpa","bookkeeping","gaap","assurance","controls",
#             "financial reporting"
#         ],
#         "clubs": ["Beta Alpha Psi","Accounting Society"],
#         "roles": ["Audit/Assurance","Tax Associate","Staff Accountant"],
#         "companies": ["EY","PwC","KPMG","Deloitte"]
#     },
#     {
#         "id": "mgmt",
#         "name": "Business Management",
#         "keywords": [
#             "management","operations","ops","leadership","strategy","organizational","project management",
#             "supply chain","hr","people","manager"
#         ],
#         "clubs": ["Management Consulting Group","SHRM","PMI/Project Clubs"],
#         "roles": ["Operations Coordinator","Project Manager (assoc)","People Ops"],
#         "companies": ["Honeywell","Northrop","Target","Amazon Ops"]
#     },
#     {
#         "id": "mkt",
#         "name": "Marketing",
#         "keywords": [
#             "marketing","brand","branding","social","social media","advertising","ads","seo","sem","content",
#             "copy","consumer","ux research","growth","go to market","gtm"
#         ],
#         "clubs": ["AMA","Ad Clubs","UX groups"],
#         "roles": ["Marketing Analyst","Growth","Product Marketing (assoc)","Brand Coordinator"],
#         "companies": ["HubSpot","Adobe","Intuit","Canva"]
#     },
#     {
#         "id": "entre",
#         "name": "Entrepreneurship (senior-year sequence)",
#         "keywords": ["entrepreneur","entrepreneurship","startup","founder","venture","innovation","accelerator","incubator"],
#         "clubs": ["Venture Studio","Entrepreneurship Clubs","Hackathons"],
#         "roles": ["Founder","Venture Fellow","Product Builder"],
#         "companies": ["AZ Forge","University iLabs"],
#         "seniorOnly": True
#     }
# ]

# ENG = [
#     {"id":"aero","name":"Aerospace","keywords":["aero","aircraft","space","rocket","propulsion","orbital","flight","avionics"]},
#     {"id":"me","name":"Mechanical","keywords":["mechanics","thermo","manufacturing","cad","solidworks","mech","dynamics","design"]},
#     {"id":"ece","name":"Electrical & Computer","keywords":["circuits","electronics","embedded","fpga","microcontroller","signal","control","power","ece"]},
#     {"id":"ind","name":"Industrial & Systems","keywords":["operations","ops","optimization","supply","lean","six sigma","logistics","systems"]},
#     {"id":"civil","name":"Civil","keywords":["civil","structures","bridge","geotech","transportation","water","hydro","environmental"]},
#     {"id":"che","name":"Chemical","keywords":["chemical","process","reactor","thermodynamics","separation","plant"]},
#     {"id":"bio","name":"Biomedical","keywords":["bio","biomed","medical","prosthetic","device","tissue"]},
#     {"id":"mat","name":"Materials","keywords":["materials","metallurgy","polymers","ceramics","semiconductor","composite"]},
#     {"id":"min","name":"Mining","keywords":["mining","mine","haul","pit","drill","blast","ventilation","geology"]},
#     {"id":"sys","name":"Systems","keywords":["systems","architecture","modeling","control","simulation"]},
# ]

# MINING_CLUSTER = [
#     {"id":"mgeo","name":"Mining & Geological Engineering","keywords":["mining","geological","mine","rock","geomechanics","processing","surveying","ventilation","safety"]},
#     {"id":"geosci","name":"Geosciences","keywords":["geology","geoscience","petrology","sedimentology","mapping","tectonics"]},
#     {"id":"ees","name":"Earth & Environmental Sciences","keywords":["environmental","hydrology","earth systems","ecology","climate","remediation"]},
#     {"id":"materials","name":"Materials Science / Metallurgy","keywords":["materials","metallurgy","smelting","refining","alloy","mineral processing"]},
#     {"id":"energy","name":"Energy Resources / Extractives","keywords":["energy","resources","mineral economics","operations","planning","automation"]},
# ]

# STEM_TRACKS = [
#     {"id":"cs","name":"Computer Science","keywords":["software","coding","programming","python","java","systems","hci"]},
#     {"id":"ds","name":"Data Science","keywords":["data","analytics","ml","ai","statistics","r","sql"]},
#     {"id":"math","name":"Math/Statistics","keywords":["proof","theory","algebra","calculus","probability","statistics"]},
#     {"id":"phys","name":"Physics","keywords":["physics","quantum","optics","relativity","astrophysics"]},
#     {"id":"chem","name":"Chemistry","keywords":["chemistry","organic","lab","analytical","materials"]},
#     {"id":"bio","name":"Biology","keywords":["biology","biotech","neuro","genetics","ecology"]},
#     {"id":"earth","name":"Earth/Geo","keywords":["geology","earth","climate","atmosphere","ocean","geophysics"]},
# ]

# # =============================================================================
# # Gold blueprint + report builders
# # =============================================================================
# def md_table(rows: List[List[str]], header: List[str]) -> str:
#     body = "\n".join(["| " + " | ".join(r) + " |" for r in rows])
#     sep = "| " + " | ".join([":--" if i == 0 else "--:" if i == len(header)-1 else "---" for i,_ in enumerate(header)]) + " |"
#     return "| " + " | ".join(header) + " |\n" + sep + "\n" + body

# def bullets(lines: List[str]) -> str:
#     return "\n".join([f"- {l}" for l in lines])

# def year_plan_for_eller(top: Dict[str,Any], constraints: str = "") -> List[str]:
#     base = top["name"].split(" (")[0]
#     extra = []
#     t = constraints.lower()
#     if re.search(r"budget|\$|scholarship|aid|cost|tuition", t):
#         extra.append("Budget-aware plan: prioritize scholarships, campus roles (RA/TA), and paid internships.")
#     if re.search(r"accelerated|fast|3\s*year|3-year|early grad", t):
#         extra.append("Accelerated interest: use AP/CLEP credit, summer terms, and tight prerequisite mapping.")
#     if re.search(r"part\s*time|part-time|work while studying|working", t):
#         extra.append("Part-time load: consider lighter terms and mix evening/online sections.")
#     # 4 years
#     y1 = bullets([
#         "Business calc; micro/macro econ; business writing",
#         "Tech/data literacy: spreadsheet modeling + intro information systems",
#         "Explore 2–3 clubs aligned to your top matches",
#         "Career setup: resume, LinkedIn; 1 informational chat/month"
#     ])
#     y2 = bullets([
#         "Accounting I/II; business statistics; ops/management survey",
#         f"Major preview: entry {base} or tools (SQL/Excel/Tableau)",
#         "Project #1: team case/hackathon; document outcomes",
#         "Apply for paid summer internship"
#     ])
#     y3 = bullets([
#         f"2–3 upper-division {base} courses; build 2 portfolio artifacts",
#         "Versatility elective (SQL/Python/BI or research methods)",
#         "Take a club leadership role; mentor a freshman",
#         "Summer internship aligned to top major"
#     ])
#     y4 = bullets([
#         f"Capstone & advanced {base} coursework; job-search sprints (2/week)",
#         "Entrepreneurship sequence (senior year) if desired",
#         "Ship final portfolio (2 projects + 1 case write-up + reflection)",
#         "Network flywheel: alumni coffees + targeted applications"
#     ])
#     out = [
#         f"**Year 1 – Discover & Foundations**\n\n{y1}",
#         f"\n**Year 2 – Core & First Projects**\n\n{y2}",
#         f"\n**Year 3 – Depth & Leadership**\n\n{y3}",
#         f"\n**Year 4 – Capstone & Launch**\n\n{y4}",
#     ]
#     if extra:
#         out.append(f"\n**Constraints & Preferences Applied**\n\n{bullets(extra)}")
#     return out

# def assemble_eller_report(intake: Dict[str,Any]) -> Tuple[str, List[Dict[str,Any]]]:
#     # intake normalization
#     text = "\n".join([
#         intake.get("a", {}).get("strengths",""),
#         intake.get("a", {}).get("goals",""),
#         intake.get("a", {}).get("interests",""),
#         intake.get("b", {}).get("experience",""),
#         intake.get("b", {}).get("regions",""),
#         intake.get("b", {}).get("constraints",""),
#     ])
#     ranked = rank_items(text, ELLER)
#     top5 = ranked[:5]

#     # executive summary
#     names = ", ".join([r["name"] for r in top5]) if top5 else "No clear matches"
#     exec_md = (
#         f"**Top 5 matches (strongest → weakest):** {names}.\n\n"
#         "The ranking reflects explicit interests/skills found in your intake (with heavier weight for rigorous signals like SQL, Python, statistics, security, etc.)."
#     )

#     # ranked table
#     rows = []
#     for i, r in enumerate(top5, start=1):
#         sig = ", ".join(r["hits"][:8]) if r["hits"] else "—"
#         rows.append([str(i), r["name"], f"{r['match']}%", sig])
#     table = md_table(rows, ["#", "Major", "Match", "Signals Detected"])

#     # skill gaps per top major
#     top = top5[0] if top5 else ELLER[0]
#     gaps = {
#         "mis": ["SQL foundations + query design", "Python or Java basics", "Systems analysis / ERD", "API & cloud fundamentals", "Security hygiene"],
#         "ba":  ["Statistics refresh", "SQL for analytics", "Python or R for data prep & modeling", "BI tool (Tableau/Power BI)", "Experimental design (A/B)"],
#         "fin": ["Excel modeling (DCF, 3-statement)", "Corporate finance core", "Valuation frameworks", "Markets literacy & news habit"],
#         "acc": ["Intermediate accounting I/II", "Audit/tax concepts", "Excel / ERP basics", "CPA roadmap planning"],
#         "mgmt":["Ops & org behavior", "Project management practice", "People leadership & communication", "Basic analytics for managers"],
#         "mkt": ["Customer research methods", "Content & performance marketing", "Analytics basics (GA4/Attribution)", "Brand storytelling"],
#         "entre":["Customer discovery", "Rapid prototyping", "Basic finance/legal for startups", "Pitching & storytelling"],
#     }.get(top.get("id","mis"), gaps := ["Statistics/SQL", "Portfolio building", "Internship search process"])

#     # plan
#     plan_blocks = year_plan_for_eller(top, intake.get("b",{}).get("constraints",""))

#     # 30/60/90
#     clubs = ", ".join(top.get("clubs", [])[:4]) or "Eller clubs"
#     qplan = bullets([
#         "Week 0–2: pick a tools course (SQL / Tableau); refresh resume + LinkedIn",
#         "Day 30: 1 finished mini-project + 3 informational chats",
#         "Day 60: apply to 10 on-campus roles; join two clubs (" + clubs + ")",
#         "Day 90: publish a 2-artifact portfolio; request two referrals"
#     ])

#     # companies/resources
#     companies = ", ".join(top.get("companies", [])[:6]) or "regional employers via Handshake"
#     resources = bullets([
#         f"**Companies to target:** {companies}",
#         f"**Clubs:** {clubs or 'Eller clubs'}",
#         "**Resources:** Advising, Handshake, case libraries, alumni directory",
#     ])

#     # resume keywords
#     kws = [k for k in top.get("keywords", []) if len(k) > 2][:18]
#     keywords_line = ", ".join(kws) if kws else "business analysis, stakeholder communication, Excel, SQL"

#     md = []
#     md.append(f"# Eller College BSBA Major Recommendation Report")
#     md.append(f"\n## Executive Summary\n{exec_md}")
#     md.append(f"\n## Ranked Recommendations\n{table}")
#     md.append(f"\n## Why This Fit\nDetected signals for **{top['name']}**: {', '.join(top.get('hits',[])[:12]) or 'general business aptitude'}.\n")
#     md.append(f"## Skill Gaps & How to Close\n{bullets(gaps)}")
#     md.append(f"\n## Chronological Plan (based on top match: **{top['name']}**)\n" + "\n\n".join(plan_blocks))
#     md.append(f"\n## 30/60/90-Day Action Plan\n{qplan}")
#     md.append(f"\n## Companies, Clubs & Resources\n{resources}")
#     md.append(f"\n## Resume Keywords to Weave In\n{keywords_line}")

#     return ("\n".join(md), ranked)

# def assemble_engineering_report(intake: Dict[str,Any]) -> Tuple[str, List[Dict[str,Any]]]:
#     text = "\n".join([
#         intake.get("e",{}).get("strengths",""),
#         intake.get("e",{}).get("goals",""),
#         intake.get("e",{}).get("interests",""),
#         intake.get("e",{}).get("experience",""),
#         intake.get("e",{}).get("preferences",""),
#         intake.get("e",{}).get("constraints",""),
#     ])
#     ranked = rank_items(text, ENG)
#     top5 = ranked[:5]
#     names = ", ".join([r["name"] for r in top5]) if top5 else "No clear matches"
#     rows = []
#     for i, r in enumerate(top5, start=1):
#         rows.append([str(i), r["name"], f"{r['match']}%", (", ".join(r["hits"][:8]) or "—")])
#     table = md_table(rows, ["#", "Discipline", "Match", "Signals Detected"])

#     top = top5[0] if top5 else ENG[0]
#     core = bullets([
#         "Calculus I–III, Differential Equations, Linear Algebra",
#         "Physics I–II (calculus-based), Chemistry I",
#         "Programming (Python/C/C++); Intro to Engineering design"
#     ])
#     projects = bullets([
#         "Starter: Arduino/embedded sensor logger (ECE) or CAD + 3D-print assembly (ME)",
#         "Intermediate: BLDC with PID (ECE/ME) or supply-chain optimization (IND)"
#     ])
#     qplan = bullets([
#         "30d: math baseline refresh + 1 mini-build",
#         "60d: join a design/build team (Robotics/Formula/CubeSat)",
#         "90d: complete prototype cycle; line up summer co-op/internship"
#     ])
#     md = [
#         "# UArizona – Engineering Major Selector Report",
#         f"\n## Executive Summary\n**Top 5 matches (strongest → weakest):** {names}.",
#         f"\n## Ranked Recommendations\n{table}",
#         f"\n## Foundational Core (first two years)\n{core}",
#         f"\n## Projects to Ship\n{projects}",
#         f"\n## 30/60/90-Day Action Plan\n{qplan}",
#         "\n## Next Steps\n- Visit 2 department info sessions\n- Join 1–2 relevant engineering clubs (design/build teams ideal)\n- Draft a two-semester prerequisite map with an advisor",
#     ]
#     return ("\n".join(md), ranked)

# def assemble_mining_report(intake: Dict[str,Any]) -> Tuple[str, List[Dict[str,Any]]]:
#     text = "\n".join([
#         intake.get("m",{}).get("strengths",""),
#         intake.get("m",{}).get("goals",""),
#         intake.get("m",{}).get("interests",""),
#         intake.get("m",{}).get("experience",""),
#         intake.get("m",{}).get("regions",""),
#         intake.get("m",{}).get("constraints",""),
#     ])
#     ranked = rank_items(text, MINING_CLUSTER)
#     top5 = ranked[:5]
#     names = ", ".join([r["name"] for r in top5]) if top5 else "No clear matches"
#     rows = []
#     for i, r in enumerate(top5, start=1):
#         rows.append([str(i), r["name"], f"{r['match']}%", (", ".join(r["hits"][:8]) or "—")])
#     table = md_table(rows, ["#", "Program", "Match", "Signals Detected"])

#     field_ready = bullets([
#         "Pursue **MSHA Part 46/48** training early; complete PPE checklist",
#         "GIS/CAD basics (ArcGIS/QGIS, AutoCAD); drone mapping intro",
#         "Schedule 2 site visits (local quarries/ops) + 1 safety toolbox talk"
#     ])
#     qplan = bullets([
#         "30d: safety training + equipment orientation; 2 informational chats",
#         "60d: complete a blast-plan case or haul-road design mini-project",
#         "90d: internship outreach to AZ/NV/UT sites; prep for remote rotations"
#     ])
#     roles = "Operations, planning, processing, automation. Employers: Freeport-McMoRan, Komatsu, Caterpillar, Rio Tinto, BHP."
#     md = [
#         "# Mining & Related Majors — Recommendation Report",
#         f"\n## Executive Summary\n**Top 5 matches (strongest → weakest):** {names}.",
#         f"\n## Ranked Recommendations\n{table}",
#         f"\n## Field Readiness\n{field_ready}",
#         f"\n## 30/60/90-Day Plan\n{qplan}",
#         f"\n## Roles & Employers\n{roles}",
#     ]
#     return ("\n".join(md), ranked)

# def assemble_stem_report(intake: Dict[str,Any]) -> Tuple[str, List[Dict[str,Any]]]:
#     text = "\n".join([
#         intake.get("s",{}).get("strengths",""),
#         intake.get("s",{}).get("goals",""),
#         intake.get("s",{}).get("interests",""),
#         intake.get("s",{}).get("experience",""),
#         intake.get("s",{}).get("track",""),
#         intake.get("s",{}).get("constraints",""),
#     ])
#     ranked = rank_items(text, STEM_TRACKS)
#     top5 = ranked[:5]
#     names = ", ".join([r["name"] for r in top5]) if top5 else "No clear matches"
#     rows = []
#     for i, r in enumerate(top5, start=1):
#         rows.append([str(i), r["name"], f"{r['match']}%", (", ".join(r["hits"][:8]) or "—")])
#     table = md_table(rows, ["#", "Pathway", "Match", "Signals Detected"])

#     core = bullets([
#         "Calculus sequence; statistics; programming (Python/Java/C++)",
#         "Physics and/or Chemistry as appropriate",
#         "Version control (Git), Linux shell; technical communication"
#     ])
#     ramp = bullets([
#         "Weeks 1–2: replicate a canonical tutorial/paper in top pathway",
#         "Weeks 3–6: build a small project/dataset + 1-page methods note",
#         "Weeks 7–12: submit to a student venue or publish as a portfolio repo; meet two mentors"
#     ])
#     md = [
#         "# STEM Career Recommender — Personalized Report",
#         f"\n## Executive Summary\n**Top 5 matches (strongest → weakest):** {names}.",
#         f"\n## Ranked Recommendations\n{table}",
#         f"\n## Core Foundations\n{core}",
#         f"\n## 12-Week Research/Industry Ramp\n{ramp}",
#         "\n## Next Steps\n- Join a lab or competition team\n- Ship 2–3 small, outcome-oriented projects per year\n- Pursue internships each summer",
#     ]
#     return ("\n".join(md), ranked)

# # =============================================================================
# # Optional LLM polish (keeps our ranking intact)
# # =============================================================================
# GOLD_TONE = (
#     "Onyx+Gold tone: crisp, confident, student-centered. Be precise, practical, and actionable. "
#     "Preserve the provided ranking and any tables verbatim; you may add concise narrative before/after sections."
# )

# def llm_polish(markdown: str, intake_snippet: str = "") -> str:
#     if not client:
#         return markdown
#     try:
#         messages = [
#             {"role":"system","content": GOLD_TONE},
#             {"role":"user","content": (
#                 "Polish the following Markdown report for clarity and flow. "
#                 "Do NOT reorder ranked items or modify tables; instead add or tighten language around them. "
#                 "Keep headings and structure. "
#                 + ("\n\nIntake context:\n" + intake_snippet if intake_snippet else "")
#             )},
#             {"role":"user","content": f"```md\n{markdown}\n```"}
#         ]
#         res = client.chat.completions.create(
#             model=os.getenv("OPENAI_MODEL","gpt-4o"),
#             messages=messages,
#             temperature=0.3,
#         )
#         content = res.choices[0].message.content or ""
#         # try to pull content back out of code block if present
#         m = re.search(r"```(?:md|markdown)?\s*([\s\S]*?)```", content, re.I)
#         return (m.group(1).strip() if m else content.strip()) or markdown
#     except Exception as e:
#         log.warning(f"LLM polish failed: {e}")
#         return markdown

# # =============================================================================
# # HTTP: discovery + schemas
# # =============================================================================
# AGENT_LIST = [
#     {
#         "slug":"course-major-recommender",
#         "name":"Eller Major Recommender",
#         "emoji":"🎓",
#         "endpoint":"/api/course-major-recommender/chat",
#         "description":"Rank Eller BSBA majors from your profile and generate a four-year plan. Entrepreneurship runs senior-year only.",
#     },
#     {
#         "slug":"engineering-major-recommender",
#         "name":"Engineering Major Recommender",
#         "emoji":"🛠️",
#         "endpoint":"/api/engineering-major-recommender/chat",
#         "description":"Map UArizona engineering disciplines to your strengths/goals with projects and a staged plan.",
#     },
#     {
#         "slug":"mining-major-recommender",
#         "name":"Mining & Related Recommender",
#         "emoji":"⛏️",
#         "endpoint":"/api/mining-major-recommender/chat",
#         "description":"Assess fit for Mining/Geological/Materials/Earth cluster with field-ready actions.",
#     },
#     {
#         "slug":"stem-major-recommender",
#         "name":"STEM Major Recommender",
#         "emoji":"🧪",
#         "endpoint":"/api/stem-major-recommender/chat",
#         "description":"Recommend STEM pathways (CS/DS/Math/Physics/etc.) with a 12-week ramp plan.",
#     },
# ]

# SCHEMAS = {
#     "course-major-recommender": {
#         "schema": [
#             {"key":"intakeA","title":"Intake A","note":"Academic strengths, career goals, and interests.","fields":[
#                 {"type":"textarea","name":"a.strengths","label":"Academic strengths (subjects, grades)","full":True},
#                 {"type":"textarea","name":"a.goals","label":"Career goals","full":True},
#                 {"type":"textarea","name":"a.interests","label":"Interests & hobbies","full":True},
#             ]},
#             {"key":"intakeB","title":"Intake B","note":"Experience, regions, constraints.","fields":[
#                 {"type":"textarea","name":"b.experience","label":"Relevant experience","full":True},
#                 {"type":"textarea","name":"b.regions","label":"Preferred regions","full":True},
#                 {"type":"textarea","name":"b.constraints","label":"Constraints or preferences","full":True},
#             ]},
#             {"key":"review","title":"Review & Generate","note":"Optional notes before generating.","fields":[
#                 {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
#             ]},
#         ]
#     },
#     "engineering-major-recommender": {
#         "schema": [
#             {"key":"engA","title":"Intake A","note":"Strengths, goals, interests.","fields":[
#                 {"type":"textarea","name":"e.strengths","label":"Technical strengths","full":True},
#                 {"type":"textarea","name":"e.goals","label":"Career goals","full":True},
#                 {"type":"textarea","name":"e.interests","label":"Interests","full":True},
#             ]},
#             {"key":"engB","title":"Intake B","note":"Experience & preferences.","fields":[
#                 {"type":"textarea","name":"e.experience","label":"Projects / labs / comps","full":True},
#                 {"type":"select","name":"e.math_readiness","label":"Math readiness","options":["Pre-Calc","Calculus I","Calculus II+"]},
#                 {"type":"select","name":"e.physics_readiness","label":"Physics readiness","options":["None","Mechanics","E&M / Waves"]},
#                 {"type":"textarea","name":"e.preferences","label":"Preferences","full":True},
#                 {"type":"textarea","name":"e.constraints","label":"Constraints","full":True},
#             ]},
#             {"key":"review","title":"Review & Generate","note":"Notes (optional).","fields":[
#                 {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
#             ]},
#         ]
#     },
#     "mining-major-recommender": {
#         "schema": [
#             {"key":"minA","title":"Intake A","note":"Background & goals.","fields":[
#                 {"type":"textarea","name":"m.strengths","label":"Strengths","full":True},
#                 {"type":"textarea","name":"m.goals","label":"Career goals","full":True},
#                 {"type":"textarea","name":"m.interests","label":"Interests","full":True},
#             ]},
#             {"key":"minB","title":"Intake B","note":"Experience, regions, constraints.","fields":[
#                 {"type":"textarea","name":"m.experience","label":"Experience","full":True},
#                 {"type":"select","name":"m.fieldwork_tolerance","label":"Fieldwork tolerance","options":["Low","Medium","High"]},
#                 {"type":"textarea","name":"m.regions","label":"Preferred regions","full":True},
#                 {"type":"textarea","name":"m.constraints","label":"Constraints","full":True},
#             ]},
#             {"key":"review","title":"Review & Generate","note":"Notes (optional).","fields":[
#                 {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
#             ]},
#         ]
#     },
#     "stem-major-recommender": {
#         "schema": [
#             {"key":"sA","title":"Intake A","note":"Strengths, goals, interests.","fields":[
#                 {"type":"textarea","name":"s.strengths","label":"Strengths","full":True},
#                 {"type":"textarea","name":"s.goals","label":"Career goals","full":True},
#                 {"type":"select","name":"s.track","label":"Preferred track","options":["Industry","Research","Open / Unsure"]},
#                 {"type":"textarea","name":"s.interests","label":"Interests","full":True},
#             ]},
#             {"key":"sB","title":"Intake B","note":"Experience & constraints.","fields":[
#                 {"type":"textarea","name":"s.experience","label":"Projects / labs / internships","full":True},
#                 {"type":"textarea","name":"s.constraints","label":"Constraints or preferences","full":True},
#                 {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
#             ]},
#         ]
#     },
# }

# @app.get("/api/agents")
# def list_agents():
#     return jsonify(AGENT_LIST)

# @app.get("/api/<slug>/schema")
# def get_schema(slug: str):
#     sch = SCHEMAS.get(slug)
#     if not sch:
#         return jsonify({"error":"unknown agent"}), 404
#     return jsonify(sch)

# # =============================================================================
# # Chat endpoints (deterministic ranking + optional LLM polish)
# # =============================================================================
# def _polish_if_enabled(md: str, intake_for_prompt: Dict[str,Any]) -> str:
#     snippet = json.dumps(intake_for_prompt, ensure_ascii=False)
#     return llm_polish(md, snippet)

# @app.post("/api/course-major-recommender/chat")
# def course_major_chat():
#     data = request.get_json(force=True) or {}
#     structured = data.get("structured_input") or {}
#     # Optional lightweight scraping for any pasted URLs in free text
#     free = json.dumps(structured, ensure_ascii=False)
#     for url in URL_RE.findall(free):
#         fetched = fetch_text(url, 140)
#         if fetched:
#             structured.setdefault("__web__", []).append({"url":url,"text":fetched})
#     md, ranked = assemble_eller_report(structured)
#     md = _polish_if_enabled(md, structured)
#     return jsonify({
#         "markdown_report": md,
#         "ranked": [{"id":r["id"],"name":r["name"],"match":r["match"]} for r in ranked[:5]]
#     })

# @app.post("/api/engineering-major-recommender/chat")
# def engineering_major_chat():
#     data = request.get_json(force=True) or {}
#     structured = data.get("structured_input") or {}
#     free = json.dumps(structured, ensure_ascii=False)
#     for url in URL_RE.findall(free):
#         fetched = fetch_text(url, 140)
#         if fetched:
#             structured.setdefault("__web__", []).append({"url":url,"text":fetched})
#     md, ranked = assemble_engineering_report(structured)
#     md = _polish_if_enabled(md, structured)
#     return jsonify({
#         "markdown_report": md,
#         "ranked": [{"id":r["id"],"name":r["name"],"match":r["match"]} for r in ranked[:5]]
#     })

# @app.post("/api/mining-major-recommender/chat")
# def mining_major_chat():
#     data = request.get_json(force=True) or {}
#     structured = data.get("structured_input") or {}
#     free = json.dumps(structured, ensure_ascii=False)
#     for url in URL_RE.findall(free):
#         fetched = fetch_text(url, 140)
#         if fetched:
#             structured.setdefault("__web__", []).append({"url":url,"text":fetched})
#     md, ranked = assemble_mining_report(structured)
#     md = _polish_if_enabled(md, structured)
#     return jsonify({
#         "markdown_report": md,
#         "ranked": [{"id":r["id"],"name":r["name"],"match":r["match"]} for r in ranked[:5]]
#     })

# @app.post("/api/stem-major-recommender/chat")
# def stem_major_chat():
#     data = request.get_json(force=True) or {}
#     structured = data.get("structured_input") or {}
#     free = json.dumps(structured, ensure_ascii=False)
#     for url in URL_RE.findall(free):
#         fetched = fetch_text(url, 140)
#         if fetched:
#             structured.setdefault("__web__", []).append({"url":url,"text":fetched})
#     md, ranked = assemble_stem_report(structured)
#     md = _polish_if_enabled(md, structured)
#     return jsonify({
#         "markdown_report": md,
#         "ranked": [{"id":r["id"],"name":r["name"],"match":r["match"]} for r in ranked[:5]]
#     })
# @app.route("/")
# def index():
#     return render_template("/templates/index.html")

# # =============================================================================
# # Run
# # =============================================================================
# if __name__ == "__main__":
#     port = int(os.getenv("PORT", "5000"))
#     debug = os.getenv("FLASK_DEBUG", "1").lower() in ("1","true","yes")
#     log.info(f"Key-Void Gold backend starting on :{port} (debug={debug})")
#     if client:
#         log.info("OpenAI polish: enabled")
#     else:
#         log.info("OpenAI polish: disabled (no OPENAI_API_KEY)")
#     app.run(host="0.0.0.0", port=port, debug=debug)
# app.py
import os
import json
import re
import logging
from typing import List, Dict, Any, Optional

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

# =========================
# Bootstrap
# =========================
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keyvoid-backend")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__, static_folder=".", template_folder=".")
CORS(app)

URL_PATTERN = re.compile(r"(https?://\S+)", re.IGNORECASE)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; KeyVoidAgent/1.0)"}

FRONTEND_FILE = os.getenv("FRONTEND_FILE", "index.html")

# =========================
# Small helpers
# =========================
def fetch_text(url: str, max_tokens: int = 160) -> str:
    try:
        r = requests.get(url, timeout=8, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "noscript", "iframe"]):
            t.decompose()
        tokens = list(soup.stripped_strings)
        return " ".join(tokens[:max_tokens])
    except Exception as e:
        logger.debug(f"fetch_text failed for {url}: {e}")
        return ""

def tokenize(s: str) -> List[str]:
    return re.sub(r"[^a-z0-9+\s]", " ", (s or "").lower()).split()

def parse_constraints_notes(s: str) -> List[str]:
    t = (s or "").lower()
    notes = []
    if re.search(r"budget|\$|scholarship|aid|cost|tuition", t):
        notes.append("Budget-aware: apply for department scholarships; prioritize paid internships and campus jobs.")
    if re.search(r"accelerated|fast|3\s*year|3-year|early grad", t):
        notes.append("Accelerated: use AP/CLEP credit, summer terms, and tight prerequisite mapping with an advisor.")
    if re.search(r"part\s*time|part-time|work while studying|working", t):
        notes.append("Part-time load: consider lighter terms and evening/online sections.")
    m = re.search(r"english|spanish|hindi|mandarin|german|french", t)
    if m:
        notes.append(f"Language preference: {m.group(0)} — consider a related certificate/minor or short study-abroad.")
    return notes

# =========================
# Domain catalogs (keywords → ranking)
# =========================
def _eller_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": "mis",
            "name": "Management Information Systems (MIS)",
            "blurb": "Bridge tech and business: systems analysis, databases, product & data workflows.",
            "keywords": ["mis","information systems","systems","database","sql","python","java","coding","software","product","cloud","cyber","cybersecurity","ai","ml","data","analytics","it","technology","architecture","api","erp"],
            "clubs": ["Cyber Cats","Data Cats","Product Club","Coding Clubs"],
            "roles": ["Product Analyst","Business Systems Analyst","Data Engineer (entry)","IT Analyst"],
        },
        {
            "id": "ba",
            "name": "Business Analytics",
            "blurb": "Quant for decisions: statistics, predictive modeling, experimentation, BI.",
            "keywords": ["analytics","data","statistics","statistical","modeling","machine learning","ml","tableau","power bi","experiments","ab testing","sql","python","r","forecast","quant"],
            "clubs": ["Data Cats","Analytics Club","Kaggle/ML groups"],
            "roles": ["Data Analyst","Business Analyst","Growth Analyst","Ops Analytics"],
        },
        {
            "id": "fin",
            "name": "Finance",
            "blurb": "Capital decisions: corporate finance, markets, valuation, risk.",
            "keywords": ["finance","investment","banking","ib","valuation","equity research","portfolio","trading","discounted cash flow","dcf","markets","hedge","risk","financial modeling","cfa"],
            "clubs": ["Investments Club","Wall Street Scholars","Financial Modeling"],
            "roles": ["Financial Analyst","IB Analyst (prep)","Corporate Finance","FP&A"],
        },
        {
            "id": "acc",
            "name": "Accounting",
            "blurb": "Financial reporting, audit, tax; precision, rules, and controls.",
            "keywords": ["accounting","audit","auditing","tax","cpa","bookkeeping","gaap","assurance","controls","financial reporting"],
            "clubs": ["Beta Alpha Psi","Accounting Society"],
            "roles": ["Staff Accountant","Audit/Assurance","Tax Associate","Controllers Track"],
        },
        {
            "id": "mgmt",
            "name": "Business Management",
            "blurb": "People, operations, and strategy: leading teams and running processes.",
            "keywords": ["management","operations","ops","leadership","strategy","organizational","project management","supply chain","hr","people","manager"],
            "clubs": ["Management Consulting Group","SHRM","Project Management"],
            "roles": ["Operations Coordinator","Project Manager (assoc)","People Ops","Consulting Analyst"],
        },
        {
            "id": "mkt",
            "name": "Marketing",
            "blurb": "Audience, brand, and growth: research, creative, digital & product marketing.",
            "keywords": ["marketing","brand","branding","social","social media","advertising","ads","seo","sem","content","copy","consumer","ux research","growth","go to market","gtm"],
            "clubs": ["American Marketing Association","Ad Clubs","UX groups"],
            "roles": ["Marketing Analyst","Growth/Performance","Product Marketing (assoc)","Brand Coordinator"],
        },
        {
            "id": "entre",
            "name": "Entrepreneurship (senior-year sequence)",
            "blurb": "Company creation, venture skills, and innovation – capped in senior year.",
            "keywords": ["entrepreneur","entrepreneurship","startup","founder","venture","innovation","accelerator","incubator"],
            "clubs": ["Venture Studio / Entrepreneurship clubs","Hackathons"],
            "roles": ["Founder","Product Builder","Venture Fellow (intern)"],
            "seniorOnly": True,
        },
    ]

def _engineering_catalog() -> List[Dict[str, Any]]:
    # Short blurbs + common keyword sets for matching
    return [
        {"id":"aero","name":"Aerospace Engineering","blurb":"Flight, space systems, fluids, structures, propulsion.",
         "keywords":["aero","aerospace","flight","space","satellite","propulsion","aircraft","rocket","orbit","cfd","structures"]},
        {"id":"bme","name":"Biomedical Engineering","blurb":"Medical devices, imaging, bioinstrumentation, biomechanics.",
         "keywords":["biomedical","medical","bio","prosthetic","imaging","biomechanics","biomaterials","devices","healthcare"]},
        {"id":"bse","name":"Biosystems Engineering","blurb":"Ag/food/biological systems, sustainability, water/soil.",
         "keywords":["biosystems","agriculture","agro","soil","water","sustainability","food","environmental biology"]},
        {"id":"chem","name":"Chemical Engineering","blurb":"Reactions, separations, process design for chemicals/energy.",
         "keywords":["chemical","chem","reactions","process","plant","separations","thermo","catalyst","polymers"]},
        {"id":"civil","name":"Civil Engineering","blurb":"Structures, transportation, water resources, geotechnical.",
         "keywords":["civil","bridge","structures","transportation","pavement","geotech","hydrology","water resources"]},
        {"id":"ce","name":"Computer Engineering","blurb":"Hardware/software co-design, embedded systems, digital design.",
         "keywords":["computer engineering","embedded","fpga","verilog","vhdl","digital logic","microcontroller","firmware"]},
        {"id":"ece","name":"Electrical & Computer Engineering","blurb":"Circuits, signals, communications, power, controls.",
         "keywords":["electrical","circuits","signals","signal processing","communications","rf","antenna","power","controls","robotics","ece"]},
        {"id":"env","name":"Environmental Engineering","blurb":"Air/water quality, remediation, sustainable infrastructure.",
         "keywords":["environmental","remediation","air quality","water quality","wastewater","sustainability","esg","climate"]},
        {"id":"ie","name":"Industrial Engineering","blurb":"Optimization, operations research, logistics, quality.",
         "keywords":["industrial","operations research","optimization","logistics","supply chain","lean","six sigma","manufacturing"]},
        {"id":"mse","name":"Materials Science & Engineering","blurb":"Metals, ceramics, polymers, nano, electronic materials.",
         "keywords":["materials","metallurgy","ceramics","polymers","nano","semiconductor","microstructure","alloy","composites"]},
        {"id":"me","name":"Mechanical Engineering","blurb":"Mechanics, thermal/fluids, design, manufacturing.",
         "keywords":["mechanical","mechanics","cad","solidworks","thermo","fluids","mechatronics","manufacturing","dynamics"]},
        {"id":"mining","name":"Mining & Geological Engineering","blurb":"Mine planning, geomechanics, mineral processing, safety.",
         "keywords":["mining","geological","mine","geomechanics","drilling","blasting","mineral processing","rocks","surveying"]},
        {"id":"optics","name":"Optical Sciences & Engineering","blurb":"Lasers, imaging, photonics, optical design.",
         "keywords":["optical","optics","photonics","laser","imaging","lens","interferometry","fiber"]},
        {"id":"systems","name":"Systems Engineering","blurb":"Complex systems, modeling, controls, integration.",
         "keywords":["systems engineering","systems","modeling","controls","simulation","architecture","integration"]},
    ]

def _mining_cluster_catalog() -> List[Dict[str, Any]]:
    return [
        {"id":"mining","name":"Mining & Geological Engineering","blurb":"Geomechanics, mine planning, mineral processing, safety.",
         "keywords":["mining","geological","geomechanics","mine","drilling","blasting","processing","surveying","ventilation"]},
        {"id":"geosci","name":"Geosciences (BS)","blurb":"Earth processes, rocks/minerals, field mapping, tectonics.",
         "keywords":["geoscience","geology","rocks","minerals","fieldwork","mapping","sediment","tectonics","stratigraphy"]},
        {"id":"earthenv","name":"Earth & Environmental Sciences","blurb":"Earth systems, climate, water, sustainability.",
         "keywords":["earth","environmental","climate","hydrology","water","sustainability","ecosystem","remote sensing"]},
        {"id":"materials","name":"Materials Science / Metallurgy track","blurb":"Ore processing, extractive metallurgy, materials.",
         "keywords":["materials","metallurgy","smelting","extractive","processing","alloy","ceramics"]},
        {"id":"hydro","name":"Hydrology / Geohydrology","blurb":"Water in earth systems, aquifers, groundwater modeling.",
         "keywords":["hydrology","geohydrology","groundwater","aquifer","flow","water resources","contaminant transport"]},
        {"id":"energy","name":"Energy Resources & Extractive Ops (adjacent)","blurb":"Energy systems, operations, policy & safety.",
         "keywords":["energy","oil","gas","renewable","extraction","operations","esg","safety"]},
    ]

def _stem_catalog() -> List[Dict[str, Any]]:
    return [
        {"id":"cs","name":"Computer Science & Software","blurb":"Programming, data structures, systems, apps.",
         "keywords":["computer science","software","coding","programming","python","java","c++","web","backend","frontend","systems","algorithms"]},
        {"id":"ds","name":"Data Science / Statistics","blurb":"Inference, modeling, ML, analytics.",
         "keywords":["data","data science","statistics","statistical","r","python","pandas","sql","machine learning","ml","experiment","ab test"]},
        {"id":"ece","name":"Electrical / Computer / Robotics","blurb":"Hardware, signals, embedded, robotics & control.",
         "keywords":["electrical","ece","embedded","robotics","controls","signals","circuits","firmware","fpga","verilog","vhdl"]},
        {"id":"me","name":"Mechanical / Aerospace","blurb":"Mechanics, thermal/fluids, mechatronics, design.",
         "keywords":["mechanical","aero","aerospace","thermo","fluids","cad","mechatronics","manufacturing","robot"]},
        {"id":"bio","name":"Biomedical / Bioinformatics","blurb":"Biology+computing, medical data, devices.",
         "keywords":["bio","biomedical","medical","bioinformatics","genomics","imaging","healthcare","devices"]},
        {"id":"chem","name":"Chemistry / Chemical Engineering","blurb":"Reactions, materials, analytical chem, process.",
         "keywords":["chemistry","chemical","reactions","lab","spectroscopy","process","polymers"]},
        {"id":"math","name":"Mathematics / Applied Math","blurb":"Proofs, modeling, optimization, computation.",
         "keywords":["math","mathematics","applied math","optimization","modeling","numerical","theory","proof"]},
        {"id":"env","name":"Environmental / Earth Systems","blurb":"Climate, ecology, hydrology, sustainability.",
         "keywords":["environmental","earth","climate","hydrology","ecology","remote sensing","gis","sustainability"]},
        {"id":"mse","name":"Materials / Nanoscience","blurb":"Semiconductors, nano, polymers, ceramics, metals.",
         "keywords":["materials","nano","semiconductor","metals","polymers","ceramics","thin film"]},
    ]

CATALOGS: Dict[str, List[Dict[str, Any]]] = {
    "course-major-recommender": _eller_catalog(),
    "engineering-major-recommender": _engineering_catalog(),
    "mining-major-recommender": _mining_cluster_catalog(),
    "stem-major-recommender": _stem_catalog(),
}

WEIGHTY_TERMS = re.compile(r"sql|python|r(?![a-z])|statistics|statistical|model|machine|ml|data|coding|java|cloud|cyber|cfa|audit|controls|optimization|embedded|robot|fpga|verilog", re.I)

def rank_catalog(intake_text: str, catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tokens = tokenize(intake_text)
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1

    ranked = []
    for item in catalog:
        score = 0
        hits = []
        for kw in item.get("keywords", []):
            k = kw.lower()
            f = freq.get(k, 0)
            if f > 0:
                weight = 2 if WEIGHTY_TERMS.search(k) else 1
                score += f * weight
                hits.append(k)
        # small bonus if ID shows up verbatim
        score += len(re.findall(rf"\b{re.escape(item['id'])}\b", intake_text.lower())) * 2
        ranked.append({**item, "score": score, "hits": sorted(set(hits))})

    max_score = max(1, *(r["score"] for r in ranked))
    for r in ranked:
        r["norm"] = round((r["score"] / max_score) * 100)
    ranked.sort(key=lambda r: r["norm"], reverse=True)
    return ranked

# =========================
# Prompting & fallback rendering
# =========================
ONYX_GOLD_TONE = (
    "Onyx+Gold tone: crisp, confident, helpful. Prefer clarity over fluff. "
    "Be precise, practical, and student-centered."
)

def model_report(slug: str, intake: Dict[str, Any], ranked: List[Dict[str, Any]], constraint_notes: List[str]) -> str:
    """
    Ask the LLM to produce a polished Markdown that respects the *exact* ranking order we computed.
    If OPENAI_API_KEY is not set, this function will raise to trigger fallback rendering.
    """
    if not client:
        raise RuntimeError("LLM unavailable")

    ordered_top5 = [
        {
            "Major": r["name"],
            "WhySignals": r["hits"][:12],
            "SeniorOnly": bool(r.get("seniorOnly", False)),
            "Blurb": r.get("blurb", ""),
            "Clubs": r.get("clubs", []),
            "EarlyRoles": r.get("roles", []),
        }
        for r in ranked[:5]
    ]

    system = (
        f"You are the Key-VΦid report writer for '{slug}'. {ONYX_GOLD_TONE} "
        "You will receive a fixed ranking of recommended options and must keep that order. "
        "Do NOT include percentages; present items 1→N in descending fit. "
        "Write a detailed, actionable report."
    )

    user = {
        "intake": intake,
        "constraint_notes": constraint_notes,
        "fixed_ranking_top5": ordered_top5,
        "instructions": (
            "Output Markdown with these sections:\n"
            "1) Overview (brief purpose + how recommendations were derived from interests/strengths)\n"
            "2) Top 5 Recommendations (numbered 1–5, each with: Why it fits (plain language), "
            "What you’ll learn early (bullets), Early career roles, Clubs/portfolio ideas). "
            "Keep this exact order from 'fixed_ranking_top5'. No percentages.\n"
            "3) Chronological Plan (Year 1–4 bullets; place Entrepreneurship in senior year if present)\n"
            "4) Constraints Applied (if any)\n"
            "5) Next Steps (high-leverage, concrete actions for the next 2–4 weeks)\n"
        )
    }

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
        messages=messages,
    )
    return resp.choices[0].message.content or ""

def fallback_plan(top_name: str, entrepreneur: bool, notes: List[str]) -> str:
    base = top_name.split(" (")[0]
    y1 = [
        "Pre-business foundations: calculus, micro/macro econ, business writing/communication",
        "Technology & data literacy: spreadsheet modeling, intro information systems",
        "Explore: attend 2–3 club meetings aligned to top matches",
        "Career setup: resume, LinkedIn, 1 informational chat/week",
    ]
    y2 = [
        "Core business: accounting I/II, statistics, operations/management survey",
        f"Major preview: entry course in {base} or tools (SQL/Excel/Tableau)",
        "Project #1: case/hackathon; document outcomes",
        "Apply for on-campus or part-time summer internship",
    ]
    y3 = [
        f"Major depth: 2–3 upper-division {base} courses; build portfolio artifacts",
        "Keep versatility: one analytics/tech or research-methods elective",
        "Leadership: take a role in a club; mentor a freshman",
        "Summer: full internship aligned to your top major",
    ]
    y4 = [
        f"Capstone & advanced {base} coursework; job-search sprints (2/week)",
        "Entrepreneurship sequence (senior-year): discovery → prototyping → launch showcase" if entrepreneur
        else "Cross-functional elective (negotiations, product, design thinking)",
        "Ship final portfolio: 2 projects, 1 case write-up, 1 reflection",
        "Network flywheel: referrals, alumni coffees, targeted applications",
    ]
    extras = ""
    if notes:
        extras = "\n\n**Constraints applied**\n\n- " + "\n- ".join(notes)
    mk = lambda title, arr: f"**{title}**\n\n- " + "\n- ".join(arr)
    return "\n\n".join([
        mk("Year 1 – Discover & Foundations", y1),
        mk("Year 2 – Core & First Projects", y2),
        mk("Year 3 – Depth & Leadership", y3),
        mk("Year 4 – Capstone & Launch", y4),
    ]) + extras

def fallback_report(slug: str, intake: Dict[str, Any], ranked: List[Dict[str, Any]], notes: List[str]) -> str:
    title_map = {
        "course-major-recommender": "Eller College BSBA Major Recommendations",
        "engineering-major-recommender": "UArizona Engineering — Major Recommendations",
        "mining-major-recommender": "Mining & Related Majors — Recommendations",
        "stem-major-recommender": "STEM Pathways — Personalized Recommendations",
    }
    title = title_map.get(slug, "Personalized Recommendations")
    top = ranked[0]
    ent = any(r.get("seniorOnly") for r in ranked[:5])
    # Build “Top 5” without percentages, in the fixed order
    lines = []
    for i, r in enumerate(ranked[:5], start=1):
        sig = (", ".join(r.get("hits", [])[:10])) or "signals from your intake"
        clubs = ", ".join(r.get("clubs", [])[:4]) or "see department clubs"
        roles = ", ".join(r.get("roles", [])[:4]) or "entry roles tied to this path"
        lines.append(
            f"**{i}. {r['name']}**  \n"
            f"_Why it fits:_ matched on {sig}.  \n"
            f"_What you’ll learn early:_ department intros + foundational tools.  \n"
            f"_Early career roles:_ {roles}.  \n"
            f"_Clubs/portfolio:_ {clubs}."
        )
    plan_md = fallback_plan(top["name"], ent, notes)
    return "\n".join([
        f"# {title}",
        "\n## Overview",
        "Recommendations ranked by how strongly your strengths, goals, interests, and experience match each program.",
        "\n## Top 5 Recommendations",
        "\n\n".join(lines),
        "\n## Chronological Plan",
        plan_md,
        "\n## Next Steps",
        "- Attend two club meetings aligned to your top 2 matches.\n"
        "- Book a 20-minute chat with a junior/senior and one academic advisor.\n"
        "- Start a 1–2 week project that showcases your tools.\n"
        "- Refresh resume and LinkedIn; queue 5 targeted applications.",
    ])

# =========================
# Schemas for Workbench (optional but nice)
# =========================
SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
    "course-major-recommender": [
        {"key":"intakeA","title":"Intake A","note":"Academic strengths, career goals, interests.","fields":[
            {"type":"textarea","name":"a.strengths","label":"Academic strengths (subjects, grades)","full":True},
            {"type":"textarea","name":"a.goals","label":"Career goals","full":True},
            {"type":"textarea","name":"a.interests","label":"Interests & hobbies","full":True},
        ]},
        {"key":"intakeB","title":"Intake B","note":"Experience, regions, constraints.","fields":[
            {"type":"textarea","name":"b.experience","label":"Relevant experience","full":True},
            {"type":"textarea","name":"b.regions","label":"Preferred regions","full":True},
            {"type":"textarea","name":"b.constraints","label":"Constraints or preferences","full":True},
        ]},
        {"key":"review","title":"Review & Generate","note":"Optional notes.","fields":[
            {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
        ]},
    ],
    "engineering-major-recommender": [
        {"key":"engA","title":"Intake A","note":"Strengths, goals, interests.","fields":[
            {"type":"textarea","name":"e.strengths","label":"Technical strengths","full":True},
            {"type":"textarea","name":"e.goals","label":"Career goals","full":True},
            {"type":"textarea","name":"e.interests","label":"Interests","full":True},
        ]},
        {"key":"engB","title":"Intake B","note":"Experience & preferences.","fields":[
            {"type":"textarea","name":"e.experience","label":"Projects / labs / comps","full":True},
            {"type":"select","name":"e.math_readiness","label":"Math readiness","options":["Pre-Calc","Calculus I","Calculus II+"]},
            {"type":"select","name":"e.physics_readiness","label":"Physics readiness","options":["None","Mechanics","E&M / Waves"]},
            {"type":"textarea","name":"e.preferences","label":"Preferences","full":True},
            {"type":"textarea","name":"e.constraints","label":"Constraints","full":True},
        ]},
        {"key":"review","title":"Review & Generate","note":"Optional notes.","fields":[
            {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
        ]},
    ],
    "mining-major-recommender": [
        {"key":"minA","title":"Intake A","note":"Background & goals.","fields":[
            {"type":"textarea","name":"m.strengths","label":"Strengths","full":True},
            {"type":"textarea","name":"m.goals","label":"Career goals","full":True},
            {"type":"textarea","name":"m.interests","label":"Interests","full":True},
        ]},
        {"key":"minB","title":"Intake B","note":"Experience, regions, constraints.","fields":[
            {"type":"textarea","name":"m.experience","label":"Experience","full":True},
            {"type":"select","name":"m.fieldwork_tolerance","label":"Fieldwork tolerance","options":["Low","Medium","High"]},
            {"type":"textarea","name":"m.regions","label":"Preferred regions","full":True},
            {"type":"textarea","name":"m.constraints","label":"Constraints","full":True},
        ]},
        {"key":"review","title":"Review & Generate","note":"Optional notes.","fields":[
            {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
        ]},
    ],
    "stem-major-recommender": [
        {"key":"sA","title":"Intake A","note":"Strengths, goals, interests.","fields":[
            {"type":"textarea","name":"s.strengths","label":"Strengths","full":True},
            {"type":"textarea","name":"s.goals","label":"Career goals","full":True},
            {"type":"select","name":"s.track","label":"Preferred track","options":["Industry","Research","Open / Unsure"]},
            {"type":"textarea","name":"s.interests","label":"Interests","full":True},
        ]},
        {"key":"sB","title":"Intake B","note":"Experience & constraints.","fields":[
            {"type":"textarea","name":"s.experience","label":"Projects / labs / internships","full":True},
            {"type":"textarea","name":"s.constraints","label":"Constraints or preferences","full":True},
            {"type":"textarea","name":"review.notes","label":"Additional notes (optional)","full":True},
        ]},
    ],
}

AGENT_LIST = [
    {
        "slug": "course-major-recommender",
        "name": "Eller Major Recommender",
        "emoji": "🎓",
        "endpoint": "/api/course-major-recommender/chat",
        "description": "Rank Eller BSBA majors from most-to-least fit and generate a chronological 4-year plan. Entrepreneurship is scheduled senior-year.",
    },
    {
        "slug": "engineering-major-recommender",
        "name": "Engineering Major Recommender",
        "emoji": "🛠️",
        "endpoint": "/api/engineering-major-recommender/chat",
        "description": "Match UArizona engineering majors to your profile; staged math/science + design plan.",
    },
    {
        "slug": "mining-major-recommender",
        "name": "Mining & Related Recommender",
        "emoji": "⛏️",
        "endpoint": "/api/mining-major-recommender/chat",
        "description": "Assess fit for Mining, Geological, Materials, Hydrology, and adjacent energy/earth disciplines.",
    },
    {
        "slug": "stem-major-recommender",
        "name": "STEM Major Recommender",
        "emoji": "🧪",
        "endpoint": "/api/stem-major-recommender/chat",
        "description": "Recommend STEM pathways (CS, DS/Stats, ECE/Robotics, Mech/Aero, Math, Bio, Chem, Env, Materials).",
    },
]

# =========================
# Routes
# =========================

@app.route("/")
def index():
    # Serve whatever "index.html" you dropped next to app.py (or set FRONTEND_FILE)
    if os.path.exists(FRONTEND_FILE):
        return send_from_directory(".", FRONTEND_FILE)
    # fallback: any of the provided HTML files
    for fallback in ("templates/index.html", "Key-vφid • Agent Workbench (onyx + Gold).html", "index.htm"):
        if os.path.exists(fallback):
            directory, fname = os.path.split(fallback)
            return send_from_directory(directory or ".", fname)
    return "Key-VΦid backend is running. Place your index.html next to app.py."

@app.route("/api/agents", methods=["GET"])
def list_agents():
    # Workbench discovers agents from here
    return jsonify(AGENT_LIST)

@app.route("/api/<slug>/schema", methods=["GET"])
def get_schema(slug: str):
    schema = SCHEMAS.get(slug)
    if not schema:
        return jsonify({"error": f"No schema for {slug}"}), 404
    return jsonify({"schema": schema})

@app.route("/api/<slug>/chat", methods=["POST"])
def chat(slug: str):
    if slug not in CATALOGS:
        return jsonify({"error": f"Unknown agent slug: {slug}"}), 404

    payload = request.get_json(force=True) or {}
    structured = payload.get("structured_input") or {}

    # Flatten likely shapes from the Workbench into a single intake text blob
    # Eller shape
    strengths = (
        structured.get("a", {}).get("strengths")
        or structured.get("e", {}).get("strengths")
        or structured.get("m", {}).get("strengths")
        or structured.get("s", {}).get("strengths")
        or ""
    )
    goals = (
        structured.get("a", {}).get("goals")
        or structured.get("e", {}).get("goals")
        or structured.get("m", {}).get("goals")
        or structured.get("s", {}).get("goals")
        or ""
    )
    interests = (
        structured.get("a", {}).get("interests")
        or structured.get("e", {}).get("interests")
        or structured.get("m", {}).get("interests")
        or structured.get("s", {}).get("interests")
        or ""
    )
    experience = (
        structured.get("b", {}).get("experience")
        or structured.get("e", {}).get("experience")
        or structured.get("m", {}).get("experience")
        or structured.get("s", {}).get("experience")
        or ""
    )
    regions = (
        structured.get("b", {}).get("regions")
        or structured.get("m", {}).get("regions")
        or ""
    )
    constraints = (
        structured.get("b", {}).get("constraints")
        or structured.get("e", {}).get("constraints")
        or structured.get("m", {}).get("constraints")
        or structured.get("s", {}).get("constraints")
        or ""
    )

    intake = {
        "strengths": strengths,
        "goals": goals,
        "interests": interests,
        "experience": experience,
        "regions": regions,
        "constraints": constraints,
    }

    # Build the ingestion text (also scrape any pasted URLs)
    text_parts = [strengths, goals, interests, experience, regions, constraints]
    for u in URL_PATTERN.findall(" ".join(text_parts)):
        scraped = fetch_text(u, 160)
        if scraped:
            text_parts.append(scraped)

    # Rank by keywords (most → least)
    catalog = CATALOGS[slug]
    ranked = rank_catalog("\n".join(text_parts), catalog)
    constraint_notes = parse_constraints_notes(constraints)

    # Try LLM report first (it must honor ranking order & omit percentages)
    markdown_report = ""
    try:
        markdown_report = model_report(slug, intake, ranked, constraint_notes)
    except Exception as e:
        logger.info(f"LLM unavailable or failed ({e}); using fallback renderer.")
        markdown_report = fallback_report(slug, intake, ranked, constraint_notes)

    # Ship both the human text and the machine-readable ranking
    return jsonify({
        "markdown_report": markdown_report,
        "ranking": [
            {"id": r["id"], "name": r["name"], "score": r["norm"], "hits": r["hits"]}
            for r in ranked
        ],
        "intake": intake,
    })

# =========================
# Run
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
