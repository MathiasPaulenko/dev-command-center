# DevCommandCenter — Agent Rules & Standards

Documento de referencia para agentes que colaboren en el proyecto. Aplica tanto a código funcional como a la interfaz visual.

---

## 1. Stack & Arquitectura

| Capa | Tecnología | Notas |
|---|---|---|
| Lenguaje | Python 3.12+ | Type hints obligatorios en APIs públicas (`dict`, `list`, `Optional`, `\|` union) |
| UI Framework | PySide6 (Qt6) | Signal-slot nativo; evitar threads manuales para I/O de proceso |
| Base de datos | SQLite + SQLAlchemy 2.0 | ORM con `Mapped[]`, sesiones explícitas con `SessionLocal()` |
| Procesos | `QProcess` (no `subprocess`) | Un `ManagedProcess` por `command_id`; state machine `STOPPED/RUNNING/FAILED` |
| Empaquetado | PyInstaller (futuro) | Evitar dependencias que no sean empaquetables |

### Estructura de carpetas

```
devcommandcenter/
├── __init__.py
├── config.py              # APP_NAME, APP_VERSION, DATABASE_URL
├── database/
│   ├── connection.py        # SessionLocal, init_db, engine
│   └── models.py            # SQLAlchemy ORM models (Command, ExecutionLog)
├── services/
│   ├── command_service.py   # CRUD de comandos
│   ├── execution_log_service.py  # Persistencia de logs de ejecución
│   └── process_service.py   # Gestión de QProcess, señales de estado/salida
├── ui/
│   ├── theme.py             # Paleta, stylesheets, helpers de color
│   ├── main_window.py       # MainWindow + CommandCard
│   ├── log_window.py        # Ventana no-modal de logs por comando
│   └── command_dialog.py    # Modal crear/editar comando
└── utils/
    └── (helpers generales)
tests/
└── test_mvp.py              # Suite mínima de validación
```

**Regla de oro:** cada módulo hace **una** cosa. Si una clase pasa de ~300 líneas, dividir en sub-componentes o helpers.

---

## 2. Convenciones de Código

### Imports
- `from __future__ import annotations` si se usa syntax moderna de uniones.
- Orden: `stdlib` → `third-party` → `first-party` (cada grupo separado por línea en blanco).
- Nunca importar con `*`.

### Naming
| Elemento | Convención | Ejemplo |
|---|---|---|
| Clases | PascalCase | `MainWindow`, `CommandCard` |
| Funciones/variables | snake_case | `load_commands`, `_filter_state` |
| Constantes | UPPER_SNAKE_CASE | `BG_BASE`, `APP_VERSION` |
| Atributos privados | `_prefijo` | `self._cards`, `self._is_running` |
| Señales Qt | camelCase (convención Qt) | `stateChanged`, `outputReady` |

### Type hints
- Todos los parámetros de métodos públicos deben tener tipo.
- Retorno `-> None` en procedimientos; retorno explícito en funciones con valor.
- Usar `dict[str, ...]`, `list[...]`, `\|` en vez de `typing.Dict`, `typing.List`, `Optional`.

### Manejo de sesiones DB
```python
session = SessionLocal()
try:
    service = SomeService(session)
    service.do_work()
finally:
    session.close()
```
Nunca dejar una sesión abierta más allá del scope de la operación.

---

## 3. UI/UX Standards

### Paleta (accesible WCAG AA)
Todos los colores están centralizados en `devcommandcenter/ui/theme.py`. **Nunca hardcodear colores en widgets.**

| Token | Hex | Uso |
|---|---|---|
| `BG_BASE` | `#0d1117` | Fondo principal |
| `BG_SIDEBAR` | `#010409` | Sidebar / topbar |
| `BG_CARD` | `#161b22` | Superficie de tarjetas |
| `BG_ELEVATED` | `#21262d` | Hover, inputs, badges |
| `TEXT_PRIMARY` | `#e6edf3` | Texto principal (~14:1) |
| `TEXT_SECONDARY` | `#9da7b3` | Texto secundario (~6:1) |
| `TEXT_DISABLED` | `#6e7681` | Deshabilitado (~4:1) |
| `GREEN_FILL` | `#238636` | Botón Run (texto blanco ≥4.6:1) |
| `RED_FILL` | `#da3633` | Botón Stop/Delete (texto blanco ≥4.5:1) |
| `ACCENT_FILL` | `#1f6feb` | Botón primario (texto blanco ≥5:1) |

**Reglas de contraste:**
- Texto normal (< 18px) sobre cualquier superficie debe ser ≥ 4.5:1.
- Botones de acción usan **fondo sólido + texto blanco**. Nunca texto del mismo tono que el fondo translúcido.
- Badges de estado usan `BG_ELEVATED` de fondo + borde del color de estado.

