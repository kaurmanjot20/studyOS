# Development-oriented image: runs `next dev` with hot reload against a bind mount.
# A production multi-stage build (standalone output) is added in the polish phase.
FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
