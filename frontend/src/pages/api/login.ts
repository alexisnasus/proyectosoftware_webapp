// src/pages/api/login.ts
export const prerender = false;

import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  // Leemos directamente el JSON del body
  const { username = '', password = '' } = await request.json();
  const user = String(username).trim();
  const pass = String(password).trim();

  // URL absoluta de tu Django en Docker Compose
  const BACKEND_URL = 'http://127.0.0.1:8000';

  // Llamada real al endpoint de login de Django
  const res = await fetch(`${BACKEND_URL}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: user, password: pass }),
  });

  // Si Django no devuelve 200, redirige al login con el error
  if (!res.ok) {
    const params = new URLSearchParams({ error: 'Credenciales incorrectas' });
    return new Response(null, {
      status: 302,
      headers: { Location: `/login?${params.toString()}` },
    });
  }

  // Extrae los tokens y devuélvelos al front
  const { access, refresh } = await res.json();
  return new Response(JSON.stringify({ access, refresh }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};
