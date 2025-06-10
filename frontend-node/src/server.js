// frontend-node/src/server.js  (versión ES Module)

import express from "express";
import path from "path";
import cors from "cors";

const app = express();
const PORT = process.env.PORT || 3000;

// 1) Habilitar CORS
app.use(cors({ origin: "*" }));

// 2) Servir archivos estáticos desde /public
const publicPath = path.join(process.cwd(), "public");
app.use(express.static(publicPath));

// 3) Rutas limpias
app.get("/", (req, res) => {
  res.sendFile(path.join(publicPath, "index.html"));
});
app.get("/login", (req, res) => {
  res.sendFile(path.join(publicPath, "index.html"));
});
app.get("/dashboard", (req, res) => {
  res.sendFile(path.join(publicPath, "dashboard.html"));
});
app.get("/inventario", (req, res) => {
  res.sendFile(path.join(publicPath, "inventario.html"));
});
app.get("/pos", (req, res) => {
  res.sendFile(path.join(publicPath, "pos.html"));
});

// Nueva ruta para historial de compras
app.get("/historial-compras", (req, res) => {
  res.sendFile(path.join(publicPath, "historial.html"));
});

app.get("/trabajadores", (req, res) => {
  res.sendFile(path.join(publicPath, "trabajadores.html"));
});

// 4) 404 por defecto
app.use((req, res) => {
  res.status(404).sendFile(path.join(publicPath, "index.html"));
});

// 5) Iniciar servidor
app.listen(PORT, () => {
  console.log(`⚡ Frontend Node.js escuchando en http://localhost:${PORT}`);
});
