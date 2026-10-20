"""Extrae los textos traducibles y compila las traducciones, sin necesitar GNU gettext.

    python manage.py traducciones extraer   # actualiza locale/en/LC_MESSAGES/django.po
    python manage.py traducciones compilar  # genera django.mo a partir del .po

Flujo para agregar o cambiar textos:
  1. Marca el texto con {% translate %} / {% blocktranslate %} en plantillas o con _() en Python.
  2. Ejecuta "extraer": los textos nuevos aparecen en el .po con msgstr vacío.
  3. Escribe la traducción en inglés en el .po y ejecuta "compilar".
"""
import ast
import re
import struct
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation.template import templatize

IDIOMA = 'en'
CARPETAS_EXCLUIDAS = {'venv', '.venv', 'staticfiles', 'node_modules', '.git', 'docs', 'locale', '__pycache__', 'migrations'}
FUNCIONES = {'_', 'gettext', 'gettext_lazy', 'gettext_noop', 'N_', 'ngettext', 'ngettext_lazy'}
CADENA = r"""u?(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
LLAMADA_PLANTILLA = re.compile(rf"\b(gettext|ngettext|_)\(\s*({CADENA})(?:\s*,\s*({CADENA}))?")


def _ruta_po():
    return Path(settings.BASE_DIR) / 'locale' / IDIOMA / 'LC_MESSAGES' / 'django.po'


def _archivos(extension):
    for ruta in sorted(Path(settings.BASE_DIR).rglob(f'*{extension}')):
        if not CARPETAS_EXCLUIDAS.intersection(ruta.relative_to(settings.BASE_DIR).parts):
            yield ruta


# ---------- extracción ----------

def _de_python(ruta, mensajes):
    arbol = ast.parse(ruta.read_text(encoding='utf-8'))
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = getattr(nodo.func, 'id', None) or getattr(nodo.func, 'attr', None)
        if nombre not in FUNCIONES or not nodo.args:
            continue
        textos = [a.value for a in nodo.args[:2] if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        if not textos:
            continue
        if nombre.startswith('ngettext') and len(textos) == 2:
            mensajes.setdefault((textos[0], textos[1]), ruta)
        else:
            mensajes.setdefault((textos[0], None), ruta)


def _de_plantilla(ruta, mensajes):
    codigo = templatize(ruta.read_text(encoding='utf-8'), origin=str(ruta))
    for funcion, singular, plural in LLAMADA_PLANTILLA.findall(codigo):
        singular = ast.literal_eval(singular)
        plural = ast.literal_eval(plural) if plural and funcion == 'ngettext' else None
        mensajes.setdefault((singular, plural), ruta)


# ---------- formato .po ----------

def _escapar(texto):
    return texto.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')


def _desescapar(texto):
    return ast.literal_eval('"' + texto + '"') if texto else ''


def leer_po(ruta):
    """Devuelve {(msgid, msgid_plural): [msgstr, ...]}."""
    entradas, actual, campo = {}, {}, None
    if not ruta.exists():
        return entradas

    def guardar():
        if 'msgid' in actual:
            clave = (actual['msgid'], actual.get('msgid_plural'))
            formas = [actual[k] for k in sorted(k for k in actual if k.startswith('msgstr'))]
            entradas[clave] = formas

    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#'):
            if not linea and actual:
                guardar()
                actual, campo = {}, None
            continue
        if linea.startswith('"'):
            actual[campo] += _desescapar(linea[1:-1])
            continue
        campo, _, valor = linea.partition(' ')
        if campo == 'msgid' and 'msgid' in actual and any(k.startswith('msgstr') for k in actual):
            guardar()
            actual = {}
        actual[campo] = _desescapar(valor.strip()[1:-1])
    if actual:
        guardar()
    return entradas


def escribir_po(ruta, mensajes, traducciones):
    lineas = [
        '# Traducción al inglés de Gestión de Conjuntos.',
        '# Generado con: python manage.py traducciones extraer',
        'msgid ""',
        'msgstr ""',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Language: en\\n"',
        '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"',
        '',
    ]
    for (singular, plural), origen in sorted(mensajes.items(), key=lambda m: (str(m[1]), m[0][0])):
        formas = traducciones.get((singular, plural), [])
        lineas.append(f'#: {Path(origen).relative_to(settings.BASE_DIR).as_posix()}')
        if '%(' in singular or '%s' in singular:
            lineas.append('#, python-format')
        lineas.append(f'msgid "{_escapar(singular)}"')
        if plural is None:
            lineas.append(f'msgstr "{_escapar(formas[0] if formas else "")}"')
        else:
            lineas.append(f'msgid_plural "{_escapar(plural)}"')
            for i in range(2):
                lineas.append(f'msgstr[{i}] "{_escapar(formas[i] if len(formas) > i else "")}"')
        lineas.append('')
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text('\n'.join(lineas), encoding='utf-8')


def compilar_mo(entradas, ruta_mo):
    """Escribe un .mo (formato GNU gettext) con las entradas traducidas."""
    cabecera = 'Content-Type: text/plain; charset=UTF-8\nLanguage: en\nPlural-Forms: nplurals=2; plural=(n != 1);\n'
    pares = {'': cabecera}
    for (singular, plural), formas in entradas.items():
        if not singular or not any(formas):
            continue
        if plural is None:
            pares[singular] = formas[0]
        else:
            pares[singular + '\0' + plural] = '\0'.join(f or singular for f in formas)

    claves = sorted(pares)
    ids = [k.encode('utf-8') for k in claves]
    strs = [pares[k].encode('utf-8') for k in claves]
    n = len(claves)
    inicio_ids = 7 * 4
    inicio_strs = inicio_ids + n * 8
    datos = inicio_strs + n * 8
    tabla_ids, tabla_strs, cuerpo = [], [], b''
    for texto in ids:
        tabla_ids.append((len(texto), datos + len(cuerpo)))
        cuerpo += texto + b'\0'
    for texto in strs:
        tabla_strs.append((len(texto), datos + len(cuerpo)))
        cuerpo += texto + b'\0'
    salida = struct.pack('<7I', 0x950412de, 0, n, inicio_ids, inicio_strs, 0, 0)
    salida += b''.join(struct.pack('<2I', *t) for t in tabla_ids)
    salida += b''.join(struct.pack('<2I', *t) for t in tabla_strs)
    ruta_mo.write_bytes(salida + cuerpo)
    return n - 1


class Command(BaseCommand):
    help = 'Extrae textos traducibles al .po en inglés o compila el .po a .mo.'

    def add_arguments(self, parser):
        parser.add_argument('accion', choices=['extraer', 'compilar'])

    def handle(self, *args, accion, **options):
        ruta_po = _ruta_po()
        if accion == 'extraer':
            mensajes = {}
            for ruta in _archivos('.py'):
                try:
                    _de_python(ruta, mensajes)
                except (UnicodeDecodeError, SyntaxError):
                    self.stderr.write(f'Se omitió {ruta.name}: no es un archivo Python válido en UTF-8.')
            for ruta in _archivos('.html'):
                _de_plantilla(ruta, mensajes)
            mensajes.pop(('', None), None)
            traducciones = leer_po(ruta_po)
            escribir_po(ruta_po, mensajes, traducciones)
            faltan = sum(1 for clave in mensajes if not any(traducciones.get(clave, [])))
            self.stdout.write(self.style.SUCCESS(f'{len(mensajes)} textos en {ruta_po.name}; {faltan} sin traducir.'))
        else:
            if not ruta_po.exists():
                raise CommandError('No existe el .po. Ejecuta primero: python manage.py traducciones extraer')
            total = compilar_mo(leer_po(ruta_po), ruta_po.with_suffix('.mo'))
            self.stdout.write(self.style.SUCCESS(f'{total} traducciones compiladas en django.mo.'))
