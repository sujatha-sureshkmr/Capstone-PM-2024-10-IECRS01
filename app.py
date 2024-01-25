from flask import Flask, render_template, redirect, url_for, request, flash
app = Flask(__name__)


@app.route('/')
def index():
    name='sujatha'
    return render_template('index.html')

@app.route('/aienginnerguide.html')
def aienginnerguide():
   return render_template('aienginnerguide.html')

@app.route('/aidocumentprocessing.html')
def aidocumentprocessing():
   return render_template('aidocumentprocessing.html')

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


