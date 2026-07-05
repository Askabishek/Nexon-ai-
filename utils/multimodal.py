import PyPDF2
import io
from PIL import Image
import base64


def extract_pdf_text(uploaded_file) -> str:
    """Extract text from uploaded PDF file."""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text[:3000]  # Limit context size
    except Exception as e:
        return f"[PDF extraction failed: {str(e)}]"


def extract_image_base64(uploaded_file) -> str:
    """Convert uploaded image to base64 string."""
    try:
        img = Image.open(uploaded_file)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        return ""


def get_file_context(uploaded_file) -> str:
    """
    Process uploaded file and return extracted text context.
    Supports: PDF, TXT, images (returns placeholder for images).
    """
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.type

    if file_type == "application/pdf":
        return extract_pdf_text(uploaded_file)
    elif file_type == "text/plain":
        return uploaded_file.read().decode("utf-8")[:3000]
    elif file_type.startswith("image/"):
        return "[Image uploaded — visual analysis not yet supported in this version]"
    else:
        return ""
