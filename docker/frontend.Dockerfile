FROM node:22

ARG UID=1000
ARG GID=1000

RUN groupadd --non-unique --gid $GID app \
&& useradd --non-unique --gid ${GID} --uid ${UID} --create-home --shell /bin/bash app

WORKDIR /app

# Run as root to fix volume ownership, install deps as app, then run dev server as app
CMD ["sh", "-c", "chown app:app node_modules && exec su -s /bin/sh app -c 'if [ ! -x node_modules/.bin/vite ] || [ ! -f node_modules/.package-lock.json ] || [ package-lock.json -nt node_modules/.package-lock.json ]; then npm install; fi; exec npm run dev -- --port 3000'"]
