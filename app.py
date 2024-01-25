from flask import Flask, render_template, redirect, url_for, request, flash
app = Flask(__name__)
 
@app.route('/index.html')
def index():
    name='sujatha'
    return render_template('index.html')
 
if __name__ == '__main__':
   app.run()


