"""
Simple app to upload an image via a web form 
and view the inference results on the image in the browser.
"""
import argparse
import io
import os
from PIL import Image
import base64 
from flask_ngrok import run_with_ngrok

import torch
from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
run_with_ngrok(app) 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedBack.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class IMG(db.Model):
  id = db.Column(db.Integer,  primary_key=True)
  rendered_data = db.Column(db.Text, nullable=False)
  filename = db.Column(db.Text, nullable=False)

  def __init(self, rendered_data, filename):
    self.rendered_data = rendered_data
    self.filename = filename


class feedBack(db.Model):
  id = db.Column(db.Integer,  primary_key=True)
  text = db.Column(db.Text)
  name = db.Column(db.Text)
  email = db.Column(db.Text)

  def __init(self, text, name, mail):
    self.text = text
    self.name = name
    self.mail = mail


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
      formid = request.args.get('formid', 1, type=int)
      if formid == 1:
        if "file" not in request.files:
            return redirect(request.url)
        file = request.files["file"]
        if not file:
            return redirect(request.url)
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
          img_bytes = file.read()
          img_before = io.BytesIO(img_bytes)
          img = Image.open(img_before)

          option = request.form['select']
          print(option)
          s=0
          m=0
          l=0
          if option == 'yolov5m':
            m=1
            results = modelm(img, size=416)
          elif option =='yolov5l':
            l=1
            results = modell(img, size=416)
          else:
            s=1
            results = model(img, size=416)

          results.render()  # updates results.imgs with boxes and labels
          for img in results.imgs:
              img_base64 = Image.fromarray(img)
              img_byte_arr = io.BytesIO()
              img_base64.save(img_byte_arr, format='JPEG')
              imgg = base64.encodebytes(img_byte_arr.getvalue()).decode('ascii')

              image_save = IMG(rendered_data = imgg, filename=file.filename)
              db.session.add(image_save)
              db.session.commit()

          if s == 1:
            Check = 'checked'
            Check2 = ''
            Check3 = ''
          elif m == 1:
            Check = ''
            Check2 = 'checked'
            Check3 = ''
          elif l == 1:
            Check = ''
            Check2 = ''
            Check3 = 'checked'
          
          return render_template("index.html", img_data=imgg, scrollToAnchor="seconde", filename=file.filename, download_text="Download", check=Check, check2=Check2, check3=Check3 )
        
        else:
          return redirect(request.url)
      if formid == 2:
        name = request.form.get("y")
        email = request.form.get("x")
        text = request.form.get("z")

        if name == '': 
          return render_template("index.html", text="you forgot your name :(", color="red", scrollToAnchor="feed-back");
        elif text == '':
          return render_template("index.html", text="you forgot your opinion :(", color="red", scrollToAnchor="feed-back");
        elif email == '':
          return render_template("index.html", text="you forgot your email :(", color="red", scrollToAnchor="feed-back");
        else:
          feed_back = feedBack(name=name, email=email, text=text)
          db.session.add(feed_back)
          db.session.commit()

          t="thnx for the feed-back :)"
          return render_template("index.html", text=t, color="lime", scrollToAnchor="feed-back");
        

    return render_template("index.html", check='checked')


@app.route('/<string:filename>')
def display(filename):
  get_pic = IMG.query.filter_by(filename=filename).first()
  return '<img src="data:image/jpeg;base64,'+get_pic.rendered_data+'" width="500px">'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask app exposing yolov5 models")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    args = parser.parse_args()

    model = torch.hub.load(
        "ultralytics/yolov5", "custom", path="best.pt", force_reload=True
    ).autoshape()  # force_reload = recache latest code
    model.eval()

    modelm = torch.hub.load(
        "ultralytics/yolov5", "custom", path="bestm.pt", force_reload=True
    ).autoshape()  # force_reload = recache latest code
    modelm.eval()

    modell = torch.hub.load(
        "ultralytics/yolov5", "custom", path="bestl.pt", force_reload=True
    ).autoshape()  # force_reload = recache latest code
    modell.eval()

    db.create_all()
    app.run()  # debug=True causes Restarting with stat
