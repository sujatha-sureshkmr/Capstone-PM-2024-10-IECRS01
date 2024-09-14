### Confirmed pdf splitter

from pypdf import PdfReader, PdfWriter
class pdfsplitter:
    def __init__(self,source_pdf_file_path,out_folder,filename,page_from,page_to):
        self.source_pdf_file_path = source_pdf_file_path  
        self.out_folder = out_folder
        self.filename = filename
        self.page_from = page_from 
        self.page_to = page_to 
        pages = [(int(page_from), int(page_to))]
      
        # Open the PDF file
        pdf_reader = PdfReader(source_pdf_file_path)
        
        for page_indices in pages:
            pdf_writer = PdfWriter()  # we want to reset this when starting a new pdf
            for idx in range(page_indices[0] - 1, page_indices[1]):
                pdf_writer.add_page(pdf_reader.pages[idx])
            output_filename = f"{self.out_folder}/{self.filename}"  # Corrected the output filename
            with open(output_filename, "wb") as out:
                pdf_writer.write(out)