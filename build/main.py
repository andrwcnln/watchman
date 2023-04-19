# author: @andrwcnln
# v1.0
# apr 2023
# a script to create a newspaper-esque pdf from rss feeds
# and send it to my kindle

with open('edition.txt','r+') as f:
    currentEdition = str(f.read())
    nextEdition = int(currentEdition) + 1
    f.seek(0)
    f.truncate()
    f.write(str(nextEdition))

import yaml
from bs4 import BeautifulSoup
import requests
from datetime import date, datetime
import smtplib
import os
from dotenv import load_dotenv

from email.message import EmailMessage

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import BaseDocTemplate, Paragraph, Frame, PageTemplate
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

stylesheet = getSampleStyleSheet()
normalStyle = stylesheet['Normal']
paraStyle = ParagraphStyle(
    name='Normal',
    fontName='Helvetica',
    fontSize=20,
    firstLineIndent=30,
    alignment=TA_JUSTIFY,
    leading=20,
    spaceAfter=10
)

titleStyle = ParagraphStyle(
    name='Normal',
    fontName='Times-Bold',
    fontSize=32,
    alignment=TA_LEFT,
    leading=32,
    spaceAfter=10
)

authorStyle = ParagraphStyle(
    name='Normal',
    fontName='Times-Italic',
    fontSize=20,
    firstLineIndent=5,
    alignment=TA_LEFT,
    leading=20,
    spaceAfter=10
)


load_dotenv()
USER = os.getenv('GMAIL')
PASS = os.getenv('GMAIL_PASSWORD')
KINDLE = os.getenv('KINDLE')


def login():
    try:
        print('[' + str(datetime.now()) + '] Opening secure connection...')
        s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        print('[' + str(datetime.now()) + '] Logging in...')
        s.login(USER, PASS)
        return s
    except Exception as e:
        print('[' + str(datetime.now()) + '] Something went wrong :(')
        print('[' + str(datetime.now()) + '] Error message:')
        print('[' + str(datetime.now()) + '] ' + str(e))


def generateEmail(directory, filename):
    try:
        print('[' + str(datetime.now()) + '] Generating email...')
        msg = EmailMessage()

        msg['Subject'] = filename
        msg['From'] = USER
        msg['To'] = KINDLE

        with open(directory + filename, 'rb') as f:
            content = f.read()
            msg.add_attachment(content, maintype='application',
                               subtype='pdf', filename=filename)

        return msg

    except Exception as e:
        print('[' + str(datetime.now()) + '] Something went wrong :(')
        print('[' + str(datetime.now()) + '] Error message:')
        print('[' + str(datetime.now()) + '] ' + str(e))


def sendEmail(s, msg):
    try:
        print('[' + str(datetime.now()) + '] Sending email...')
        s.send_message(msg)
    except Exception as e:
        print('[' + str(datetime.now()) + '] Something went wrong :(')
        print('[' + str(datetime.now()) + '] Error message:')
        print('[' + str(datetime.now()) + '] ' + str(e))


def createPDF(parsed):
    try:
        print('[' + str(datetime.now()) + '] Creating pdf...')
        today = date.today()
        directory = 'pdfs/'
        filename = today.strftime('%d_%m_%Y') + '.pdf'
        canvas = Canvas(directory + filename)
        # PDFTitle(canvas,today)
        doc = BaseDocTemplate(directory + filename,
                              leftMargin=0.1*inch, rightMargin=0.1*inch,
                              topMargin=0.1*inch, bottomMargin=0.1*inch)
        col1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width /
                     2-6, doc.height-(1.2*inch), id='col1')
        col2 = Frame(doc.leftMargin+doc.width/2+6, doc.bottomMargin,
                     doc.width/2-6, doc.height-(1.2*inch), id='col2')
        doc.addPageTemplates(PageTemplate(
            id='page1', frames=[col1, col2], onPage=PDFTitle))
        paras = []
        counter = 0
        if len(parsed) == 3:
            noContent = Paragraph('No new content :(', titleStyle)
            paras.append(noContent)
        else:
            del parsed[0:3]
            while counter < len(parsed):
                title = Paragraph(parsed[counter], titleStyle)
                author = Paragraph(parsed[counter+1], authorStyle)
                content = Paragraph(parsed[counter+2], paraStyle)
                paras.append(title)
                paras.append(author)
                paras.append(content)
                counter += 3
        # paras.append(a)
        # paras.append(a)
        # paras.append(a)
        doc.build(paras)
        # canvas.save()
        return directory, filename
    except Exception as e:
        print('[' + str(datetime.now()) + '] Something went wrong :(')
        print('[' + str(datetime.now()) + '] Error message:')
        print('[' + str(datetime.now()) + '] ' + str(e))


