FROM python:3.6
RUN pip install Flask Flask-Migrate requests boto3 clova-cek-sdk pykintone
COPY ./ /app
WORKDIR /app
EXPOSE 5000
ENV FLASK_APP=run.py FLASK_DEBUG=1
CMD bash -c "flask run --host=0.0.0.0"
