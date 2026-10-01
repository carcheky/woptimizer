# Propuesta OpenSpec: Ampliación de Cobertura de Testing y Contratos de Persistencia (TASK-041)

- **Change ID**: `2026-10-01-testing-quality-expansion-c31`
- **Área**: Testing & Calidad (Ciclo #31)
- **Agente responsable**: `architect-review`
- **Estado**: Propuesto

---

## 1. Contexto y Justificación
En el Área 5 (Testing & Calidad), la robustez del sistema depende de asegurar que todos los casos límite de persistencia, evolución de modelos Pydantic y telemetría de memoria en `ProcessService` tengan pruebas discriminantes sin regresiones.
En particular, `ProcessService.kill_processes` calcula `freed_mb` iterando sobre diccionarios `memory_info` (o objetos con `.rss`), y los modelos `Pack` / `AppData` admiten evoluciones con `extra="allow"`.
Agregar tests headless discriminantes garantizará la estabilidad de la persistencia frente a evoluciones futuras del modelo de datos y cálculo exacto de RSS liberada.

## 2. Objetivos
1. **Tests de Contrato de Persistencia Pydantic (`extra="allow"`)**:
   - Comprobar que atributos adicionales no estándar en `AppData` o `Pack` persisten sin perderse tras ciclos de `save()` y `load()`.
2. **Test de Telemetría RSS & Memory Info**:
   - Validar que `freed_mb` agregue correctamente memoria RSS física (en MB) cuando se reciben dicts o estructuras `memory_info` diversas.
3. **Validación de la Suite**:
   - Elevar la suite de tests en `run_tests.py` a 85 tests en verde.

## 3. Invariantes
- **Ejecución Headless**: Ningún test nuevo debe requerir display visual ni colgar la consola runner.
- **Separación de Capas**: UI no accede a psutil ni a archivos JSON directamente.
