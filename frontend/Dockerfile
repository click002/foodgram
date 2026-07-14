# build env

FROM node:21-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build

FROM alpine:3.18
WORKDIR /app
COPY --from=build /app/build /app/result_build
