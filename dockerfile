FROM golang:1.22 AS builder
WORKDIR /src/orchestrator

COPY go.mod .
COPY go.sum .
RUN go mod download

COPY orchestrator/ .
RUN go build -o /bin/orchestrator main.go

FROM python:3.11.9-slim-bookworm
WORKDIR /app

COPY extractor/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY extractor/ ./extractor/
COPY --from=builder /bin/orchestrator ./orchestrator

RUN mkdir -p /app/input /app/output

ENTRYPOINT ["./orchestrator"]
