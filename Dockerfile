FROM python:3.10-slim

# Install system dependencies
RUN apt-get update &&     apt-get install -y graphviz libgraphviz-dev &&     apt-get clean

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "cli_updated.py", "--template", "template.json", "--parameters", "parameters.json", "--docx_template", "template.docx"]
