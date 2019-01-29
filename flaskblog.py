from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

GOOGLE_CHROME_BIN = '/app/.apt/usr/bin/google-chrome'
CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
# chrome_options = Options()
# chrome_options.binary_location = GOOGLE_CHROME_BIN
# chrome_options.add_argument('--disable-gpu')
# chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH) #chrome_options=chrome_options)

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import re
from nltk.stem import WordNetLemmatizer
import heapq  
from textblob import TextBlob
import datetime

now = datetime.datetime.now()

def Summarizer(article_text):
    # Removing Square Brackets and Extra Spaces
    article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)  
    article_text = re.sub(r'\s+', ' ', article_text)

    # Removing special characters and digits
    formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )  
    formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text) 
    
    lemma = WordNetLemmatizer()
    formatted_article_text = lemma.lemmatize(article_text)
    
    clean_list = []
    sentence_list = TextBlob(formatted_article_text).sentences
    for sent in sentence_list:
        clean_list.append(str(sent))
        
    stopwords = nltk.corpus.stopwords.words('english')

    word_frequencies = {}  
    for word in word_tokenize(formatted_article_text):
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word.lower()] = 1
            else:
                word_frequencies[word.lower()] += 1

    maximum_frequency = max(word_frequencies.values())
    max_keys = [k for k, v in word_frequencies.items() if v == maximum_frequency]

    for word in word_frequencies.keys():  
        word_frequencies[word] = (word_frequencies[word]/maximum_frequency)

    sentence_scores = {}  
    for sent in clean_list:  
        for word in TextBlob(formatted_article_text).words:
            if word in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word]
                else:
                    sentence_scores[sent] += word_frequencies[word]
    
    summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)
    if len(' '.join(summary_sentences)) > 1000:
        summary_sentences = heapq.nlargest(4, sentence_scores, key=sentence_scores.get)
    max_keys = heapq.nlargest(10, word_frequencies, key=word_frequencies.get)
    for x in max_keys:
        if x.isalpha():
            Max = x
            break
    summary = ' '.join(summary_sentences)
    return(summary,Max) 


def Crawl_Fox():
    url = 'https://www.foxnews.com/'
    driver.get(url)
    html = driver.page_source
    Link = []
    soup = BeautifulSoup(html, 'lxml')
    
    for link in soup.select('main[class=main-content] article div[class=m] > a'):
        Link.append(link['href'])
    return(Link)

def Get_Text_Fox(Number):
    Link_Fox = Crawl_Fox()
    Articles = []
    Titles = []
    Strong = []
    Link_Fox_Clean = []
    for link in Link_Fox:
        if 'https://video.' not in link:
            Link_Fox_Clean.append(link)
    for article in Link_Fox_Clean[:Number]:
        driver.get(article)
        driver.implicitly_wait(30)
        html1 = driver.page_source
        soup1 = BeautifulSoup(html1, 'lxml')
        for title in soup1.find_all('h1', class_='headline'):
            Titles.append(title.get_text())
        article_text = ""
        all_ps = soup1.select('div[class=article-body] p')
        for p in all_ps[1:]:
            if p.get_text().isupper():
                Strong.append(p)
            else:
                article_text += p.get_text() + ' '
        Articles.append(article_text)
    return(Articles, Titles)

def Crawl_MSNBC():
    url = 'https://www.nbcnews.com/latest-stories'
    driver.get(url)
#     driver.maximize_window()
    html = driver.page_source
    Link = []
    soup = BeautifulSoup(html, 'lxml')
    
    for link in soup.select('div[class=teaseCard__picture] > a'):
        Link.append(link['href'])
    Link[:] = (x for x in Link if 'nbcsports' not in x)
    Link_Clean = Link[:]
    return(Link_Clean)

def Get_Text_MSNBC(Number):
    Articles = []
    Titles = []
    Link_MSNBC_Clean = []
    Link_MSNBC = Crawl_MSNBC()
    for link in Link_MSNBC:
        if 'https://www.nbcnews.com/video' not in link:
            Link_MSNBC_Clean.append(link)
    for article in Link_MSNBC_Clean[:Number]:
        driver.get(article)
        driver.implicitly_wait(30)
        html1 = driver.page_source
        soup1 = BeautifulSoup(html1, 'lxml')
        for title in soup1.find_all('h1', class_='headline___CuovH f8 f9-m fw3 mb3 mt0 founders-cond lh-none f10-xl'):
            Titles.append(title.get_text())
        article_text = ""
        all_ps = soup1.select('p')
        for p in all_ps[:-1]:
            article_text += p.get_text() + ' '
        Articles.append(article_text)
    return(Articles, Titles)


def HTML_Writer(Text,Name):
    Articles = Text[0]
    Titles = Text[1]

    title_list = []
    for i in range(len(Titles)):
        title_list.append('title'+str([i+1]))
    title_dict = dict(zip(title_list, Titles))
    
    article_list = []
    for i in range(len(Articles)):
        article_list.append('article'+str([i+1]))
    article_dict = dict(zip(article_list,Articles))
    
    title_html = []
    for i in range(len(Titles)):
        title_html.append(title_dict[title_list[i]])
    one_word_html = []
    for i in range(len(Articles)):
        one_word_html.append("One Word Summary: "+Summarizer(article_dict[article_list[i]])[1])
    article_html = []
    for i in range(len(Articles)):
        article_html.append(Summarizer(article_dict[article_list[i]])[0])
    body_html = ""
    for i in range(len(Titles)):
        body_html += title_html[i]+one_word_html[i]+article_html[i]
        
    name = Name
    date = now.strftime("%Y-%m-%d %H:%M")
    body_html = zip(title_html,one_word_html, article_html)

    return(name,date,body_html)
def execute():   
	Fox = Get_Text_Fox(5)
	MSNBC = Get_Text_MSNBC(5)
	Page_Fox = HTML_Writer(Fox,'Fox')
	Page_MSNBC = HTML_Writer(MSNBC,'MSNBC')
	return(Page_Fox,Page_MSNBC)

Text = execute()    
Page_Fox = Text[0]
Page_MSNBC = Text[1]

app = Flask(__name__)


@app.route("/")
@app.route("/home")
def home(): 
	return render_template('home.html', Page_Fox = Page_Fox, Page_MSNBC = Page_MSNBC)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/All")
def All():
    return render_template('NewsSummaries_All.html')
    
# @app.route("/MSNBC")
# def MSNBC():
#     return render_template('NewsSummaries_MSNBC.html')

# @app.route("/Fox")
# def FOX():
#     return render_template('NewsSummaries_Fox.html')  

if __name__ =='__main__':
    app.run(debug=True)
    
