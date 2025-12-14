import streamlit as st
import dotenv
import langchain
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
import os
os.environ["GOOGLE_API_KEY"] = os.getenv("gemini")
import zipfile
from PyPDF2 import PdfReader  
from docx import Document

st.set_page_config(page_title = "AI Website Creation", page_icon = "📰", layout = "centered")

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

if input_mode == "Manual Prompt":
    st.subheader("✍️ Manual Input")
    user_input = st.text_area("Write here about the website you want to create:")

elif input_mode == "Upload Resume":
    st.subheader("📄 Upload Resume")
    uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"])

# ------------------ Extract text from uploaded resume ------------------
    def extract_pdf_text(file):
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def extract_docx_text(file):
        doc = Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text



    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            user_input = extract_pdf_text(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            user_input = extract_docx_text(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a PDF or DOCX file.")

        st.success("Resume uploaded successfully ✅")

# ------------------ Generate Website ------------------
if st.button("Generate Website"):

    if not user_input.strip():
        st.warning("Please upload a resume or enter a prompt before generating the website.")
        st.stop()

    message = [("system", """You are a expert in web development creating professional.
                so create html, css, javascript code for creating a frontend based on user prompt.
                    
                the output should be only contain clean code in the below format:
                    
                --html--
                <html code>
                --html--
                  
                --css--
                <css code>  
                --css--
                    
                --javascript--
                <javascript code>
                --javascript--"""
                )]
    message.append(("user", user_input))

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

    with st.spinner('Generating your portfolio website...'):
        response = model.invoke(message)


    with open("index.html", "w",) as file:
        file.write(response.content.split("--html--")[1].strip())

    with open("style.css", "w",) as file:
        file.write(response.content.split("--css--")[1].strip())

    with open("script.js", "w",) as file:
        file.write(response.content.split("--javascript--")[1].strip())

    with zipfile.ZipFile("website.zip", "w") as zip:
        zip.write("index.html")
        zip.write("style.css")
        zip.write("script.js")
    
    st.download_button("Click to Download", 
                        data=open("website.zip", "rb"), 
                        file_name="website.zip")

    st.success("Your website generated successfully!")