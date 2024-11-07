import os
import pypdf
import pandas as pd
from tqdm import tqdm
import logging
import traceback
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(pdf_path):
    text = ""

    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()

    return text



def fix_pdf_error_stream(input_dir, output_dir):

    def reset_eof_of_pdf_return_stream(pdf_stream_in:list):
        # find the line position of the EOF
        actual_line = None
        for i, x in enumerate(txt[::-1]):
            if b'%%EOF' in x:
                actual_line = len(pdf_stream_in)-i
                print(f'EOF found at line position {-i} = actual {actual_line}, with value {x}')
                break

        # return the list up to that point
        return pdf_stream_in[:actual_line] if actual_line else pdf_stream_in

    # opens the file for reading
    with open(input_dir, 'rb') as p:
        txt = (p.readlines())

    # get the new list terminating correctly
    txtx = reset_eof_of_pdf_return_stream(txt)

    # write to new pdf
    with open(output_dir, 'wb') as f:
        f.writelines(txtx)


if __name__ == "__main__":
    output_root = "downloads/sec_pdfs_fixed"
    input_root = "downloads/sec_pdfs"

    os.makedirs(output_root,exist_ok=True)


    contents = []
    for pdf_file in tqdm(os.listdir(input_root)):
        input_file = os.path.join(input_root, pdf_file)
        output_file = os.path.join(output_root, pdf_file)

        #fix_pdf_error_stream(input_file,output_file)
        try:
            contents.append((input_file, extract_text_from_pdf(output_file)))
        except:
                try:
                    logging.error(f"Trouble parsing pdf file {pdf_file}. error: {traceback.print_exc()}")
                    fix_pdf_error_stream(input_file,output_file)
                    contents.append((input_file, extract_text_from_pdf(output_file)))

                except:
                    logging.error("sexius")
                    continue
            

    pd.DataFrame().assign(url = [_tuple[0] for _tuple in contents]).assign(source = "SEC").assign(content = [_tuple[1] for _tuple in contents]).to_csv("downloads/sec.csv",index=False)



