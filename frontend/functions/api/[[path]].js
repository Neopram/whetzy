export async function onRequestPost(context) {
  try {
    const { request } = context;
    const body = await request.json();
    return new Response(JSON.stringify({ success: true, message: "Autenticado correctamente" }), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  }
}

export async function onRequestGet(context) {
  return new Response(JSON.stringify({ message: "Ruta GET activa" }), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}