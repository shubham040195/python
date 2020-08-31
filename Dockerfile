FROM ubuntu

MAINTAINER Shubham

RUN apt-get update

RUN apt-get install -y python

ADD duplicate.py /home/duplicate.py

ENTRYPOINT ["python","/home/duplicate.py"]

CMD ["/home/"]
