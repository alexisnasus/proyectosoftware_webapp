// src/pages/api/login.ts
export const prerender = false;

import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  // Leemos JSON en vez de formData
  const { username = '', password = '' } = await request.json(); 
  const user = String(username).trim();
  const pass = String(password).trim();

  // Llamada real al backend Django
  const res = await fetch(`${import.meta.env.API_URL}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: user, password: pass }),
  });

  if (!res.ok) {
    const params = new URLSearchParams({ error: 'Credenciales incorrectas' });
    return new Response(null, {
      status: 302,
      headers: { Location: `/login?${params.toString()}` },
    });
  }

  const { access, refresh } = await res.json();
  return new Response(JSON.stringify({ access, refresh }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};
