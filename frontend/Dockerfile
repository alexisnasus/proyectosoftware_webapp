FROM node:20-bullseye-slim
WORKDIR /app

# 1. Copia archivos de configuración
COPY package.json package-lock.json ./

# 2. Instala dependencias con versión fija de Vite
RUN npm install --force && \
    npm install vite@5.0.0

# 3. Copia el resto del proyecto
COPY . .

# 4. Usa node para mayor estabilidad
CMD ["node", "node_modules/astro/dist/cli/index.js", "dev"]