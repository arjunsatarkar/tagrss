FROM python:3.11-alpine

RUN mkdir /tagrss_data/
COPY . /tagrss
WORKDIR /tagrss
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

STOPSIGNAL SIGINT

CMD ["python3", "-O", "serve.py", "--host", "0.0.0.0", "--storage-path", "/tagrss_data/tagrss_data.db"]
