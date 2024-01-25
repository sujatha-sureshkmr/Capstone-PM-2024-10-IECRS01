from flask import Flask, render_template, redirect, url_for, request, flash
import sys
sys.path.insert(0, './pythonlib')
import imghdr
import os
from glob import glob
import torch
import torchvision
import shutil
from flask import Flask, render_template, request, redirect, url_for, abort, \
    send_from_directory
from werkzeug.utils import secure_filename
#from roboflow import Roboflow
import pandas as pd
#from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
import xml.etree.ElementTree as ET
from PIL import Image
from PIL import ImageDraw
from pathlib import Path

app = Flask(__name__)


app.secret_key = 'super secret key'
model = YOLO('yolov5m.yaml')  # build a new model from scratch
#model = YOLO("static/models/t1a-v5m-640.pt")  # load a pretrained model (recommended for training)

model_2 = YOLO("yolov8m.yaml")  # build a new model from scratch
#model_2 = YOLO("static/models/Seg_v8_0904.pt")  # load a pretrained model (recommended for training)

calib_filename = os.path.join(os.path.join('static/', 'models'), 'savecoeefficients.xml')



app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg']
#app.config['UPLOAD_PATH'] = 'uploads'

app.config['UPLOAD_PATH'] = os.path.join('static/', 'uploads/')
app.config['PROCESSED_PATH'] = os.path.join('static/', 'processed/')
app.config['RECOGNIZED_PATH'] = os.path.join('static/', 'recognized/')
app.config['SEGMENT_PATH'] = os.path.join('static/', 'segment/')
app.config['MODEL_PATH'] = os.path.join('static/', 'models/')

hists=[]
for file in os.listdir('static/uploads'):
    if file.endswith('.jpg'):
        hists.append('static/uploads/'+file)


recgs=[]
for file in os.listdir('static/recognized'):
    if file.endswith('.jpg'):
        recgs.append('static/recognized/'+file)

process=[]
for file in os.listdir('static/processed'):
    if file.endswith('.jpg'):
        process.append('static/processed/'+file)

segment=[]
for file in os.listdir('static/segment'):
    if file.endswith('.jpg'):
        segment.append('static/segment/'+file)

   

objdmodels=[]
for file in os.listdir(app.config['MODEL_PATH']):
    if file.startswith('t'):
        objdmodels.append(file)
segmodels=[]
for file in os.listdir(app.config['MODEL_PATH']):
    if file.startswith('Seg'):
        segmodels.append(file)

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')
    
def load_from_opencv_xml(filename, elementname, dtype='float32'):
    try:
        tree = ET.parse(filename)
        rows = int(tree.find(elementname).find('rows').text)
        cols = int(tree.find(elementname).find('cols').text)
        return np.fromstring(tree.find(elementname).find('data').text, dtype, count=rows*cols, sep=' ').reshape((rows, cols))
    except Exception as e:
        print(e)
        return None

def get_zone(x1,y1):
    zone_div_x = 4096/3
    zone_div_y = 3000/3
    if x1 >= 0 and x1 <= zone_div_x and y1 >= 0 and y1 <= zone_div_y:
        return 8
    if x1 >= zone_div_x and x1 <= zone_div_x*2 and y1 >= 0 and y1 <= zone_div_y:
        print(x1,y1)
        return 1
    if x1 >= zone_div_x and x1 <= zone_div_x*3 and y1 >= 0 and y1 <= zone_div_y:
        return 2
    
    if x1 >= 0 and x1 <= zone_div_x and y1 >= zone_div_y and y1 <= zone_div_y*2:
        return 7
    if x1 >= zone_div_x and x1 <= zone_div_x*2 and y1 >= zone_div_y and y1 <= zone_div_y*2:
        return 0
    if x1 >= zone_div_x and x1 <= zone_div_x*3 and y1 >= zone_div_y and y1 <= zone_div_y*2:
        return 3
    
    if x1 >= 0 and x1 <= zone_div_x and y1 >= zone_div_y*2 and y1 <= zone_div_y*3:
        return 6
    if x1 >= zone_div_x and x1 <= zone_div_x*2 and y1 >= zone_div_y*2 and y1 <= zone_div_y*3:
        return 5
    if x1 >= zone_div_x and x1 <= zone_div_x*3 and y1 >= zone_div_y*2 and y1 <= zone_div_y*3:
        return 4
    else:
      return -1

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413



