FROM denoland/deno:2.8.2

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY main.ts .

RUN deno cache main.ts

EXPOSE 8000

CMD ["run", "--allow-net", "--allow-env", "main.ts"]
