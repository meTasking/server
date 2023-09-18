# pull official base image
FROM python:3.11.5-slim-bookworm

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DATABASE_URL "sqlite:////data/database.db"
ENV READ_ONLY "false"

# set command to run when container starts
CMD ["./docker-init.sh"]

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# add app
COPY . .
