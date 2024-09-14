from flask import Flask, render_template, request, flash, session
from flask_socketio import SocketIO, emit
import os
import sys
import pandas as pd
import csv
import json
import re
import shutil

sys.path.insert(0, './pythonlib')
from pdfsplitfile import pdfsplitter
from pdf2contentintegrated import pdf2content_integrated
from doc2contentintegrated import doc2content_integrated
from aimodelbuild import aienginmodelbuild
from qa_write_query import main as qa_write_query_main
#from llm import llm
#from pdfsplitfile import pdfsplitter

app = Flask(__name__)
app.secret_key = 'sujatha'
socketio = SocketIO(app)

app.config["KDB_DIR"] = "static/knowledgedb"
app.config["MODEL_DIR"] = "static/models"
app.config["DROP_DOWNS"] = "static/dropdowns"

faiss_model_names = 'all-MiniLM-L6-v2'
qa_model_names = 'distilbert-base-uncased-distilled-squad'

product_type_file = os.path.join(app.config['DROP_DOWNS'], "product_type.txt")
product_manufacturer_file = os.path.join(app.config['DROP_DOWNS'], "product_manufacturer.txt")
product_manufactured_year_file = os.path.join(app.config['DROP_DOWNS'], "product_manufactured_year.txt")

global llmfolderstructure
llmfolderstructure = ""

ALLOWED_EXTENSIONS = {'pdf'}

def read_values_from_file(file_path):
    try:
        with open(file_path, "r") as f:
            values = f.read().splitlines()
           
        return values
    except FileNotFoundError:
        return []
def custom_enumerate(iterable):
    return zip(range(len(iterable)), iterable)

def createdir(dir):
    if not os.path.exists(dir):
            os.makedirs(dir)
            print(f"Directory '{dir}' created.")

