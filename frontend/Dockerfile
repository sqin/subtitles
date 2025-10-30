# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json /app/
RUN npm ci
COPY . /app
RUN npm run build

# Serve via vite preview (no nginx)
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app /app

EXPOSE 13000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "13000"]


