# Guía de Conexión 3CX - VoIP Demo

Esta aplicación ahora funciona como un **Softphone SIP real** que se conecta directamente a tu central 3CX usando WebSockets (WSS).

## 1. Requisitos Previos en 3CX

Para que la conexión funcione, necesitas asegurarte de lo siguiente en tu consola de administración 3CX:

1.  **Extensiones**: Debes tener una extensión creada (ej: `101`).
2.  **Habilitar "Disallow use of extension outside the LAN" (Opcional)**: Si estás probando desde fuera de la red local de la PBX, asegúrate de **desmarcar** esta opción en las opciones de la extensión (Pestaña "Options").
3.  **Contraseña SIP**: No uses la contraseña de acceso web. Ve a la pestaña "Phone Provisioning" (o "General" en versiones nuevas) y busca la **SIP Authentication Password**.
4.  **CORS (Importante)**:
    *   3CX por defecto puede bloquear conexiones WebSocket desde dominios desconocidos.
    *   Si tienes acceso root al servidor 3CX (Linux), es posible que necesites ajustar la configuración de Nginx para permitir CORS desde `localhost` o tu dominio de despliegue.
    *   *Nota*: Si no puedes modificar CORS en 3CX, es posible que necesites un proxy inverso, pero intenta primero la conexión directa.

## 2. Ejecutar la Aplicación

### Opción A: Con Docker (Recomendado)
Asegúrate de que Docker Desktop esté corriendo.

```bash
./start.sh
```

### Opción B: Local (Si tienes Python instalado)
Si Docker te da problemas, puedes correr el backend (que ahora es muy ligero) directamente:

```bash
# Instalar dependencias mínimas
pip install fastapi uvicorn websockets

# Ejecutar servidor
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Usar la Aplicación

1.  Abre `http://localhost:8000` en tu navegador.
2.  Verás el formulario de conexión.
3.  Ingresa los datos:
    *   **Display Name**: Tu nombre (ej: `Juan Perez`).
    *   **SIP Extension**: Tu extensión completa (ej: `101` o `101@1453.3cx.cloud`).
    *   **SIP Password**: La contraseña SIP que obtuviste en el paso 1.
    *   **WSS URL**: `ws://localhost:8000/sip-proxy` (¡Importante! Usamos este proxy local para evitar bloqueos de 3CX).

## 4. Verificación

*   **Registro**: Si todo va bien, el indicador pasará a **Verde (Registered)**.
*   **Llamadas**:
    *   Marca el número de otra extensión (ej: `102`) y presiona "Call".
    *   Deberías ver el flujo SIP en la pantalla "Call Details": `INVITE` -> `TRYING` -> `RINGING` -> `OK`.
    *   ¡El audio debería funcionar en ambas direcciones!

## Solución de Problemas

*   **Error "WebSocket Disconnected"**:
    *   Asegúrate de que el backend esté corriendo (`./start.sh`).
    *   El backend actúa como puente hacia 3CX. Si el backend falla, la conexión falla.
*   **Error "Registration Failed"**:
    *   Verifica usuario y contraseña. Recuerda: ¡Contraseña SIP, no la de la web!
