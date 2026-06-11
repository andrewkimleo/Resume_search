import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(docx_path):
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.XML(xml_content)
            WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            paragraphs = []
            for paragraph in tree.iter(WORD_NAMESPACE + 'p'):
                texts = [node.text for node in paragraph.iter(WORD_NAMESPACE + 't') if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
            return '\\n'.join(paragraphs)
    except Exception as e:
        return f"Error: {e}"

jd_path = r"d:\\VS_Code\\Projs\\Resume_search\\[PUB] India_runs_data_and_ai_challenge\\India_runs_data_and_ai_challenge\\job_description.docx"
text = extract_text_from_docx(jd_path)
with open(r"d:\\VS_Code\\Projs\\Resume_search\\jd.txt", "w", encoding="utf-8") as f:
    f.write(text)
