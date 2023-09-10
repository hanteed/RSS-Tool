import feedparser
import sqlite3
import xml.dom.minidom
from bs4 import BeautifulSoup
from transformers import pipeline
import time


db = 'data/rssdb.db'

def translate(textlist, source_language, dest_language):
    translatedlist = []
    source_language = source_language.lower()[:2]
    print("\nTranslating source language [%s] to [%s]..." % (source_language, dest_language))
    translationmodel = "Helsinki-NLP/opus-mt-" + source_language + "-" + dest_language
    translation_pipeline = pipeline('translation',model = translationmodel)
    for text in textlist:
        translated_text = translation_pipeline(text)[0]['translation_text']
        translatedlist.append(translated_text)
    return translatedlist

def opmlparser(file_path):
    sources = []
    with open(file_path, 'r', encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'xml')
        outlines = soup.find_all('outline', {'type': 'rss'})
        for outline in outlines:
            sources.append(outline['xmlUrl'])
    return sources

def opmladd(file_path, title, source):
    feed = feedparser.parse(source)
    
    if title.isspace() or title == "" or title == None:
        return "Title seems to be empty, please enter a valid title."
    
    if feed.bozo == 1:
        return "RSS feed seems to be invalid."
    
    with open(file_path, 'r') as f:
        soup = BeautifulSoup(f, 'xml')
        outlines = soup.find_all('outline', {'type': 'rss'})
        for outline in outlines:
            if outline['xmlUrl'] == source:
                return "RSS feed already exists."
    
    new_outline = soup.new_tag('outline', type='rss', text=title,xmlUrl=source)
    parent_outline = soup.find('outline', {'text': 'Custom Sources'})
    if parent_outline is None:
        parent_outline = soup.new_tag('outline', text='Custom Sources')
        soup.body.append(parent_outline)
    parent_outline.append(new_outline)
    
    with open(file_path, 'w') as f:
        f.write(str(soup))
    
    format_opml(file_path)
    return f"RSS feed successfully added to {file_path}."
    
def format_opml(file_path):
    with open(file_path, 'r') as f:
        dom = xml.dom.minidom.parseString(f.read())
            
    with open(file_path, 'w') as f:
        f.write(dom.toprettyxml())

def rssparser(source,processed_sources,language):
    
    connexion = sqlite3.connect(db)

    cursor = connexion.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS rss (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT,
                        title TEXT,
                        url TEXT UNIQUE,
                        date TEXT,
                        content TEXT,
                        language TEXT
                    )''')    

    cursor.execute('''CREATE TABLE IF NOT EXISTS sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT UNIQUE,
                        lastupdate TEXT
                        )''')
    cursor.execute("SELECT url FROM rss")
    existing_urls = [row[0] for row in cursor.fetchall()]

    try:
        news = feedparser.parse(source)
        
        if len(news.entries) > 0:
            
            if news.feed.title not in processed_sources:
                print("✅ RSS Feed : %s." % (news.feed.title))
                current_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                cursor.execute('''INSERT OR IGNORE INTO sources (source, lastupdate) VALUES (?, ?)''', (news.feed.title, news.feed.updated))
                processed_sources.add(news.feed.title)
            
            for entry in news.entries:
                try:
                    if entry.link not in existing_urls:
                        contentcleared = BeautifulSoup(entry.description, 'html.parser').get_text()
                        if news.feed.language.lower()[:2] != language:
                            translated_content = translate([entry.title,contentcleared], news.feed.language, language)
                        
                            cursor.execute('''INSERT OR IGNORE INTO rss (source, title, url, date, content, language)
                                            VALUES (?, ?, ?, ?, ?, ?)''',
                                        (news.feed.title, translated_content[0], entry.link, entry.published, translated_content[1], news.feed.language + " (translated in " + language + ")"))
                        else:
                            cursor.execute('''INSERT OR IGNORE INTO rss (source, title, url, date, content, language)
                                            VALUES (?, ?, ?, ?, ?, ?)''',
                                        (news.feed.title, entry.title, entry.link, entry.published, contentcleared, news.feed.language))
                
                        print("> Data URL : [URL] " + entry.link)
                        connexion.commit()
                
                except Exception as e:
                    if "UNIQUE constraint failed" in str(e):
                        if news.feed.title not in processed_sources:
                            print("🟰 Entry already exists in database for feed %s." % (news.feed.title))
                            processed_sources.add(news.feed.title)
                    else:
                        if news.feed.title not in processed_sources:
                            print("❌ Error while inserting entry on feed %s: %s" % (news.feed.title, e))
                            processed_sources.add(news.feed.title)
        else:
            try:
                print("❌ Feed %s is empty." % (news.feed.title))
            except:
                print("❌ Connection error / Feed is empty with no title.")
    
    except Exception as e:
        if source not in processed_sources:
            print("❌ Error while retrieving feed %s: %s" % (source, e))
            processed_sources.add(source)


    connexion.commit()
    cursor.close()
    connexion.close()