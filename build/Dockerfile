FROM python:3

COPY . .
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

RUN touch /var/log/cron.log

RUN apt-get update \  
&& apt-get install cron -y

RUN chmod +x main.py

RUN crontab crontab 

CMD cron -f

