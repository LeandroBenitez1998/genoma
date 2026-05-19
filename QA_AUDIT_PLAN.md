# Auditoría de Funcionalidad - Hermes Dashboard

## Contexto del Sistema

| Campo | Descripción |
|-------|-------------|
| **Propósito** | Dashboard de monitoreo y evolución autónoma de agentes IA |
| **Stack** | Next.js / React, TypeScript, Framer Motion |
| **Módulo auditado** | Varias páginas y componentes |

---

## Plan de Auditoría

### 1. Caminos Felices (Happy Path)

| Escenario de Prueba | Resultado Esperado | Riesgo Potencial | Sugerencia de Mejora |
|--------------------|--------------------|--------------------|--------------------|
| Carga inicial del dashboard | Página Overview carga con todas las métricas visibles | Bajo | - |
| Navegación entre páginas via Sidebar | Transición suave entre Overview, Evolution, Metrics, etc. | Bajo | Verificar lazy loading de páginas |
| Inicio de evolución de skill | Modal de Launch Evolution abre correctamente | Medio | Agregar validación de campos requeridos |
| Colapso/expansión del Sidebar | Animación fluida, estado persiste | Bajo | Guardar estado en localStorage |

---

### 2. Casos de Borde (Edge Cases)

| Escenario de Prueba | Resultado Esperado | Riesgo Potencial | Sugerencia de Mejora |
|--------------------|--------------------|--------------------|--------------------|
| API no responde (timeout) | Mostrar mensaje de error con opción de reintentar | Alto | Implementar retry con backoff exponencial |
| Métricas con valores nulos/undefined | Mostrar "N/A" o "-" en lugar de crash | Alto | Agregar default values en fetchMetrics |
| Strings excesivamente largos en logs | Truncar con "..." y tooltip completo | Medio | Implementar ellipsis con hover expandable |
| Sidebar en viewport muy pequeño (<320px) | Ocultar texto, mostrar solo iconos | Medio | Testear en viewport iPhone SE |
| Navegación durante carga de datos | Mostrar loader sin duplicar requests | Medio | Cancelar requests pendientes con AbortController |

---

### 3. Lógica de Negocio

| Escenario de Prueba | Resultado Esperado | Riesgo Potencial | Sugerencia de Mejora |
|--------------------|--------------------|--------------------|--------------------|
| Skill sin nombre | Rechazar con mensaje de validación | Alto | Validación en frontend + backend |
| Permisos insuficientes para acción | Mostrar error 403, deshabilitar botón | Alto | Verificar RBAC en API routes |
| Evolución ya en proceso | Deshabilitar botón "Launch", mostrar estado | Medio | Poll estado hasta completarse |
| Cálculo de métricas (uptime, success rate) | Fórmulas correctas con edge cases (div/0) | Medio | Manejar división por cero |

---

### 4. Consistencia de UI/UX

| Escenario de Prueba | Resultado Esperado | Riesgo Potencial | Sugerencia de Mejora |
|--------------------|--------------------|--------------------|--------------------|
| Tema claro/oscuro (si aplica) | Colores consistentes en todos los componentes | Medio | Crear constantes de tema centralizadas |
| Indicadores de carga | Spinner/skeleton visible durante fetches | Medio | Implementar loading states globales |
| Notificaciones toast | Aparece y desaparece sin romper layout | Bajo | Usar portal para toasts |
| Scroll en listas largas | Performance aceptable sin jank | Medio | Implementar virtualización si >100 items |

---

### 5. Negative Testing

| Escenario de Prueba | Resultado Esperado | Riesgo Potencial | Sugerencia de Mejora |
|--------------------|--------------------|--------------------|--------------------|
| Inyección de código en inputs | Sanitizar output, no ejecutar | Alto | Escapar caracteres especiales |
| Requests malformados a API | Retornar error 400 con mensaje claro | Alto | Validación Zod en API |
| Manipulación de estado via DevTools | Revertir a estado válido | Alto | Verificaciones en backend |
| Carga de archivos binarios como logs | Ignorar o mostrar error | Medio | Validar content-type |

---

### 6. Validación de Estado

| Escenario de Prueba | Resultado Esperado | Riesgo Potencial | Sugerencia de Mejora |
|--------------------|--------------------|--------------------|--------------------|
| Refresco de página | Estado de sidebar persiste, no reinicia | Medio | Sincronizar con URL params o Context |
| Browser back/forward | Historial de navegación funcional | Bajo | - |
| Desconexión de red durante operación | Estado local preservado, sync al reconectar | Alto | Implementar offline queue |

---

## Casos de Prueba - Formato Gherkin

### Feature: Navegación del Dashboard

```gherkin
Feature: Navegación entre páginas
  Scenario: Usuario navega a página de Evolution
    Given Usuario está en OverviewPage
    When Usuario hace click en "Evolution" en el sidebar
    Then URL cambia a /evolution
    And EvolutionPage se muestra con animación de entrada

  Scenario: Usuario colapsa el sidebar
    Given Sidebar está expandido
    When Usuario hace click en botón de colapsar
    Then Sidebar se reduce a iconos
    And Iconos permanecen visibles
```

### Feature: Evolución de Skills

```gherkin
Feature: Launch Evolution
  Scenario: Evolución exitosa
    Given Campos de skill están completos
    When Usuario clickea "Launch Evolution"
    Then Modal muestra loading spinner
    And Botón se deshabilita
    And Después de éxito, mostrar toast "Evolution started"

  Scenario: Campo requerido faltante
    Given Campo "Skill" está vacío
    When Usuario clickea "Launch Evolution"
    Then Mostrar error "Skill es requerido"
    And Modal permanece abierto
```

### Feature: Manejo de Errores

```gherkin
Feature: Respuestas de API
  Scenario: API timeout
    Given API no responde en 10 segundos
    When Usuario está esperando datos
    Then Mostrar "Connection timeout. Retry?"
    And Botón de reintentar visible

  Scenario: Error 500 del servidor
    Given API retorna 500 Internal Server Error
    When Usuario recibe respuesta
    Then Mostrar "Something went wrong"
    And Log error para debugging
```

---

## Priorización de Pruebas

| Prioridad | Tipo de Prueba | Tiempo Estimado |
|----------|--------------|---------------|
| P0 - Crítico | Happy path básico, manejo de errores API | 2h |
| P1 - Alto | Edge cases, validación de estado | 3h |
| P2 - Medio | Negative testing, consistencia UI | 2h |
| P3 - Bajo | Edge cases visuales, optimizaciones | 1h |

---

## Checklist de Ejecución

- [ ] Verificar build pasa sin errores
- [ ] Verificar TypeScript sin errors
- [ ] Probar en viewport móvil (375px, 768px, 1440px)
- [ ] Probar sin conexión de red (Network throttling)
- [ ] Verificar consola sin errores en producción
- [ ] Audit accessibility (contraste, keyboard nav)
- [ ] Verificar performance (LCP < 2.5s)