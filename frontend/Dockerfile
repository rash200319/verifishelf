FROM node:20

WORKDIR /app

COPY package*.json ./
RUN rm -f package-lock.json && npm install --legacy-peer-deps

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]