
FROM python:3.9-slim

WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the application code (main.py, generate_demo_data.py) into the container
COPY . .

# Run the data generation script to create the sample_data directory and its contents
RUN python generate_demo_data.py

EXPOSE 8501

# Define environment variable for Streamlit configuration (optional, but good practice)
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# Run main.py when the container launches using Streamlit
CMD ["streamlit", "run", "main.py"]