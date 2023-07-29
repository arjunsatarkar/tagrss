FROM python:3.11-bookworm

RUN mkdir /tagrss_data/
COPY . /tagrss
WORKDIR /tagrss
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["./serve.py", "--host", "0.0.0.0", "--storage-path", "/tagrss_data/tagrss_data.db"]