@app.route('/')
def index():
    df_ini = pd.read_csv(os.path.join(app.config['SEGMENT_PATH'], 'datapoints.csv'), header=0)
    #print(hists)
    return render_template('index.html', hists = hists,recgs=recgs,process=process,segment=segment,objdmodels=objdmodels,segmodels=segmodels,tables=[df_ini.to_html(classes=['data',"table-bordered", "table-striped", "table-hover"])], titles=df_ini.columns.values)


@app.route('/index.html', methods=['GET','POST'])
def upload_files():
    '''for filename_ups in Path(app.config['UPLOAD_PATH']).glob("*.jpg"):
        filename_ups.unlink()'''
    for zippath in Path('static/uploads/').glob("*"):
        #print('remove files',zippath)
        os.remove(zippath)
    for filename_pro in Path('static/processed/').glob("*"):
        os.remove(filename_pro)
    for filename_rec in Path('static/recognized/').glob("*.jpg"):
        os.remove(filename_rec)
    for filename_seg in Path('static/segment/').glob("*.jpg"):
        os.remove(filename_seg)
    '''
    for filename_pro in Path(app.config['PROCESSED_PATH']).glob("*.jpg"):
        print('filename_pro',filename_pro)
        filename_pro.unlink()
    for filename_rec in Path(app.config['RECOGNIZED_PATH']).glob("*.jpg"):
        filename_rec.unlink()
    for filename_seg in Path(app.config['SEGMENT_PATH']).glob("*.jpg"):
        filename_seg.unlink()'''

        
    print('file upload started')
    files = os.listdir(app.config['UPLOAD_PATH'])
    uploaded_file = request.files['file']
    print(uploaded_file)
    processed_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    print(filename)
    if filename != '':
        print('filename')
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return "Invalid image", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        print('Copied')

        hists = os.listdir(app.config['UPLOAD_PATH'] )
        recgs = os.listdir('static/recognized')
        process = os.listdir(app.config['PROCESSED_PATH'] )

        hists = [app.config['UPLOAD_PATH'] + file for file in hists]
        recgs = [app.config['RECOGNIZED_PATH'] + file for file in recgs]
        process = [app.config['PROCESSED_PATH']  + file for file in process]
            
        segment=[]
        for file in os.listdir(app.config['SEGMENT_PATH']):
            if file.endswith('.jpg'):
                segment.append(app.config['SEGMENT_PATH']+file)
                
    return render_template('index.html', files=files, hists = hists,recgs=recgs,process=process,segment=segment)


@app.route('/', methods=['GET','POST'])
def request_recognition():
    input_data = list(request.form.values())
    print(input_data)
    sel_objdmodel = input_data[0]
    print(sel_objdmodel)
    sel_segmodels = input_data[1]
    print(str(sel_segmodels))
    df2 = pd.DataFrame(columns=['date_time','filename','x1','y1','x2','y2','confidence','class','x_final_centre_point','y_final_centre_point','x_coordinate_in_mm','y_coordinate_in_mm','zone'])
    model = YOLO('static/models/'+sel_objdmodel)  # load a pretrained model (recommended for training)

    model_2 = YOLO('static/models/'+sel_segmodels)  # load a pretrained model (recommended for training)
    print('sel_objdmodel' ,sel_objdmodel)
    print('file transfer started')
    files = os.listdir(app.config['UPLOAD_PATH'])
    
    df = pd.DataFrame(recognition(model,model_2))
    df2 = df[['date_time','filename','x1','y1','x2','y2','confidence','class','x_final_centre_point','y_final_centre_point','x_coordinate_in_mm','y_coordinate_in_mm','zone']]
    hists = os.listdir('static/uploads')
    hists = ['static/uploads/' + file for file in hists]
    
    recgs=[]
    for file in os.listdir('static/recognized'):
        if file.endswith('.jpg'):
            recgs.append('static/recognized/'+file)
    
    process=[]
    for file in os.listdir('static/processed'):
        if file.endswith('.jpg'):
            process.append('static/processed/'+file)

    segment=[]
    for file in os.listdir('static/segment'):
        if file.endswith('.jpg'):
            segment.append('static/segment/'+file)

    objdmodels=[]
    for file in os.listdir('static/models'):
        if file.startswith('t'):
            objdmodels.append(file)
    segmodels=[]
    for file in os.listdir('static/models'):
        if file.startswith('Seg'):
            segmodels.append(file)
    
    #print(hists)
    return render_template('index.html', files=files, hists = hists,recgs=recgs,process=process,segment=segment,objdmodels=objdmodels,segmodels=segmodels,tables=[df.to_html(classes=['data',"table-bordered", "table-striped", "table-hover"])], titles=df.columns.values)

