# Guía de Configuración Linphone

Usa estos datos exactos para configurar tus softphones.

## Usuario 1 (Tu PC/Móvil)
*   **Nombre de usuario:** `101`
*   **Contraseña:** `1234`
*   **Dominio:** `TU_IP_LOCAL` (La que muestra ./start.sh)
*   **Nombre para mostrar:** `Alumno 1`
*   **Transporte:** `UDP` (¡Muy importante!)

### Configuración Avanzada (Si la pide)
*   **ID de autenticación:** `101`
*   **SIP Proxy:** `TU_IP_LOCAL` (o dejar vacío si ya pusiste el dominio)
*   **AVPF:** Desactivado (Off)
*   **Encryption:** None (Ninguna)

---

## Usuario 2 (El otro dispositivo)
*   **Nombre de usuario:** `201`
*   **Contraseña:** `1234`
*   **Dominio:** `TU_IP_LOCAL`
*   **Nombre para mostrar:** `Alumno 2`
*   **Transporte:** `UDP`

## Prueba
1. Marca `201` desde el usuario 1.
2. Debería timbrar y tener audio bidireccional.
