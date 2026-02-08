# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install a simple server to serve the build
RUN npm install -g serve

COPY --from=build-stage /app/dist /app/dist

EXPOSE 5173

# Serve the production build on port 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
