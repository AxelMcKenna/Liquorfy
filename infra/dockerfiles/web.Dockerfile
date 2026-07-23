FROM node:22-alpine

WORKDIR /app/web

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web ./

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