@app.route('/save', methods=['POST'])   
def save():
    print('stage-save')
    current_data = []
    for key, value in request.form.items():
        if '_' in key:
            try:
                index, column_name = key.split('_')
                index = int(index)
                while len(current_data) <= index:
                    current_data.append({})
                current_data[index][column_name] = value
            except ValueError:
                print(f"Issue with key: {key}")

    # Merge original data with current changes
    original_data = session.get('original_data', [])
    merged_data = original_data[:]
    for i, row in enumerate(current_data):
        if i < len(merged_data):
            for key, value in row.items():
                merged_data[i][key] = value
        else:
            merged_data.append(row)

    # Write merged data to a CSV file
    fieldnames = merged_data[0].keys()
    with open('output.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)

    return "Data saved successfully!"


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
               source_filename_pdf=f"{filename}.{file_ext}"
               KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], filename)
               if os.path.exists(KDB_PRODUCT_DIR):
                    # Delete the folder and all its contents
                    shutil.rmtree(KDB_PRODUCT_DIR)
                    print(f"The folder '{KDB_PRODUCT_DIR}' has been deleted.")

               app.config["UPLOAD_DIR"] = os.path.join(KDB_PRODUCT_DIR, "uploads")
               app.config["PROCESSING"] = os.path.join(KDB_PRODUCT_DIR, "processing")
               app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
               app.config["IMG_FOLDER"] = os.path.join(KDB_PRODUCT_DIR, "img_folder")
               app.config["CONFIRMED_KDB"] = os.path.join(KDB_PRODUCT_DIR, "confirmedkdb")
               createdir(KDB_PRODUCT_DIR)
               createdir(app.config["UPLOAD_DIR"])
               createdir(app.config["PROCESSING"] )
               createdir(app.config["KNOWLEDGE_GRAPH"])
               createdir(app.config["IMG_FOLDER"])
               createdir(app.config["CONFIRMED_KDB"] )
               createdir(os.path.join(app.config["IMG_FOLDER"], "segmentimages"))
               main_component_file_path=os.path.join(app.config['CONFIRMED_KDB'], 'main_component.txt')
               with open(main_component_file_path, 'w') as file_name:
                    print('main_component.txt file creation completed')
                    file_name.write("")
                    pass
               sub_component_file_path=os.path.join(app.config['CONFIRMED_KDB'], 'sub_component.txt')
               with open(sub_component_file_path, 'w') as file_name:
                    print('sub_component.txt file creation completed')
                    file_name.write("")
                    pass
                
               print('main_component.txt file creation completed')
               #source_filename_data=f"{product_type}_{product_manufacturer}_{product_manufactured_year}_kg_data.csv"
               #source_filename_image=f"{product_type}_{product_manufacturer}_{product_manufactured_year}_kg_image.csv"
               if page_checked == 'on':
                  file.save(os.path.join(app.config['PROCESSING'], source_filename_pdf))
                
                  pdfsplitter(os.path.join(app.config['PROCESSING'], source_filename_pdf), app.config['UPLOAD_DIR'],
                                source_filename_pdf, page_from, page_to)                      
                  pdf2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename,app.config["MODEL_DIR"],app.config["IMG_FOLDER"],app.config["CONFIRMED_KDB"])
                  #doc2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
                  #qa_write_query_main('write',faiss_model_names,qa_model_names,app.config['KNOWLEDGE_GRAPH']+"/",os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf))
                  qa_write_query_main('write',faiss_model_names,qa_model_names,KDB_PRODUCT_DIR,os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf))
               else:
                  #filename = filename+f"
                  file.save(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf))
                  pdf2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename,app.config["MODEL_DIR"],app.config["IMG_FOLDER"],app.config["CONFIRMED_KDB"])
                  qa_write_query_main('write',faiss_model_names,qa_model_names,KDB_PRODUCT_DIR,os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf))
                  #file.save(os.path.join(app.config['KNOWLEDGE_GRAPH'], source_filename_pdf))
                  #doc2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
                  #shutil.copy(os.path.join(app.config['UPLOAD_DIR'], faiss_model_names+'_data.csv'), os.path.join(app.config['CONFIRMED_KDB'], faiss_model_names+'_data.csv'))
               #source_knowledge_graph = os.path.join(app.config['UPLOAD_DIR'], filename+"."+f"{file_ext}")
               #pdf2content_integrated(os.path.join(app.config['UPLOAD_DIR'], source_filename_pdf), app.config['KNOWLEDGE_GRAPH'],filename)
               try:
                    with open(product_type_file, "r") as f:
                        product_types = set(f.read().splitlines())
               except FileNotFoundError:
                    product_types = set()

               print('product_type file creation completed')
               try:
                    with open(product_manufacturer_file, "r") as f:
                        product_manufacturers = set(f.read().splitlines())
               except FileNotFoundError:
                    product_manufacturers = set()

               print('product_manufacturer_file file creation completed')
               try:
                    with open(product_manufactured_year_file, "r") as f:
                        product_years = set(f.read().splitlines())
               except FileNotFoundError:
                    product_years = set()

               print('product_years file creation completed')
               if product_type not in product_types:
                    with open(product_type_file, "a") as f:
                        f.write(product_type + "\n")
                        f.close()
               if product_manufacturer not in product_manufacturers:
                    with open(product_manufacturer_file, "a") as f:
                        f.write(product_manufacturer + "\n")
                        f.close()
               if product_manufactured_year not in product_years:
                    with open(product_manufactured_year_file, "a") as f:
                        f.write(product_manufactured_year + "\n")
                        f.close()

               return render_template("aidocumentprocessing.html", msg="File uploaded successfully.")
    except Exception as error:
        print("An exception occurred:", error)
        exc_type, fname, lineno = sys.exc_info()
        print(exc_type, fname, lineno)
        
    return render_template("aidocumentprocessing.html", msg="")


