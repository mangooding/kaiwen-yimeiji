FROM python:3.12-slim

WORKDIR /app
COPY . .

ENV HOST=0.0.0.0
ENV PORT=8891
EXPOSE 8891

CMD ["python", "server.py", "--host", "0.0.0.0"]
