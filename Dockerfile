FROM amd64/python:3.9-slim

WORKDIR /usr/app

RUN pip install -U pip \
    && pip install "fastapi[all]"

COPY 5_crud_pydantic.py 5_crud_pydantic.py

CMD ["uvicorn", "5_crud_pydantic:app", "--host", "0.0.0.0", "--reload"]