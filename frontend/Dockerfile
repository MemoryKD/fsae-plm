FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM busybox
COPY --from=build /app/dist /site
CMD ["sh", "-c", "cp -r /site/* /out/"]
