import streamlit as st
import os
import zipfile
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI

# ------------------ ENV SETUP ------------------
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("gemini")

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="AI-Powered Resume to Portfolio Website Generator",
    page_icon="📰",
    layout="centered"
)

# ------------------ PROMPTS ------------------
RESUME_TO_SPEC_PROMPT = """
You are an expert career coach and portfolio website strategist.

Task: Read the full resume text provided by the user and produce a structured website specification
for a personal portfolio.

The output MUST be a well-structured description (not code) that clearly defines:
- Name and headline/tagline
- Short bio / about section (2–3 sentences)
- Skills (grouped by categories if possible)
- Experience (roles, companies, dates, 2–3 bullet points each)
- Projects (name, brief description, tech stack, links if given)
- Achievements / awards / certifications
- Education
- Contact info (email, phone, location, portfolio links if any)
- Design style (e.g., modern, minimal, dark/light theme, preferred colors inferred from resume if any)

Write this as a clear narrative and bullet points that an engineer could use
to design a portfolio website.
"""

SPEC_TO_WEBSITE_PROMPT = """
You are a senior frontend engineer and UI/UX expert.

Goal:
Generate a complete, production-ready static portfolio website based ONLY on the structured website
specification provided by the user (not the raw resume).

Requirements:
- Use modern, semantic HTML5 structure (header, main, section, footer, etc.).
- Add clear sections: hero, skills, experience, projects, education, achievements, contact, and any
  extra sections mentioned in the specification.
- Ensure the layout is responsive and mobile-friendly using flexbox or CSS grid (no CSS frameworks).
- Use clean, readable class names and consistent indentation.
- Do NOT include inline CSS or inline JavaScript inside the HTML.

Styling:
- Provide all styling in a separate CSS file.
- Use a modern look with good spacing, hierarchy, and accessible color contrast.
- Import a simple Google Font (e.g., "Poppins" or "Inter") in the CSS.
- Include hover states for buttons and links.
- Respect any style or color hints present in the specification.

Behavior (JavaScript):
- Only write vanilla JavaScript.
- If there is a navbar with internal links, implement smooth scrolling.
- Add small, useful interactions if relevant (e.g., mobile nav toggle, simple fade-in animations,
  FAQ accordion, etc.).
- Do NOT use external JS libraries or frameworks.

Output format (STRICT):
Return your answer in EXACTLY this structure with no extra text, comments, or explanations:

--html--
[HTML CODE]
--html--
--css--
[CSS CODE]
--css--
--js--
[JS CODE]
--js--
"""

# ------------------ HELPERS ------------------
def extract_block(text, tag):
    parts = text.split(f"--{tag}--")
    if len(parts) < 3:
        return None
    return parts[1].strip()

def extract_pdf_text(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_docx_text(file):
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs)

# ------------------ SESSION STATE ------------------
if "specification" not in st.session_state:
    st.session_state.specification = None

# ------------------ UI ------------------
st.title("AI-POWERED RESUME TO PORTFOLIO WEBSITE GENERATOR")
st.caption("Turn your resume or idea into a professional portfolio website")

st.sidebar.title("⚙️ Input Settings")
input_mode = st.sidebar.radio(
    "Choose Input Method",
    ("Manual Prompt", "Upload Resume")
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Resume2Web AI automatically creates a modern portfolio website "
    "from your resume or description."
)

user_input = ""

# ------------------ INPUT HANDLING ------------------
if input_mode == "Manual Prompt":
    st.subheader("✍️ Manual Input")
    user_input = st.text_area(
        "Write your website specification or idea:",
        height=200
    )

elif input_mode == "Upload Resume":
    st.subheader("📄 Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF or DOCX)",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            user_input = extract_pdf_text(uploaded_file)
        elif uploaded_file.type == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            user_input = extract_docx_text(uploaded_file)
        else:
            st.error("Unsupported file type")

        st.success("Resume uploaded successfully ✅")

# ------------------ GENERATE WEBSITE ------------------
if st.button("Generate Website"):

    if not user_input.strip():
        st.warning("Please provide input before generating.")
        st.stop()

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7
    )

    # -------- STEP 1: Resume → Specification --------
    if input_mode == "Upload Resume":
        with st.spinner("Analyzing resume..."):
            spec_response = model.invoke([
                ("system", RESUME_TO_SPEC_PROMPT),
                ("user", user_input)
            ])

        st.session_state.specification = spec_response.content

        st.subheader("📄 Generated Website Specification")
        st.text_area(
            "Specification",
            st.session_state.specification,
            height=400
        )

    # -------- STEP 2: Manual Prompt --------
    if input_mode == "Manual Prompt":
        st.session_state.specification = user_input

    # -------- STEP 3: Specification → Website --------
    with st.spinner("Generating website files..."):
        site_response = model.invoke([
            ("system", SPEC_TO_WEBSITE_PROMPT),
            ("user", st.session_state.specification)
        ])

    content = site_response.content

    html_code = extract_block(content, "html")
    css_code = extract_block(content, "css")
    js_code = extract_block(content, "js")

    if not all([html_code, css_code, js_code]):
        st.error("AI output format error. Please retry.")
        st.text_area("Raw AI Output (Debug)", content, height=300)
        st.stop()

    # -------- STEP 4: SAVE FILES --------
    files = {
        "index.html": html_code,
        "style.css": css_code,
        "script.js": js_code
    }

    for name, code in files.items():
        with open(name, "w", encoding="utf-8") as f:
            f.write(code)

    # -------- STEP 5: ZIP + DOWNLOAD --------
    with zipfile.ZipFile("website.zip", "w") as zipf:
        for name in files:
            zipf.write(name)

    st.download_button(
        "⬇️ Download Website ZIP",
        data=open("website.zip", "rb"),
        file_name="website.zip"
    )

    st.success("🎉 Website generated successfully!")
