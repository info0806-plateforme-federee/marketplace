FROM node:22

ARG UID=1000
ARG GID=1000

RUN groupadd --non-unique --gid $GID app \
    && useradd --non-unique --gid ${GID} --uid ${UID} --create-home --shell /bin/bash app

USER app:app
WORKDIR /app/packages/frontend

COPY --chown=app:app packages/frontend/package*.json ./
RUN npm install

COPY --chown=app:app packages/frontend ./
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
