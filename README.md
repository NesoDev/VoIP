# VoIP Demo: Asterisk PBX Local

Este proyecto despliega un servidor **Asterisk PBX** en Docker, preconfigurado para demostraciones de VoIP usando softphones estándar (como Linphone).

## Requisitos
*   Docker Desktop (Mac/Windows/Linux)
*   Un Softphone (Linphone, Zoiper, MicroSIP) instalado en tu PC o Móvil.

## Inicio Rápido

1.  **Iniciar el servidor:**
    ```bash
    ./start.sh
    ```
    Este script:
    *   Detectará tu IP local.
    *   Configurará Asterisk automáticamente.
    *   Te mostrará los datos de conexión.

2.  **Conectar Softphones:**
    Usa los datos que muestra el script (Usuario `101` o `201`, Password `1234`, Dominio `TU_IP`).

3.  **Ver Logs en Tiempo Real:**
    Para ver la señalización SIP (INVITE, ACK, BYE) mientras haces llamadas:
    ```bash
    docker logs -f voip-asterisk
    ```

## Estructura
*   `asterisk/`: Archivos de configuración (`pjsip.conf`, `extensions.conf`).
*   `docker-compose.yml`: Definición del contenedor.
*   `start.sh`: Script de automatización.
