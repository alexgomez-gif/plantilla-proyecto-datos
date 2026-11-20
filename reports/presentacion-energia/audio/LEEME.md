# Audios de la presentación

Generados con ElevenLabs a partir de los prompts de la Parte A de `prompts_audio_y_animacion.md`
(efectos con *Sound Effects v3*, ambiente con *Music v2.5*). Flujo en ElevenLabs:
«Energía · audios de la presentación».

## Procesado (ffmpeg)

- Efectos: mono, 44,1 kHz, MP3 128 kbps, normalizados a −18 LUFS, sin silencio al inicio
  (salvo `intro.mp3`, que conserva 0,35 s para quedar sincronizada con el título).
- `chispa1`–`chispa4`: cuatro tomas distintas, igualadas por RMS (son demasiado cortas para medir LUFS).
- `pasa.mp3` / `vuelve.mp3`: la misma toma con paneo de izquierda a derecha y de derecha a izquierda (estéreo).
- `ambiente.mp3`: estéreo, −24 LUFS, loop de 87 s (116 pulsos a 80 BPM) con fundido cruzado de 2 s.
- `sube.mp3` y `pasa.mp3` quedan ~1 dB por debajo del objetivo por el limitador de picos (−1 dBFS).

Si falta algún archivo, `index_5.html` lo sintetiza en el navegador.
