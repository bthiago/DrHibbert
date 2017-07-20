FROM tiangolo/uwsgi-nginx-flask:flask

# copy requirements.txt file
COPY requirements.txt /tmp/

# upgrade pip and install required python packages
RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

# copy app code
COPY ./app /app

