import sqlite3

db = 'data/rssdb.db'

def research(research, language, year):
    res = []
    connexion = sqlite3.connect(db)
    cursor = connexion.cursor()
    
    if research.isspace() or research == "" or research == None:
        cursor.execute("SELECT * FROM rss WHERE date LIKE ?", ['2023%'])
        results = cursor.fetchall()
        for row in results:
            format = [row[1], row[4], row[2], row[5], row[6], row[3]]
            res.append(format)
        if res == []:
            res.append("No results found.")
        return res
    
    words = research.split()
    wordslist = ["%{}%".format(word) for word in words]
    query = "SELECT * FROM rss WHERE " + " OR ".join(["title LIKE ? OR content LIKE ?" for _ in words])
    cursor.execute(query, [p for item in wordslist for p in (item, item)])
    results = cursor.fetchall()
    
    if len(results) > 0: 
        for row in results:
            try:
                format = [row[1], row[4], row[2], row[5], row[6], row[3]]
                if year != "All":                
                    yeararticle = int(row[4].split(" ")[3])    
                    if yeararticle >= year:
                        if language == "All":
                            res.append(format)
                        else:
                            if row[6].lower()[:2] == language:
                                res.append(format)
                else:
                    if language == "All":
                            res.append(format)
                    else:
                        if row[6].lower()[:2] == language:
                            res.append(format)
            except :
                pass

    else:
        res.append("No results found.")
        
    if res==[]:
        res.append("No results found.")    
        
    connexion.commit()
    cursor.close()
    connexion.close()
    
    return res