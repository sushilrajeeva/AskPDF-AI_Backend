# Use AWS’s Python 3.12 Lambda base image
FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Tell Lambda which handler to invoke
CMD ["app.main.handler"]
