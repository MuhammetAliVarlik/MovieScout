from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search_movies', methods=['POST', 'GET'])
def search_movies():
    movieName = request.form.get('movieName')  # Get the movie name from the form
    return render_template('index.html', movieName=movieName)
if __name__ =="__main__":
    app.run(debug =True)