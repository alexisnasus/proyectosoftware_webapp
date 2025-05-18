// src/pages/api/login.ts

export const prerender = false;

import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request, redirect }) => {
  // Leer el form data correctamente
  const form = await request.formData();
  const user = String(form.get('username') || '').trim();
  const pass = String(form.get('password') || '').trim();

  // Credenciales fijas
  if (user === 'admin' && pass === 'admin123') {
    return redirect('/admin/dashboard');
  }
  if (user === 'trabajador' && pass === 'worker123') {
    return redirect('/user/dashboard');
  }

  // Volvemos con query param error
  const params = new URLSearchParams({ error: 'Credenciales incorrectas' });
  return redirect('/?' + params.toString());
};



