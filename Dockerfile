FROM python:3.8

# System deps:
RUN pip install poetry

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

# Creating folders, and files for a project:
COPY . /code

CMD ["poetry", "run", "./main.py"]
