import requests
import os
import pypdf
import pandas as pd
import tiktoken

def download_file(link, download_dir="downloads"):
    try:
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        response = requests.get(link)
        filename = link.split("/")[-1]
        file_path = os.path.join(download_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    except Exception as e:
        print(f"Error occurred during file download: {e}")

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += (page.extract_text() or "")  # Ensure no None is added
        return text
    except Exception as e:
        print(f"Error occurred while reading PDF: {e}")
        return None

def create_token_chunks(text, encoding, chunk_size=123000, overlap=400):
    tokens = encoding.encode(text)
    chunks = []
    num_tokens = len(tokens)
    chunk_number = 0

    # Calculate the number of chunks needed
    num_chunks = (num_tokens - overlap) // (chunk_size - overlap) + 1

    for i in range(num_chunks):
        start = i * (chunk_size - overlap)
        end = start + chunk_size
        if end > num_tokens:
            end = num_tokens
        chunks.append((chunk_number, encoding.decode(tokens[start:end])))
        chunk_number += 1

    return chunks

def main():
    download_url = "https://www.govinfo.gov/content/pkg/COMPS-265/pdf/COMPS-265.pdf"
    pdf_path = download_file(download_url, download_dir="downloads/fdic")
    
    content = []
    if pdf_path:
        text = extract_text_from_pdf(pdf_path)
        if text:
            encoding = tiktoken.encoding_for_model("gpt-4o-mini")
            chunks = create_token_chunks(text, encoding)
            for i, chunk in enumerate(chunks):
                content.append((f"chunk_{i}", chunk))


    data = (pd.DataFrame()
    .assign(url = [_tuple[0] for _tuple in chunks])
    .assign(source = "FDIC")
    .assign(content = [_tuple[1] for _tuple in chunks])
    ).to_csv("downloads/fdic.csv",index=False)


if __name__ == "__main__":
    main()