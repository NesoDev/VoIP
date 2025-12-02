# Solución al Problema de Audio

## Problema Identificado

```
WARNING: Unable to find a codec translation path: (ulaw) -> (opus)
```

**Causa:** Linphone estaba negociando diferentes codecs para cada dispositivo (uno usaba OPUS, otro ULAW), y Asterisk no puede transcodificar entre ellos sin módulos adicionales.

**Síntomas:**
- ✅ Llamada se conecta
- ✅ Timbra en ambos lados
- ❌ NO hay audio

## Solución Aplicada

Forzar **ULAW** como único codec en `pjsip.conf.tpl`:

```ini
disallow=all
allow=ulaw
```

Esto garantiza que todos los dispositivos usen el mismo codec.

## Comandos para Actualizar

```bash
# En Lightsail:
git pull
./start.sh

# Vuelve a crear usuarios desde la web UI
# Prueba llamadas - ahora debería escucharse
```

## Verificación

Después de aplicar el fix, los logs deberían mostrar:
```
Got RTP packet from...
Sent RTP packet to...
```

Sin warnings de codec translation.
