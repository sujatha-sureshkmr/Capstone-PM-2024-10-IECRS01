from flask import Flask, render_template, redirect, url_for, request, flash
import os
import sys
sys.path.insert(0, './pythonlib')
from pdfsplitfile import pdfsplitter

app = Flask(__name__)

app.config["UPLOAD_DIR"] = "static/uploads"
app.config["PROCESSING"] = "static/processing"

ALLOWED_EXTENSIONS = {'doc', 'pdf', 'docx'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    name='sujatha'
    return render_template('index.html')

@app.route('/aienginnerguide.html')
def aienginnerguide():
   return render_template('aienginnerguide.html')


@app.route("/upload", methods = ["GET", "POST"])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        product_type = request.form["Product_Type"]
        file.save(os.path.join(app.config['UPLOAD_DIR'], file.filename))
        return render_template("aidocumentprocessing.html", msg = "File uplaoded successfully.")
    return render_template("aidocumentprocessing.html", msg = "")


@app.route('/aidocumentprocessing.html', methods = ["GET", "POST"])
def aidocumentprocessing():
   if request.method == 'POST':
        product_type = request.form["Product_Type"]
        product_manufacturer = request.form["Product_Manufacturer"]
        product_manufactured_year = request.form["Product_Manufactured_Year"]
        page_from = request.form["page_from"]
        page_to = request.form["page_to"]
         # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return render_template("aidocumentprocessing.html", msg = "No file part'")
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return render_template("aidocumentprocessing.html", msg = "No selected file")
        if file and allowed_file(file.filename):
            file_ext=file.filename.rsplit('.', 1)[1].lower()
            #out_folder = os.path.join(app.config['UPLOAD_DIR'], filename)
            filename=product_type+'_'+product_manufacturer+'_'+product_manufactured_year+'.'+file_ext
            file.save(os.path.join(app.config['PROCESSING'], filename))
            pdfsplitter(os.path.join(app.config['PROCESSING'], filename), app.config['UPLOAD_DIR'],filename,page_from, page_to) 
            #file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
            return render_template("aidocumentprocessing.html", msg = "File uplaoded successfully.")
        '''
        file = request.files['file']
        file_extention = filename.rsplit('.', 1)[1].lower()
        
        file.save(os.path.join(app.config['UPLOAD_DIR'], file_name))
        return render_template("aidocumentprocessing.html", msg = "File uplaoded successfully.")'''
   return render_template("aidocumentprocessing.html", msg = "")

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


