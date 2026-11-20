"""Produce el audio final de un video infantil para TikTok.

Uso:
    python videos/producir_audio.py videos/listos/<nombre>.json [--musica RUTA]

Necesita:
    ELEVENLABS_API_KEY   clave de ElevenLabs
    ELEVENLABS_VOICE_ID  voz cálida y expresiva (sin él, lista las voces disponibles)
    assets/musica/<animo>/  al menos una pista con licencia
    assets/sfx/             un archivo por "clave" de efecto (p. ej. pop.wav)

Si falta algo, se detiene y lo dice: no inventa assets ni sustituye la voz.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1"
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
TEMPO_MAX = 1.15  # acelerar la voz más que esto suena atropellado


def fallar(msg):
    sys.exit(f"ERROR: {msg}")


def ff(*args):
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True
    )


def duracion(ruta):
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(ruta),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())


def comprobar_entradas(cfg, musica_arg):
    faltan = []
    if not os.environ.get("ELEVENLABS_API_KEY"):
        faltan.append("variable ELEVENLABS_API_KEY")
    if musica_arg:
        musica = Path(musica_arg)
        if not musica.is_file():
            faltan.append(f"música {musica}")
    else:
        carpeta = RAIZ / "assets/musica" / cfg["animo_musica"]
        pistas = sorted(p for p in carpeta.glob("*") if p.suffix.lower() in AUDIO_EXT)
        musica = pistas[0] if pistas else None
        if not musica:
            faltan.append(f"música en {carpeta.relative_to(RAIZ)}/")
    sfx = {}
    for clave in sorted({e["clave"] for e in cfg["efectos"]}):
        hits = sorted(
            p
            for p in (RAIZ / "assets/sfx").glob(f"{clave}*")
            if p.suffix.lower() in AUDIO_EXT
        )
        if hits:
            sfx[clave] = hits[0]
        else:
            faltan.append(f"efecto assets/sfx/{clave}.*")
    if faltan:
        fallar("faltan entradas:\n  - " + "\n  - ".join(faltan))
    return musica, sfx


def elegir_voz(clave):
    voz = os.environ.get("ELEVENLABS_VOICE_ID")
    if voz:
        return voz
    r = requests.get(f"{API}/voices", headers={"xi-api-key": clave}, timeout=30)
    r.raise_for_status()
    print(
        "Voces disponibles (elige una cálida y expresiva, que no imite a nadie famoso):"
    )
    for v in r.json()["voices"]:
        etiquetas = ", ".join(
            f"{k}={val}" for k, val in (v.get("labels") or {}).items()
        )
        print(f"  {v['voice_id']}  {v['name']}  [{etiquetas}]")
    fallar("define ELEVENLABS_VOICE_ID con una de las voces de arriba")


def generar_voz(cfg, carpeta):
    clave = os.environ["ELEVENLABS_API_KEY"]
    voz = elegir_voz(clave)
    guion = cfg["guion"]
    clips = []
    for i, frase in enumerate(guion, 1):
        mp3 = carpeta / f"{i:02d}.mp3"
        if not mp3.exists():
            r = requests.post(
                f"{API}/text-to-speech/{voz}",
                params={"output_format": "mp3_44100_128"},
                headers={"xi-api-key": clave},
                json={
                    "text": frase["texto"],
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.35,
                        "use_speaker_boost": True,
                    },
                    "previous_text": guion[i - 2]["texto"] if i > 1 else None,
                    "next_text": guion[i]["texto"] if i < len(guion) else None,
                },
                timeout=120,
            )
            if r.status_code != 200:
                fallar(
                    f"ElevenLabs respondió {r.status_code} en la frase {i}: "
                    f"{r.text[:300]}"
                )
            mp3.write_bytes(r.content)

        # Ajusta la frase a su ventana; si no cabe ni acelerando un 15 %, avisa.
        hueco = frase["fin"] - frase["inicio"]
        dur = duracion(mp3)
        tempo = min(max(dur / hueco, 1.0), TEMPO_MAX)
        wav = carpeta / f"{i:02d}.wav"
        ff(
            "-i",
            str(mp3),
            "-af",
            f"atempo={tempo:.3f}",
            "-ar",
            "48000",
            "-ac",
            "1",
            str(wav),
        )
        dur_final = dur / tempo
        if dur_final > hueco + 0.3:
            print(
                f"AVISO: frase {i} dura {dur_final:.2f}s y su ventana es {hueco:.2f}s"
            )
        clips.append({**frase, "wav": wav, "dur": dur_final, "tempo": tempo})
    return clips


def pista_voz(clips, total, salida):
    entradas, filtros = [], []
    for k, c in enumerate(clips):
        entradas += ["-i", str(c["wav"])]
        ms = int(c["inicio"] * 1000)
        filtros.append(f"[{k}:a]adelay={ms}|{ms}[v{k}]")
    mezcla = "".join(f"[v{k}]" for k in range(len(clips)))
    filtros.append(
        f"{mezcla}amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{total}[out]"
    )
    ff(
        *entradas,
        "-filter_complex",
        ";".join(filtros),
        "-map",
        "[out]",
        "-ar",
        "48000",
        str(salida),
    )


def premezcla(voz, musica, sfx, efectos, total, salida):
    entradas = ["-i", str(voz), "-stream_loop", "-1", "-i", str(musica)]
    filtros = [
        "[0:a]asplit[voz][sc]",
        f"[1:a]aresample=48000,atrim=0:{total},volume=0.35,"
        f"afade=t=in:d=0.5,afade=t=out:st={total - 2.5}:d=2.5[mus]",
        # Ducking: la música baja cuando habla la voz.
        "[mus][sc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[musd]",
    ]
    etiquetas = ["[voz]", "[musd]"]
    for k, e in enumerate(efectos, start=2):
        entradas += ["-i", str(sfx[e["clave"]])]
        ms = int(e["t"] * 1000)
        filtros.append(
            f"[{k}:a]aresample=48000,afade=t=in:d=0.01,volume={e['vol']},adelay={ms}|{ms}[s{k}]"
        )
        etiquetas.append(f"[s{k}]")
    filtros.append(
        f"{''.join(etiquetas)}amix=inputs={len(etiquetas)}:normalize=0,"
        f"atrim=0:{total},alimiter=limit=0.89:attack=5:release=50[out]"
    )
    ff(
        *entradas,
        "-filter_complex",
        ";".join(filtros),
        "-map",
        "[out]",
        "-ar",
        "48000",
        "-ac",
        "2",
        str(salida),
    )


def normalizar_y_exportar(video, mezcla, total, salida):
    objetivo = "I=-14:TP=-1:LRA=11"
    medida = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(mezcla),
            "-af",
            f"loudnorm={objetivo}:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stderr
    m = json.loads(medida[medida.rindex("{") :])
    ln = (
        f"loudnorm={objetivo}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
        f"offset={m['target_offset']}:linear=true"
    )
    ff(
        "-i",
        str(video),
        "-i",
        str(mezcla),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-af",
        f"{ln},aresample=48000",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-t",
        str(total),
        "-movflags",
        "+faststart",
        str(salida),
    )


def subtitulos(voz, guion, salida):
    from faster_whisper import WhisperModel

    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    pista = " ".join(f["texto"] for f in guion)  # ayuda a Whisper con la ortografía
    segmentos, _ = modelo.transcribe(
        str(voz), language="es", initial_prompt=pista, vad_filter=True
    )

    def ts(s):
        h, rem = divmod(int(s * 1000), 3_600_000)
        m, rem = divmod(rem, 60_000)
        return f"{h:02d}:{m:02d}:{rem // 1000:02d},{rem % 1000:03d}"

    lineas = [
        f"{n}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n"
        for n, s in enumerate(segmentos, 1)
    ]
    salida.write_text("\n".join(lineas), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--musica", help="pista concreta dentro de assets/musica/")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    nombre = Path(args.config).stem
    video = RAIZ / cfg["video"]
    total = cfg["duracion"]
    musica, sfx = comprobar_entradas(cfg, args.musica)

    trabajo = RAIZ / "videos/trabajo" / nombre
    (trabajo / "voz").mkdir(parents=True, exist_ok=True)
    finales = RAIZ / "videos/finales"
    finales.mkdir(parents=True, exist_ok=True)

    clips = generar_voz(cfg, trabajo / "voz")
    voz = trabajo / "voz.wav"
    pista_voz(clips, total, voz)
    mezcla = trabajo / "mezcla.wav"
    premezcla(voz, musica, sfx, cfg["efectos"], total, mezcla)
    final = finales / f"{nombre}_final.mp4"
    normalizar_y_exportar(video, mezcla, total, final)
    srt = finales / f"{nombre}.srt"
    subtitulos(voz, cfg["guion"], srt)

    print(f"\nVideo final: {final.relative_to(RAIZ)}")
    print(f"Subtítulos:  {srt.relative_to(RAIZ)}")
    print(f"Música: {musica.relative_to(RAIZ)}")
    for e in cfg["efectos"]:
        ruta = sfx[e["clave"]].relative_to(RAIZ)
        print(f"  {e['t']:>5.1f}s  {ruta}  ({e['nota']})")
    print("\nGuion con tiempos reales:")
    for c in clips:
        print(
            f"  {c['inicio']:>5.1f}-{c['inicio'] + c['dur']:>5.1f}s  "
            f"x{c['tempo']:.2f}  {c['texto']}"
        )


if __name__ == "__main__":
    main()