### Layout
- **Sidebar izquierdo** (220 px fijo) con filtros de estado.
- **Topbar** con título de página + search box alineado a la derecha.
- **Grid responsive** de tarjetas fijas: `320 × 300 px`.
- Columnas calculadas dinámicamente según ancho disponible (`avail // 336`).
- Reflow automático en `resizeEvent` y `showEvent`.

### Tarjetas (`CommandCard`)
- Barra lateral de acento de 4 px que cambia de color según estado (gris → verde → rojo).
- Nombre en bold, badge de estado a la derecha.
- Chip de comando: `$` verde + comando en texto blanco sobre fondo oscuro.
- Tags como pills con fondo neutro + texto azul claro (`#79c0ff`).
- Botón **Run** verde sólido, **Stop** rojo sólido, **Delete** con hover a rojo sólido.

### Ventanas de logs (`LogWindow`)
- **No-modal** (`QDialog` sin `exec()`; se abre con `show()`).
- Una ventana **por comando**. Soportar múltiples ventanas simultáneas.
- Al abrir un comando que ya terminó, cargar la última ejecución desde BD.
- Al iniciar una nueva ejecución, limpiar el output y marcar timestamp.
- `closeEvent` debe desconectar señales y emitir `finished` para que el owner libere la referencia.

---

## 4. Patrones de Diseño

### Signal-Slot
- `ProcessService` emite señales compartidas (`stateChanged`, `outputReady`, `errorReady`).
- Cada `LogWindow` se conecta a estas señales y filtra por su `command_id`.
- `MainWindow` se conecta a `stateChanged` y `logReady` para actualizar tarjetas y persistir.

### Gestión de procesos
```
ProcessService (singleton) → ManagedProcess (1 por command_id) → QProcess
```
- `start()` → crea `ManagedProcess` si no existe o reemplaza uno detenido.
- `stop()` → `terminate()` + `kill()` forzado a los 3 segundos.
- `get_state()` → devuelve estado actual o `Stopped` si no existe.

### Ciclo de vida de ventanas de logs
```python
# MainWindow mantiene registro
self._log_windows: dict[int, LogWindow] = {}

# Al abrir: reutilizar si existe, sino crear
win = self._log_windows.get(cmd.id)
if win is not None and win.isVisible():
    win.raise_(); return

win = LogWindow(...)
win.finished.connect(lambda: self._log_windows.pop(cmd.id, None))
self._log_windows[cmd.id] = win
win.show()
```

### Filtros en el grid
- `_filter_state`: `"All" | "Running" | "Stopped" | "Failed"`.
- `_filter_text`: búsqueda por nombre, descripción o tag.
- `_apply_filter()` oculta/muestra cards; `_relayout_grid()` recalcula posiciones.

---

## 5. Base de Datos

### Modelos

**Command**
- `id`, `name`, `description`, `working_directory`, `command`, `arguments`, `env_vars`, `auto_run`, `tags`, `created_at`, `updated_at`

**ExecutionLog**
- `id`, `command_id` (indexado), `output`, `error`, `exit_code`, `started_at`, `finished_at`

### Servicios
- `CommandService`: `create`, `get_all`, `get_by_id`, `update`, `delete`
- `ExecutionLogService`: `create`, `get_by_command_id`, `get_latest`

### Migraciones (MVP)
- `init_db()` crea tablas si no existen (`Base.metadata.create_all(bind=engine)`).
- Futuro: Alembic para migraciones formales.

---

## 6. Testing

### Verificación mínima antes de cada commit
```bash
python -m py_compile main.py devcommandcenter/ui/*.py devcommandcenter/services/*.py
tests/test_mvp.py
```

### MVP test (`tests/test_mvp.py`)
- Crea un comando de prueba.
- Verifica persistencia.
- Debe pasar siempre antes de push.

---

## 7. Git Workflow

- **Conventional Commits**:
  - `feat(ui): ...` — nueva funcionalidad UI
  - `fix(logs): ...` — corrección en logs
  - `refactor(services): ...` — mejora de código sin cambiar comportamiento
- Commits atómicos: un cambio lógico por commit.
- Push a `main` tras cada commit verificado.

---

## 8. Lista de Verificación para Cambios UI

Antes de considerar un cambio de UI como completo:

- [ ] Compila sin errores (`python -m py_compile`)
- [ ] Tests pasan (`python tests/test_mvp.py`)
- [ ] Contraste de texto verificado (ningún texto del mismo tono que su fondo)
- [ ] Botones de acción usan fondo sólido + texto blanco
- [ ] Badges de estado legibles (fondo oscuro sólido + borde de color)
- [ ] Grid reflowea correctamente al redimensionar
- [ ] Ventanas de logs se pueden reabrir tras cerrarlas
- [ ] Señales de Qt se conectan/desconectan sin errores al reabrir logs

---

*Última actualización: 2026-06-08*
