# Etapa 1: Construcción
FROM node:20 AS build

# Establece el directorio de trabajo
WORKDIR /app

# Copia package.json y package-lock.json
COPY package*.json ./

# Instala dependencias
RUN npm install 

# Copia el resto de los archivos del proyecto
COPY . /app/

# Construye la aplicación React
RUN npm run build

CMD ["npm", "start"]