@app.route('/aimodeltraining.html', methods=["GET", "POST"])
def aimodeltraining():
    product_types = read_values_from_file(product_type_file)
    product_manufacturers = read_values_from_file(product_manufacturer_file)
    product_years = read_values_from_file(product_manufactured_year_file)
   
    
    filenamebeginswith=''
    try:
            if request.method == 'POST':
                print('print statement: Post Method')
                print('print statement: stage 1 :',request.form)
                if 'extract' in request.form:
                    read_product_type = request.form["product_type"]
                    read_product_manufacturer = request.form["product_manufacturer"]
                    read_product_manufactured_year = request.form["manufactured_year"]
                    print('print statement: stage 2 : read_product_manufactured_year ')

                    session['read_product_type'] = read_product_type
                    session['read_product_manufacturer'] = read_product_manufacturer
                    session['read_product_manufactured_year'] = read_product_manufactured_year
                    
                    #filenamebeginswith = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    folderstructure=f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    
                    KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], folderstructure)
                    app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
                    app.config["IMG_FOLDER"] = os.path.join(KDB_PRODUCT_DIR, "img_folder")
                    app.config["CONFIRMED_KDB"] = os.path.join(KDB_PRODUCT_DIR, "confirmedkdb")
                    datafilename = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}_kdb_data.csv"

                    main_component = read_values_from_file(os.path.join(app.config["CONFIRMED_KDB"], "main_component.txt"))
                    sub_component = read_values_from_file( os.path.join(app.config["CONFIRMED_KDB"], "sub_component.txt"))
                    session['main_component'] = main_component
                    session['sub_component'] = sub_component
                    
                    return render_template('/aimodeltraining.html',main_component=main_component,sub_component=sub_component,product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years)
               
                print(request.form)
                if 'fetchkdb' in request.form:
                    main_component_flag = ''
                    print('print statement: fetchkdb Name post method')
                    read_main_component = request.form["main_component"]
                    read_sub_component = request.form["sub_component"]

                    print('print statement stage 1 : main_component,subcomponent',read_main_component,read_sub_component)
                    read_product_type = session.get('read_product_type')
                    print('print statement stage 2 : session.get',session.get('read_product_type'))
                    read_product_manufacturer = session.get("read_product_manufacturer")
                    read_product_manufactured_year = session.get("read_product_manufactured_year")
                    main_component = session.get("main_component")
                    sub_component = session.get("sub_component")
                    
                    folderstructure=f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    
                    KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], folderstructure)
                    app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
                    app.config["IMG_FOLDER"] = os.path.join(KDB_PRODUCT_DIR, "img_folder")
                    app.config["CONFIRMED_KDB"] = os.path.join(KDB_PRODUCT_DIR, "confirmedkdb")
                    datafilename = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}_kdb_data.csv"
                    aiengineerextract_folder = os.path.join(app.config["CONFIRMED_KDB"], datafilename)
                    print('main_component_df',read_main_component)
                    print('sub_component_df',read_sub_component)
                    aiengineerextract = pd.DataFrame(pd.read_csv(os.path.join(app.config["CONFIRMED_KDB"], datafilename)))
                    print('aiengineerextract.shape',aiengineerextract.shape)
                    aiengineerextract['cc_segment_image'] = aiengineerextract.apply(lambda row: app.config["IMG_FOLDER"]+"/segmentimages/"+row['cc_segment_image']  if '_CC_' in row['cc_segment_image'] else app.config["IMG_FOLDER"]+"/"+row['cc_segment_image'],axis=1 )

                    #aiengineerextract['cc_segment_image'] = app.config["IMG_FOLDER"]+"/segmentimages/"+aiengineerextract['cc_segment_image'] 
                    #main_component_df = aiengineerextract[(aiengineerextract['Header_image'] == 'read_main_component')]
                    sub_component_check_df = aiengineerextract[(aiengineerextract['Header_image'] == read_main_component) & (aiengineerextract['Text'] == read_sub_component)]
                    sub_component_df = aiengineerextract[(aiengineerextract['Text'] == read_sub_component)]
                    
                    showcase_df = aiengineerextract[aiengineerextract['Header_image'].isin(sub_component_df['Header_image'])]
                    parent_header_image_main = showcase_df['Header_image'].unique()
                    print('parent_header_image_main',parent_header_image_main)
                    column_to_check = 'Text'

                    duplicates_mask = showcase_df[showcase_df.duplicated(subset=[column_to_check], keep=False)]
                    print('duplicates_mask.shape',duplicates_mask.shape)
                    print('showcase_df.shape',showcase_df.shape)
                    if sub_component_check_df.empty:
                        main_component_flag = 'You have chosen incorrect main component. The results below is based on the sub component you have chosen.'
                        item = None
                    processed_list=[]
                    for item in parent_header_image_main:
                        modified_string = re.sub(r'[^\w]' , '', item)
                        parent_Header_image = ''.join(e for e in modified_string if e.isalnum())+'.png'
                        print('parent_Header_image',parent_Header_image)
                        item = app.config["IMG_FOLDER"]+'/knowledgegraph/'+parent_Header_image
                        processed_list.append(item)
                    print('process complete')
                    columns = showcase_df.columns.tolist()
                    data = showcase_df.to_dict(orient="records")
                    enumerated_data = custom_enumerate(data)

                    if duplicates_mask.shape[0]>=1:
                        dup_columns = duplicates_mask.columns.tolist()
                        dup_data = duplicates_mask.to_dict(orient="records")
                        dup_enumerated_data = custom_enumerate(dup_data)
                    else:
                        dup_columns=[]  
                        dup_data={}
                        dup_enumerated_data=None
                    return render_template('/aimodeltraining.html',knowledgedbgraph=processed_list,aiengineerextract_folder=aiengineerextract_folder,dup_data=dup_enumerated_data, dup_columns=dup_columns,data=enumerated_data, columns=columns,main_component_flag= main_component_flag,main_component=main_component,sub_component=sub_component,product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years)

                return render_template('/aimodeltraining.html',main_component=main_component,sub_component=sub_component,product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years)
                
    except Exception as error:
        print("An exception occurred:", error)
        exc_type, fname, lineno = sys.exc_info()
        print(exc_type, fname, lineno)
    
    return render_template("aimodeltraining.html",product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years,filenamebeginswith=filenamebeginswith)
    #return render_template("aimodeltraining.html", "")

