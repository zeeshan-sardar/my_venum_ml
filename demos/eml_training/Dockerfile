FROM python:3.11-slim

WORKDIR /app

# Create wheelhouse directory
RUN mkdir -p wheelhouse

# Copy requirements and local wheel
COPY requirements.txt .
COPY venumML-0.2.2b1-py3-none-manylinux_2_31_x86_64.whl ./wheelhouse/

# Install packages (local wheels first, then PyPI for others)
RUN pip install --no-cache-dir \
    --find-links=./wheelhouse \
    -r requirements.txt \
    ./wheelhouse/venumML-0.2.2b1-py3-none-manylinux_2_31_x86_64.whl

COPY ./main.py .

CMD ["python", "main.py"]
