# Build a minimalist dockerfile to run a FASTAPI python application
FROM python:3.8-slim-buster

# Set the working directory to /app
WORKDIR /app

# copy requirements and install with cache to speed up build
COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# set working directory to /app
# WORKDIR /app

# run the app using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]