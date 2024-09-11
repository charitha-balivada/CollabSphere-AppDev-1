from flask import Flask, render_template
#from models import db
app = Flask(__name__)

#app.app_context().push()

import config
import models
import influencer_routes
import sponsor_routes
import admin_routes

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
    