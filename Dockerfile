FROM dockerpull.org/python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

COPY . .

CMD ["gunicorn", "geminar_console.wsgi:application", "--bind", "0.0.0.0:8000"]

