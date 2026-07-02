FROM python:3.12-slim

WORKDIR /app
COPY demo/requirements.txt /app/demo/requirements.txt
RUN pip install --no-cache-dir -r /app/demo/requirements.txt

COPY hawkesrank /app/hawkesrank
COPY sample_candidates.json /app/sample_candidates.json
COPY demo/app.py /app/demo/app.py
COPY .streamlit /app/.streamlit

EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "demo/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