def PDFTitle(canvas, doc):
    today = date.today()
    canvas.saveState()
    canvas.setFont('Times-Bold', 87)
    canvas.drawString(doc.leftMargin, doc.height-0.7*inch, 'The Watchman')
    canvas.setFont('Times-Bold', 14)
    canvas.drawCentredString(doc.width/2, doc.height-1*inch, today.strftime('%A, %-d %B %Y') +
                             '   |   ' + 'Edition ' + currentEdition + '   |   ' + 'Do not go gentle into that good night')
    canvas.line(doc.leftMargin, doc.height-1.1 *
                inch, doc.width, doc.height-1.1*inch)
    canvas.restoreState()


def getRSS(parsed, site, config):
    try:
        # parsed = []
        url = config['url']
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'xml')

        newContent = checkCache(str(soup), site)

        if newContent:
            print('[' + str(datetime.now()) + '] Saving cache...')
            saveCache(str(soup), site)

            article = soup.find(config['article'])

            if config['fulltext'] == True:
                contentHTML = article.find(config['content']).text
                contentHTML = BeautifulSoup(contentHTML,'html.parser')
                content = contentHTML.get_text()
            else:
                link = article.find(config['content']).text
                r = requests.get(link)
                contentHTML = BeautifulSoup(r.content, 'html.parser')
                content = contentHTML.find(config['tag'],id=config['id']).text

            title = article.find(config['title']).text
            
            if config['authorIncluded'] == True:
                author = article.find(config['author']).text
            else:
                author = config['author']

            publishDate = article.find(config['publishDate']).text
            publishDate = datetime.strptime(publishDate, config['dateFormat'])
            publishDate = publishDate.strftime('%-d/%-m/%y')

            details = author + ', ' + publishDate

            # h = html2text.HTML2Text()
            # h.ignore_links = True
            # h.ignore_emphasis = False

            parsed.append(title)
            parsed.append(details)
            parsed.append(content)
            return parsed



        else:
            print('[' + str(datetime.now()) + '] No new content for ' + site)
            return parsed
    except Exception as e:
        print('[' + str(datetime.now()) + '] Something went wrong :(')
        print('[' + str(datetime.now()) + '] Error message:')
        print('[' + str(datetime.now()) + '] ' + str(e))


def checkCache(soup, site):
    try:
        filename = 'cache/' + site + '.cache'
        with open(filename, 'r') as f:
            content = f.read()
        if content == soup:
            return False
        else:
            return True
    except OSError as e:
        if e.strerror == 'No such file or directory':
            print('[' + str(datetime.now()) + '] No existing cache for ' + site)
            return True
        else:
            print('[' + str(datetime.now()) + '] Something went wrong :(')
            print('[' + str(datetime.now()) + '] Error message:')
            print('[' + str(datetime.now()) + '] ' + str(e))
            return False
    except Exception as e:
        print('[' + str(datetime.now()) + '] Something went wrong :(')
        print('[' + str(datetime.now()) + '] Error message:')
        print('[' + str(datetime.now()) + '] ' + str(e))
        return False


def saveCache(soup, site):
    filename = 'cache/' + site + '.cache'
    with open(filename, 'w') as f:
        f.write(soup)


def clearCache():
    os.system('rm -rf cache')
    os.system('mkdir cache')


def loadConfig():
    with open('config.yml', 'r+') as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            print('[' + str(datetime.now()) + '] Something went wrong :(')
            print('[' + str(datetime.now()) + '] Error message:')
            print('[' + str(datetime.now()) + '] ' + str(e))


# clearCache()
config = loadConfig()
parsed = ["", "", ""]
for site in config:
    parsed = getRSS(parsed, site, config[site])

directory, filename = createPDF(parsed)

s = login()
msg = generateEmail(directory,filename)
sendEmail(s,msg)
s.close()

print('[' + str(datetime.now()) + '] Success!')