def cameracalibration(files):
    filename = os.path.basename(files)
    print(calib_filename)
    camera_matrix = load_from_opencv_xml(calib_filename, 'K', dtype='float32')
    dist_coeffs = load_from_opencv_xml(calib_filename, 'D', dtype='float32')
    
    print('camera_matrix : ',camera_matrix)
    print('dist_coeffs : ',dist_coeffs)

    img = cv2.imread(files)
    h, w = img.shape[:2]
    
    img = cv2.resize(img,(int(4096),int(3000)))

    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w,h), 1, (w,h))
    print(newcameramtx)
    print(roi)
    # undistort
    dst = cv2.undistort(img, camera_matrix, dist_coeffs, None, newcameramtx)
    #print(dst)
    # crop the image
    x, y, w, h = roi
    print(x,y,w,h)
    dst = dst[y:y+h, x:x+w]
    #print(dst)
    cv2.imwrite(os.path.join(app.config['PROCESSED_PATH'], filename), dst)
    return None 



def recognition(model,model_2):
    
    #device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    #sam_checkpoint = os.path.join(os.path.join('static/', 'models'),'sam_vit_h_4b8939.pth')
    #model_type = "vit_h"
    #sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    #predictor = SamPredictor(sam)
    
    # infer on a local image
    #print(model.predict(PATH_TO_IMAGE, confidence=40, overlap=30).json())
    
    df2 = pd.DataFrame(columns=['date_time','filename','x1','y1','x2','y2','confidence','class','x_final_centre_point','y_final_centre_point','x_coordinate_in_mm','y_coordinate_in_mm','zone'])
   
    for files in glob(app.config['UPLOAD_PATH']+"/*.jpg"):
        cameracalibration(files)
        print('complete')

    for files in glob(app.config['PROCESSED_PATH']+"/*.jpg"):
        filename = os.path.basename(files)
        # visualize your prediction
        results = model.predict(source=files, conf=0.2, save=True,project=app.config['RECOGNIZED_PATH'],exist_ok=True)
        df = pd.DataFrame(columns=['x1','y1','x2','y2','confidence','class'])
        bbox = []
        for result in results:
          boxes = result.boxes
          t=0
          for i in boxes:
            #print(i)
            xyxy = boxes.xyxy.tolist()[t]
            n = boxes.cls.tolist()[t]
            c = boxes.conf.tolist()[t]
            t+=1
            df.loc[len(df)] = [xyxy[0],xyxy[1],xyxy[2],xyxy[3],c,n]
            bbox.append(xyxy[0])
            bbox.append(xyxy[1])
        print(bbox)

        df['date_time']= pd.Timestamp("now")
        df['filename'] = filename
        df['center_x']=0
        df['center_y']=0
        df['crop_x1']=0
        df['crop_y1']=0
        df['zone']=-1
        df['polygon']=''
 
        df = df[df['class'] <= 10].reset_index()
        
        
        #df.to_csv(os.path.join(app.config['RECOGNIZED_PATH'], 'datapoints.csv'), encoding='utf-8', index=False)
        shutil.copy(os.path.join(os.path.join(app.config['RECOGNIZED_PATH'], 'predict'),filename), os.path.join(app.config['RECOGNIZED_PATH'], filename))
        image = cv2.cvtColor(cv2.imread(files), cv2.COLOR_BGR2RGB)
        #predictor.set_image(image)
        
        for ind in df.index:
            print(df['x1'][ind], df['y1'][ind],df['x2'][ind], df['y2'][ind])
            img = Image.open(os.path.join(app.config['PROCESSED_PATH'], filename))
            img2 = img.crop((df['x1'][ind], df['y1'][ind],df['x2'][ind], df['y2'][ind]))
            #img2.save(os.path.join(path,"img2.jpg"))
            results_2 = model_2.predict(source=img2, conf=0.2, save=True)
            for result_2 in results_2:
              boxes_2 = result_2.boxes.data

            for i in boxes_2:
              test_2 = i.tolist()
              df['crop_x1'][ind]=test_2[0]
              df['crop_y1'][ind]=test_2[1]

            #plt.imshow(new_image.astype(np.uint8))
            #display(img2)
            result_2 = results_2[0]
            masks = result_2.masks
            #len(masks)
            mask1 = masks[0]
            mask = mask1.data[0].numpy()
            polygon = mask1.xy[0]

            #print(polygon)
            mask_img = Image.fromarray(mask,"I")
            #mask_img

            img = img2
            draw = ImageDraw.Draw(img)
            draw.polygon(polygon,outline=(0,255,0), width=5)
            img
            num_vertices = len(polygon)
            center_x = sum(x for x, y in polygon) / num_vertices
            center_y = sum(y for x, y in polygon) / num_vertices
            print("Center Point:", (center_x, center_y))
            df['center_x'][ind]=center_x
            df['center_y'][ind]=center_y
            df['date_time'][ind] = pd.Timestamp("now").strftime('%d-%b-%Y %H:%M:%S')
            polygon2 = polygon
            for i in range(0,len(polygon2)):
                polygon2[i,0] = polygon2[i,0]+df['x1'][ind]
                polygon2[i,1] = polygon2[i,1]+df['y1'][ind]
            df['polygon'][ind] = polygon2
            
            #img = Image.open(os.path.join(path, "img2.jpg"))
        df['x_final_centre_point'] = df['x1']+df['center_x']
        df['y_final_centre_point'] = df['y1']+df['center_y']
        df['x_coordinate_in_mm'] = df['x_final_centre_point']*0.1697168
        df['y_coordinate_in_mm'] = df['y1']+df['center_y']*0.1697168
        img = Image.open(os.path.join(app.config['PROCESSED_PATH'], filename))
        draw = ImageDraw.Draw(img)
        #draw.polygon(polygon,outline=(0,255,0), width=5)
        radius = 5  # Adjust the size of the circle as needed
        fill_color = (255, 0, 0)  # Red color

        for ind in df.index:
          draw.ellipse(
            [(df['x_final_centre_point'][ind] - radius, df['y_final_centre_point'][ind] - radius), (df['x_final_centre_point'][ind] + radius, df['y_final_centre_point'][ind] + radius)],
            outline=(255, 0, 0),# Red color
            fill=fill_color  # Fill color (red)
          )
          draw.polygon(
            df['polygon'][ind],
            outline=(1, 249, 198),# teal color
            width=5  # Fill color (red)
          )

        img.save(os.path.join(app.config['SEGMENT_PATH'], filename))
        #print('Error state trouble shooting',df.shape)
        if len(df) >0:
            df['zone']= df.apply(lambda x: get_zone(x.x1,x.y1), axis=1)
        #df2 = 
        print('df2.shape PRE',df2.shape)
        print('df.shape',df.shape)
        df_inter = df[['date_time','filename','x1','y1','x2','y2','confidence','class','x_final_centre_point','y_final_centre_point','x_coordinate_in_mm','y_coordinate_in_mm','zone']]
        df2 = pd.concat([df2, df_inter], ignore_index=True)
        #df2.append(df[['date_time','filename','x1','y1','x2','y2','confidence','class','x_final_centre_point','y_final_centre_point','zone']])
        print('df2.shape POST',df2.shape)
        #files = os.listdir(app.config['UPLOAD_PATH'])
        
    
   
    hists = os.listdir('static/uploads')
    hists = ['static/uploads/' + file for file in hists]
    
    recgs = os.listdir('static/recognized')
    recgs = ['static/recognized/' + file for file in recgs]
    
    process = os.listdir('static/processed')
    process = ['static/processed/' + file for file in process]
    
    segment=[]
    for file in os.listdir('static/segment'):
        if file.endswith('.jpg'):
            segment.append('static/segment/'+file)
    #segment = ['static/segment/' + file for file in segment]
    #files = os.listdir('static/recognized/predict')
    dir_list = os.listdir('static/recognized/predict')
    for f in dir_list:
        print(os.path.join('static/recognized/predict',f))
        os.remove('static/recognized/predict/'+f)
    shutil.rmtree('runs', ignore_errors=True)

    objdmodels=[]
    for file in os.listdir('static/models'):
        if file.startswith('t'):
            objdmodels.append(file)
    segmodels=[]
    for file in os.listdir('static/models'):
        if file.startswith('Seg'):
            segmodels.append(file)
    df2.to_csv(os.path.join(app.config['SEGMENT_PATH'], 'datapoints.csv'), encoding='utf-8', index=False)
    
    return df2#render_template('index.html', files=files, hists = hists,recgs=recgs,process=process,segment=segment,tables=[df.to_html(classes='data')], titles=df.columns.values)
    