#product_types=product_types, product_manufacturers=product_manufacturers, product_years=product_years,filenamebeginswith=filenamebeginswith)


@app.route('/mechenginnerguide.html', methods=["GET", "POST"])
def mechenginnerguide():
    return render_template('mechenginnerguide.html')


@app.route('/mechchatbotmanual.html', methods=["GET", "POST"])
def mechchatbotmanual():
    print('mechchatbotmanual begins')
    product_types = read_values_from_file(product_type_file)
    product_manufacturers = read_values_from_file(product_manufacturer_file)
    product_years = read_values_from_file(product_manufactured_year_file)
    filenamebeginswith=''
    print('product_types',product_types)
    try:
            if request.method == 'POST':
                print('print statement: Post Method')
                print('print statement: stage 1 :',request.form)
                if 'extract' in request.form:
                    read_product_type = request.form["product_type"]
                    read_product_manufacturer = request.form["product_manufacturer"]
                    read_product_manufactured_year = request.form["manufactured_year"]
                    print('print statement: stage 2 : read_product_manufactured_year ')

                    session['read_product_type'] = read_product_type
                    session['read_product_manufacturer'] = read_product_manufacturer
                    session['read_product_manufactured_year'] = read_product_manufactured_year
                    
                    #filenamebeginswith = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    folderstructure=f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    
                    KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], folderstructure)
                    app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
                    app.config["IMG_FOLDER"] = os.path.join(KDB_PRODUCT_DIR, "img_folder")
                    app.config["CONFIRMED_KDB"] = os.path.join(KDB_PRODUCT_DIR, "confirmedkdb")
                    datafilename = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}_kdb_data.csv"

                    main_component = read_values_from_file(os.path.join(app.config["CONFIRMED_KDB"], "main_component.txt"))
                    sub_component = read_values_from_file( os.path.join(app.config["CONFIRMED_KDB"], "sub_component.txt"))
                    session['main_component'] = main_component
                    session['sub_component'] = sub_component
                    
                    return render_template('/mechchatbotmanual.html',main_component=main_component,sub_component=sub_component,product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years)
               
                print(request.form)
                if 'fetchkdb' in request.form:
                    main_component_flag = ''
                    print('print statement: fetchkdb Name post method')
                    read_main_component = request.form["main_component"]
                    read_sub_component = request.form["sub_component"]

                    print('print statement stage 1 : main_component,subcomponent',read_main_component,read_sub_component)
                    read_product_type = session.get('read_product_type')
                    print('print statement stage 2 : session.get',session.get('read_product_type'))
                    read_product_manufacturer = session.get("read_product_manufacturer")
                    read_product_manufactured_year = session.get("read_product_manufactured_year")
                    main_component = session.get("main_component")
                    sub_component = session.get("sub_component")
                    
                    folderstructure=f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    
                    KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], folderstructure)
                    app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
                    app.config["IMG_FOLDER"] = os.path.join(KDB_PRODUCT_DIR, "img_folder")
                    app.config["CONFIRMED_KDB"] = os.path.join(KDB_PRODUCT_DIR, "confirmedkdb")
                    datafilename = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}_kdb_data.csv"
                    aiengineerextract_folder = os.path.join(app.config["CONFIRMED_KDB"], datafilename)
                    print('main_component_df',read_main_component)
                    print('sub_component_df',read_sub_component)
                    aiengineerextract = pd.DataFrame(pd.read_csv(os.path.join(app.config["CONFIRMED_KDB"], datafilename)))
                    print('aiengineerextract.shape',aiengineerextract.shape)
                    aiengineerextract['cc_segment_image'] = aiengineerextract.apply(lambda row: app.config["IMG_FOLDER"]+"/segmentimages/"+row['cc_segment_image']  if '_cc_' in row['cc_segment_image'] else app.config["IMG_FOLDER"]+"/"+row['cc_segment_image'],axis=1 )

                    #aiengineerextract['cc_segment_image'] = app.config["IMG_FOLDER"]+"/segmentimages/"+aiengineerextract['cc_segment_image'] 
                    #main_component_df = aiengineerextract[(aiengineerextract['Header_image'] == 'read_main_component')]
                    sub_component_check_df = aiengineerextract[(aiengineerextract['Header_image'] == read_main_component) & (aiengineerextract['Text'] == read_sub_component)]
                    sub_component_df = aiengineerextract[(aiengineerextract['Text'] == read_sub_component)]
                    
                    showcase_df = aiengineerextract[aiengineerextract['Header_image'].isin(sub_component_df['Header_image'])]
                    parent_header_image_main = showcase_df['Header_image'].unique()
                    print('parent_header_image_main',parent_header_image_main)
                    column_to_check = 'Text'

                    duplicates_mask = showcase_df[showcase_df.duplicated(subset=[column_to_check], keep=False)]
                    print('duplicates_mask.shape',duplicates_mask.shape)
                    print('showcase_df.shape',showcase_df.shape)
                    if sub_component_check_df.empty:
                        main_component_flag = 'You have chosen incorrect main component. The results below is based on the sub component you have chosen.'
                        item = None
                    processed_list=[]
                    for item in parent_header_image_main:
                        modified_string = re.sub(r'[^\w]' , '', item)
                        parent_Header_image = ''.join(e for e in modified_string if e.isalnum())+'.png'
                        print('parent_Header_image',parent_Header_image)
                        item = app.config["IMG_FOLDER"]+'/knowledgegraph/'+parent_Header_image
                        processed_list.append(item)
                    print('process complete')
                    columns = showcase_df.columns.tolist()
                    data = showcase_df.to_dict(orient="records")
                    enumerated_data = custom_enumerate(data)

                    if duplicates_mask.shape[0]>=1:
                        dup_columns = duplicates_mask.columns.tolist()
                        dup_data = duplicates_mask.to_dict(orient="records")
                        dup_enumerated_data = custom_enumerate(dup_data)
                    else:
                        dup_columns=[]  
                        dup_data={}
                        dup_enumerated_data=None
                    return render_template('/mechchatbotmanual.html',knowledgedbgraph=processed_list,aiengineerextract_folder=aiengineerextract_folder,dup_data=dup_enumerated_data, dup_columns=dup_columns,data=enumerated_data, columns=columns,main_component_flag= main_component_flag,main_component=main_component,sub_component=sub_component,product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years)

                return render_template('/mechchatbotmanual.html',main_component=main_component,sub_component=sub_component,product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years)
                
    except Exception as error:
        print("An exception occurred:", error)
        exc_type, fname, lineno = sys.exc_info()
        print(exc_type, fname, lineno)
    
    return render_template("mechchatbotmanual.html",product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years,filenamebeginswith=filenamebeginswith)
    #return render_template("aimodeltraining.html", "")


