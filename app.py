from flask import Flask, render_template, request, flash
import os
import sys

sys.path.insert(0, './pythonlib')
from pdfsplitfile import pdfsplitter
from pdf2contentintegrated import pdf2content_integrated
from doc2contentintegrated import doc2content_integrated
#from pdfsplitfile import pdfsplitter

app = Flask(__name__)

app.config["UPLOAD_DIR"] = "static/uploads"
app.config["PROCESSING"] = "static/processing"
app.config["KNOWLEDGE_GRAPH"] = "static/knowledgegraph"

ALLOWED_EXTENSIONS = {'doc', 'pdf', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    name = 'sujatha'
    return render_template('index.html')


@app.route('/aienginnerguide.html')
def aienginnerguide():
    return render_template('aienginnerguide.html')


@app.route('/aidocumentprocessing.html', methods=["GET", "POST"])
def aidocumentprocessing():
    try:
        if request.method == 'POST':
            product_type = request.form["Product_Type"]
            product_manufacturer = request.form["Product_Manufacturer"]
            product_manufactured_year = request.form["Product_Manufactured_Year"]
            page_checked = request.form.get('checkbox_page')

            if page_checked == 'on':
                page_from = request.form["page_from"]
                page_to = request.form["page_to"]

            if 'file' not in request.files:
                flash('No file part')
                return render_template("aidocumentprocessing.html", msg="No file part'")
            
            file = request.files['file']
            
            if file.filename == '':
                flash('No selected file')
                return render_template("aidocumentprocessing.html", msg="No selected file")
            
            if file and allowed_file(file.filename):
               file_ext = file.filename.rsplit('.', 1)[1].lower()
               filename = f"{product_type}_{product_manufacturer}_{product_manufactured_year}"
               source_filename_pdf=f"{product_type}_{product_manufacturer}_{product_manufactured_year}.{file_ext}"
               #source_filename_data=f"{product_type}_{product_manufacturer}_{product_manufactured_year}_kg_data.csv"
               #source_filename_image=f"{product_type}_{product_manufacturer}_{product_manufactured_year}_kg_image.csv"
               if page_checked == 'on':
                  file.save(os.path.join(app.config['PROCESSING'], source_filename_pdf))
                  if file_ext == 'pdf':
                     pdfsplitter(os.path.join(app.config['PROCESSING'], source_filename_pdf), app.config['UPLOAD_DIR'],
                                 source_filename_pdf, page_from, page_to)                      
                     pdf2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
                  else:
                        doc2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
               else:
                  #filename = filename+f"
                  file.save(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf))
                  if file_ext == 'pdf':
                     pdf2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
                  else:
                     print(source_filename_pdf)
                     doc2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
                  
               #source_knowledge_graph = os.path.join(app.config['UPLOAD_DIR'], filename+"."+f"{file_ext}")
               #pdf2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
               return render_template("aidocumentprocessing.html", msg="File uploaded successfully.")
    except Exception as error:
        print("An exception occurred:", error)
        exc_type, fname, lineno = sys.exc_info()
        print(exc_type, fname, lineno)
        
    return render_template("aidocumentprocessing.html", msg="")


@app.route('/aimodeltraining.html')
def aimodeltraining():
    return render_template('aimodeltraining.html')


@app.route('/mechenginnerguide.html')
def mechenginnerguide():
    return render_template('mechenginnerguide.html')


@app.route('/mechchatbotmanual.html')
def mechchatbotmanual():
    return render_template('mechchatbotmanual.html')


@app.route('/mechchatbotllm.html')
def mechchatbotllm():
    return render_template('mechchatbotllm.html')


if __name__ == '__main__':
    app.run()
