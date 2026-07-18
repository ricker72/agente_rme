<div align="center">

![RME Agente AI](assets/images/rme_agent_ai_banner.png)

# RME Agente AI Alpha

**Plataforma de planificacion, generacion y edicion asistida de mapas OpenTibia**

[![Estado](https://img.shields.io/badge/estado-alpha-C9A227?style=for-the-badge)](#estado-del-proyecto)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](#lenguajes-y-tecnologias)
[![OTBM](https://img.shields.io/badge/formato-OTBM-C96F26?style=for-the-badge)](#compatibilidad)
[![Canary RME](https://img.shields.io/badge/referencia-Canary%20RME-555555?style=for-the-badge)](#fuentes-de-verdad)

[Desarrollador](https://github.com/ricker72) | [Portafolio y noticias](https://ricker72.github.io/)

</div>

## Que es RME Agente AI

RME Agente AI es un proyecto orientado a crear el sucesor asistido por inteligencia artificial de los flujos de trabajo de Remere's Map Editor. Su objetivo no es producir dibujos aproximados ni colocar IDs inventados: busca construir mapas OpenTibia originales mediante materiales oficiales, reglas reales de brushes, edicion transaccional y validacion OTBM.

El proyecto esta formado por dos partes que trabajan en conjunto:

- **Agente RME:** nucleo de planificacion, conocimiento, materiales, brushes, OTBM, render y control de calidad.
- **RME Workspace:** aplicacion de escritorio que funciona como editor visual y como interfaz del agente, con viewport, paletas, historial, metadatos y propuestas de IA revisables.

El proyecto se encuentra en fase **Alpha**. La compatibilidad, el renderizado y las herramientas de edicion continúan evolucionando y se verifican contra Canary's Map Editor y sus fuentes.

## Objetivo principal

Permitir que una persona describa una ciudad, hunt, isla, cueva o region jugable y que el sistema pueda:

1. Interpretar la intencion sin convertir texto directamente en IDs.
2. Diseñar una geometria nueva y jugable mediante el Planner semantico.
3. Seleccionar materiales, grounds, borders, walls y doodads oficiales.
4. Materializar el diseño con brushes compatibles con la gramatica de RME.
5. Mostrar la construccion en un viewport editable con sprites reales.
6. Detectar defectos visuales, repeticiones y problemas de jugabilidad.
7. Aplicar reparaciones mediante transacciones con undo y rollback.
8. Exportar un OTBM compacto y validado para abrirlo en Canary/RME.

## Arquitectura actual

```text
Prompt o edicion humana
        |
        v
Mapper Planner + Scene Graph semantico
        |
        v
Contextual Material Resolver
        |
        v
Ground / Border / Wall / Doodad Brush Engines
        |
        v
Editable Map + transacciones atomicas
        |
        v
OTBM lossless + roundtrip validator
        |
        v
Render sprite-backed + Visual QA + Gameplay QA
        |
        v
Revision humana y exportacion
```

### Nucleo certificado

- Lectura, mutacion copy-on-write y serializacion OTBM.
- Preservacion de payloads OTBM desconocidos durante la edicion.
- Catalogo de materiales compilado desde definiciones oficiales.
- Resolucion contextual de GroundBrush, WallBrush y DoodadBrush.
- AutoBorder basado en mascara completa de ocho vecinos.
- ItemType flags y stacks validados antes de exportar.
- Renderizado independiente de la UI mediante `rme_rendering`.
- QA visual para sprites ausentes, tiles negros, stacks y draw order.

### Planner y aprendizaje controlado

- Planner jerarquico para regiones, rutas, estructuras y gameplay.
- Scene Graph y mascaras semanticas por capas.
- Analisis abstracto de mapas de referencia sin copiar coordenadas.
- Base de conocimiento SQLite con procedencia verificable.
- Ecological Distribution Planner para distribuir familias naturales.
- Density Budget para limitar saturacion y mantener zonas transitables.
- Repetition Critic para detectar dominancia, patrones repetidos y mala separacion.
- Similarity Guard para proteger la originalidad de la geometria generada.
- Ciclo de propuesta, inspeccion, reparacion y aprobacion humana.

### RME Workspace

- Ciclo de vida de documentos y mapas editables.
- Viewport con sprites oficiales, pisos, zoom y navegacion.
- Paletas de terreno, doodads, items, casas, criaturas y RAW.
- Seleccion, copy/paste, fill, replace, undo y redo transaccionales.
- Edicion de towns, houses, zones, waypoints, spawns, NPCs y propiedades.
- Panel AI Studio para generar propuestas y revisar diferencias antes de aplicar cambios.
- Historial de acciones, rollback atomico y validacion visual.

## Fuentes de verdad

RME Agente AI no permite que un modelo invente materiales o IDs. La autoridad tecnica se consulta en este orden:

1. Sources y materiales de Canary/RME.
2. `appearances-*.dat` y `catalog-content.json` del cliente compatible.
3. OTB, ItemType flags y estructura OTBM.
4. Metricas abstractas de `world.otbm` y mapas de referencia autorizados.
5. Reglas del Planner con procedencia almacenada.
6. Sugerencias de modelos locales o cloud.

La salida de una IA es intencion semantica. Solo el Material Resolver y los Brush Engines certificados pueden escoger items concretos.

## Lenguajes y tecnologias

| Area | Tecnologias |
|---|---|
| Nucleo y Planner | Python 3.10+ |
| Aplicacion de escritorio | Python, PySide6 / Qt 6 |
| Persistencia | SQLite, SQL, JSON |
| Materiales OpenTibia | XML, OTB, DAT y catalogos JSON |
| Mapas y gameplay | OTBM, XML y Lua |
| Render | Sprites oficiales, Pillow y servicios `rme_rendering` |
| Herramientas web locales | HTML, CSS y JavaScript |
| Automatizacion | PowerShell y shell scripts |
| Fuentes de referencia | C++ de Canary/RME y reglas auditadas de SharpMapTracker en C# |

## Modelos de IA

El servidor local puede orquestar proveedores configurados por el usuario:

- Ollama local o cloud.
- OpenRouter.
- PaxSenix.
- Modo de consenso entre varios modelos cuando el equipo y la configuracion lo permiten.

Las credenciales no se incluyen en el repositorio. Se obtienen mediante variables de entorno o un almacen seguro del sistema operativo. Ningun modelo puede escribir directamente un ID al mapa ni saltarse los validadores.

## Compatibilidad

El desarrollo esta dirigido a flujos OpenTibia compatibles con:

- OTBM y mapas editables en Canary/RME.
- Materiales y brushes de Canary's Map Editor v4.
- Assets oficiales proporcionados localmente por el usuario.
- Servidores OpenTibia que consuman mapas, spawns, NPCs y scripts compatibles.

Los assets del cliente, mapas de referencia, bases compiladas y builds no se distribuyen dentro del repositorio cuando exceden las politicas de GitHub o sus respectivas licencias.

## Ejecucion para desarrollo

Clona el repositorio y prepara un entorno Python compatible. Los assets oficiales deben seleccionarse localmente; no se descargan ni se incluyen automaticamente.

```powershell
# Interfaz de Agente RME
python rme_ai_studio_launcher.py

# Superficie CLI disponible
python rme.py --help

# Diagnostico del nucleo
python rme.py health
```

La arquitectura detallada y las reglas obligatorias se encuentran en [docs/wiki/README.md](docs/wiki/README.md).

## Estado del proyecto

**RME Agente AI Alpha** esta en desarrollo activo. Ya cuenta con una base funcional para lectura OTBM, materiales, brushes, Planner, render y edicion asistida, pero la paridad total con RME y la generacion autonoma consistente de mapas profesionales siguen siendo objetivos en progreso.

No se considera terminada una funcion por mostrar una interfaz o producir un archivo. Cada bloque debe probarse contra datos oficiales, abrirse correctamente en Canary/RME y superar validaciones visuales, estructurales y de jugabilidad.

## Metas de desarrollo

### Corto plazo

- Completar la paridad interactiva de paletas, menus, shortcuts y herramientas RME.
- Mejorar la fluidez del viewport y la actualizacion incremental de chunks.
- Cerrar la orientacion contextual de walls, mountains, roofs y doodads.
- Fortalecer la generacion de biomas con familias y densidades coherentes.
- Estabilizar las propuestas AI sin bloquear la interfaz.

### Mediano plazo

- Generar ciudades, hunts, cuevas e islas pequeñas con calidad jugable repetible.
- Completar la simulacion de rutas, spawns, zonas seguras y conectividad vertical.
- Ampliar el ciclo de aprendizaje con QA automatica y validacion humana.
- Alcanzar comparacion visual consistente entre Workspace y Canary/RME.

### Vision

Construir un editor OpenTibia moderno donde el usuario y la IA trabajen sobre el mismo mapa en tiempo real: diseñar, observar, corregir, validar y exportar sin abandonar las reglas reales del ecosistema RME.

## Principios del proyecto

- Solo codigo funcional respaldado por fuentes OpenTibia y la wiki del proyecto.
- Prohibido inventar IDs, flags, brushes o resultados de validacion.
- Los mapas de referencia enseñan estilo y metricas; nunca se copia su geometria.
- Toda mutacion importante debe ser transaccional y reversible.
- Las credenciales y datos personales no se almacenan en Git.
- Ningun archivo normal de Git puede alcanzar 95 MiB.
- Los builds antiguos se reemplazan al producir una nueva version valida.

## Desarrollo y autor

RME Agente AI es creado y desarrollado por **Ricker72**.

- GitHub: [github.com/ricker72](https://github.com/ricker72)
- Portafolio: [ricker72.github.io](https://ricker72.github.io/)

En el portafolio se publicaran noticias del desarrollo, futuros parches, herramientas adicionales y avances de RME Workspace.

## Contribuciones

Antes de modificar codigo es obligatorio leer [AGENTS.md](AGENTS.md) y la [wiki tecnica](docs/wiki/README.md). Toda contribucion debe:

1. Identificar la fuente oficial que define el comportamiento.
2. Trabajar sobre la ruta de runtime activa.
3. Evitar datos inventados y motores duplicados.
4. Ejecutar validaciones reales del subsistema modificado.
5. Pasar los controles de secretos y tamaño antes de publicar.

```powershell
python scripts/secret_guard.py --tracked --history
python scripts/github_size_guard.py --tracked --history
```

## Aviso

Tibia es una marca de CipSoft GmbH. RME Agente AI es un proyecto independiente para el ecosistema OpenTibia y no esta afiliado ni respaldado por CipSoft.

<div align="center">

**Diseñar, observar, corregir y exportar mapas OpenTibia con conocimiento real de RME.**

</div>