#@socketio.on('user_message')

@app.route('/chatbot.html', methods=["GET", "POST"])
def chatbot():
    product_types = read_values_from_file(product_type_file)
    product_manufacturers = read_values_from_file(product_manufacturer_file)
    product_years = read_values_from_file(product_manufactured_year_file)
    filenamebeginswith=''
    try:
            if request.method == 'POST':
                print('print statement: Post Method')
                print('print statement: stage 1 :',request.form)
                if 'extract' in request.form:
                    read_product_type = request.form["product_type"]
                    read_product_manufacturer = request.form["product_manufacturer"]
                    read_product_manufactured_year = request.form["manufactured_year"]
                    print('print statement: stage 2 : read_product_manufactured_year ')

                    session['read_product_type'] = read_product_type
                    session['read_product_manufacturer'] = read_product_manufacturer
                    session['read_product_manufactured_year'] = read_product_manufactured_year

                    app.config["KDB_DIR"] = "static/knowledgedb"
                    #filenamebeginswith = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    folderstructure=f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
                    
                    KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], folderstructure)
                    app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
                    
                    datafilename = f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}_kdb_data.csv"
                    global llmfolderstructure
                    #product_types=read_product_types,product_manufacturers=read_product_manufacturers,product_years=read_product_years
                    return render_template('/chatbot.html',product_types=read_product_type,product_manufacturers=read_product_manufacturer,product_years=read_product_year)
    except Exception as error:
        print("An exception occurred:", error)
        exc_type, fname, lineno = sys.exc_info()
        print(exc_type, fname, lineno)
    
    return render_template("chatbot.html",product_types=product_types,product_manufacturers=product_manufacturers,product_years=product_years,filenamebeginswith=filenamebeginswith)
    #return render_template("aimodeltraining.html", "")       
    #return render_template('mechchatbotllm.html')

