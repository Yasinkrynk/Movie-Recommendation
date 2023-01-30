from flask import Flask,render_template,request,flash,redirect
import pandas as pd
import numpy as np


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "super secret key"

import re

def clean_title(title):
    return re.sub("[^a-zA-Z0-9 ]","",title)

def read_movies():
    movies = pd.read_csv('ml-latest-small/movies.csv')
    movies["clean_title"]=movies["title"].apply(clean_title)
    return movies


def find_similar_movies(movie_id,rt):
    rating=pd.read_csv('ml-latest-small/ratings.csv')

    similar_users=rating[(rating["movieId"]==movie_id) & (rating["rating"]>=rt)]["userId"].unique()
    similar_user_recs=rating[(rating["userId"].isin(similar_users)) & (rating["rating"]>=rt)]["movieId"]
    similar_user_recs=similar_user_recs.value_counts()/len(similar_users)

    similar_user_recs=similar_user_recs[similar_user_recs>0.1]
    all_users=rating[(rating["movieId"].isin(similar_user_recs.index)) & (rating["rating"]>=rt)]
    all_users_recs=all_users["movieId"].value_counts()/len(all_users["userId"].unique())

    rec_percentages=pd.concat([similar_user_recs,all_users_recs], axis=1)
    rec_percentages.columns=["similar","all"]

    rec_percentages["score"]=rec_percentages["similar"]/rec_percentages["all"]
    rec_percentages=rec_percentages.sort_values("score",ascending=False)
    
    return rec_percentages.head(11).merge(movies,left_index=True,right_on="movieId")

def create_recommention(r_list):
    blankIndex=[''] * len(r_list)
    r_list.index=blankIndex
    r_list=r_list.iloc[1:]['title']
    print(r_list)
    df=pd.read_csv('info.csv')
    arr=[]
    empty_url='https://m.media-amazon.com/images/S/sash/4FyxwxECzL-U1J8.png'
    for i in r_list:
        movie = df[df['movie']==i]
        if movie.empty:
            arr.append(empty_url)
            for j in range(1,8):
                arr.append('')
            print(arr)
        else:
            vote=movie.iloc[0]["vote"]
            time=movie.iloc[0]["time_minute"]
            metascore=movie.iloc[0]["metascore"]
            gross_earning=movie.iloc[0]["gross_earning"]
            img_url=movie.iloc[0]["img_url"]
            genres=movie.iloc[0]["genres"]
            summary=movie.iloc[0]["summary"]
            imdb_rating=movie.iloc[0]["imdb_rating"]
            arr.append(img_url)
            arr.append(str(time))
            arr.append(genres)
            arr.append(str(imdb_rating))
            arr.append(str(metascore))
            arr.append(summary)
            arr.append(str(vote))
            arr.append(str(gross_earning))
    arr=np.array(arr)
    arr=np.reshape(arr, (-1, 8))
    print(arr)
    return arr

def find_movie(index):
    r_list=find_similar_movies(index,4)
    if len(r_list)==0:
        r_list=find_similar_movies(index,3)
        arr=create_recommention(r_list)
        return arr,r_list.iloc[1:]['title']
    else:
        arr=create_recommention(r_list)
        return arr,r_list.iloc[1:]['title']

@app.route("/", methods=["POST", "GET"])
def home():
    global movies,data
    movies=read_movies()
    data=movies["clean_title"].unique()
    return render_template("home.html",data=data)

@app.route("/movies",methods=["POST","GET"])
def movies():
    movie_name = request.form.get("search")
    if movie_name in data:
        movie = movies[movies['clean_title']==movie_name]
        index=movie.iloc[0]["movieId"]
        arr,r_list=find_movie(index)
        print(r_list)
        return render_template("movies.html",data=data,r_list=r_list,arr=arr)
    else:
        flash("The movie does not exist!")
        return redirect("/")

if __name__ =='__main__':
    app.run()