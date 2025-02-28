FROM public.ecr.aws/lambda/python:3.13

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt

# Copy code maintaining directory structure
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Set the CMD to your handler (Mangum)
CMD [ "src.main.handler" ]