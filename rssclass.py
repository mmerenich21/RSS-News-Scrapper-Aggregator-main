import feedparser, urllib, json, os, re, requests
from newspaper import Article
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime

#Define a simple function to create a directory if it does not exist
def make_directory(path):
    if not os.path.exists(path):
        os.mkdir(path)

def get_html(url):
    """Grab html code of a page given its URL"""
    try:
        url = requests.get(url)
        htmltext = url.text        
    except:
        htmltext = "FORBIDDEN URL TO DOWNLOAD"
    
    return htmltext
    
#Create RssClass        
class RssClass:
    
    #initiate instance
    def __init__(self, url = 'https://news.google.com/', topic = 'Top stories'):
        
        ##the topics with they're respective links are stored along with the souped rss feed by topic
        self.souped = {}
        self.topics = {}

        ##The google news rss feeds are structure differently, this will scrape the links
        if url == 'https://news.google.com/':
            html_text = urllib.request.urlopen(url).read()
            
            soup = BeautifulSoup(html_text, 'html.parser')
            soup_body = soup.find('body')
            topic_key = 'aria-label'
            
            ##The urls for each topic are forwards and the rss address is not intuitive, thus a dict of the topic url is created by scraping from the front page of news.google.com
            ##This also will help to prevent the topic links from breaking
            self.topics = {i.get('aria-label'): url+'rss'+i.get('href').strip('.') for i in soup_body('a')
                           if i.get('class') == ['SFllF'] 
                           
                           ##get rid of any feeds that don't exist
                           and feedparser.parse(url+'rss'+i.get('href').strip('.')).entries[0].title != 'This feed is not available.'}
           
            ##Create a new rss feed if the target topic is not one of the home page main topics
            if topic not in self.topics:
                topic_url = topic.replace(' ', '+')
                self.topics[topic] = f'https://news.google.com/rss/search?q={topic_url}'
            ##create a list of souped summary
            for topic in self.topics:
                self.souped.setdefault(topic, [])         
                parsed = feedparser.parse(self.topics[topic])
                for entry in parsed.entries:
                    ##The summary of google news rss is a collection of similar stories and their links, not a summary of the story.
                    ##We want to grab these indiviual stories and links to use with newspaper module.
                    soup = BeautifulSoup(entry.summary, features = 'xml')
                    self.souped[topic].append(soup)
  
    def headline_summary(self, topic = 'Top stories'):
        ##reate the topic level directory
        make_directory(f"./data/{topic}")
        fh = open(f"data/{topic}/story_meta.json", 'w')
        fh.close() 
        
        stry_group_meta = {}
        ##iterate over the stories/headlines ('entries') in the topic. Enumerate to store group number
        for stry_group, entry in enumerate(self.souped[topic], start = 1):
            ##gather all of the links in the entry
            links = entry.find_all('a')
            
            article_meta = {}
            ##assign the story group ID
            stry_group_ID = f"{topic}-{stry_group}"
            ##assign the stroy group headline
            stry_group_headline = links[0].text
            ##create story group directory
            make_directory(f"./data/{topic}/{stry_group_ID}")
           
            outlet_list = []
            story_lvl_dict_list = []
            
            story_num = 1

            outlets = defaultdict()

            ##If there is only one story in the group, it will need to be parsed differently
            if len(links) <= 1:
                i=0
                ##Assign each story a unique story ID
                unique_stry_ID = f"{topic}-{stry_group}-{story_num}"
                ##gather the outlet name(s)
                outlet_list.append(links[0].text)
       
                story_num += 1
                ## Create the article object using the Newspaper module
                article = Article(links[0].get('href'))
                
                ## Some articule access is forbidden by the site.  Try to grab the data and return Forbidden if not
                try:
                    article.download()
                    article.parse()
                    art_txt = article.text
                    art_pub_date = article.publish_date.strftime('%a, %Y-%d-%m, %H:%M')
                    art_auth = article.authors
                except:
                    art_txt = 'FORBIDDEN URL TO DOWNLOAD: ' + str(links[i].get('href'))
                    art_pub_date = 'FORBIDDEN URL TO DOWNLOAD'
                    art_auth = 'FORBIDDEN URL TO DOWNLOAD'
                
                ## create the article text file
                fh = open(f"data/{topic}/{stry_group_ID}/{unique_stry_ID}.txt", 'w', encoding="utf-8")
                fh.write(art_txt)
                fh.close()
                
                ## create the original html file of the article
                fh = open(f"data/{topic}/{stry_group_ID}/{unique_stry_ID}-html.txt", 'w', encoding="utf-8")
                fh.writelines(get_html(links[0].get('href')))
                fh.close()
                
                ## store the article meta data
                story_lvl_dict = {'Article ID':unique_stry_ID, 'Article Title':links[i].text,'Publish Date':art_pub_date, 'Author(s)':art_auth, "Link":links[i].get('href')}

                story_lvl_dict_list.append(story_lvl_dict)
                story_num += 1

                
            ## if there is more than one story in the group
            else:
                i = 0
                for outlet in entry.find_all('font'):
                    ##Assign each story a unique story ID
                    unique_stry_ID = f"{topic}-{stry_group}-{story_num}"
                    ##gather the outlet name(s)
                    outlet_list.append(outlet.text)
                    
                    ## Create the article object using the Newspaper module
                    article = Article(links[i].get('href'))
                    
                     ## Some articule access is forbidden by the site.  Try to grab the data and return Forbidden if not
                    try:
                        article.download()
                        article.parse()
                        art_txt = article.text
                        art_pub_date = article.publish_date.strftime('%a, %Y-%d-%m, %H:%M')
                        art_auth = article.authors
                    except:
                        art_txt = 'FORBIDDEN URL TO DOWNLOAD: ' + str(links[i].get('href'))
                        art_pub_date = 'FORBIDDEN URL TO DOWNLOAD'
                        art_auth = 'FORBIDDEN URL TO DOWNLOAD'
                    ## create the article text file
                    fh = open(f"data/{topic}/{stry_group_ID}/{unique_stry_ID}.txt", 'w', encoding="utf-8")
                    fh.write(art_txt)
                    fh.close()
                   
                    ## create the original html file of the article
                    fh = open(f"data/{topic}/{stry_group_ID}/{unique_stry_ID}-html.txt", 'w', encoding="utf-8")
                    fh.writelines(get_html(links[0].get('href')))
                    fh.close()
                    ## store the article meta data
                    story_lvl_dict = {'Article ID':unique_stry_ID, 'Article Title':links[i].text,'Publish Date':art_pub_date, 'Author(s)':art_auth, "Link":links[i].get('href')}

                    story_lvl_dict_list.append(story_lvl_dict)
                    story_num += 1
                    i += 1

                    

            ## create the story group metadata file
            
            
            stry_group_meta[stry_group_ID] = {"Group Headline":stry_group_headline,"Outlets":outlet_list}

                         
            ## create the article metadata file and stry_group_metafile

            for s in story_lvl_dict_list:
                ID_tag = s["Article ID"]
                article_meta[ID_tag]= {'Article Title':s['Article Title'],'Publish Date':s['Publish Date'], 'Author(s)':s['Author(s)'], 'Link':s['Link']}
                
            with open(f"data/{topic}/{stry_group_ID}/article_metadata.json", 'w') as unqiue_story:
                JSON_data = json.dumps(article_meta)
                unqiue_story.write(JSON_data)  
                    
        with open(f"data/{topic}/story_meta.json", 'w') as stry_group_metafile:
   
            JSON_data = json.dumps(stry_group_meta)
            stry_group_metafile.write(JSON_data)
