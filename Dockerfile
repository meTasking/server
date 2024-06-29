# pull official base image
FROM docker.io/library/python:3.11.9

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV TZ=Europe/Prague
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV ROOT_PATH ""
ENV DATABASE_URL "sqlite:////data/database.db"
ENV READ_ONLY "false"

# set command to run when container starts
CMD ["./docker-init.sh"]

# install python dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# add app
COPY . .
