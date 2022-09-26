import keyword
from re import search
from traceback import print_tb
import pandas as pd
import requests
from bs4 import BeautifulSoup as BS
import time
import random
# 106 pages


def parse_genres():
    genres_list = []
    url = 'https://animego.org/anime'
    r = requests.get(url)
    html = BS(r.content, 'html.parser')
    genres = html.select(".form-group.genres")[0]
    genres_span = genres.find_all('span', {"class": "custom-control-description"})

    for genre in genres_span:
        genre_name = genre['data-text']
        genres_list.append(genre_name)

    return genres_list

def get_anime(url, gnrs):
    data = []
    anime_request = requests.get(url)
    anime_html = BS(anime_request.content, 'html.parser')

    # get anime title
    try:
        title = anime_html.find('h1').text
    except:
        title = "No Title"
        return 0
    # get synonims
    try:
        list_synonyms = anime_html.find_all('ul')[3]
        synonym = list_synonyms.find('li').text
    except:
        synonym = "No Title"
    try:
        poster = anime_html.select('.anime-poster')[0]
        poster = poster.find('img')['src']      
    except:
        poster = ""

    try:
        description = anime_html.select('.description')[0].text.strip()    
    except:
        description = ""
            

    first_col = anime_html.select('.row > .col-6.col-sm-4')
    second_col = anime_html.select('.row > .col-6.col-sm-8.mb-1')
    rating_1 = anime_html.select('.rating-value')
    rating_2 = anime_html.select('.rating-count')
    if len(rating_1):
        rating_val = float(rating_1[0].text.strip().replace(',','.'))
        num_votes = int(rating_2[0].text)
    else:
        rating_val = float(0)
        num_votes = 0

    # search key
    row_name = {
        'Тип': None,
        'Жанр': None,
        'Выпуск': None,
        'Студия': None,
        'Возрастные ограничения': None,
        'Длительность': None
    }
    key_ = 0
    for row in first_col:
        # print(row)
        if row.text.strip() in row_name:
            row_name[row.text.strip()] = key_
        key_ += 1

    anime_type = 0
    anime_genre = 0
    anime_season = 0
    anime_studio = 0
    age_restrictions = 0
    duration = 0

    # get anime type
    if row_name['Тип'] != None:
        anime_type = second_col[row_name['Тип']].text
        
    # get anime genre
    if row_name['Жанр'] != None:
        genre_list = second_col[row_name['Жанр']]
        anime_genre = ""
        for genre in genre_list.find_all('a'):
            anime_genre += genre.text+" "
    try:
        genres = [(lambda i: 1 if i in list(anime_genre.split()) else 0)(i) for i in gnrs]
    except:
        genres = [0 for i in gnrs]
    #get anime season
    if row_name['Выпуск'] != None:
        anime_season = int(second_col[row_name['Выпуск']].text[-4::])
        if not(anime_season):
            anime_season = None
        
    #get anime studio
    if row_name['Студия'] != None:
        anime_studio = second_col[row_name['Студия']].text
        anime_studio = anime_studio.split(',', 1)[0]
        if not(anime_studio):
            anime_studio = None

    #get anime age restrictions
    if row_name['Возрастные ограничения'] != None:
        age_restrictions = int(second_col[row_name['Возрастные ограничения']].text.strip().replace('+', ''))
    
    #get anime duration
    if row_name['Длительность'] != None:
        duration = second_col[row_name['Длительность']].text.strip().replace('~ серия', '')

    data = [url, poster, title, synonym, description, anime_type, anime_season, anime_studio, age_restrictions, duration, rating_val, num_votes] + genres
    
    return data

def parse_page(url, gnrs):
    r = requests.get(url)
    html = BS(r.content, 'html.parser')
    cnt_on_page = 0
    anime_data = []
    for anime in html.select(".animes-list-item > .media-body"):
        href = anime.find_all('a')[0]
        anime_url = href['href']
        anime_row = get_anime(anime_url, gnrs)
        if not(anime_row):
            continue
        anime_data.append(anime_row)
        cnt_on_page += 1
    return anime_data, cnt_on_page

def get_data(genres, cnt_pages = 107):
    l = 0
    data = []
    cnt = 0
    for page_num in range(1,cnt_pages+1):
        url = f"https://animego.org/anime?sort=a.createdAt&direction=desc&type=animes&page={page_num}"
        page_data, num_anime = parse_page(url, genres)
        cnt += num_anime
        data += page_data
        print(f"Page {page_num} parsed! Founded {num_anime}")
        if page_num%5 == 0:
            time.sleep(random.randint(10,15))
        time.sleep(random.randint(5,15))
    # url = f"https://animego.org/anime?sort=a.createdAt&direction=desc&type=animes&page={1}"
    
    return data, cnt


def save_data(data, genres):
    cols = ['Url', 'Poster', 'Title', 'Synonym', 'Description', 'Type', 'Year', 'Studio', 'Age', 'Duration', 'Rating', 'Num votes'] + genres
    df = pd.DataFrame(data, columns=cols)
    # df = df.drop(['Unnamed: 0'], axis = 1)
    df.to_csv('Data/data.csv') 


def add_new_anime():
    genres = parse_genres()
    old_data = pd.read_csv('Data/data.csv')
    last = list(old_data.drop(['Unnamed: 0'], axis = 1).iloc[0])[1]
    data, cnt = get_data(genres, cnt_pages=3)
    new_anime = []
    cnt = 0
    for anime in data:
        if anime[1] == last:
            break
        new_anime.append(anime)
    new_data = new_anime+old_data.drop(['Unnamed: 0'], axis = 1).values.tolist()

    save_data(new_data, genres)
    print(f"DONE!!! Founded {len(new_anime)} new anime!")




def main():
    genres = parse_genres()
    data, cnt = get_data(genres)
    save_data(data, genres)
    print(f"DONE!!! Founded {cnt} anime!")

if __name__ == '__main__':
    main()