@socketio.on('user_message')
def handle_message(data):
    components_list = []
    component_urls = {}
    unique_joint_list = []
    unique_joint_list = []
    user_message = data['message']
    read_product_type = data.get('product_type')
    read_product_manufacturer = data.get('product_manufacturer')
    read_product_manufactured_year = data.get('manufactured_year')
    app.config["KDB_DIR"] = "static/knowledgedb/"
    llmfolderstructure=f"{read_product_type}_{read_product_manufacturer}_{read_product_manufactured_year}"
    KDB_PRODUCT_DIR = os.path.join(app.config['KDB_DIR'], llmfolderstructure)
    app.config["KNOWLEDGE_GRAPH"] = os.path.join(KDB_PRODUCT_DIR, "knowledgedatabase")
    #/img_folder/segmentimages
    app.config["SEGMENTIMAGES"] = os.path.join(os.path.join(KDB_PRODUCT_DIR, "img_folder"),"segmentimages")
    folder_structure=KDB_PRODUCT_DIR+"/"
    print('llmfolderstructure',llmfolderstructure)
    if llmfolderstructure!='':
        llm_result = qa_write_query_main('query',faiss_model_names,qa_model_names,folder_structure, '',user_message)
        #decoded_text = llm_result.llmmodel()
        #print(llm_result.shape)
        response = llm_result[0]
        #print(response)
        components_list = list(llm_result[1])
        component_urls =  dict(llm_result[2])
        unique_tool_list = list(llm_result[3])
        unique_joint_list = list(llm_result[4])


    else:
        response='You havent chosen the product type, manufacturer and year. Please choose it and click submit and then try again.'
        components_list = []
        component_urls = {}
        unique_joint_list = []
        unique_joint_list = []
    print(components_list)
    print()
    #print(response)
    emit('bot_response', {'message': response, 'components_list':components_list,'component_urls':component_urls,'SEGMENTIMAGES':app.config["SEGMENTIMAGES"],'unique_tool_list':unique_tool_list,'unique_joint_list':unique_joint_list})
    #emit('bot_response', {'message': response, 'components_list':components_list,'component_urls':component_urls,'SEGMENTIMAGES':app.config["SEGMENTIMAGES"]})#,'unique_tool_list':unique_tool_list,'unique_joint_list':unique_joint_list})
if __name__ == '__main__':
    app.run()
